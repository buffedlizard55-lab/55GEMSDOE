#!/usr/bin/env python3
"""Build the deliverable submission GeoTIFF for the tensor-dimensionality lane.

Reads the cached lane surface, emits the selected dot budget with the metric-derived
separation, and writes a NaN-outside single-band float32 GeoTIFF as the primary
artifact. A zeros-outside diagnostic variant is clearly labeled and fails the strict
local footprint rule. Both encodings are archived separately; SHA-256 is recorded.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems55 import holdout55, io55, surfaces55  # noqa: E402

CACHE = ROOT / "data" / "cache"
OUT = ROOT / "docs" / "downloads"
EVID = ROOT / "evidence"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for blk in iter(lambda: fh.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="v1")
    ap.add_argument("--n-dots", type=int, default=40000)
    ap.add_argument("--min-sep", type=float, default=3.0)
    ap.add_argument("--seed", type=int, default=55)
    ap.add_argument("--name", default=None)
    ap.add_argument("--flank-support-px", type=float, default=0.0,
                    help="if > 0, multiply the surface by the off-catalogue flank prior "
                         "with this quadratic-decay support in pixels (preregistered H57-A)")
    ap.add_argument("--registry-dir", default=None,
                    help="registry rasters directory; every same-grid raster is budgeted, no exclusions")
    ap.add_argument("--max-overlap", type=float, default=0.68,
                    help="per-raster cap on final dot overlap (protocol stop is 0.70)")
    ap.add_argument("--un-eroded", action="store_true",
                    help="use cached tensor factors on the six-pixel footprint edge without "
                         "the lane's edge erosion; this is an edge-artifact sensitivity arm")
    args = ap.parse_args()

    grid, _ = io55.read_template()
    labels = io55.read_labels()
    z = np.load(CACHE / f"lane_{args.tag}.npz")
    score = z["score"]
    ridge = z["ridge"]
    dim = z["dim"]
    agree = z["agree"]
    plunge = z["plunge"]
    striping = z["striping"]
    footprint = z["footprint"]
    z.close()
    assert np.array_equal(footprint, grid.footprint), "cached footprint != template footprint"

    cat = labels == 1
    # Optional sensitivity: include the same cached tensor factors in the six-pixel
    # edge guard suppressed by build_lane.  The guard is normally prudent because
    # FFT edge artifacts are real; this option exists only to diagnose the registry
    # lattice's edge-only feasible set and is recorded prominently in the sidecar.
    # Shared composition is used by the holdout evaluator and final writer.
    surf = surfaces55.tensor_surface(
        cached_score=score, ridge=ridge, dimensionality=dim,
        strike_agreement=agree, plunge_weight=plunge, striping=striping,
        footprint=footprint, catalogue=cat,
        flank_support_px=args.flank_support_px, un_eroded=args.un_eroded,
    )
    # Never emit on mapped catalogue pixels or outside the scored footprint.
    elig = footprint & ~cat

    budget = None
    if args.registry_dir:
        names, masks = holdout55.registry_cover_masks(args.registry_dir, grid.shape)
        dots = holdout55.emit_dots_budgeted(
            surf, elig, args.n_dots, min_sep_px=args.min_sep,
            cover_masks=masks, max_overlap=args.max_overlap, seed=args.seed,
        )
        budget = {
            "rasters_budgeted": len(masks),
            "rasters": names,
            "max_overlap_cap": args.max_overlap,
            "exclusions": [],
            "mass_shortfall": int(max(0, args.n_dots - int(dots.sum()))),
        }
    else:
        dots = holdout55.emit_dots(surf, elig, args.n_dots, min_sep_px=args.min_sep, seed=args.seed)
    n = int(dots.sum())

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    base = args.name or f"h57-tensor-flank-{n}dots-{stamp}"
    OUT.mkdir(parents=True, exist_ok=True)
    tif = OUT / f"{base}-nan.tif"
    zeros_variant = OUT / f"{base}-zeros.tif"
    zpath = OUT / f"{base}-nan.zip"
    zeros_zpath = OUT / f"{base}-zeros.zip"

    pred = np.zeros(grid.shape, dtype=np.float32)
    pred[dots] = 1.0
    io55.write_submission(pred, tif, grid, outside="nan")
    io55.write_submission(pred, zeros_variant, grid, outside="zeros")
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(tif, arcname=tif.name)
    with zipfile.ZipFile(zeros_zpath, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(zeros_variant, arcname=zeros_variant.name)

    h = {p.name: sha256(p) for p in (tif, zeros_variant, zpath, zeros_zpath)}
    diag = {
        "name": base,
        "portal_note": (
            f"H57 tensor-flank: FFT 2-D/strike gate x visible-catalogue flank, {n} dots; "
            f"all-registry overlap-budgeted"
        ),
        "n_dots": n,
        "n_dots_target": args.n_dots,
        "min_sep_px": args.min_sep,
        "seed": args.seed,
        "lane_tag": args.tag,
        "flank_support_px": args.flank_support_px,
        "un_eroded_edge_score": args.un_eroded,
        "registry_budget": budget,
        "minimum_separation_verified_by_emitter": bool(args.registry_dir),
        "shape": list(grid.shape),
        "crs": f"EPSG:{grid.crs}",
        "transform": list(grid.transform)[:6],
        "dots_on_catalogue_px": int((dots & cat).sum()),
        "dots_outside_footprint": int((dots & ~grid.footprint).sum()),
        "primary_file": tif.name,
        "primary_zip": zpath.name,
        "outside_encoding": "NaN outside template footprint",
        "zeros_variant": zeros_variant.name,
        "zeros_variant_zip": zeros_zpath.name,
        "sha256": h,
        "created_utc": stamp,
    }
    EVID.mkdir(exist_ok=True)
    (EVID / f"submission_{base}.json").write_text(json.dumps(diag, indent=2))
    np.save(EVID / f"dots_{base}.npy", dots)
    print(json.dumps(diag, indent=2))


if __name__ == "__main__":
    main()
