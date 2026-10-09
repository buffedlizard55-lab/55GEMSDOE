#!/usr/bin/env python3
"""Strict lane-drift/uniqueness check against every registry raster.

The protocol is deliberately fail-closed:
  * continuous candidate surface: absolute Spearman rho > 0.90 => stop;
  * final positive dots: >70% within 3 pixels of one registry raster => stop.

A chance-adjusted overlap is reported as a diagnostic because dense historical
rasters can make the raw test saturate, but it NEVER changes the strict verdict.
No registry pixel is copied into a candidate.
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
from gems55 import io55  # noqa: E402

REG = ROOT / "registry" / "rasters"
EVID = ROOT / "evidence"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def read_surface(path: Path, key: str) -> np.ndarray:
    if path.suffix == ".npz":
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


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("tif", type=Path)
    ap.add_argument("--surface", type=Path, default=None,
                    help="pre-placement continuous surface (.npz or GeoTIFF)")
    ap.add_argument("--surface-key", default="score")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    grid, _ = io55.read_template()
    with rasterio.open(args.tif) as src:
        ours = src.read(1).astype(np.float32)
        if (src.height, src.width) != grid.shape:
            raise SystemExit("candidate shape does not match the official template")
    dots = np.nan_to_num(ours, nan=0.0) > 0
    n_ours = int(dots.sum())
    yy, xx = np.nonzero(dots)
    surface = read_surface(args.surface, args.surface_key) if args.surface else ours
    if surface.shape != grid.shape:
        raise SystemExit("surface shape does not match the official template")
    surface = np.nan_to_num(surface, nan=0.0, posinf=0.0, neginf=0.0)

    rng = np.random.default_rng(0)
    rows: list[dict] = []
    registry_files = sorted(REG.glob("*.tif"))
    for path in registry_files:
        with rasterio.open(path) as src:
            if (src.width, src.height) != (grid.width, grid.height):
                continue
            ref = src.read(1).astype(np.float32)
        ref = np.nan_to_num(ref, nan=0.0)
        ref_pos = ref > 0
        if not ref_pos.any():
            continue
        close = ndimage.distance_transform_edt(~ref_pos)
        overlap = float(np.mean(close[yy, xx] <= 3.0)) if n_ours else float("nan")
        inter = int((dots & ref_pos).sum())
        union = int((dots | ref_pos).sum())
        srho = rho_sample(surface, ref, grid.footprint, rng)
        crho = rho_sample(ours, ref, grid.footprint, rng)
        rows.append({
            "raster": path.name,
            "sha256": sha256(path),
            "registry_positive_px": int(ref_pos.sum()),
            "jaccard": round(inter / max(union, 1), 6),
            "final_dot_overlap_within_3px": round(overlap, 4),
            "surface_spearman": None if not np.isfinite(srho) else round(srho, 4),
            "final_binary_spearman": None if not np.isfinite(crho) else round(crho, 4),
            "strict_duplicate_flag": bool(
                (np.isfinite(srho) and abs(srho) > 0.90) or
                (np.isfinite(overlap) and overlap > 0.70)
            ),
        })

    max_overlap = max((r["final_dot_overlap_within_3px"] for r in rows), default=float("nan"))
    max_abs_surface = max(
        (abs(r["surface_spearman"]) for r in rows if r["surface_spearman"] is not None),
        default=float("nan"),
    )
    max_binary = max(
        (abs(r["final_binary_spearman"]) for r in rows if r["final_binary_spearman"] is not None),
        default=float("nan"),
    )
    # Diagnostic only; never used to override strict_duplicate_flag.
    ctrl = np.zeros(grid.shape, dtype=bool)
    pool = np.flatnonzero(grid.footprint.ravel() & ~dots.ravel())
    if n_ours and pool.size >= n_ours:
        ctrl.ravel()[rng.choice(pool, n_ours, replace=False)] = True
    cy, cx = np.nonzero(ctrl)
    for row in rows:
        with rasterio.open(REG / row["raster"]) as src:
            ref_pos = np.nan_to_num(src.read(1), nan=0.0) > 0
        row["random_control_overlap_within_3px"] = round(
            float(ndimage.binary_dilation(ref_pos, iterations=3)[cy, cx].mean()), 4
        ) if n_ours else None
        row["overlap_excess_over_random_control"] = round(
            row["final_dot_overlap_within_3px"] - row["random_control_overlap_within_3px"], 4
        ) if n_ours else None

    duplicate_rows = [r for r in rows if r["strict_duplicate_flag"]]
    if not rows:
        verdict = "NO-REGISTRY-FAIL-CLOSED"
    elif duplicate_rows:
        verdict = "DUPLICATE-STOP"
    else:
        verdict = "PASS-UNIQUE"
    out = {
        "candidate": args.tif.name,
        "candidate_sha256": sha256(args.tif),
        "candidate_positive_px": n_ours,
        "surface_source": str(args.surface) if args.surface else args.tif.name,
        "registry_rasters_scanned": len(rows),
        "max_abs_surface_spearman": None if not np.isfinite(max_abs_surface) else round(max_abs_surface, 4),
        "max_abs_final_binary_spearman": None if not np.isfinite(max_binary) else round(max_binary, 4),
        "max_final_dot_overlap_within_3px": None if not np.isfinite(max_overlap) else round(max_overlap, 4),
        "thresholds": {"abs_surface_spearman": 0.90, "final_dot_overlap_within_3px": 0.70},
        "strict_duplicate_rows": len(duplicate_rows),
        "strict_verdict": verdict,
        "verdict": verdict,
        "control_adjusted_overlap_is_diagnostic_only": True,
        "rows": sorted(rows, key=lambda r: -r["final_dot_overlap_within_3px"]),
    }
    dest = args.out or (EVID / "uniqueness.json")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=2))
    print(json.dumps({k: v for k, v in out.items() if k != "rows"}, indent=2))
    for row in out["rows"][:8]:
        print(
            f"  {row['raster'][:58]:58s} n={row['registry_positive_px']:7d} "
            f"overlap={row['final_dot_overlap_within_3px']:.3f} "
            f"control={row['random_control_overlap_within_3px']:.3f} "
            f"surface_rho={row['surface_spearman']} "
            f"DUP={row['strict_duplicate_flag']}"
        )
    print("VERDICT:", verdict)
    print("wrote", dest)
    # A duplicate or unavailable registry is a deliberate non-zero stop signal.
    raise SystemExit(0 if verdict == "PASS-UNIQUE" else 2)


if __name__ == "__main__":
    main()
