#!/usr/bin/env python3
"""Experiment 1 (surface build): tensor-dimensionality lane surface + products.

Lane protocol (Pedersen & Rasmussen 1990; Beiki & Pedersen 2010):
  * inputs: competition band 2 (reduced-to-pole magnetic anomaly) and band 13
    (isostatic gravity anomaly) only -- no catalogue/label-derived feature;
  * low-pass before differentiating (FFT derivative noise amplification), then
    FFT horizontal + vertical derivatives of each grid;
  * per-pixel eigenstructure -> dimensionality index (0 = strike-extended 2-D,
    1 = compact 3-D) and eigenvector strike;
  * gradient ridges kept where near-2-D AND eigenvector strike agrees with the
    ridge's own orientation; compact 3-D signatures down-weighted;
  * east-west flight-line striping is one-dimensional by construction and is
    masked with a long-lag coherence test in both axis directions.

Memory-frugal two-phase design (the sandbox has ~3 GB RAM): phase 1 computes
and caches per-field tensor products one field at a time; phase 2 combines and
scores them. All intermediates live under ``outputs/`` (gitignored).

This script builds a label-free surface. It is not a holdout and not a score.
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

from gems55 import fields55, io55, lanes55, tensor55  # noqa: E402

OUT = ROOT / "outputs"
FIELDS = ("mag", "grav")


def phase1(cfg: lanes55.LaneConfig, along_axis: int) -> None:
    """Per-field tensor products, cached to ``outputs/products_<field>.npz``."""
    grid, _ = io55.read_template()
    footprint = grid.footprint
    for band, field_name in ((io55.BAND_RTP_MAG, "mag"), (io55.BAND_ISO_GRAV, "grav")):
        t0 = time.time()
        raw, valid_band = io55.read_band(band)
        valid = footprint & valid_band
        print(f"[phase1] field={field_name} band={band} valid={int(valid.sum())}", flush=True)
        P = lanes55._field_products(raw, valid, cfg, along_axis)
        # _field_products returns float32 maps keyed bp, hg, dim_inv, dim_eig,
        # strike, plunge, ridge_az.  Cache them exactly as computed.
        np.savez_compressed(
            OUT / f"products_{field_name}.npz",
            **{k: v for k, v in P.items()},
        )
        del P, raw, valid_band
        import gc
        gc.collect()
        print(f"[phase1] field={field_name} done in {time.time()-t0:.1f}s", flush=True)


def phase2(cfg: lanes55.LaneConfig) -> dict:
    """Combine the two cached fields into the lane score and diagnostics."""
    grid, _ = io55.read_template()
    footprint = grid.footprint
    rtp_raw, rtp_valid = io55.read_band(io55.BAND_RTP_MAG)
    grav_raw, grav_valid = io55.read_band(io55.BAND_ISO_GRAV)
    valid = footprint & rtp_valid & grav_valid

    Pm = dict(np.load(OUT / "products_mag.npz"))
    Pg = dict(np.load(OUT / "products_grav.npz"))
    t0 = time.time()
    products = lanes55._score_products(Pm, Pg, valid, footprint, cfg)
    print(f"[phase2] scoring done in {time.time()-t0:.1f}s", flush=True)

    lane = lanes55.TensorLane(
        cfg=cfg,
        footprint=footprint,
        ridge=products["ridge"],
        dim=products["dim"],
        strike_agree=products["agree"],
        plunge_w=products["plunge"],
        striping_mask=products["striping"],
        strike=products["strike"],
        ridge_az=products["ridge_az"],
        score=products["score"],
        products={k: products[k] for k in (
            "ridge_mag", "ridge_grav", "dim_inv", "dim_eig", "dtheta", "coh_x", "coh_y"
        )},
    )
    np.savez_compressed(
        OUT / "surface.npz",
        score=lane.score,
        ridge=lane.ridge,
        dim=lane.dim,
        agree=lane.strike_agree,
        plunge=lane.plunge_w,
        striping=lane.striping_mask,
        strike=lane.strike,
        ridge_az=lane.ridge_az,
        ridge_mag=lane.products["ridge_mag"],
        ridge_grav=lane.products["ridge_grav"],
        dim_inv=lane.products["dim_inv"],
        dim_eig=lane.products["dim_eig"],
        dtheta=lane.products["dtheta"],
        coh_x=lane.products["coh_x"],
        coh_y=lane.products["coh_y"],
        valid=valid,
    )
    print(f"[phase2] surface cached to {OUT/'surface.npz'}", flush=True)

    s = lane.score[valid]
    return {
        "score_positive_cells": int((lane.score[valid] > 0).sum()),
        "score_valid_cells": int(valid.sum()),
        "score_max": float(s.max()),
        "score_mean_positive": float(s[s > 0].mean()) if (s > 0).any() else 0.0,
        "striping_masked_cells": int(lane.striping_mask[valid].sum()),
        "dim_median": float(np.median(lane.dim[valid])),
        "strike_agree_median": float(np.median(lane.strike_agree[valid])),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--along-axis", type=int, default=1,
                    help="numpy axis along the flight lines (1 = east-west lines)")
    ap.add_argument("--lowpass-m", type=float, default=400.0)
    ap.add_argument("--highpass-m", type=float, default=6000.0)
    ap.add_argument("--phase", choices=("1", "2", "all"), default="all")
    args = ap.parse_args()

    OUT.mkdir(exist_ok=True)
    cfg = lanes55.LaneConfig(lowpass_m=args.lowpass_m, highpass_m=args.highpass_m)

    # Striping diagnostic on the raw RTP band (documentation, not a score).
    grid, _ = io55.read_template()
    x2, v2 = io55.read_band(io55.BAND_RTP_MAG)
    striping = fields55.measure_striping_axis(
        np.where(grid.footprint & v2, x2, np.nan), grid.footprint & v2, cfg.res_m
    )
    (OUT / "striping_measurement.json").write_text(json.dumps(striping, indent=2) + "\n")
    print(f"[striping] measured flight_line_direction={striping['flight_line_direction']} "
          f"(axis={striping['flight_line_axis_numpy']}); using along_axis={args.along_axis}",
          flush=True)

    if args.phase in ("1", "all"):
        phase1(cfg, args.along_axis)
    stats = phase2(cfg)
    (OUT / "surface_stats.json").write_text(json.dumps(stats, indent=2) + "\n")
    print(json.dumps(stats, indent=2), flush=True)


if __name__ == "__main__":
    main()
