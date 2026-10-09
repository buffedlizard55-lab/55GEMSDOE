"""Repository-local transcription of the published distance-weighted Tversky metric.

Reference definition: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/
With R = 300 m = 3 px at 100 m resolution, k(d) = max(1 - d/R, 0),
alpha = 0.2, beta = 0.8:

    TP_w = sum_{g in G}  max_{x: d(x,g) <= R}  p(x) k(d(x,g))
    FP_w = sum_{x: p(x)>0}  p(x) [1 - max_{g in G} k(d(x,g))]
    FN_w = sum_{g in G} [1 - max_{x: d(x,g) <= R} p(x) k(d(x,g))]
    DTI  = TP_w / (TP_w + alpha FP_w + beta FN_w + eps)

This is a local code transcription, not the organizer's executable or an
authorized shared evaluator. It has synthetic regression tests but has not been
reconciled with the shared template for promotion use. Never infer
``TP_w + FP_w = N`` or replace the denominator with a count-only expression.

Implementation notes
--------------------
* ``FP_w`` uses ``max_g k(d(x,g)) = k(d(x, G))`` via the Euclidean distance to
  the nearest ground-truth pixel.
* ``TP_w``/``FN_w`` use a weighted max-filter over all integer offsets within
  the 3-pixel Euclidean disk. At radius 3 there are 29 offsets; this is exact for
the stated grid discretization, not an approximation.
* ``tests_numeric/test_core.py`` checks the weighted max-filter against a literal
  brute-force reference on synthetic arrays and checks the published worked
  example arithmetic. These tests do not validate an organizer receipt or
  competition-scale evaluator agreement.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import ndimage

EVALUATOR_VERSION = "gems55.dti55/2.0-local"
ALPHA = 0.2
BETA = 0.8
EPS = 1e-12
R_PX = 3.0  # 300 m at 100 m resolution


def kernel_offsets(r_px: float = R_PX) -> list[tuple[int, int, float]]:
    """Offsets inside the kernel disk with their triangular weights ``k(|o|)``."""
    out = []
    r = int(np.floor(r_px + 1e-9))
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            d = float(np.hypot(dx, dy))
            if d <= r_px + 1e-9:
                out.append((dy, dx, max(1.0 - d / r_px, 0.0)))
    return out


def _weighted_max_filter(pred: np.ndarray, r_px: float = R_PX) -> np.ndarray:
    """For every truth pixel, maximum weighted prediction inside kernel disk."""
    p = np.asarray(pred, dtype=np.float64)
    M = np.zeros_like(p, dtype=np.float64)
    ny, nx = p.shape
    for dy, dx, k in kernel_offsets(r_px):
        if k <= 0.0:
            continue
        # For truth location g=(y,x), sample prediction at x+offset.
        y0, y1 = max(0, -dy), min(ny, ny - dy)
        x0, x1 = max(0, -dx), min(nx, nx - dx)
        if y0 >= y1 or x0 >= x1:
            continue
        M[y0:y1, x0:x1] = np.maximum(
            M[y0:y1, x0:x1],
            k * p[y0 + dy : y1 + dy, x0 + dx : x1 + dx],
        )
    return M


def distance_to_set(mask: np.ndarray) -> np.ndarray:
    """Euclidean distance (in pixels) from every pixel to the nearest True pixel."""
    mask = np.asarray(mask, dtype=bool)
    if not mask.any():
        return np.full(mask.shape, np.inf)
    return ndimage.distance_transform_edt(~mask)


def kernel_credit(truth: np.ndarray, r_px: float = R_PX) -> np.ndarray:
    """``w(x) = max_g k(d(x,g))`` -- best kernel credit near the truth set."""
    d = distance_to_set(truth)
    return np.clip(1.0 - d / r_px, 0.0, 1.0)


@dataclass
class DTIResult:
    dti: float
    tp_w: float
    fp_w: float
    fn_w: float
    n_pred_pos: int
    n_truth: int

    def as_dict(self) -> dict:
        return {
            "dti": self.dti,
            "tp_w": self.tp_w,
            "fp_w": self.fp_w,
            "fn_w": self.fn_w,
            "n_pred_pos": self.n_pred_pos,
            "n_truth": self.n_truth,
        }


def dti_from_totals(
    tp_w: float,
    fp_w: float,
    fn_w: float,
    *,
    alpha: float = ALPHA,
    beta: float = BETA,
    eps: float = EPS,
) -> float:
    """Compute the published weighted Tversky ratio from its three totals."""
    return float(tp_w / (tp_w + alpha * fp_w + beta * fn_w + eps))


def dti(
    pred: np.ndarray,
    truth: np.ndarray,
    *,
    mask: np.ndarray | None = None,
    alpha: float = ALPHA,
    beta: float = BETA,
    r_px: float = R_PX,
    eps: float = EPS,
) -> DTIResult:
    """Local DTI transcription for synthetic tests and diagnostics."""
    p = np.asarray(pred, dtype=np.float64)
    g = np.asarray(truth, dtype=bool)
    if p.shape != g.shape:
        raise ValueError(f"pred shape {p.shape} != truth shape {g.shape}")
    if mask is not None:
        m = np.asarray(mask, dtype=bool)
        if m.shape != p.shape:
            raise ValueError(f"mask shape {m.shape} != pred shape {p.shape}")
        p = np.where(m, p, 0.0)
        g = g & m
    if not np.isfinite(p).all():
        raise ValueError("prediction contains non-finite values")

    p = np.clip(p, 0.0, 1.0)
    w = kernel_credit(g, r_px)
    M = _weighted_max_filter(p, r_px)

    pos = p > 0.0
    fp_w = float(np.sum(p[pos] * (1.0 - w[pos])))
    tp_w = float(np.sum(M[g]))
    fn_w = float(np.sum(1.0 - M[g]))
    return DTIResult(
        dti=dti_from_totals(tp_w, fp_w, fn_w, alpha=alpha, beta=beta, eps=eps),
        tp_w=tp_w,
        fp_w=fp_w,
        fn_w=fn_w,
        n_pred_pos=int(pos.sum()),
        n_truth=int(g.sum()),
    )


def weighted_contribution_maps(
    pred: np.ndarray,
    truth: np.ndarray,
    *,
    mask: np.ndarray | None = None,
    r_px: float = R_PX,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return additive maps for ``TP_w``, ``FP_w``, and ``FN_w``.

    These maps sum to the metric components and are useful in synthetic tests.
    They are not per-prediction credit maps: TP/FN are at truth cells, FP is at
    predicted cells. This local helper is not authorized for promotion evaluation.
    """
    p = np.asarray(pred, dtype=np.float64)
    g = np.asarray(truth, dtype=bool)
    if p.shape != g.shape:
        raise ValueError(f"pred shape {p.shape} != truth shape {g.shape}")
    if mask is not None:
        m = np.asarray(mask, dtype=bool)
        if m.shape != p.shape:
            raise ValueError(f"mask shape {m.shape} != pred shape {p.shape}")
        p = np.where(m, p, 0.0)
        g = g & m
    if not np.isfinite(p).all():
        raise ValueError("prediction contains non-finite values")

    p = np.clip(p, 0.0, 1.0)
    w = kernel_credit(g, r_px)
    M = _weighted_max_filter(p, r_px)
    tp_map = np.where(g, M, 0.0)
    fn_map = np.where(g, 1.0 - M, 0.0)
    fp_map = np.zeros_like(p)
    pos = p > 0.0
    fp_map[pos] = p[pos] * (1.0 - w[pos])
    return tp_map, fp_map, fn_map


def block_bootstrap_ci(
    tp_map: np.ndarray,
    fp_map: np.ndarray,
    fn_map: np.ndarray,
    *,
    block_px: int = 100,
    n_boot: int = 2000,
    seed: int = 0,
    alpha: float = ALPHA,
    beta: float = BETA,
    eps: float = EPS,
) -> dict:
    """Diagnostic percentile interval from resampling additive spatial blocks.

    This interval describes one fixed synthetic prediction/truth pair; it does
    not replace holdout validation and is not a promotion-grade CI. It is included
    for code testing only. At the 100 m grid, 100 pixels represent 10 km.
    """
    tp = np.asarray(tp_map, dtype=np.float64)
    fp = np.asarray(fp_map, dtype=np.float64)
    fn = np.asarray(fn_map, dtype=np.float64)
    if tp.ndim != 2 or tp.shape != fp.shape or tp.shape != fn.shape:
        raise ValueError("TP, FP, and FN maps must have the same 2-D shape")
    if block_px <= 0 or n_boot <= 0:
        raise ValueError("block_px and n_boot must be positive")

    ny, nx = tp.shape
    nby = (ny + block_px - 1) // block_px
    nbx = (nx + block_px - 1) // block_px
    sums = np.zeros((nby * nbx, 3), dtype=np.float64)
    for iy in range(nby):
        y0, y1 = iy * block_px, min((iy + 1) * block_px, ny)
        for ix in range(nbx):
            x0, x1 = ix * block_px, min((ix + 1) * block_px, nx)
            b = iy * nbx + ix
            sl = np.s_[y0:y1, x0:x1]
            sums[b] = (tp[sl].sum(), fp[sl].sum(), fn[sl].sum())
    sums = sums[np.sum(sums, axis=1) > 0.0]
    if sums.shape[0] == 0:
        return {
            "ci95": [float("nan"), float("nan")],
            "block_px": int(block_px),
            "n_blocks": 0,
            "n_boot": int(n_boot),
            "method": "diagnostic percentile bootstrap of spatial-block sums of additive metric terms",
        }

    rng = np.random.default_rng(seed)
    draws = rng.integers(0, sums.shape[0], size=(n_boot, sums.shape[0]))
    totals = sums[draws].sum(axis=1)
    scores = totals[:, 0] / (totals[:, 0] + alpha * totals[:, 1] + beta * totals[:, 2] + eps)
    return {
        "ci95": [float(np.quantile(scores, 0.025)), float(np.quantile(scores, 0.975))],
        "block_px": int(block_px),
        "n_blocks": int(sums.shape[0]),
        "n_boot": int(n_boot),
        "method": "diagnostic percentile bootstrap of spatial-block sums of additive metric terms",
    }


def brute_force_dti(
    pred: np.ndarray,
    truth: np.ndarray,
    *,
    alpha: float = ALPHA,
    beta: float = BETA,
    r_px: float = R_PX,
    eps: float = EPS,
) -> DTIResult:
    """Slow literal reference used only by synthetic regression tests."""
    p = np.asarray(pred, dtype=np.float64)
    g = np.asarray(truth, dtype=bool)
    if p.shape != g.shape:
        raise ValueError(f"pred shape {p.shape} != truth shape {g.shape}")
    if not np.isfinite(p).all():
        raise ValueError("prediction contains non-finite values")
    p = np.clip(p, 0.0, 1.0)
    offs = kernel_offsets(r_px)
    ys, xs = np.nonzero(g)
    tp_w = 0.0
    fn_w = 0.0
    ny, nx = p.shape
    for y, x in zip(ys, xs):
        best = 0.0
        for dy, dx, k in offs:
            yy, xx = y + dy, x + dx
            if 0 <= yy < ny and 0 <= xx < nx:
                best = max(best, k * p[yy, xx])
        tp_w += best
        fn_w += 1.0 - best
    d = distance_to_set(g)
    w = np.clip(1.0 - d / r_px, 0.0, 1.0)
    pos = p > 0.0
    fp_w = float(np.sum(p[pos] * (1.0 - w[pos])))
    return DTIResult(
        dti=dti_from_totals(tp_w, fp_w, fn_w, alpha=alpha, beta=beta, eps=eps),
        tp_w=tp_w,
        fp_w=fp_w,
        fn_w=fn_w,
        n_pred_pos=int(pos.sum()),
        n_truth=int(g.sum()),
    )


def breakeven_credit(dti_now: float, alpha: float = ALPHA) -> float:
    """Conditional single-match threshold, not a generic candidate rule.

    Under isolated assumptions and ``alpha + beta = 1``, a new unit-valued
    prediction changes TP by ``w``, FN by ``-w``, and FP by ``1-w``. The DTI
    denominator increases by alpha, so the addition helps iff
    ``w > alpha * DTI_now``. Overlapping neighborhoods, multiple truths, or
    existing predictions can break these assumptions; use an authorized shared
    evaluator for real candidate selection.
    """
    if not 0.0 <= dti_now <= 1.0:
        raise ValueError("dti_now must be in [0, 1]")
    if alpha < 0.0:
        raise ValueError("alpha must be non-negative")
    return alpha * dti_now
