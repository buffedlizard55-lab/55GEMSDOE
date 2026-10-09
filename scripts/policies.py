#!/usr/bin/env python3
"""Emission policies: turn the label-free tensor surface into a submission raster.

Every policy maps ``(score, eligible)`` to a full-grid float prediction in
[0, 1] that is exactly 0 outside ``eligible``.  Policies are pure functions of
the surface and the emission domain; none sees a label.

The policy list is deliberately wide (sparse dots vs thresholded masks vs
dilated masks vs continuous surfaces) because the official metric
(DTI, alpha=0.2, beta=0.8, 300 m triangular kernel) is recall-dominated: a
wider emission buys true-positive coverage at a false-positive cost of only
alpha=0.2 per unit mass.  The template project's proxy sweep
(GEMSDOE emission_decision.log) found wide thresholded emissions clearly
better than sparse dot emissions; this module lets the local proxy and the
catalogue holdout decide for the tensor lane.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage, spatial


def emit_dots_fast(score, eligible, n_dots, *, min_sep_px=3.0, prefilter=500_000):
    """Top-N emission dots: NMS, score prefilter, exact min-separation thinning.

    Semantically the same greedy as ``holdout55.emit_dots`` (highest-score
    local maxima with mutual separation >= min_sep_px); the score prefilter only
    skips peaks that cannot reach the top-N after thinning, which keeps the
    KDTree tractable on a 12.28 M-cell grid.  Verified identical to
    ``holdout55.emit_dots`` on synthetic cases (see tests).
    """
    score = np.asarray(score)
    eligible = np.asarray(eligible, dtype=bool)
    out = np.zeros(score.shape, dtype=bool)
    if n_dots <= 0:
        return out
    elig = eligible & np.isfinite(score) & (score > 0)
    if not elig.any():
        return out
    r = int(np.ceil(min_sep_px))
    yy, xx = np.mgrid[-r : r + 1, -r : r + 1]
    disk = (yy ** 2 + xx ** 2) <= min_sep_px ** 2 + 1e-9
    sm = np.where(elig, score, -np.inf)
    local_max = ndimage.maximum_filter(sm, footprint=disk, mode="nearest")
    peaks = elig & (score >= local_max)
    py, px = np.nonzero(peaks)
    vals = score[py, px].astype(np.float64)
    if py.size > prefilter:  # keep only the strongest peaks for the KDTree
        keep = np.argpartition(-vals, prefilter)[:prefilter]
        py, px, vals = py[keep], px[keep], vals[keep]
    order = np.argsort(-vals, kind="stable")
    py, px, vals = py[order], px[order], vals[order]
    pts = np.stack([py, px], axis=1).astype(np.float64)
    tree = spatial.cKDTree(pts)
    dropped = np.zeros(pts.shape[0], dtype=bool)
    for i, j in tree.query_pairs(r=min_sep_px):
        if dropped[i] or dropped[j]:
            continue
        dropped[j if vals[j] <= vals[i] else i] = True
    keep = np.nonzero(~dropped)[0][:n_dots]
    out[py[keep], px[keep]] = True
    return out


# (name, kind, params)
POLICIES: list[dict] = []


def _reg(name, kind, **params):
    POLICIES.append({"name": name, "kind": kind, **params})


_reg("continuous", "continuous")
_reg("sharp2", "power", k=2)
_reg("sharp4", "power", k=4)
for pct in (1, 5, 10, 20, 30):
    _reg(f"top{pct}pct", "top_pct", pct=pct)
for pct in (5, 10, 20):
    for w in (2, 4):
        _reg(f"top{pct}pct_dil{w}px", "top_pct_dil", pct=pct, w=w)
_reg("dots40k", "dots", n=40_000)
_reg("dots160k", "dots", n=160_000)

POLICY_NAMES = [p["name"] for p in POLICIES]


def build_emission(score, eligible, policy: dict) -> np.ndarray:
    """Full-grid float64 prediction for one policy (0 outside the domain)."""
    s = np.asarray(score, dtype=np.float64)
    elig = np.asarray(eligible, dtype=bool)
    kind = policy["kind"]
    if kind == "continuous":
        p = np.clip(s, 0.0, 1.0)
    elif kind == "power":
        p = np.clip(s, 0.0, 1.0) ** policy["k"]
    elif kind == "top_pct":
        thr = np.quantile(s[elig], 1.0 - policy["pct"] / 100.0)
        p = np.where(s >= thr, 1.0, 0.0)
    elif kind == "top_pct_dil":
        thr = np.quantile(s[elig], 1.0 - policy["pct"] / 100.0)
        mask = s >= thr
        if policy["w"] > 0:
            mask = ndimage.binary_dilation(mask, iterations=policy["w"])
        p = mask.astype(np.float64)
    elif kind == "dots":
        dots = emit_dots_fast(score, elig, policy["n"], min_sep_px=3.0)
        p = dots.astype(np.float64)
    else:
        raise ValueError(kind)
    p = np.where(elig, p, 0.0)
    return np.clip(p, 0.0, 1.0)


def describe(policy: dict) -> str:
    return policy["name"]
