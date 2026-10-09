"""Spatially-blocked hide-and-recover holdout for the DOE GEMS lane work.

Protocol (as specified in the run brief)
----------------------------------------
* The catalogue raster is cut into *whole fault segments*: connected components of
  the mapped-fault mask intersected with a regular block grid.
* A fold withholds a contiguous group of blocks.  Every catalogue pixel inside
  those blocks becomes hidden truth; everything outside is visible.
* A buffer of ``buffer_px`` around each withheld segment is removed from the
  visible catalogue, so no visible-catalogue feature can sit on the edge of a
  withheld segment.
* Every catalogue-derived quantity (the visible-fault mask, the "do not emit
  here" mask, any catalogue-density control) is recomputed from the *visible*
  faults only, per fold.
* Visible faults are masked pixel-exactly from emission.
* Scoring is the pooled official distance-weighted Tversky index
  (alpha = 0.2, beta = 0.8, 300 m triangular kernel) over the withheld pixels.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import ndimage

from . import dti55
from .dti55 import kernel_offsets

__all__ = ["Fold", "make_folds", "emit_dots", "strike_of_segments", "auc"]


@dataclass
class Fold:
    name: str
    withheld: np.ndarray  # bool, blocks whose catalogue is hidden truth
    visible: np.ndarray   # bool, visible catalogue pixels (buffered away from truth)
    truth: np.ndarray     # bool, the withheld catalogue pixels


def make_folds(
    labels: np.ndarray,
    footprint: np.ndarray,
    *,
    grid: tuple[int, int] = (2, 2),
    buffer_px: int = 3,
) -> list[Fold]:
    """Contiguous-quadrant folds: the most conservative spatial blocking.

    ``grid=(2, 2)`` gives 4 folds; each fold withholds one quadrant, so the
    withheld region is geographically compact and nothing about it can leak
    through a nearby visible fault.
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

    elig = np.asarray(eligible, dtype=bool) & (score > 0)
    out = np.zeros(score.shape, dtype=bool)
    if not elig.any() or n_dots <= 0:
        return out
    if random:
        rng = np.random.default_rng(seed)
        idx = np.nonzero(elig.ravel())[0]
        take = rng.choice(idx, size=int(min(n_dots, idx.size)), replace=False)
        out.ravel()[take] = True
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
    lab, n = ndimage.label(mask)
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
    """Greedy maximum-expected-credit placement (Church-Revelle MCLP, greedy form).

    The metric decomposes exactly as ``DTI = TP_w / (0.2 N + 0.8 |G|)`` because
    ``TP_w + FN_w = |G|`` identically (verified in tests/test_dti.py).  So the
    placement problem is: choose ``N`` pixels that maximise the expected captured
    credit ``sum_g m_g`` while spending as few dots as possible.  Captured credit
    is a monotone submodular function of the chosen set, so the greedy rule --
    repeatedly take the pixel with the largest remaining credit, then deplete the
    credit it just captured -- is within ``(1 - 1/e)`` of optimal.

    ``prior[x]`` is the expected kernel credit available at ``x``.  Depletion:
    placing a dot at ``p`` multiplies the remaining credit at ``p + o`` by
    ``(1 - k(|o|))``.  With a *flat* prior this reproduces a near-optimal
    triangular tiling at the metric's own 300 m kernel scale; with an informative
    prior it concentrates dots where credit is expected.

    Returns the boolean dot map and the list of per-step marginal gains.
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
    n_folds: int = 5,
    buffer_px: int = 3,
    split_px: int = 20,
    seed: int = 0,
) -> list[Fold]:
    """Hide-and-recover over *whole fault segments*, per the run brief.

    ``Fold.withheld`` is the FOOTPRINT (the region a prediction may occupy), not the
    truth neighbourhood.  See IR-55-18.

    The catalogue is cut into whole segments: connected components of the mapped
    fault mask, further split by a regular ``split_px``-pixel lattice so that one
    long mapped trace becomes several independent segments.  Segments are dealt
    round-robin (after a seeded shuffle) into ``n_folds`` folds.  In fold ``k``:

    * truth   = the pixels of the segments dealt to fold ``k``
    * buffer  = ``buffer_px`` dilation around those pixels, removed from visible
    * visible = every other catalogue pixel, minus the buffer

    Emission is masked from ``visible`` pixel-exactly and is free to land on the
    withheld segments, which is what "recover" means.  Scattered withholding (not
    whole quadrants) keeps the surrounding mapped network visible, which is what
    the real task looks like: the hidden truth is *unmapped* faults inside an
    otherwise mapped region.
    """
    cat = labels == 1
    lab, ncomp = ndimage.label(cat)
    if ncomp == 0:
        return []
    ny, nx = cat.shape
    yy, xx = np.mgrid[0:ny, 0:nx]
    # split long traces into segments on a regular lattice
    cell = (yy // split_px).astype(np.int64) * 100003 + (xx // split_px).astype(np.int64)
    seg_id = lab.astype(np.int64) * 10_000_000_007 + np.where(cat, cell, 0)
    seg_id = np.where(cat, seg_id, -1)
    uniq, inv = np.unique(seg_id, return_inverse=True)
    inv = inv.reshape(seg_id.shape)
    rng = np.random.default_rng(seed)
    order = rng.permutation(uniq.size)
    assign = np.full(uniq.size, -1, dtype=np.int64)
    assign[order] = np.arange(uniq.size) % n_folds
    fold_of_seg = np.where(seg_id >= 0, assign[inv], -1)

    folds = []
    fp = np.asarray(footprint, dtype=bool)
    for k in range(n_folds):
        truth = cat & (fold_of_seg == k)
        if truth.sum() == 0:
            continue
        buf = ndimage.binary_dilation(truth, iterations=buffer_px)
        visible = cat & ~truth & ~buf
        # IR-55-18 (fixed in this template): ``withheld`` used to be ``truth | buf``.
        # Emission is restricted to ``withheld & ~visible`` by every caller, so that
        # region was built FROM the hidden truth and placed dots on the answer
        # (random control scored 0.33 vs 0.07 on the quadrant protocol).  A fold must
        # emit and score over the whole footprint, minus the visible catalogue.
        folds.append(Fold(name=f"seg{k}", withheld=fp.copy(), visible=visible, truth=truth))
    return folds
