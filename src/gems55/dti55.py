"""Exact implementation of the competition metric: the distance-weighted Tversky index.

Transcribed line by line from the official problem description
https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/
(retrieved 2026-10-09).  With R = 300 m = 3 px at 100 m resolution,
k(d) = max(1 - d/R, 0), alpha = 0.2, beta = 0.8:

    TP_w = sum_{g in G}  max_{x: d(x,g) <= R}  p(x) k(d(x,g))
    FP_w = sum_{x: p(x)>0}  p(x) [1 - max_{g in G} k(d(x,g))]
    FN_w = sum_{g in G} [1 - max_{x: d(x,g) <= R} p(x) k(d(x,g))]
    DTI  = TP_w / (TP_w + alpha FP_w + beta FN_w + eps)

Implementation notes
--------------------
* ``FP_w`` uses ``max_g k(d(x,g)) = k(d(x, G))`` i.e. the triangular kernel of the
  Euclidean distance to the nearest ground-truth pixel, from
  ``scipy.ndimage.distance_transform_edt``.
* ``TP_w``/``FN_w`` need, for every truth pixel ``g``, the maximum of
  ``p(x) k(|x - g|)`` over the disk ``|x - g| <= R``.  Because ``k`` depends only
  on the *offset*, that is a weighted max-filter:
  ``M = max_{o: |o| <= R} k(|o|) * shift(p, o)``, evaluated over the 29 offsets
  with ``dx^2 + dy^2 <= 9``.  This is exact, not an approximation.
* ``tests_numeric/test_core.py`` checks the weighted max-filter against a
  brute-force per-truth-pixel loop, exercises the invalid ``TP_w + FP_w = N``
  shortcut, and checks the ratio against the official worked example
  (TP_w = 3.00, FP_w = 1.89, FN_w = 2.00 -> DTI = 0.60).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import ndimage

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
                out.append((dy, dx, max(0.0, 1.0 - d / r_px)))
    return out


def _weighted_max_filter(p: np.ndarray, r_px: float = R_PX) -> np.ndarray:
    """``M[y,x] = max_{|o| <= R} k(|o|) p[y+oy, x+ox]`` (zero outside the array).

    Implemented with slice views so no full-array temporaries are allocated.
    """
    p = np.asarray(p, dtype=np.float64)
    M = np.zeros_like(p, dtype=np.float64)
    ny, nx = p.shape
    for dy, dx, w in kernel_offsets(r_px):
        if w <= 0.0:
            continue
        # destination slice = source slice shifted by (-dy, -dx)
        dy0, dy1 = max(0, -dy), ny - max(0, dy)
        dx0, dx1 = max(0, -dx), nx - max(0, dx)
        if dy1 <= dy0 or dx1 <= dx0:
            continue
        src = p[dy0 + dy : dy1 + dy, dx0 + dx : dx1 + dx]
        dst = M[dy0:dy1, dx0:dx1]
        np.maximum(dst, w * src, out=dst)
    return M


def distance_to_set(mask: np.ndarray) -> np.ndarray:
    """Euclidean distance (in pixels) from every pixel to the nearest True pixel."""
    mask = np.asarray(mask, dtype=bool)
    if not mask.any():
        return np.full(mask.shape, np.inf)
    return ndimage.distance_transform_edt(~mask)


def kernel_credit(truth: np.ndarray, r_px: float = R_PX) -> np.ndarray:
    """``w(x) = max_g k(d(x,g))`` -- the best credit a dot at ``x`` could earn."""
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
    """Return the official pooled DTI from already-pooled components."""
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
    """Distance-weighted Tversky index of ``pred`` against boolean ``truth``.

    ``mask`` optionally restricts both sums to a region (e.g. the withheld blocks
    of a spatial holdout, or the survey footprint).
    """
    p = np.asarray(pred, dtype=np.float64)
    g = np.asarray(truth, dtype=bool)
    if mask is not None:
        m = np.asarray(mask, dtype=bool)
        p = np.where(m, p, 0.0)
        g = g & m

    p = np.clip(p, 0.0, 1.0)
    w = kernel_credit(g, r_px)  # w(x) = max_g k(d(x,g))
    M = _weighted_max_filter(p, r_px)  # M(g) = max_{x: d<=R} p(x) k(d(x,g))

    pos = p > 0.0
    fp_w = float(np.sum(p[pos] * (1.0 - w[pos])))
    tp_w = float(np.sum(M[g]))
    fn_w = float(np.sum(1.0 - M[g]))
    denom = tp_w + alpha * fp_w + beta * fn_w + eps
    return DTIResult(
        dti=float(tp_w / denom),
        tp_w=tp_w,
        fp_w=fp_w,
        fn_w=fn_w,
        n_pred_pos=int(pos.sum()),
        n_truth=int(g.sum()),
    )


def brute_force_dti(
    pred: np.ndarray,
    truth: np.ndarray,
    *,
    alpha: float = ALPHA,
    beta: float = BETA,
    r_px: float = R_PX,
    eps: float = EPS,
) -> DTIResult:
    """Slow, literal transcription of the metric.  Reference for the tests."""
    p = np.clip(np.asarray(pred, dtype=np.float64), 0.0, 1.0)
    g = np.asarray(truth, dtype=bool)
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
    # FP: max over truth of k(d(x,g)) for each predicted pixel
    d = distance_to_set(g)
    w = np.clip(1.0 - d / r_px, 0.0, 1.0)
    pos = p > 0.0
    fp_w = float(np.sum(p[pos] * (1.0 - w[pos])))
    denom = tp_w + alpha * fp_w + beta * fn_w + eps
    return DTIResult(
        dti=float(tp_w / denom),
        tp_w=tp_w,
        fp_w=fp_w,
        fn_w=fn_w,
        n_pred_pos=int(pos.sum()),
        n_truth=int(g.sum()),
    )


def breakeven_credit(
    dti_now: float,
    alpha: float = ALPHA,
    beta: float = BETA,
) -> float:
    """Isolated-pixel marginal threshold, not a general DTI placement rule.

    Under the simplifying assumption that one new unit prediction changes exactly
    one truth pixel by ``w`` (so TP increases by ``w``, FN decreases by ``w``, and
    FP increases by ``1-w``), the score improves when

        w > alpha * DTI / (1 - DTI * (1 - alpha - beta)).

    For the competition's ``alpha + beta == 1`` this reduces to
    ``w > alpha * DTI``.  The official metric's max-over-predictions TP term can
    make one dot affect several nearby truth pixels, and existing predictions can
    prevent any TP increase, so this scalar threshold must not be used as a
    promotion criterion.  Use ``dti`` on the complete raster for exact comparison.
    """
    if not np.isfinite(dti_now) or not 0.0 <= dti_now <= 1.0:
        raise ValueError("dti_now must be finite and in [0, 1]")
    if not np.isfinite(alpha) or not np.isfinite(beta) or alpha < 0.0 or beta < 0.0:
        raise ValueError("alpha and beta must be finite and non-negative")
    denom = 1.0 - dti_now * (1.0 - alpha - beta)
    if denom <= 0.0:
        return float("inf")
    return float(alpha * dti_now / denom)
