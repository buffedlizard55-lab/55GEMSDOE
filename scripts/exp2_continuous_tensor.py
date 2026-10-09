#!/usr/bin/env python3
"""Experiment 2: Continuous tensor surface (not dotted) with optimized threshold.

This variant uses the full continuous score surface instead of sparse dots.
The DTI metric gives partial credit for predictions near truth (within 300m),
so a wider prediction band captures more truth pixels at the cost of some FP.
With β=0.8 >> α=0.2, recall is more important than precision.

Key difference from Experiment 1:
- Continuous surface (not sparse dots)
- No concordance gate (relaxed)
- Lower highpass (4000m) to include more regional structures
- Optimized threshold to maximize estimated DTI
"""
from __future__ import annotations

import gc
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems55 import io55, tensor55, fields55, lanes55, dti55


def main() -> None:
    t0 = time.time()
    print("=" * 70)
    print("Experiment 2: Continuous tensor surface")
    print("=" * 70)

    # Load data
    print("\n[1/5] Loading data...")
    grid, template = io55.read_template()
    labels = io55.read_labels()
    rtp, rtp_valid = io55.read_band(io55.BAND_RTP_MAG)
    grav, grav_valid = io55.read_band(io55.BAND_ISO_GRAV)
    footprint = grid.footprint.copy()
    valid = footprint & rtp_valid & grav_valid

    # Build tensor lane with wider bandpass
    print("\n[2/5] Building dual-scale tensor lane (wider bandpass)...")
    cfg = lanes55.LaneConfig(
        res_m=io55.RES_M,
        lowpass_m=250.0,
        highpass_m=4000.0,  # wider: include more regional structures
        block_px=64,
        striping_lag_px=60,
        striping_thresh=0.55,
        striping_tol_deg=20.0,
        strike_sigma_deg=30.0,  # wider strike tolerance
        dim_power=0.8,  # less aggressive dim weighting
        dim_variant="invariant",
        combine="corroborated",
        erode_px=4,  # less erosion
        pad_frac=0.10,
        eig_chunk=400_000,
    )

    lane = lanes55.build_multiscale_lane(
        rtp, rtp_valid, grav, grav_valid, footprint,
        cfg=cfg, along_axis=0, scales_m=(250.0, 500.0, 1000.0),
    )
    score = lane.score.copy()
    del lane
    gc.collect()

    print(f"  Score: min={score[footprint].min():.6f}, max={score[footprint].max():.6f}")

    # Threshold optimization: try different thresholds
    print("\n[3/5] Threshold optimization...")
    # We want to find the threshold that maximizes estimated DTI
    # Since we don't know the test truth, we optimize against the catalogue
    # as a proxy (not the actual competition metric, but a diagnostic)
    truth = labels == 1
    thresholds = [0.02, 0.05, 0.08, 0.10, 0.15, 0.20, 0.25, 0.30]
    
    best_dti = 0.0
    best_thresh = 0.10
    
    for thresh in thresholds:
        pred_t = np.where(score > thresh, score, 0.0).astype(np.float64)
        pred_t = np.clip(pred_t, 0.0, 1.0)
        n_pos = int((pred_t > 0).sum())
        if n_pos == 0:
            continue
        result = dti55.dti(pred_t, truth, mask=footprint)
        print(f"  thresh={thresh:.2f}: n_pos={n_pos:>8,}, DTI_vs_cat={result.dti:.6f}")
        if result.dti > best_dti:
            best_dti = result.dti
            best_thresh = thresh

    print(f"\n  Best threshold (vs catalogue): {best_thresh:.2f} (DTI={best_dti:.6f})")
    print(f"  NOTE: This is vs the CATALOGUE, not the test set.")
    print(f"  The actual competition metric scores against NEW faults.")

    # Use a moderate threshold that gives good coverage
    # Lower threshold = more predictions = higher recall but more FP
    # Since β >> α, we favor recall
    use_thresh = max(best_thresh * 0.5, 0.03)  # be more permissive
    print(f"  Using threshold: {use_thresh:.3f}")

    # Build continuous prediction field
    print("\n[4/5] Building continuous prediction field...")
    pred = np.where(score > use_thresh, score, 0.0).astype(np.float32)
    pred = np.clip(pred, 0.0, 1.0)
    
    # Ensure zero outside footprint
    pred[~footprint] = 0.0
    pred[~valid] = 0.0
    
    n_pos = int((pred > 0).sum())
    pos_vals = pred[pred > 0]
    print(f"  Positive pixels: {n_pos:,}")
    print(f"  Value range: [{pos_vals.min():.6f}, {pos_vals.max():.6f}]")
    print(f"  Mean (positive): {pos_vals.mean():.6f}")

    # Write output
    print("\n[5/5] Writing output...")
    ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    n_dots = n_pos
    
    # Zeros-outside variant
    out_name = f"tensor-continuous-{n_dots}px-{ts}-zeros.tif"
    out_path = ROOT / "docs" / "downloads" / out_name
    out_path.parent.mkdir(parents=True, exist_ok=True)
    io55.write_submission(pred, out_path, grid, outside="zeros")
    sha256 = hashlib.sha256(out_path.read_bytes()).hexdigest()

    print(f"\n{'=' * 70}")
    print(f"OUTPUT: {out_path.name}")
    print(f"  SHA-256: {sha256}")
    print(f"  Size: {out_path.stat().st_size:,} bytes")
    print(f"  Positive pixels: {n_pos:,}")
    print(f"  Threshold: {use_thresh:.3f}")
    print(f"  All finite: True")
    print(f"  Values in [0,1]: True")
    print(f"  Time: {time.time() - t0:.1f}s")
    print(f"{'=' * 70}")

    # NaN variant
    out_name_nan = out_name.replace("-zeros.tif", "-nan.tif")
    out_path_nan = out_path.parent / out_name_nan
    io55.write_submission(pred, out_path_nan, grid, outside="nan")
    sha256_nan = hashlib.sha256(out_path_nan.read_bytes()).hexdigest()
    print(f"  NaN variant: {out_name_nan}")
    print(f"  SHA-256 (nan): {sha256_nan}")

    # Metadata
    note = f"tensor-continuous t={use_thresh:.3f} n={n_dots} {ts[:8]} zeros"
    print(f"\n  Submission note ({len(note)}/140 chars):")
    print(f"  {note}")

    meta = {
        "name": f"tensor-continuous-{n_dots}px-{ts}",
        "note": note,
        "experiment": 2,
        "hypothesis": "Continuous tensor surface with wider bandpass and lower threshold",
        "threshold": use_thresh,
        "n_positive_pixels": n_pos,
        "sha256_zeros": sha256,
        "sha256_nan": sha256_nan,
        "timestamp_utc": ts,
    }
    meta_path = out_path.with_suffix(".json")
    meta_path.write_text(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()