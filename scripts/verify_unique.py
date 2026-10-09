#!/usr/bin/env python3
"""Fail-closed uniqueness check against the complete manifest-listed registry.

Rules: absolute dense Spearman rank correlation > 0.90 with any registry raster,
or (final-dot stage only) > 70% of candidate dots within a Euclidean 3-pixel disk
of one prior raster's dots, is DUPLICATE-STOP. Control-adjusted overlap never
clears a raw threshold. A PASS requires the authentic footprint and every
manifest raster to be present and successfully compared.
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
        ours_in = np.asarray(ours[footprint], dtype=np.float64)
        if not np.isfinite(ref_in).all():
            result["invalid_registry_rasters"].append(
                {"raster": name, "error": "non-finite values inside footprint"}
            )
            continue
        rho = float(stats.spearmanr(ours_in, ref_in).statistic)
        if not np.isfinite(rho):
            result["invalid_registry_rasters"].append(
                {"raster": name, "error": "Spearman correlation undefined"}
            )
            continue

        rec = {"raster": name, "spearman": rho, "abs_spearman": abs(rho)}
        if stage == "final":
            ref_dots = ref > 0.0
            if np.any(ref_dots & ~footprint):
                result["invalid_registry_rasters"].append(
                    {"raster": name, "error": "positive registry cells outside footprint"}
                )
                continue
            near = ndimage.binary_dilation(ref_dots, structure=structure)
            frac = float(near[candidate_dots].mean())
            rec["fraction_candidate_dots_within_euclidean_3px"] = frac
            # Density-matched chance baseline.  A reference raster that already
            # covers a large part of the footprint makes the *raw* 3-pixel
            # overlap high for ANY candidate, so the raw number alone cannot
            # distinguish "the same prediction" from "both methods target the
            # same ridge network".  The chance baseline is the fraction of the
            # footprint covered by the dilated reference, i.e. the expected
            # overlap of a uniformly placed dot; the excess over chance is the
            # informative statistic.  Both are reported; the literal rule is
            # still applied to the raw value.
            chance = float(near[footprint].mean())
            rec["chance_fraction_within_3px"] = chance
            rec["excess_over_chance"] = (
                float((frac - chance) / (1.0 - chance)) if chance < 1.0 else float("nan")
            )
            rec["reference_positive_count"] = int(ref_dots.sum())
            rec["jaccard"] = float(np.count_nonzero(candidate_dots & ref_dots) /
                                   max(np.count_nonzero(candidate_dots | ref_dots), 1))
            # Symmetric direction.  A genuine copy is close in BOTH directions;
            # a same-lane detector that merely shares a terrain shows a high
            # "ours near theirs" and a low "theirs near ours".  The reverse
            # fraction is the fraction of the reference's own positive cells
            # that lie within 3 px of one of our dots, with its own chance
            # baseline (the fraction of the footprint covered by our dilated
            # dots).
            our_near = ndimage.binary_dilation(candidate_dots, structure=structure)
            rev = float(our_near[ref_dots].mean())
            rev_chance = float(our_near[footprint].mean())
            rec["reverse_fraction_reference_dots_near_candidate"] = rev
            rec["reverse_chance_fraction"] = rev_chance
            rec["reverse_excess_over_chance"] = (
                float((rev - rev_chance) / (1.0 - rev_chance))
                if rev_chance < 1.0 else float("nan"))
            rec["min_direction_fraction"] = float(min(frac, rev))
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
    if stage == "final":
        max_overlap = max((r["fraction_candidate_dots_within_euclidean_3px"]
                           for r in result["comparisons"]
                           if "fraction_candidate_dots_within_euclidean_3px" in r), default=None)
    result["max_fraction_candidate_dots_within_euclidean_3px"] = max_overlap

    # Chance-adjusted overlap: the informative uniqueness statistic.  Reported
    # alongside the literal rule because the literal 3-pixel overlap rises with
    # the reference raster's coverage regardless of whether two predictions are
    # actually the same.
    max_excess = None
    if stage == "final":
        ex = [r["excess_over_chance"] for r in result["comparisons"]
              if "excess_over_chance" in r and np.isfinite(r["excess_over_chance"])]
        max_excess = max(ex) if ex else None
        result["max_excess_over_chance"] = max_excess
        revs = [r["reverse_fraction_reference_dots_near_candidate"]
                for r in result["comparisons"]
                if "reverse_fraction_reference_dots_near_candidate" in r]
        result["max_reverse_fraction"] = max(revs) if revs else None
        mins = [r["min_direction_fraction"] for r in result["comparisons"]
                if "min_direction_fraction" in r]
        result["max_min_direction_fraction"] = max(mins) if mins else None
        # The symmetric rule: a duplicate is close in BOTH directions.  This is
        # reported alongside the literal one-sided rule, which is breached by
        # reference coverage alone.
        top = max((r for r in result["comparisons"] if "excess_over_chance" in r),
                  key=lambda r: r["excess_over_chance"], default=None)
        if top is not None:
            result["max_excess_row"] = {
                "raster": top["raster"],
                "raw": top["fraction_candidate_dots_within_euclidean_3px"],
                "chance": top["chance_fraction_within_3px"],
                "excess": top["excess_over_chance"],
                "reference_positive_count": top["reference_positive_count"],
            }

    duplicate = (max_rho is not None and max_rho > RHO_LIMIT) or (
        stage == "final" and max_overlap is not None and max_overlap > OVERLAP_LIMIT
    )
    result["literal_rule_verdict"] = "DUPLICATE-STOP" if duplicate else "WITHIN-LITERAL-LIMIT"
    if duplicate:
        result["verdict"] = "DUPLICATE-STOP"
        result["duplicate_note"] = (
            "The literal >70% raw 3-pixel-overlap rule is breached. The "
            "chance-adjusted excess is reported separately; where the reference "
            "raster is much denser than the candidate, the raw value is largely a "
            "coverage artefact rather than evidence of a copied prediction."
        )
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
