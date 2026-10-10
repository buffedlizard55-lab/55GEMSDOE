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
from pathlib import Path

import numpy as np
from scipy import ndimage

from . import dti55, io55, registry55
from .dti55 import kernel_offsets

__all__ = [
    "Fold",
    "make_folds",
    "emit_dots",
    "emit_dots_budgeted",
    "flank_weight",
    "registry_cover_masks",
    "strike_of_segments",
    "auc",
]


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

    scores = np.asarray(score)
    elig = np.asarray(eligible, dtype=bool)
    if scores.shape != elig.shape:
        raise ValueError("score and eligible must have the same shape")
    out = np.zeros(elig.shape, dtype=bool)
    if n_dots <= 0 or not elig.any():
        return out
    if random:
        # The matched null is sampled from eligibility only; candidate scores
        # must not restrict or weight its support.
        rng = np.random.default_rng(seed)
        idx = np.flatnonzero(elig.ravel())
        take = rng.choice(idx, size=int(min(n_dots, idx.size)), replace=False)
        out.ravel()[take] = True
        return out
    elig = elig & np.isfinite(scores) & (scores > 0)
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


def flank_weight(visible_cat: np.ndarray, support_px: float = 15.0) -> np.ndarray:
    """Off-catalogue flank prior in [0, 1]: quadratic decay away from the *visible* catalogue.

    ``w(p) = max(0, 1 - d(p)/support_px)**2`` for pixels at Euclidean distance
    ``d >= 1`` px from the nearest visible (mapped) catalogue pixel, and ``0`` on the
    visible catalogue itself (a dot on a mapped pixel can never earn credit, so the
    prior is strictly off-catalogue).  ``support_px = 15`` (1.5 km at 100 m) is the
    preregistered H57-A value: the organiser's hidden test set is *newly identified*
    faults absent from the USGS catalogue, so an unmapped trace should lie along or
    beside a mapped one, and the measured median offset of the strongest prior
    adjacency raster (d28, 0.2600 class) is 15 px -- see ``docs/anchor-0.2778.html``.

    Only *visible* catalogue pixels ever enter: in the hide-and-recover holdout the
    withheld segments never contribute, so the prior cannot leak the hidden truth.
    If no visible catalogue pixel exists the prior is neutral (all ones).
    """
    cat = np.asarray(visible_cat, dtype=bool)
    if not cat.any():
        return np.ones(cat.shape, dtype=np.float32)
    d = dti55.distance_to_set(cat)
    w = np.clip(1.0 - d / float(support_px), 0.0, 1.0) ** 2
    w[cat] = 0.0
    return w.astype(np.float32)


def registry_cover_masks(
    registry_dir,
    shape: tuple[int, int],
    *,
    max_dist_px: float = 3.0,
) -> tuple[list[str], list[np.ndarray]]:
    """Per-raster "covered" masks, exactly as the strict uniqueness gate measures them.

    Every GeoTIFF in ``registry_dir`` is aligned to the official competition grid
    by the shared ``registry55`` loader.  Geometry shifts are nearest-neighbor
    reprojected, and invalid/unreferenced rasters fail closed.  Each returned mask
    is the set of pixels within ``max_dist_px`` (Euclidean) of a positive pixel:
    ``distance_transform_edt(~pos) <= max_dist_px`` with ``pos = nan_to_num(band1) > 0``
    -- the identical definition used by ``scripts/verify_unique.py``.  No raster
    is silently excluded; if an artifact makes the literal rule unsatisfiable, the
    emitter returns an empty/shortfall result and the caller must stop.
    """
    if tuple(shape) == (io55.HEIGHT, io55.WIDTH):
        grid, _ = io55.read_template()
    else:
        # Small synthetic grids are used by unit tests; keep the competition CRS
        # and pixel transform while replacing only the dimensions.
        grid = io55.Grid(
            height=int(shape[0]), width=int(shape[1]), crs=io55.CRS_EPSG,
            transform=io55.TRANSFORM,
            footprint=np.ones(shape, dtype=bool),
        )
    names, masks, warped = registry55.cover_masks(
        registry_dir, grid, max_dist_px=max_dist_px
    )
    if warped:
        print(f"[registry] reprojected {len(warped)} misaligned raster(s) to the official template: "
              + ", ".join(warped), flush=True)
    return names, masks


def emit_dots_budgeted(
    score: np.ndarray,
    eligible: np.ndarray,
    n_dots: int,
    *,
    min_sep_px: float = 3.0,
    cover_masks=(),
    max_overlap: float = 0.68,
    seed: int = 0,
    random: bool = False,
) -> np.ndarray:
    """Place score-ranked dots under per-raster overlap and separation constraints.

    This uses the exact pixel eligibility and Euclidean <=3 px cover definition
    used by ``scripts/verify_unique.py``.  Every registry mask is applied.  The
    score arm visits candidates in descending score order; the random control
    visits the identical eligible set in seeded random order.  Both use the same
    per-raster cap ``floor(max_overlap * requested_n)`` and the same strict
    ``min_sep_px`` thinning (a selected point blocks the disk neighborhood before
    the next candidate is considered).

    If exactly ``n_dots`` are returned, every mask has overlap <= ``max_overlap``
    by construction.  If the constraints make the requested mass infeasible, a
    repair pass may return fewer dots; the final ratios are still rechecked, and an
    empty set means the candidate is blocked.  Callers must not treat a shortfall
    as a matched-mass holdout or as submission clearance.
    """
    score = np.asarray(score, dtype=np.float32)
    elig = np.asarray(eligible, dtype=bool)
    if score.shape != elig.shape:
        raise ValueError("score and eligible must have the same shape")
    out = np.zeros(score.shape, dtype=bool)
    if n_dots <= 0 or not elig.any():
        return out
    masks = [np.asarray(m, dtype=bool) for m in cover_masks]
    if any(m.shape != score.shape for m in masks):
        raise ValueError("every cover mask must match score shape")
    if not 0.0 <= max_overlap < 1.0:
        raise ValueError("max_overlap must be in [0, 1)")
    if min_sep_px < 0.0:
        raise ValueError("min_sep_px must be nonnegative")

    valid = elig if random else elig & np.isfinite(score) & (score > 0)
    idx = np.flatnonzero(valid.ravel())
    if idx.size == 0:
        return out
    rng = np.random.default_rng(seed)
    if random:
        order = rng.permutation(idx.size)
    else:
        vals = score.ravel()[idx]
        order = np.argsort(-vals, kind="stable")
    idx = idx[order]
    vals = (np.zeros(idx.size, dtype=np.float64) if random
            else score.ravel()[idx].astype(np.float64, copy=False))

    # Membership matrix for the ordered candidates.  On this grid its worst-case
    # size is bounded by candidate_count x registry_count bytes (bool), and avoids
    # 56 separate raster reads in the placement loop.
    if masks:
        flat_masks = [m.ravel() for m in masks]
        membership = np.empty((idx.size, len(masks)), dtype=bool)
        for j, mask in enumerate(flat_masks):
            membership[:, j] = mask[idx]
        caps = np.full(len(masks), int(np.floor(max_overlap * n_dots)), dtype=np.int64)
    else:
        membership = np.empty((idx.size, 0), dtype=bool)
        caps = np.empty(0, dtype=np.int64)

    # A rasterized exclusion disk guarantees strict minimum separation without
    # post-hoc top-ups that can accidentally violate it.
    r = int(np.ceil(min_sep_px))
    gy, gx = np.mgrid[-r:r + 1, -r:r + 1]
    disk = (gy * gy + gx * gx) <= min_sep_px * min_sep_px + 1e-9
    blocked = np.zeros(score.shape, dtype=bool)
    ny, nx = score.shape
    selected_idx: list[int] = []
    selected_scores: list[float] = []
    counts = np.zeros(len(masks), dtype=np.int64)

    for k, flat_idx in enumerate(idx):
        y, x = divmod(int(flat_idx), nx)
        if blocked[y, x]:
            continue
        row = membership[k]
        if row.size and row.any():
            hit = np.flatnonzero(row)
            if np.any(counts[hit] >= caps[hit]):
                continue
            counts[hit] += 1
        out[y, x] = True
        selected_idx.append(int(flat_idx))
        selected_scores.append(float(vals[k]))
        y0, y1 = max(0, y - r), min(ny, y + r + 1)
        x0, x1 = max(0, x - r), min(nx, x + r + 1)
        blocked[y0:y1, x0:x1] |= disk[y0 - (y - r):y1 - (y - r), x0 - (x - r):x1 - (x - r)]
        if len(selected_idx) >= n_dots:
            break

    if not masks or not selected_idx:
        return out

    # If constraints stopped before target mass, caps were based on requested N.
    # Reconcile the achieved-mass denominator.  Removing covered dots preserves
    # minimum separation; iterating until no over-budget mask remains is fail-closed.
    chosen = np.asarray(selected_idx, dtype=np.int64)
    chosen_scores = np.asarray(selected_scores, dtype=np.float64)
    # Candidate ``idx`` is in score/random order, so retain exact membership rows
    # by looking up each selected flat pixel once (the number of selected pixels
    # is at most the requested dot budget, not the millions of candidate pixels).
    sel_rows = []
    lookup = {int(i): k for k, i in enumerate(idx)}
    for i in chosen:
        sel_rows.append(membership[lookup[int(i)]])
    chosen_membership = np.asarray(sel_rows, dtype=bool)
    while chosen.size:
        ratios = chosen_membership.sum(axis=0) / chosen.size
        over = np.flatnonzero(ratios > max_overlap + 1e-12)
        if over.size == 0:
            break
        worst = int(over[np.argmax(ratios[over])])
        covered = np.flatnonzero(chosen_membership[:, worst])
        if covered.size == 0:
            break
        # Drop the lowest-priority dot that causes this raster to exceed its cap.
        drop = int(covered[np.argmin(chosen_scores[covered])])
        out.ravel()[chosen[drop]] = False
        chosen = np.delete(chosen, drop)
        chosen_scores = np.delete(chosen_scores, drop)
        chosen_membership = np.delete(chosen_membership, drop, axis=0)

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
    labels = np.asarray(labels)
    fp = np.asarray(footprint, dtype=bool)
    if labels.ndim != 2 or fp.ndim != 2 or labels.shape != fp.shape:
        raise ValueError("labels and footprint must have the same 2D shape")
    if n_folds < 2:
        raise ValueError("n_folds must be at least two")
    if buffer_px < 0 or split_px <= 0:
        raise ValueError("buffer_px must be nonnegative and split_px must be positive")
    cat = labels == 1
    lab, ncomp = ndimage.label(cat)
    if ncomp == 0:
        return []
    ny, nx = cat.shape
    yy, xx = np.mgrid[0:ny, 0:nx]
    # split long traces into segments on a regular lattice
    cell = (yy // split_px).astype(np.int64) * 100003 + (xx // split_px).astype(np.int64)
    if np.unique(cell[cat]).size < 2:
        raise ValueError("catalogue occupies fewer than two spatial bins")
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
