#!/usr/bin/env python3
"""Strict surface + final-dot uniqueness check against every registry raster.

Protocol thresholds (fail closed):
  * continuous surface absolute Spearman |rho| > 0.90 => stop;
  * >70% of final positive dots within 3 px (Euclidean) of one registry raster => stop;
  * identical bytes or an incomplete/incompatible registry => stop.

The shared registry must be complete and aligned to the official template. No
raster is silently omitted. Repeat ``--additional`` for archived local predecessor
TIFs; these are measured with the same thresholds but are reported separately from
the shared registry. The random-control overlap uses the same Euclidean distance-
transform statistic as the gate; it is a diagnostic only and never changes verdict.

Pre-placement surface check:
  python scripts/verify_unique.py --surface data/cache/candidate.tif --surface-only \\
      --out evidence/uniqueness_surface.json
Final-dot check:
  python scripts/verify_unique.py docs/downloads/candidate.tif \\
      --surface data/cache/candidate.tif --out evidence/uniqueness_final.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage, stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems55 import io55, registry55  # noqa: E402

REG = ROOT / "registry" / "rasters"
EVID = ROOT / "evidence"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def read_surface(path: Path, key: str) -> np.ndarray:
    if path.suffix.lower() == ".npz":
        with np.load(path) as z:
            if key not in z:
                raise KeyError(f"{key!r} not found in {path}")
            return np.asarray(z[key], dtype=np.float32)
    with rasterio.open(path) as src:
        return src.read(1).astype(np.float32)


def rho_sample(a: np.ndarray, b: np.ndarray, mask: np.ndarray, rng: np.random.Generator) -> float:
    idx = np.flatnonzero(mask.ravel())
    if idx.size > 300_000:
        idx = rng.choice(idx, 300_000, replace=False)
    if idx.size < 10:
        return float("nan")
    r = stats.spearmanr(a.ravel()[idx], b.ravel()[idx]).statistic
    return float(r) if np.isfinite(r) else float("nan")


def aligned(src, grid) -> bool:
    return (
        (src.height, src.width) == grid.shape
        and src.crs is not None
        and src.crs.to_epsg() == grid.crs
        and tuple(src.transform)[:6] == tuple(grid.transform)[:6]
        and src.count == 1
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("tif", type=Path, nargs="?", default=None,
                    help="final candidate GeoTIFF; omit only with --surface-only")
    ap.add_argument("--surface", type=Path, default=None,
                    help="pre-placement continuous surface (.npz or GeoTIFF)")
    ap.add_argument("--surface-key", default="score")
    ap.add_argument("--surface-only", action="store_true",
                    help="run the continuous-surface gate before dot placement")
    ap.add_argument("--additional", type=Path, action="append", default=[],
                    help="extra prior/control raster to check; repeat for each locally archived TIF")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    if args.surface_only and args.tif is not None:
        ap.error("omit the positional TIF when using --surface-only")
    if not args.surface_only and args.tif is None:
        ap.error("provide the candidate TIF, or use --surface-only with --surface")
    if args.surface_only and args.surface is None:
        ap.error("--surface-only requires --surface")

    grid, _ = io55.read_template()
    rng = np.random.default_rng(0)
    incompatible: list[dict] = []
    rows: list[dict] = []
    registry_files = sorted(REG.glob("*.tif"))
    additional_files = [Path(p) for p in args.additional]
    missing_additional = [str(p) for p in additional_files if not p.is_file()]
    if missing_additional:
        raise SystemExit(f"additional comparison raster(s) not found: {missing_additional}")
    comparison_files = [("registry", p) for p in registry_files] + [
        ("local_historical", p) for p in additional_files
    ]

    if args.surface_only:
        candidate_surface = read_surface(args.surface, args.surface_key)
        if candidate_surface.shape != grid.shape:
            raise SystemExit("surface shape does not match the official template")
        candidate_surface = np.nan_to_num(candidate_surface, nan=0.0, posinf=0.0, neginf=0.0)
        candidate_dots = None
        candidate_digest = None
    else:
        assert args.tif is not None
        with rasterio.open(args.tif) as src:
            if not aligned(src, grid):
                raise SystemExit("candidate CRS/shape/transform/band count does not match the official template")
            candidate = src.read(1).astype(np.float32)
        candidate_dots = np.nan_to_num(candidate, nan=0.0, posinf=0.0, neginf=0.0) > 0
        candidate_surface = (
            read_surface(args.surface, args.surface_key) if args.surface else candidate
        )
        if candidate_surface.shape != grid.shape:
            raise SystemExit("surface shape does not match the official template")
        candidate_surface = np.nan_to_num(candidate_surface, nan=0.0, posinf=0.0, neginf=0.0)
        candidate_digest = sha256(args.tif)

    n_ours = 0 if candidate_dots is None else int(candidate_dots.sum())
    yy, xx = (np.array([], dtype=np.int64), np.array([], dtype=np.int64)) if candidate_dots is None else np.nonzero(candidate_dots)
    ctrl = np.zeros(grid.shape, dtype=bool)
    if n_ours:
        pool = np.flatnonzero(grid.footprint.ravel() & ~candidate_dots.ravel())
        if pool.size < n_ours:
            incompatible.append({"registry": "random-control", "reason": "candidate mass exceeds control pool"})
        else:
            ctrl.ravel()[rng.choice(pool, n_ours, replace=False)] = True
    cy, cx = np.nonzero(ctrl)

    for source, path in comparison_files:
        try:
            ref, was_reprojected = registry55.read_on_grid(path, grid)
        except Exception as exc:  # fail closed and disclose the exact unreadable entry
            incompatible.append({"source": source, "raster": path.name, "reason": f"alignment/read error: {exc}"})
            continue

        ref = np.nan_to_num(ref, nan=0.0, posinf=0.0, neginf=0.0)
        ref_pos = ref > 0
        ref_sha = sha256(path)
        close = ndimage.distance_transform_edt(~ref_pos) if ref_pos.any() else np.full(grid.shape, np.inf)
        overlap = float(np.mean(close[yy, xx] <= 3.0)) if n_ours else None
        ref_cover = close <= 3.0
        inter = int((candidate_dots & ref_pos).sum()) if candidate_dots is not None else None
        union = int((candidate_dots | ref_pos).sum()) if candidate_dots is not None else None
        srho = rho_sample(candidate_surface, ref, grid.footprint, rng)
        crho = (
            rho_sample(candidate.astype(np.float32), ref, grid.footprint, rng)
            if candidate_dots is not None else float("nan")
        )
        identical = bool(candidate_digest is not None and ref_sha == candidate_digest)
        duplicate = bool(
            identical
            or (np.isfinite(srho) and abs(srho) > 0.90)
            or (overlap is not None and overlap > 0.70)
        )
        random_overlap = float(ref_cover[cy, cx].mean()) if n_ours else None
        rows.append({
            "source": source,
            "raster": path.name,
            "path": str(path),
            "sha256": ref_sha,
            "reprojected_to_template": bool(was_reprojected),
            "identical_bytes": identical,
            "registry_positive_px": int(ref_pos.sum()),
            "jaccard": (round(inter / max(union, 1), 6) if inter is not None else None),
            "final_dot_overlap_within_3px": (round(overlap, 4) if overlap is not None else None),
            "random_control_overlap_within_3px": (round(random_overlap, 4) if random_overlap is not None else None),
            "overlap_excess_over_random_control": (
                round(overlap - random_overlap, 4)
                if overlap is not None and random_overlap is not None else None
            ),
            "surface_spearman": None if not np.isfinite(srho) else round(srho, 4),
            "final_binary_spearman": None if not np.isfinite(crho) else round(crho, 4),
            "strict_duplicate_flag": duplicate,
        })

    overlaps = [r["final_dot_overlap_within_3px"] for r in rows if r["final_dot_overlap_within_3px"] is not None]
    surface_rhos = [abs(r["surface_spearman"]) for r in rows if r["surface_spearman"] is not None]
    binary_rhos = [abs(r["final_binary_spearman"]) for r in rows if r["final_binary_spearman"] is not None]
    duplicate_rows = [r for r in rows if r["strict_duplicate_flag"]]
    max_overlap = max(overlaps, default=None)
    max_abs_surface = max(surface_rhos, default=None)
    max_binary = max(binary_rhos, default=None)
    registry_rows = [r for r in rows if r["source"] == "registry"]
    local_rows = [r for r in rows if r["source"] == "local_historical"]
    registry_incompatible = [r for r in incompatible if r.get("source") == "registry"]
    local_incompatible = [r for r in incompatible if r.get("source") == "local_historical"]

    if incompatible:
        verdict = "REGISTRY-INCOMPLETE-STOP"
    elif not registry_files:
        verdict = "NO-REGISTRY-FAIL-CLOSED"
    elif not rows:
        verdict = "NO-REGISTRY-FAIL-CLOSED"
    elif duplicate_rows:
        verdict = "DUPLICATE-STOP"
    else:
        verdict = "PASS-SURFACE-UNIQUE" if args.surface_only else "PASS-UNIQUE"

    out = {
        "candidate": "surface-only" if args.surface_only else args.tif.name,
        "candidate_sha256": candidate_digest,
        "candidate_positive_px": n_ours,
        "surface_source": str(args.surface) if args.surface else ("candidate TIF" if args.tif else None),
        "surface_only": bool(args.surface_only),
        "registry_rasters_total": len(registry_files),
        "registry_rasters_scanned": len(registry_rows),
        "registry_rasters_reprojected": sum(bool(r.get("reprojected_to_template")) for r in registry_rows),
        "registry_rasters_incompatible": len(registry_incompatible),
        "local_historical_rasters_total": len(additional_files),
        "local_historical_rasters_scanned": len(local_rows),
        "local_historical_rasters_reprojected": sum(bool(r.get("reprojected_to_template")) for r in local_rows),
        "local_historical_rasters_incompatible": len(local_incompatible),
        "comparison_rasters_total": len(registry_files) + len(additional_files),
        "comparison_rasters_scanned": len(rows),
        "incompatible_registry_entries": incompatible,
        "max_abs_surface_spearman": max_abs_surface,
        "max_abs_final_binary_spearman": max_binary,
        "max_final_dot_overlap_within_3px": max_overlap,
        "thresholds": {"abs_surface_spearman": 0.90, "final_dot_overlap_within_3px": 0.70},
        "strict_duplicate_rows": len(duplicate_rows),
        "strict_verdict": verdict,
        "verdict": verdict,
        "control_adjusted_overlap_is_diagnostic_only": True,
        "rows": sorted(rows, key=lambda r: -(r["final_dot_overlap_within_3px"] or -1.0)),
    }
    dest = args.out or (EVID / ("uniqueness_surface.json" if args.surface_only else "uniqueness.json"))
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=2))
    print(json.dumps({k: v for k, v in out.items() if k != "rows"}, indent=2))
    for row in out["rows"][:8]:
        print(
            f"  {row['raster'][:58]:58s} n={row['registry_positive_px']:7d} "
            f"overlap={row['final_dot_overlap_within_3px']} "
            f"control={row['random_control_overlap_within_3px']} "
            f"surface_rho={row['surface_spearman']} exact={row['identical_bytes']} "
            f"DUP={row['strict_duplicate_flag']}"
        )
    print("VERDICT:", verdict)
    print("wrote", dest)
    raise SystemExit(0 if verdict in ("PASS-SURFACE-UNIQUE", "PASS-UNIQUE") else 2)


if __name__ == "__main__":
    main()
