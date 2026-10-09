"""Distance-weighted Tversky index (DTI) exactly as published by the competition.

Source (verified 2026-10-09): DrivenData problem description,
https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/
  k(d) = max(1 - d/R, 0), R = 300 m (3 px at 100 m)
  TP_w = sum_g max_{x: d(x,g)<=R} p(x) k(d(x,g))
  FP_w = sum_{x: p(x)>0} p(x) [1 - max_g k(d(x,g))]
  FN_w = sum_g [1 - max_{x: d(x,g)<=R} p(x) k(d(x,g))]
  DTI  = TP_w / (TP_w + alpha FP_w + beta FN_w + eps), alpha=0.2, beta=0.8

Worked example from the same page: TP_w=3.00, FP_w=1.89, FN_w=2.00 -> 0.60.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage

ALPHA = 0.2
BETA = 0.8
CELL_M = 100.0
R_M = 300.0
EPS = 1e-12


def kernel_offsets(cell: float = CELL_M, radius: float = R_M):
    """All integer pixel offsets (dy, dx) with non-zero triangular weight, and weight."""
    rpx = int(np.ceil(radius / cell))
    out = []
    for dy in range(-rpx, rpx + 1):
        for dx in range(-rpx, rpx + 1):
            d = cell * np.hypot(dx, dy)
            k = max(1.0 - d / radius, 0.0)
            if k > 0:
                out.append((dy, dx, k))
    return out


def _shift(a: np.ndarray, dy: int, dx: int) -> np.ndarray:
    """out[i, j] = a[i + dy, j + dx], zero outside the array."""
    out = np.zeros_like(a)
    H, W = a.shape
    ys0, ys1 = max(0, -dy), min(H, H - dy)
    xs0, xs1 = max(0, -dx), min(W, W - dx)
    if ys1 > ys0 and xs1 > xs0:
        out[ys0:ys1, xs0:xs1] = a[ys0 + dy:ys1 + dy, xs0 + dx:xs1 + dx]
    return out


def components(p: np.ndarray, gt: np.ndarray, domain: np.ndarray | None = None):
    """Return per-pixel contributions and totals.

    p      : float predictions in [0,1]; NaN treated as 0 (outside footprint).
    gt     : boolean ground-truth mask (True = fault).
    domain : boolean scoring footprint (defaults to all pixels).
    """
    p = np.where(np.isfinite(p), p, 0.0).astype(np.float64)
    gt = gt.astype(bool)
    if domain is None:
        domain = np.ones_like(gt, dtype=bool)
    p = np.where(domain, p, 0.0)
    gt = gt & domain

    # M[g] = max over neighbourhood of p(x) k(d(x,g)) : TP and FN terms, evaluated at ground truth
    M = np.zeros_like(p)
    for dy, dx, k in kernel_offsets():
        # pixel g = (i,j) looks at x = (i+dy, j+dx), so d(x,g) = offset magnitude
        M = np.maximum(M, _shift(p, dy, dx) * k)
    TP_pix = np.where(gt, M, 0.0)
    FN_pix = np.where(gt, 1.0 - M, 0.0)

    # max_g k(d(x,g)) = k(distance to nearest ground-truth pixel), evaluated at predictions
    if gt.any():
        dist_m = ndimage.distance_transform_edt(~gt) * CELL_M
        kmax = np.maximum(1.0 - dist_m / R_M, 0.0)
    else:
        kmax = np.zeros_like(p)
    FP_pix = np.where((p > 0) & domain, p * (1.0 - kmax), 0.0)

    return {
        "TP_pix": TP_pix, "FN_pix": FN_pix, "FP_pix": FP_pix,
        "TP": float(TP_pix.sum()), "FN": float(FN_pix.sum()), "FP": float(FP_pix.sum()),
        "n_gt": int(gt.sum()),
    }


def dti_from_totals(TP: float, FP: float, FN: float, alpha: float = ALPHA, beta: float = BETA) -> float:
    return TP / (TP + alpha * FP + beta * FN + EPS)


def dti(p: np.ndarray, gt: np.ndarray, domain: np.ndarray | None = None) -> float:
    c = components(p, gt, domain)
    return dti_from_totals(c["TP"], c["FP"], c["FN"])
