#!/usr/bin/env python3
"""Write the tensor-lane competition raster.

The lane score is built from the cached geophysical tensor stack only.  The
catalogue (``labels.tif``) is used for exactly one thing: masking the pixels
that are already mapped, because the competition's ground truth is a *new* fault
set, so a prediction sitting on a mapped fault can only ever be a false
positive.

Output contract (problem description, "Submission format")
    * single band, float32, EPSG:32611, 100 m
    * same shape/bounds/transform as the organiser template
    * values in [0, 1] inside the footprint, NaN outside
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from gems55 import dti55, io55, tensor55  # noqa: E402
import evaluate_holdout as EH  # noqa: E402


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", type=Path, default=EH.CACHE)
    ap.add_argument("--arm", type=str, default="tensor_full")
    ap.add_argument("--n-dots", type=int, default=20000)
    ap.add_argument("--min-sep", type=float, default=3.0)
    ap.add_argument("--dilate", type=int, default=0)
    ap.add_argument("--value", type=float, default=1.0)
    ap.add_argument("--name", type=str, default=None)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--holdout-json", type=Path,
                    default=ROOT / "evidence" / "holdout55_v1.json")
    args = ap.parse_args()

    grid, _tmpl = io55.read_template()
    labels = io55.read_labels()
    footprint = np.asarray(grid.footprint, dtype=bool)
    C = EH.load_cache(args.cache)
    S = EH.build_arm_surfaces(C, footprint)
    if args.arm not in S:
        raise SystemExit(f"unknown arm {args.arm}; available: "
                         f"{[k for k in S if not k.startswith('_')]}")
    surf = S[args.arm]
    valid = S["_valid"]

    mapped = (labels == 1) & footprint
    eligible = valid & ~mapped
    dots = EH.emit_dots(surf, eligible, n_dots=args.n_dots,
                        min_sep_px=args.min_sep, dilate_px=args.dilate)
    pred = np.where(dots > 0, float(args.value), 0.0).astype(np.float32)

    # --- integrity assertions before anything is written ------------------- #
    assert pred.shape == grid.shape
    assert not np.any((pred > 0) & ~footprint), "positive cell outside footprint"
    assert not np.any((pred > 0) & mapped), "positive cell on a mapped catalogue pixel"
    inside = pred[footprint]
    assert np.isfinite(inside).all(), "non-finite value inside the footprint"
    assert inside.min() >= 0.0 and inside.max() <= 1.0, "value outside [0,1]"

    out_arr = np.where(footprint, pred, np.nan).astype(np.float32)

    tag = args.name or (f"gems55-{args.arm}-n{args.n_dots}-sep{args.min_sep:g}"
                        f"-d{args.dilate}")
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    outdir = ROOT / "docs" / "downloads"
    outdir.mkdir(parents=True, exist_ok=True)
    out = args.out or (outdir / f"{tag}-{stamp}-nan.tif")
    profile = {
        "driver": "GTiff", "height": grid.height, "width": grid.width, "count": 1,
        "dtype": "float32", "crs": rasterio.crs.CRS.from_epsg(io55.CRS_EPSG),
        "transform": grid.transform, "compress": "lzw", "nodata": float("nan"),
    }
    with rasterio.open(out, "w", **profile) as dst:
        dst.write(out_arr, 1)

    n_pos = int((out_arr > 0).sum())
    rec = {
        "evidence_class": "SUBMISSION-ARTIFACT",
        "built_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "file": str(out.relative_to(ROOT)),
        "sha256": sha256(out),
        "size_bytes": int(out.stat().st_size),
        "arm": args.arm,
        "n_dots_requested": int(args.n_dots),
        "n_positive_cells": n_pos,
        "min_sep_px": float(args.min_sep),
        "dilate_px": int(args.dilate),
        "emit_value": float(args.value),
        "footprint_px": int(footprint.sum()),
        "positive_fraction_of_footprint": n_pos / float(footprint.sum()),
        "mapped_fault_pixels_masked": int(mapped.sum()),
        "cache": str(args.cache),
        "evaluator_version": dti55.EVALUATOR_VERSION,
    }
    meta = out.with_suffix(".json")
    meta.write_text(json.dumps(rec, indent=1))
    print(json.dumps(rec, indent=1))
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
