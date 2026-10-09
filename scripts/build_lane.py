#!/usr/bin/env python3
"""Build the tensor-dimensionality lane products and cache them.

Outputs data/cache/lane_<tag>.npz with every per-pixel product as float32, plus
data/cache/lane_<tag>.meta.json.  The cache is what ``evaluate_holdout.py`` and
``submission_writer.py`` read, so the surface is computed once and every
experiment downstream sees byte-identical inputs.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems55 import io55, lanes55  # noqa: E402

CACHE = ROOT / "data" / "cache"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="v1")
    ap.add_argument("--lowpass-m", type=float, default=400.0)
    ap.add_argument("--highpass-m", type=float, default=6000.0)
    ap.add_argument("--dim-variant", default="invariant", choices=["invariant", "eigratio"])
    ap.add_argument("--combine", default="corroborated", choices=["corroborated", "max", "mag", "grav"])
    ap.add_argument("--strike-sigma", type=float, default=25.0)
    ap.add_argument("--dim-power", type=float, default=1.0)
    ap.add_argument("--block-px", type=int, default=64)
    ap.add_argument("--along-axis", type=int, default=0, help="numpy axis running along the flight lines")
    args = ap.parse_args()

    t0 = time.time()
    grid, _ = io55.read_template()
    labels = io55.read_labels()
    footprint = grid.footprint
    rtp, rv = io55.read_band(io55.BAND_RTP_MAG)
    grav, gv = io55.read_band(io55.BAND_ISO_GRAV)

    cfg = lanes55.LaneConfig(
        res_m=io55.RES_M,
        lowpass_m=args.lowpass_m,
        highpass_m=args.highpass_m,
        block_px=args.block_px,
        strike_sigma_deg=args.strike_sigma,
        dim_power=args.dim_power,
        dim_variant=args.dim_variant,
        combine=args.combine,
    )
    print(f"[{time.time()-t0:6.1f}s] building lane (combine={cfg.combine}, dim={cfg.dim_variant})", flush=True)
    lane = lanes55.build_lane(rtp, rv, grav, gv, footprint, cfg, along_axis=args.along_axis)
    del rtp, grav

    CACHE.mkdir(parents=True, exist_ok=True)
    out = CACHE / f"lane_{args.tag}.npz"
    payload = {
        "score": lane.score,
        "ridge": lane.ridge.astype(np.float32),
        "dim": lane.dim.astype(np.float32),
        "agree": lane.strike_agree.astype(np.float32),
        "plunge": lane.plunge_w.astype(np.float32),
        "striping": lane.striping_mask,
        "ridge_mag": lane.products["ridge_mag"].astype(np.float32),
        "ridge_grav": lane.products["ridge_grav"].astype(np.float32),
        "dim_inv": lane.products["dim_inv"].astype(np.float32),
        "dim_eig": lane.products["dim_eig"].astype(np.float32),
        "dtheta": lane.products["dtheta"].astype(np.float32),
        "coh_x": lane.products["coh_x"].astype(np.float32),
        "coh_y": lane.products["coh_y"].astype(np.float32),
        "strike": lane.strike.astype(np.float32),
        "ridge_az": lane.ridge_az.astype(np.float32),
        "labels": labels,
        "footprint": footprint,
    }
    np.savez_compressed(out, **payload)
    valid = footprint & ~lane.striping_mask
    meta = {
        "tag": args.tag,
        "config": cfg.__dict__,
        "along_axis": args.along_axis,
        "seconds": round(time.time() - t0, 1),
        "n_footprint": int(footprint.sum()),
        "n_striping_masked": int((footprint & lane.striping_mask).sum()),
        "n_valid": int(valid.sum()),
        "score_stats": {
            "min": float(lane.score.min()),
            "max": float(lane.score.max()),
            "mean": float(lane.score[valid].mean()),
            "p99": float(np.quantile(lane.score[valid], 0.99)),
            "p999": float(np.quantile(lane.score[valid], 0.999)),
            "nonzero": int((lane.score > 0).sum()),
        },
        "dim_stats": {
            "mean": float(lane.dim[valid].mean()),
            "p10": float(np.quantile(lane.dim[valid], 0.10)),
            "p50": float(np.quantile(lane.dim[valid], 0.50)),
            "p90": float(np.quantile(lane.dim[valid], 0.90)),
        },
        "agree_stats": {
            "mean": float(lane.strike_agree[valid].mean()),
            "frac_gt_0p5": float((lane.strike_agree[valid] > 0.5).mean()),
        },
    }
    (CACHE / f"lane_{args.tag}.meta.json").write_text(json.dumps(meta, indent=2))
    print(json.dumps(meta, indent=2))
    print("wrote", out)


if __name__ == "__main__":
    main()
