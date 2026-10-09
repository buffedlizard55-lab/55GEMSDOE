"""Hide-and-recover holdout over catalogue fault segments (spatially blocked, quadrant folds)."""
from __future__ import annotations

import numpy as np
from scipy import ndimage
from scipy.stats import rankdata


def segments(labels_pos: np.ndarray):
    """8-connected fault segments of the catalogue raster."""
    lab, n = ndimage.label(labels_pos, structure=np.ones((3, 3), int))
    return lab, n


def quadrant_fold(rows, cols, H, W):
    ns = np.where(rows < H / 2, "N", "S")
    ew = np.where(cols < W / 2, "W", "E")
    return np.char.add(ns, ew)


def auc(pos_scores: np.ndarray, neg_scores: np.ndarray) -> float:
    """Mann-Whitney AUC (ties handled by average ranks)."""
    if len(pos_scores) == 0 or len(neg_scores) == 0:
        return float("nan")
    allv = np.concatenate([pos_scores, neg_scores])
    r = rankdata(allv)
    n1, n0 = len(pos_scores), len(neg_scores)
    return float((r[:n1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def block_bootstrap_ci(TP_pix, FP_pix, FN_pix, block: int = 100, reps: int = 1000, seed: int = 0,
                       alpha=0.2, beta=0.8):
    """Resample spatial blocks (block x block px) with replacement; return (point, lo, hi)."""
    H, W = TP_pix.shape
    nby, nbx = int(np.ceil(H / block)), int(np.ceil(W / block))
    bid = (np.arange(H)[:, None] // block) * nbx + (np.arange(W)[None, :] // block)
    nb = nby * nbx
    tp = np.bincount(bid.ravel(), TP_pix.ravel(), minlength=nb)
    fp = np.bincount(bid.ravel(), FP_pix.ravel(), minlength=nb)
    fn = np.bincount(bid.ravel(), FN_pix.ravel(), minlength=nb)
    point = tp.sum() / (tp.sum() + alpha * fp.sum() + beta * fn.sum() + 1e-12)
    rng = np.random.default_rng(seed)
    vals = np.empty(reps)
    for r in range(reps):
        c = np.bincount(rng.integers(0, nb, nb), minlength=nb).astype(float)
        T, P, N = c @ tp, c @ fp, c @ fn
        vals[r] = T / (T + alpha * P + beta * N + 1e-12)
    return float(point), float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))
