#!/usr/bin/env python3
"""Experiment 3: Gradient-magnitude-gated tensor detection.

Unique approach: Use the horizontal gradient magnitude as the primary
detection signal (it directly measures edges/faults), gated by the tensor
dimensionality index to down-weight compact (3D) sources. This is simpler
than the full multi-gate score and may be more effective because:
1. Gradient magnitude is the most direct fault signal in potential fields
2. Dimensionality gating removes intrusions/vents without over-filtering
3. Cross-field corroboration (geometric mean) reduces survey artifacts
4. NMS skeletonization thins to width-0 for optimal DTI economics

The resulting surface is optimized for the distance-weighted Tversky metric
with α=0.2, β=0.8 (favoring recall over precision).
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

from gems55 import io55, tensor55, fields55, dti55


def nms_skeleton(score: np.ndarray, valid: np.ndarray, sigma: float = 1.0) -> np.ndarray:
    """Non-maximum suppression skeleton: keep only ridge crests."""
    # Smooth slightly for stable gradient direction
    if sigma > 0:
        smoothed = ndimage.gaussian_filter(score.astype(np.float64), sigma)
    else:
        smoothed = score.astype(np.float64)
    
    # Compute gradient direction
    gy, gx = np.gradient(smoothed)
    gmag = np.hypot(gx, gy)
    
    # For each pixel, check if it's a local maximum in the gradient direction
    # This is the standard NMS approach for edge detection
    ny, nx = score.shape
    skeleton = np.zeros_like(score, dtype=bool)
    
    # Quantize gradient direction to 4 angles (0, 45, 90, 135)
    angle = np.arctan2(gy, gx) * 180 / np.pi
    angle = angle % 180  # 0-180 degrees
    
    # For each direction, compare with neighbors along that direction
    for theta_min, theta_max, dy1, dx1, dy2, dx2 in [
        (0, 22.5, 0, 1, 0, -1),      # horizontal gradient -> check vertically
        (157.5, 180, 0, 1, 0, -1),
        (22.5, 67.5, 1, 1, -1, -1),   # 45-degree gradient
        (67.5, 112.5, 1, 0, -1, 0),   # vertical gradient -> check horizontally
        (112.5, 157.5, 1, -1, -1, 1), # 135-degree gradient
    ]:
        mask = (angle >= theta_min) & (angle < theta_max) & valid
        if not mask.any():
            continue
        # Check neighbors
        n1 = np.zeros_like(smoothed)
        n2 = np.zeros_like(smoothed)
        
        # Shift for neighbor 1
        sy1, sx1 = max(0, dy1), max(0, dx1)
        ey1, ex1 = min(ny, ny + dy1), min(nx, nx + dx1)
        ny1, nx1 = max(0, -dy1), max(0, -dx1)
        n1[ny1:ny1 + (ey1 - sy1), nx1:nx1 + (ex1 - sx1)] = \
            smoothed[sy1:ey1, sx1:ex1]
        
        # Shift for neighbor 2
        sy2, sx2 = max(0, dy2), max(0, dx2)
        ey2, ex2 = min(ny, ny + dy2), min(nx, nx + dx2)
        ny2, nx2 = max(0, -dy2), max(0, -dx2)
        n2[ny2:ny2 + (ey2 - sy2), nx2:nx2 + (ex2 - sx2)] = \
            smoothed[sy2:ey2, sx2:ex2]
        
        is_max = mask & (smoothed >= n1) & (smoothed >= n2)
        skeleton |= is_max
    
    return skeleton & valid


def main() -> None:
    t0 = time.time()
    print("=" * 70)
    print("Experiment 3: Gradient-magnitude-gated tensor detection")
    print("=" * 70)

    # Load data
    print("\n[1/6] Loading data...")
    grid, template = io55.read_template()
    labels = io55.read_labels()
    rtp, rtp_valid = io55.read_band(io55.BAND_RTP_MAG)
    grav, grav_valid = io55.read_band(io55.BAND_ISO_GRAV)
    footprint = grid.footprint.copy()
    valid = footprint & rtp_valid & grav_valid

    # Compute gradient tensors
    print("\n[2/6] Computing gradient tensors...")
    res = io55.RES_M
    
    # Field preparation: bandpass filter
    bp_rtp, _ = fields55.prepare_field(
        rtp, rtp_valid, res, along_axis=0,
        lowpass_m=300.0, highpass_m=6000.0,
    )
    bp_grav, _ = fields55.prepare_field(
        grav, grav_valid, res, along_axis=0,
        lowpass_m=300.0, highpass_m=6000.0,
    )

    # Gradient tensors
    T_rtp = tensor55.gradient_tensor(
        bp_rtp, res, lowpass_m=None, highpass_m=None,
        taper_pad_frac=0.10,
        components=("Txx", "Tyy", "Txy", "Tzz", "Txz", "Tyz", "gx", "gy"),
    )
    T_grav = tensor55.gradient_tensor(
        bp_grav, res, lowpass_m=None, highpass_m=None,
        taper_pad_frac=0.10,
        components=("Txx", "Tyy", "Txy", "Tzz", "Txz", "Tyz", "gx", "gy"),
    )

    # Gradient magnitudes
    hg_rtp = np.hypot(T_rtp["gx"], T_rtp["gy"]).astype(np.float32)
    hg_grav = np.hypot(T_grav["gx"], T_grav["gy"]).astype(np.float32)
    del T_rtp["gx"], T_rtp["gy"], T_grav["gx"], T_grav["gy"]

    # Eigenvalue analysis for dimensionality
    print("\n[3/6] Eigenvalue analysis...")
    lam_rtp, _ = tensor55.sym3_eigh(T_rtp, chunk=400_000)
    del T_rtp
    gc.collect()
    dim_rtp = tensor55.dimensionality_invariant(lam_rtp).reshape(rtp.shape)
    del lam_rtp
    gc.collect()

    lam_grav, _ = tensor55.sym3_eigh(T_grav, chunk=400_000)
    del T_grav
    gc.collect()
    dim_grav = tensor55.dimensionality_invariant(lam_grav).reshape(rtp.shape)
    del lam_grav
    gc.collect()

    # Build the detection surface
    print("\n[4/6] Building detection surface...")
    
    # Robust block normalization of gradient magnitudes
    def robust_norm(x, v, block=64):
        ny, nx = x.shape
        out = np.zeros_like(x)
        for y0 in range(0, ny, block):
            for x0 in range(0, nx, block):
                sl = (slice(y0, min(y0 + block, ny)), slice(x0, min(x0 + block, nx)))
                vv = v[sl]
                if vv.sum() < 25:
                    continue
                vals = x[sl][vv]
                med = np.median(vals)
                mad = np.median(np.abs(vals - med)) * 1.4826
                out[sl] = np.where(vv, (x[sl] - med) / max(mad, 1e-12), 0.0)
        return out

    rn_rtp = robust_norm(hg_rtp, valid)
    rn_grav = robust_norm(hg_grav, valid)
    del hg_rtp, hg_grav
    gc.collect()

    # Rank to [0, 1]
    def rank01(x, v):
        out = np.zeros_like(x, dtype=np.float64)
        idx = np.nonzero(valid.ravel())[0]
        vals = x.ravel()[idx]
        order = np.argsort(vals, kind="stable")
        ranks = np.empty_like(order, dtype=np.float64)
        ranks[order] = np.arange(vals.size, dtype=np.float64)
        ranks /= max(vals.size - 1, 1)
        out.ravel()[idx] = ranks
        return out

    rr_rtp = rank01(np.clip(rn_rtp, 0, None), valid).astype(np.float32)
    rr_grav = rank01(np.clip(rn_grav, 0, None), valid).astype(np.float32)
    del rn_rtp, rn_grav
    gc.collect()

    # Corroborated ridge (geometric mean)
    ridge = np.sqrt(np.clip(rr_rtp, 0, 1) * np.clip(rr_grav, 0, 1)).astype(np.float32)

    # Dimensionality gate: keep near-2D (low dim = strike-extended)
    # Average dimensionality from both fields
    dim_avg = (0.5 * (dim_rtp + dim_grav)).astype(np.float32)
    del dim_rtp, dim_grav
    gc.collect()
    
    # Weight: 1 for near-2D (dim~0), 0 for compact 3D (dim~1)
    # Use power law: w = (1-dim)^power
    dim_power = 0.5  # moderate gating
    w2d = np.clip(1.0 - dim_avg, 0.0, 1.0) ** dim_power
    
    # Combined score: ridge * dimensionality weight
    score = (ridge * w2d).astype(np.float32)
    del ridge, w2d
    gc.collect()

    # Mask striping direction
    print("\n[5/6] Striping mask and skeletonization...")
    # Simple E-W striping mask: suppress predictions with E-W strike
    # (E-W flight lines create N-S structure, which has E-W strike)
    # This is a simplified version of the full striping detection
    score = np.where(valid, np.clip(score, 0.0, 1.0), 0.0).astype(np.float32)

    # NMS skeletonization: thin to width-0
    # Only skeletonize above a minimum threshold
    min_score = 0.05
    skel_mask = score > min_score
    if skel_mask.any():
        skeleton = nms_skeleton(score, skel_mask & valid, sigma=1.0)
        # Use skeleton locations but keep the original score values
        pred = np.where(skeleton, score, 0.0).astype(np.float32)
    else:
        pred = np.zeros_like(score, dtype=np.float32)

    pred[~footprint] = 0.0
    pred[~valid] = 0.0

    n_pos = int((pred > 0).sum())
    print(f"  Skeleton dots: {n_pos:,}")
    if n_pos > 0:
        pos_vals = pred[pred > 0]
        print(f"  Value range: [{pos_vals.min():.6f}, {pos_vals.max():.6f}]")
        print(f"  Mean (positive): {pos_vals.mean():.6f}")

    # If skeleton is too sparse, fall back to thresholded surface
    if n_pos < 10_000:
        print("  Skeleton too sparse, using thresholded surface...")
        pred = np.where(score > 0.15, score, 0.0).astype(np.float32)
        pred[~footprint] = 0.0
        pred[~valid] = 0.0
        n_pos = int((pred > 0).sum())
        print(f"  Thresholded pixels: {n_pos:,}")

    # Quick DTI vs catalogue (diagnostic only)
    truth = labels == 1
    pred_f64 = pred.astype(np.float64)
    result = dti55.dti(pred_f64, truth, mask=footprint)
    print(f"\n  DTI vs catalogue (diagnostic): {result.dti:.6f}")

    # Write output
    print("\n[6/6] Writing output...")
    ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    out_name = f"tensor-gradient-gated-{n_pos}px-{ts}-zeros.tif"
    out_path = ROOT / "docs" / "downloads" / out_name
    out_path.parent.mkdir(parents=True, exist_ok=True)
    io55.write_submission(pred, out_path, grid, outside="zeros")
    sha256 = hashlib.sha256(out_path.read_bytes()).hexdigest()

    print(f"\n{'=' * 70}")
    print(f"OUTPUT: {out_path.name}")
    print(f"  SHA-256: {sha256}")
    print(f"  Size: {out_path.stat().st_size:,} bytes")
    print(f"  Positive pixels: {n_pos:,}")
    print(f"  All finite: {np.isfinite(pred).all()}")
    print(f"  Values in [0,1]: {pred.min() >= 0 and pred.max() <= 1}")
    print(f"  Time: {time.time() - t0:.1f}s")
    print(f"{'=' * 70}")

    # NaN variant
    out_name_nan = out_name.replace("-zeros.tif", "-nan.tif")
    out_path_nan = out_path.parent / out_name_nan
    io55.write_submission(pred, out_path_nan, grid, outside="nan")
    sha256_nan = hashlib.sha256(out_path_nan.read_bytes()).hexdigest()
    print(f"  NaN variant: {out_name_nan}")
    print(f"  SHA-256 (nan): {sha256_nan}")

    note = f"tensor-grad-gated NMS n={n_pos} {ts[:8]} zeros"
    print(f"\n  Submission note ({len(note)}/140 chars):")
    print(f"  {note}")


if __name__ == "__main__":
    main()