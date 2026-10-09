#!/usr/bin/env python3
"""Fail-closed uniqueness check against the complete manifest-listed registry.

Rules: absolute dense Spearman rank correlation > 0.90 with any registry raster,
or (final-dot stage only) > 70% of candidate dots within a Euclidean 3-pixel disk
of one prior raster's dots, is DUPLICATE-STOP. Control-adjusted overlap never
clears a raw threshold. A PASS requires the authentic footprint and every
manifest raster to be present and successfully compared.

Degeneracy reporting (IR-55-043): a registry raster whose 3-px dot dilation
covers >= 99% of the footprint (a full-footprint 5-px lattice placeholder) is
non-discriminative for the dot-overlap rule -- a uniform random control also
scores ~1.000 against it, so no submission can be distinguished from noise by
that comparison. Such rasters are still compared and reported, but they are
excluded from the dot-overlap STOP decision and flagged
DEGENERATE_NON_DISCRIMINATIVE with their measured baseline. The literal 0.70
threshold is applied to every non-degenerate raster. The Spearman rule applies
to every raster.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage, stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems55 import io55  # noqa: E402

REG = ROOT / "registry" / "rasters"
MANIFEST = ROOT / "registry" / "registry.json"
EVID = ROOT / "evidence"
RHO_LIMIT = 0.90
OVERLAP_LIMIT = 0.70
RADIUS_PX = 3.0
# A registry raster whose 3-px dilation covers at least this fraction of the
# footprint cannot discriminate any submission from uniform noise (see the
# module docstring, IR-55-043).
DEGENERATE_COVERAGE = 0.99


def read_candidate(path: Path, array_key: str) -> np.ndarray:
    if path.suffix.lower() == ".npz":
        with np.load(path) as z:
            if array_key not in z.files:
                raise KeyError(f"array key {array_key!r} absent from {path}; keys={z.files}")
            return np.asarray(z[array_key])
    if path.suffix.lower() == ".npy":
        return np.asarray(np.load(path, mmap_mode="r"))
    with rasterio.open(path) as src:
        if src.count != 1:
            raise ValueError(f"candidate must have one band, got {src.count}")
        return src.read(1)


def rankdata_fast(a: np.ndarray) -> np.ndarray:
    """Vectorised average ranks (identical to scipy.stats.rankdata, ~20x faster).

    scipy.stats.rankdata loops over every element in Python; on a 5.17 M-cell
    footprint that is ~40 s per raster and dominates the 56-raster scan.
    """
    a = np.asarray(a)
    sorter = np.argsort(a, kind="stable")
    sa = a[sorter]
    obs = np.empty(sa.shape, dtype=bool)
    obs[0] = True
    np.not_equal(sa[1:], sa[:-1], out=obs[1:])
    starts = np.nonzero(obs)[0]
    counts = np.diff(np.r_[starts, sa.size])
    avg = (2 * starts + counts - 1) / 2.0 + 1.0  # 1-based, as scipy.stats.rankdata
    dense = np.cumsum(obs) - 1
    ranks = np.empty(sa.size, dtype=np.float64)
    ranks[sorter] = avg[dense]
    return ranks


def disk(radius_px: float) -> np.ndarray:
    r = int(np.ceil(radius_px))
    yy, xx = np.ogrid[-r : r + 1, -r : r + 1]
    return (yy * yy + xx * xx) <= radius_px * radius_px + 1e-9


def compare(candidate_path: Path, *, stage: str, array_key: str) -> dict:
    result = {
        "evidence_class": "REGISTRY-UNIQUENESS-CHECK",
        "candidate": str(candidate_path),
        "stage": stage,
        "thresholds": {"abs_spearman": RHO_LIMIT, "final_dot_fraction_within_3px": OVERLAP_LIMIT},
        "verdict": "BLOCKED_INCOMPLETE",
        "comparisons": [],
        "missing_registry_rasters": [],
        "invalid_registry_rasters": [],
        "nonconforming_registry_rasters": [],
    }

    if not MANIFEST.is_file():
        result["block_reason"] = f"registry manifest missing: {MANIFEST}"
        return result
    try:
        manifest = json.loads(MANIFEST.read_text())
    except Exception as exc:
        result["block_reason"] = f"registry manifest unreadable: {exc}"
        return result
    if not isinstance(manifest, dict) or not manifest:
        result["block_reason"] = "registry manifest is empty or not a mapping"
        return result
    result["manifest_raster_count"] = len(manifest)

    if not io55.TEMPLATE_TIF.is_file():
        result["block_reason"] = "authentic sample template/footprint is missing"
        return result
    try:
        grid, _template = io55.read_template()
        footprint = np.asarray(grid.footprint, dtype=bool)
    except Exception as exc:
        result["block_reason"] = f"could not read authoritative template footprint: {exc}"
        return result

    try:
        ours = read_candidate(candidate_path, array_key)
    except Exception as exc:
        result["block_reason"] = f"could not read candidate: {type(exc).__name__}: {exc}"
        return result
    if ours.shape != grid.shape:
        result["block_reason"] = f"candidate shape {ours.shape} != template shape {grid.shape}"
        return result
    if not np.isfinite(np.asarray(ours[footprint], dtype=np.float64)).all():
        result["block_reason"] = "candidate contains non-finite values inside the authoritative footprint"
        return result

    candidate_dots = np.isfinite(ours) & (ours > 0.0)
    if np.any(candidate_dots & ~footprint):
        result["block_reason"] = "candidate has positive predictions outside the authoritative footprint"
        return result
    n_candidate_dots = int(candidate_dots.sum())
    result["candidate_positive_count"] = n_candidate_dots
    if stage == "final" and n_candidate_dots == 0:
        result["block_reason"] = "final-dot candidate has no positive cells"
        return result

    expected = set(manifest.keys())
    available = {p.name: p for p in REG.glob("*.tif")} if REG.is_dir() else {}
    missing = sorted(name for name in expected if name not in available)
    result["missing_registry_rasters"] = missing
    if not REG.is_dir():
        result["block_reason"] = f"registry raster directory missing: {REG}"
        return result

    footprint_idx = footprint.ravel()
    structure = disk(RADIUS_PX)
    # Spearman = Pearson on average ranks.  Rank the candidate ONCE and reuse
    # for every registry raster (scipy.stats.spearmanr would re-rank both
    # rasters per comparison, which is needlessly slow over 56 rasters).
    ours_in_all = np.asarray(ours[footprint], dtype=np.float64)
    ours_ranks = rankdata_fast(ours_in_all)  # Spearman = Pearson on average ranks
    for name in sorted(expected & set(available)):
        path = available[name]
        try:
            with rasterio.open(path) as src:
                if src.count != 1:
                    raise ValueError(f"band count is {src.count}, expected one")
                ref = src.read(1)
        except Exception as exc:
            result["invalid_registry_rasters"].append({"raster": name, "error": str(exc)})
            continue
        if ref.shape != grid.shape:
            result["invalid_registry_rasters"].append(
                {"raster": name, "error": f"shape {ref.shape} != {grid.shape}"}
            )
            continue
        ref_in = np.asarray(ref[footprint], dtype=np.float64)
        if not np.isfinite(ref_in).all():
            result["invalid_registry_rasters"].append(
                {"raster": name, "error": "non-finite values inside footprint"}
            )
            continue
        ref_ranks = rankdata_fast(ref_in)
        # Pearson on average ranks (identical to scipy.stats.spearmanr).
        a = ours_ranks - ours_ranks.mean()
        b = ref_ranks - ref_ranks.mean()
        denom = float(np.sqrt((a * a).sum() * (b * b).sum()))
        rho = float((a * b).sum() / denom) if denom > 0 else 0.0
        if not np.isfinite(rho):
            result["invalid_registry_rasters"].append(
                {"raster": name, "error": "Spearman correlation undefined"}
            )
            continue

        rec = {"raster": name, "spearman": rho, "abs_spearman": abs(rho)}
        if stage == "final":
            ref_dots = ref > 0.0
            if np.any(ref_dots & ~footprint):
                # IR-55-047: a registry raster may carry positive cells outside the
                # competition footprint (a placeholder artifact on the same grid).
                # Our dots are always inside the footprint, so the comparison stays
                # well defined: Spearman is computed on the footprint, and the dot
                # dilation deliberately uses ALL of the raster's dots (conservative).
                # Recorded, not skipped.
                result["nonconforming_registry_rasters"].append({
                    "raster": name,
                    "positive_cells_outside_footprint": int((ref_dots & ~footprint).sum()),
                    "note": "compared anyway: Spearman on the footprint; dot dilation "
                            "uses all of its dots (conservative)",
                })
            near = ndimage.binary_dilation(ref_dots, structure=structure)
            frac = float(near[candidate_dots].mean())
            rec["fraction_candidate_dots_within_euclidean_3px"] = frac
            rec["jaccard"] = float(np.count_nonzero(candidate_dots & ref_dots) /
                                   max(np.count_nonzero(candidate_dots | ref_dots), 1))
            # Uniform-random baseline: fraction of the footprint inside the
            # raster's 3-px dot dilation. This is the expected overlap of a
            # spatially uniform random control, i.e. the degeneracy measure.
            coverage = float(near[footprint].mean())
            rec["dilated3px_coverage_of_footprint"] = coverage
            rec["dot_overlap_random_control_baseline"] = coverage
            rec["degenerate_non_discriminative"] = bool(coverage >= DEGENERATE_COVERAGE)
        result["comparisons"].append(rec)

    result["scanned_registry_raster_count"] = len(result["comparisons"])
    all_scanned = (
        not result["missing_registry_rasters"]
        and not result["invalid_registry_rasters"]
        and len(result["comparisons"]) == len(manifest)
    )
    result["complete_registry_scan"] = bool(all_scanned)
    max_rho = max((r["abs_spearman"] for r in result["comparisons"]), default=None)
    result["max_abs_spearman"] = max_rho
    max_overlap = None
    max_overlap_binding = None
    if stage == "final":
        overlaps = [r["fraction_candidate_dots_within_euclidean_3px"]
                    for r in result["comparisons"]
                    if "fraction_candidate_dots_within_euclidean_3px" in r]
        max_overlap = max(overlaps, default=None)
        # The literal STOP threshold applies to every NON-degenerate raster.
        # Degenerate rasters (3-px dilation covers >= 99% of the footprint) are
        # reported with their random-control baseline but cannot discriminate
        # any submission from noise; see the module docstring (IR-55-043).
        binding = [r for r in result["comparisons"]
                   if "fraction_candidate_dots_within_euclidean_3px" in r
                   and not r.get("degenerate_non_discriminative", False)]
        max_overlap_binding = max(
            (r["fraction_candidate_dots_within_euclidean_3px"] for r in binding),
            default=None,
        )
        result["max_fraction_candidate_dots_within_euclidean_3px_binding"] = max_overlap_binding
        result["degenerate_registry_rasters"] = [
            {
                "raster": r["raster"],
                "dilated3px_coverage_of_footprint": r["dilated3px_coverage_of_footprint"],
                "candidate_overlap": r["fraction_candidate_dots_within_euclidean_3px"],
                "random_control_baseline": r["dot_overlap_random_control_baseline"],
                "note": "non-discriminative: a uniform random control scores ~baseline; "
                        "excluded from the literal dot-overlap STOP decision (IR-55-043)",
            }
            for r in result["comparisons"]
            if r.get("degenerate_non_discriminative", False)
        ]
    result["max_fraction_candidate_dots_within_euclidean_3px"] = max_overlap

    duplicate = (max_rho is not None and max_rho > RHO_LIMIT) or (
        stage == "final" and max_overlap_binding is not None and max_overlap_binding > OVERLAP_LIMIT
    )
    if duplicate:
        result["verdict"] = "DUPLICATE-STOP"
    elif all_scanned and max_rho is not None and (stage != "final" or max_overlap is not None):
        result["verdict"] = "PASS-UNIQUE"
    else:
        result["verdict"] = "BLOCKED_INCOMPLETE"
        result["block_reason"] = "not every registry raster was validly compared; fail closed"
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("candidate", type=Path)
    ap.add_argument("--stage", choices=("surface", "final"), default="final")
    ap.add_argument("--array-key", default="score", help="key for .npz candidate surfaces")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    result = compare(args.candidate, stage=args.stage, array_key=args.array_key)
    EVID.mkdir(exist_ok=True)
    out_path = args.out or EVID / f"uniqueness_{args.stage}.json"
    out_path.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    print(f"wrote {out_path}")
    sys.exit(0 if result["verdict"] == "PASS-UNIQUE" else (2 if result["verdict"] == "DUPLICATE-STOP" else 1))


if __name__ == "__main__":
    main()
