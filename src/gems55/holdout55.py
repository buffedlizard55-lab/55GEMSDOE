"""Repository-local synthetic/support utilities for the DOE GEMS lane.

A future authorized protocol requires whole 8-connected mapped components,
a buffer from visible labels, exact visible-fault masking, and a score-independent
random arm. These local helpers are not certified as the authorized shared
holdout/evaluator and must not be used for promotion before reconciliation.
``make_folds`` is retained only to read historical quadrant experiments;
``make_segment_folds`` assigns complete components but is only a local prototype.
``greedy_cover`` maximizes a coverage surrogate, not the official DTI ratio.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import ndimage

from . import dti55
from .dti55 import kernel_offsets

__all__ = ["Fold", "make_folds", "make_segment_folds", "emit_dots", "strike_of_segments", "auc"]


@dataclass
class Fold:
    name: str
    withheld: np.ndarray  # bool, withheld truth plus its buffer (emission domain)
    visible: np.ndarray   # bool, visible catalogue pixels outside the buffer
    truth: np.ndarray     # bool, whole withheld catalogue components


def make_folds(
    labels: np.ndarray,
    footprint: np.ndarray,
    *,
    grid: tuple[int, int] = (2, 2),
    buffer_px: int = 3,
) -> list[Fold]:
    """Legacy contiguous-region folds; not a whole-segment holdout.

    ``grid=(2, 2)`` gives 4 quadrants. A connected fault crossing a boundary is
    split between folds, so these folds are retained only for historical
    reproducibility and are not valid promotion evidence. Use
    :func:`make_segment_folds` for new hide-and-recover evaluations.
    """
    ny, nx = labels.shape
    by = ny // grid[0]
    bx = nx // grid[1]
    blocks = np.zeros((ny, nx), dtype=np.int16)
    for i in range(grid[0]):
        for j in range(grid[1]):
            sl = (slice(i * by, (i + 1) * by if i < grid[0] - 1 else ny),
                  slice(j * bx, (j + 1) * bx if j < grid[1] - 1 else nx))
            blocks[sl] = i * grid[1] + j
    cat = labels == 1
    folds = []
    for b in range(grid[0] * grid[1]):
        withheld = blocks == b
        truth = cat & withheld
        if truth.sum() == 0:
            continue
        buf = ndimage.binary_dilation(truth, iterations=buffer_px)
        visible = cat & ~withheld & ~buf
        folds.append(Fold(name=f"fold{b}", withheld=withheld, visible=visible, truth=truth))
    return folds


def emit_dots(
    score: np.ndarray,
    eligible: np.ndarray,
    n_dots: int,
    *,
    min_sep_px: float = 3.0,
    seed: int = 0,
    random: bool = False,
) -> np.ndarray:
    """Select ``n_dots`` emission pixels (binary, value 1 at the selected pixels).

    ``random=True`` draws uniformly from the eligible set: the null control at
    matched mass.  Otherwise:

    1. non-maximum suppression with a disk of radius ``ceil(min_sep_px)`` on the
       score surface, restricted to eligible pixels;
    2. exact mutual-separation thinning with ``scipy.spatial.cKDTree.query_pairs``
       (drops the lower-scoring member of every pair closer than ``min_sep_px``);
    3. take the ``n_dots`` highest-scoring survivors; if fewer peaks survive than
       requested, top up with the next-best eligible pixels by score.
    """
    from scipy import spatial

    score = np.asarray(score)
    eligible = np.asarray(eligible, dtype=bool)
    if score.shape != eligible.shape:
        raise ValueError(f"score shape {score.shape} != eligible shape {eligible.shape}")
    out = np.zeros(score.shape, dtype=bool)
    if n_dots <= 0:
        return out
    if random:
        # The null is uniform over every eligible pixel; do not condition it on
        # the candidate surface's positive support.
        idx = np.nonzero(eligible.ravel())[0]
        if idx.size == 0:
            return out
        rng = np.random.default_rng(seed)
        take = rng.choice(idx, size=int(min(n_dots, idx.size)), replace=False)
        out.ravel()[take] = True
        return out

    elig = eligible & np.isfinite(score) & (score > 0)
    if not elig.any():
        return out

    r = int(np.ceil(min_sep_px))
    yy, xx = np.mgrid[-r : r + 1, -r : r + 1]
    disk = (yy**2 + xx**2) <= min_sep_px**2 + 1e-9
    sm = np.where(elig, score, -np.inf)
    local_max = ndimage.maximum_filter(sm, footprint=disk, mode="nearest")
    peaks = elig & (score >= local_max)
    py, px = np.nonzero(peaks)
    if py.size == 0:
        py, px = np.nonzero(elig)
    vals = score[py, px].astype(np.float64)
    order = np.argsort(-vals, kind="stable")
    py, px, vals = py[order], px[order], vals[order]

    # exact thinning: drop the weaker of any pair closer than min_sep_px
    pts = np.stack([py, px], axis=1).astype(np.float64)
    tree = spatial.cKDTree(pts)
    dropped = np.zeros(pts.shape[0], dtype=bool)
    for i, j in tree.query_pairs(r=min_sep_px):
        if dropped[i] or dropped[j]:
            continue
        dropped[j if vals[j] <= vals[i] else i] = True
    keep = np.nonzero(~dropped)[0]
    chosen = keep[:n_dots]
    out[py[chosen], px[chosen]] = True

    if chosen.size < n_dots:  # top up with the next-best eligible pixels
        remaining = n_dots - chosen.size
        pool = np.nonzero(elig.ravel() & ~out.ravel())[0]
        if pool.size:
            pv = score.ravel()[pool]
            o = pool[np.argsort(-pv, kind="stable")[:remaining]]
            out.ravel()[o] = True
    return out


def strike_of_segments(mask: np.ndarray, min_px: int = 25) -> list[dict]:
    """Local strike of each catalogue connected component by total least squares.

    Returns one record per component with >= ``min_px`` pixels: the azimuth (deg
    from north, mod 180) of the first principal component of the component's
    pixel coordinates, plus its pixel count and centroid.
    """
    lab, n = ndimage.label(np.asarray(mask, dtype=bool), structure=np.ones((3, 3), dtype=np.uint8))
    out = []
    if n == 0:
        return out
    ys, xs = np.nonzero(mask)
    ids = lab[ys, xs]
    order = np.argsort(ids, kind="stable")
    ys, xs, ids = ys[order], xs[order], ids[order]
    bounds = np.searchsorted(ids, np.arange(1, n + 1))
    start = 0
    for i, end in enumerate(bounds, start=1):
        cnt = end - start
        if cnt >= min_px:
            y = ys[start:end].astype(np.float64)
            x = xs[start:end].astype(np.float64)
            c = np.stack([x - x.mean(), y - y.mean()], axis=1)
            cov = c.T @ c / cnt
            w, v = np.linalg.eigh(cov)
            pc = v[:, -1]  # (x, y) of the major axis
            az = float(np.degrees(np.arctan2(pc[0], pc[1])) % 180.0)
            out.append(
                {
                    "id": int(i),
                    "n_px": int(cnt),
                    "cy": float(y.mean()),
                    "cx": float(x.mean()),
                    "azimuth_deg": az,
                    "elongation": float(np.sqrt(w[-1] / max(w[0], 1e-12))),
                }
            )
        start = end
    return out


def auc(scores: np.ndarray, labels: np.ndarray) -> float:
    """Rank-based AUC (Mann-Whitney), no sklearn dependency."""
    s = np.asarray(scores, dtype=np.float64).ravel()
    y = np.asarray(labels, dtype=bool).ravel()
    npos, nneg = int(y.sum()), int((~y).sum())
    if npos == 0 or nneg == 0:
        return float("nan")
    order = np.argsort(s, kind="mergesort")
    ranks = np.empty(s.size, dtype=np.float64)
    ranks[order] = np.arange(1, s.size + 1, dtype=np.float64)
    # average ties
    ss = s[order]
    i = 0
    while i < ss.size:
        j = i
        while j + 1 < ss.size and ss[j + 1] == ss[i]:
            j += 1
        if j > i:
            ranks[order[i : j + 1]] = ranks[order[i : j + 1]].mean()
        i = j + 1
    return float((ranks[y].sum() - npos * (npos + 1) / 2.0) / (npos * nneg))


def greedy_cover(
    prior: np.ndarray,
    eligible: np.ndarray,
    n_dots: int,
    *,
    r_px: float = 3.0,
    stop_gain: float | None = None,
    init_cap: int = 1_500_000,
) -> tuple[np.ndarray, list[float]]:
    """Greedy maximum-coverage surrogate (not an exact DTI optimizer).

    For a fixed non-negative ``prior``, this routine greedily maximizes a
    monotone-submodular coverage surrogate: each selected location depletes the
    remaining prior-weighted credit in its triangular-kernel neighborhood. The
    classical ``1 - 1/e`` guarantee applies only to that surrogate's cardinality
    constrained objective, not to the competition DTI.

    The exact metric denominator is
    ``(1-beta) * TP_w + alpha * FP_w + beta * |G| + eps``; it is not a function
    of dot count ``N`` alone. This routine does not model the separate FP term,
    so its gains are not DTI gains and must not be interpreted as a score or as
    evidence that a candidate improves holdout DTI. Use the shared exact
    evaluator for candidate comparisons.

    Returns the boolean dot map and surrogate per-step marginal gains.
    """
    import heapq

    offs = kernel_offsets(r_px)
    offs = [(dy, dx, w) for dy, dx, w in offs if w > 0.0]
    C = np.where(eligible, prior, 0.0).astype(np.float64)
    ny, nx = C.shape
    flat = C.ravel()
    out = np.zeros(C.shape, dtype=bool)
    if n_dots <= 0 or flat.max() <= 0:
        return out, []
    # Seed the heap with the highest-prior pixels only.  C never increases, so
    # pixels only enter later through depletion updates; capping the seed keeps
    # the heap inside the memory budget on a 12.28 M-cell grid.
    pos = np.nonzero(flat > 0)[0]
    if pos.size > init_cap:
        pos = pos[np.argpartition(-flat[pos], init_cap)[:init_cap]]
    heap = [(-flat[i], int(i)) for i in pos]
    heapq.heapify(heap)
    gains: list[float] = []
    placed = 0
    stale = 0
    while heap and placed < n_dots:
        negv, i = heapq.heappop(heap)
        if -negv < flat[i] - 1e-15:  # stale entry: an older, larger value
            heapq.heappush(heap, (-flat[i], i))
            stale += 1
            if stale > 40_000_000:
                break
            continue
        if flat[i] <= 0.0:
            continue
        y, x = divmod(i, nx)
        gain = 0.0
        upd = []
        for dy, dx, w in offs:
            yy, xx = y + dy, x + dx
            if 0 <= yy < ny and 0 <= xx < nx:
                j = yy * nx + xx
                c = flat[j]
                if c > 0.0:
                    gain += c * w
                    nc = c * (1.0 - w)
                    flat[j] = nc
                    upd.append((nc, j))
        for nc, j in upd:
            heapq.heappush(heap, (-nc, j))
        if stop_gain is not None and gain < stop_gain:
            break
        out[y, x] = True
        gains.append(gain)
        placed += 1
    return out, gains


def make_segment_folds(
    labels: np.ndarray,
    footprint: np.ndarray,
    *,
    n_folds: int = 4,
    buffer_px: int = 3,
) -> list[Fold]:
    """Spatially assign *whole 8-connected fault components* to folds.

    Each connected component is assigned by its centroid to a regular spatial
    bin. It is never cut by a tile lattice or fold boundary. For each fold,
    ``truth`` contains every pixel of its assigned components, ``withheld`` is
    the truth plus a Euclidean ``buffer_px``-pixel buffer, and ``visible`` is
    the remaining mapped catalogue after that buffer is removed. The caller
    must mask ``visible`` pixel-exactly from emissions and recompute all
    catalogue-derived features from ``visible`` for each fold.
    """
    labels = np.asarray(labels)
    footprint = np.asarray(footprint, dtype=bool)
    if labels.shape != footprint.shape:
        raise ValueError(f"labels shape {labels.shape} != footprint shape {footprint.shape}")
    if n_folds < 2:
        raise ValueError("n_folds must be at least 2")
    if buffer_px < 0:
        raise ValueError("buffer_px must be non-negative")

    cat = (labels == 1) & footprint
    structure8 = np.ones((3, 3), dtype=np.uint8)
    components, ncomp = ndimage.label(cat, structure=structure8)
    if ncomp == 0:
        return []

    ny, nx = cat.shape
    ys, xs = np.nonzero(cat)
    ids = components[ys, xs]
    counts = np.bincount(ids, minlength=ncomp + 1)
    cy = np.bincount(ids, weights=ys, minlength=ncomp + 1) / np.maximum(counts, 1)
    cx = np.bincount(ids, weights=xs, minlength=ncomp + 1) / np.maximum(counts, 1)

    # A near-square grid makes folds geographically structured. If n_folds is
    # not a perfect rectangle, the final bin absorbs any remaining edge bins.
    nrows = max(1, int(np.floor(np.sqrt(n_folds))))
    ncols = int(np.ceil(n_folds / nrows))
    gy = np.minimum((cy[1:] * nrows / ny).astype(int), nrows - 1)
    gx = np.minimum((cx[1:] * ncols / nx).astype(int), ncols - 1)
    component_fold = np.minimum(gy * ncols + gx, n_folds - 1)
    fold_map = np.full(ncomp + 1, -1, dtype=np.int16)
    fold_map[1:] = component_fold
    assigned = fold_map[components]

    if buffer_px == 0:
        buffer_structure = np.ones((1, 1), dtype=bool)
    else:
        yy, xx = np.ogrid[-buffer_px : buffer_px + 1, -buffer_px : buffer_px + 1]
        buffer_structure = (yy * yy + xx * xx) <= buffer_px * buffer_px

    folds = []
    for k in range(n_folds):
        truth = cat & (assigned == k)
        if not truth.any():
            continue
        withheld = ndimage.binary_dilation(truth, structure=buffer_structure)
        visible = cat & ~withheld
        folds.append(Fold(name=f"segment_fold{k}", withheld=withheld, visible=visible, truth=truth))
    if len(folds) < 2:
        raise ValueError("fewer than two spatial bins contain mapped components; no holdout is possible")
    return folds
