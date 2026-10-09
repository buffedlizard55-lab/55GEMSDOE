#!/usr/bin/env python3
"""Build the deliverable submission GeoTIFF for the tensor-dimensionality lane.

Reads the cached lane surface, emits the holdout-selected dot budget with the
metric-derived separation, and writes a contract-compliant single-band float32
GeoTIFF plus a NaN-outside twin and a zip.  Prints the SHA-256 of every file.
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

from gems55 import dti55, holdout55, io55  # noqa: E402

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
    args = ap.parse_args()

    grid, _ = io55.read_template()
    labels = io55.read_labels()
    z = np.load(CACHE / f"lane_{args.tag}.npz")
    score = z["score"]
    striping = z["striping"]
    footprint = z["footprint"]
    z.close()
    assert np.array_equal(footprint, grid.footprint), "cached footprint != template footprint"

    cat = labels == 1
    # Down-weight (do not forbid) the survey-line artefact so coverage is kept.
    surf = score.astype(np.float32).copy()
    surf[striping] *= 0.25
    # Never emit on a mapped catalogue pixel: expected credit 0, guaranteed FP.
    elig = footprint & ~cat

    dots = holdout55.emit_dots(surf, elig, args.n_dots, min_sep_px=args.min_sep, seed=args.seed)
    n = int(dots.sum())

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    base = args.name or f"h55-tensor2d-strikegate-{n}dots-{stamp}"
    OUT.mkdir(parents=True, exist_ok=True)
    tif = OUT / f"{base}-zeros.tif"
    twin = OUT / f"{base}-nan.tif"
    zpath = OUT / f"{base}-zeros.zip"

    pred = np.zeros(grid.shape, dtype=np.float32)
    pred[dots] = 1.0
    io55.write_submission(pred, tif, grid, outside="zeros")
    io55.write_submission(pred, twin, grid, outside="nan")
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(tif, arcname=tif.name)

    h = {p.name: sha256(p) for p in (tif, twin, zpath)}
    diag = {
        "name": base,
        "portal_note": (
            f"tensor-dim lane: FFT grad-tensor RTP-mag+iso-grav, 2-D/strike-gated ridges, {n} dots"
        ),
        "n_dots": n,
        "n_dots_target": args.n_dots,
        "min_sep_px": args.min_sep,
        "seed": args.seed,
        "lane_tag": args.tag,
        "shape": list(grid.shape),
        "crs": f"EPSG:{grid.crs}",
        "transform": list(grid.transform)[:6],
        "dots_on_catalogue_px": int((dots & cat).sum()),
        "dots_outside_footprint": int((dots & ~grid.footprint).sum()),
        "sha256": h,
        "created_utc": stamp,
    }
    EVID.mkdir(exist_ok=True)
    (EVID / f"submission_{base}.json").write_text(json.dumps(diag, indent=2))
    np.save(EVID / f"dots_{base}.npy", dots)
    print(json.dumps(diag, indent=2))


if __name__ == "__main__":
    main()
