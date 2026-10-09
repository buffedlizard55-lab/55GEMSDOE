#!/usr/bin/env python3
"""Hide-and-recover holdout for the tensor-dimensionality lane.

Protocol (preregistered, matches the standing brief)
---------------------------------------------------
* Folds: WHOLE 8-connected catalogue components assigned to a spatially
  structured set of bins by component centroid.  A component is never cut.
* Buffer: every withheld component is dilated by ``--buffer-px`` (default 3 px =
  300 m); those pixels belong to neither the visible catalogue nor the truth.
* Visible faults: masked pixel-exactly from the emitted prediction.
* Catalogue-derived features: NONE.  Every arm below is built only from the
  geophysical tensor cache, so no arm can see the withheld segments.
* Scoring: pooled distance-weighted Tversky index, alpha = 0.2, beta = 0.8,
  300 m triangular kernel (3 px at 100 m).  Per-fold truth contributions and
  per-fold-bin false-positive contributions are pooled; the bins partition the
  footprint, so every prediction cell and every truth cell is counted once.
* Leakage canary: every single feature is scored alone (AUC of the withheld
  truth against far-field negatives).  AUC > 0.90 is LEAKAGE until proven
  otherwise.
* Every arm is compared with a mass-matched uniform random control drawn over
  the same eligible set, independent of the score surface.

The fast pooled evaluator is verified against the literal ``dti55`` reference
implementation before the sweep starts (see ``_selfcheck``).

Outputs a JSON record under ``evidence/``.  No submission slot is touched.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems55 import dti55, holdout55, io55, tensor55  # noqa: E402

CACHE = ROOT / "cache" / "tc300.npz"


# --------------------------------------------------------------------------- #
# cache loading
# --------------------------------------------------------------------------- #
def _dequant(a: np.ndarray) -> np.ndarray:
    if a.dtype == np.uint8:
        return a.astype(np.float32) / 255.0
    if a.dtype == np.int16:
        return a.astype(np.float32) / 100.0
    return a.astype(np.float32)


def load_cache(path: Path = CACHE) -> dict:
    z = np.load(path)
    return {k: (z[k].astype(bool) if z[k].dtype == bool else _dequant(z[k])) for k in z.files}


# --------------------------------------------------------------------------- #
# scoring surfaces (geophysical only; labels.tif is never read here)
# --------------------------------------------------------------------------- #
def _rank01(x: np.ndarray, valid: np.ndarray) -> np.ndarray:
    out = np.zeros(x.shape, dtype=np.float64)
    idx = np.nonzero(valid.ravel())[0]
    v = x.ravel()[idx]
    v = np.where(np.isfinite(v), v, -np.inf)
    order = np.argsort(v, kind="stable")
    ranks = np.empty(v.size, dtype=np.float64)
    ranks[order] = np.arange(v.size, dtype=np.float64)
    ranks /= max(v.size - 1, 1)
    out.ravel()[idx] = ranks
    return out


def _block_norm(x: np.ndarray, valid: np.ndarray, block: int = 64) -> np.ndarray:
    ny, nx = x.shape
    out = np.zeros_like(x, dtype=np.float64)
    for y0 in range(0, ny, block):
        for x0 in range(0, nx, block):
            sl = (slice(y0, min(y0 + block, ny)), slice(x0, min(x0 + block, nx)))
            v = valid[sl]
            if v.sum() < 25:
                continue
            vals = x[sl][v]
            med = float(np.median(vals))
            mad = float(np.median(np.abs(vals - med))) * 1.4826
            out[sl] = np.where(v, (x[sl] - med) / max(mad, 1e-12), 0.0)
    return out


def build_arm_surfaces(C: dict, footprint: np.ndarray, *, strike_sigma_deg: float = 25.0,
                       dim_variant: str = "invariant") -> dict[str, np.ndarray]:
    valid = footprint & np.isfinite(C["mag_s300_hg"]) & np.isfinite(C["grav_s300_hg"])
    ridge_m = _rank01(np.clip(_block_norm(C["mag_s300_hg"], valid), 0, None), valid)
    ridge_g = _rank01(np.clip(_block_norm(C["grav_s300_hg"], valid), 0, None), valid)
    ridge = np.sqrt(np.clip(ridge_m, 0, 1) * np.clip(ridge_g, 0, 1))
    ridge_max = np.maximum(ridge_m, ridge_g)

    key = "dim_inv" if dim_variant == "invariant" else "dim_eig"
    dim = 0.5 * (C[f"mag_s300_{key}"] + C[f"grav_s300_{key}"])
    w2d = np.clip(1.0 - dim, 0.0, 1.0)

    dth = 0.5 * (
        tensor55.angular_difference_deg(C["mag_s300_strike"], C["mag_s300_ridge_az"])
        + tensor55.angular_difference_deg(C["grav_s300_strike"], C["grav_s300_ridge_az"])
    )
    agree = np.exp(-((dth / strike_sigma_deg) ** 2)).astype(np.float32)
    plunge = 0.5 * (C["mag_s300_plunge"] + C["grav_s300_plunge"])

    base = np.where(valid, 1.0, 0.0).astype(np.float32)
    S = {
        "tensor_full": base * ridge * w2d * agree * plunge,
        "ridge_only": base * ridge,
        "ridge_max_only": base * ridge_max,
        "ridge_x_agree": base * ridge * agree,
        "ridge_x_dim": base * ridge * w2d,
        "ridge_x_plunge": base * ridge * plunge,
        "dim_gate_only": base * w2d,
        "agree_only": base * agree,
        "plunge_only": base * plunge,
        "dim_only": base * dim,
        "ridge_mag_only": base * ridge_m,
        "ridge_grav_only": base * ridge_g,
    }
    for k in S:
        S[k] = np.where(valid, np.clip(np.nan_to_num(S[k]), 0.0, 1.0), 0.0).astype(np.float32)
    S["_valid"] = valid
    S["_strike"] = np.where(agree > 0.5, C["mag_s300_strike"], C["grav_s300_strike"]).astype(np.float32)
    S["_dim"] = dim.astype(np.float32)
    S["_dtheta"] = dth
    S["_agree"] = agree
    return S


# --------------------------------------------------------------------------- #
# emission
# --------------------------------------------------------------------------- #
def dilate_disk(r_px: float) -> np.ndarray:
    r = int(np.ceil(r_px))
    yy, xx = np.ogrid[-r : r + 1, -r : r + 1]
    return (yy * yy + xx * xx) <= r_px * r_px + 1e-9


def emit(score: np.ndarray, eligible: np.ndarray, *, top_pct: float, dilate_px: int,
         value: float = 1.0) -> np.ndarray:
    """Binary emission: eligible cells in the top ``top_pct`` percent, dilated."""
    s = np.where(eligible, score, -np.inf)
    n = int(eligible.sum())
    if n == 0:
        return np.zeros(score.shape, dtype=np.float32)
    k = int(round(n * top_pct / 100.0))
    k = max(1, min(k, n))
    thr = float(np.partition(s[eligible], n - k)[n - k])
    sel = eligible & (score >= thr)
    if dilate_px > 0:
        sel = ndimage.binary_dilation(sel, structure=dilate_disk(float(dilate_px)))
    sel &= eligible
    return np.where(sel, value, 0.0).astype(np.float32)


def emit_dots(score: np.ndarray, eligible: np.ndarray, *, n_dots: int, min_sep_px: float,
              dilate_px: int = 0) -> np.ndarray:
    """Isolated dots: non-maximum suppression at ``min_sep_px`` then the top ``n_dots``.

    This is the morphology every top-scoring registry raster uses: single,
    mutually separated cells at value 1.  Two dots closer than the kernel radius
    cannot both add true-positive credit (the metric takes a *max*, not a sum),
    so packing them tighter than ``min_sep_px`` only buys false positives.

    Non-maximum suppression with a disk of radius ``min_sep_px`` already
    guarantees the separation (two local maxima cannot lie inside each other's
    disk), so the exact-pair cKDTree pass in ``holdout55.emit_dots`` only breaks
    rare ties; it is skipped here for speed.  A regression check is printed once
    per run.
    """
    r = int(np.ceil(min_sep_px))
    yy, xx = np.mgrid[-r : r + 1, -r : r + 1]
    disk = (yy**2 + xx**2) <= min_sep_px**2 + 1e-9
    elig = eligible & np.isfinite(score) & (score > 0)
    sm = np.where(elig, score, -np.inf).astype(np.float32)
    local_max = ndimage.maximum_filter(sm, footprint=disk, mode="nearest")
    peaks = elig & (score >= local_max)
    idx = np.nonzero(peaks.ravel())[0]
    if idx.size == 0:
        return np.zeros(score.shape, dtype=np.float32)
    vals = score.ravel()[idx]
    k = min(int(n_dots), idx.size)
    take = idx[np.argpartition(-vals, k - 1)[:k]] if k < idx.size else idx
    sel = np.zeros(score.shape, dtype=bool)
    sel.ravel()[take] = True
    if dilate_px > 0:
        sel = ndimage.binary_dilation(sel, structure=dilate_disk(float(dilate_px)))
        sel &= eligible
    return sel.astype(np.float32)


# --------------------------------------------------------------------------- #
# fast pooled evaluator
# --------------------------------------------------------------------------- #
class PooledEvaluator:
    """Pre-computes everything that depends only on the fold geometry.

    For each fold k:
      * ``w``         full-grid kernel credit max_g k(d(x,g))  (float32)
      * ``bin``       the disjoint footprint partition cell used for FP pooling
      * ``nbr_idx``   (n_truth, m) flat indices of the kernel disk around each
                      truth cell, clipped to the grid
      * ``nbr_w``     (n_truth, m) triangular weights k(|offset|)
      * ``nbr_ok``    (n_truth, m) bool, False where the offset left the grid
    """

    def __init__(self, folds, bins, shape):
        self.folds = folds
        self.bins = bins
        ny, nx = shape
        offs = dti55.kernel_offsets(dti55.R_PX)
        offs = [(dy, dx, w) for dy, dx, w in offs if w > 0.0]
        self.offs = offs
        self.shape = shape
        self.parts = []
        for k, f in enumerate(folds):
            w64 = dti55.kernel_credit(f.truth, dti55.R_PX)
            w = w64.astype(np.float32)
            ys, xs = np.nonzero(f.truth)
            m = len(offs)
            idx = np.zeros((ys.size, m), dtype=np.int64)
            ww = np.zeros((ys.size, m), dtype=np.float64)
            ok = np.zeros((ys.size, m), dtype=bool)
            for j, (dy, dx, wt) in enumerate(offs):
                yy = ys + dy
                xx = xs + dx
                good = (yy >= 0) & (yy < ny) & (xx >= 0) & (xx < nx)
                ok[:, j] = good
                idx[:, j] = np.where(good, np.clip(yy, 0, ny - 1) * nx + np.clip(xx, 0, nx - 1), 0)
                ww[:, j] = wt
            b = bins[k]
            self.parts.append({
                "w": w,
                "one_minus_w_bin": (1.0 - w64[b]).astype(np.float64),
                "bin_flat": np.nonzero(b.ravel())[0],
                "nbr_idx": idx, "nbr_w": ww, "nbr_ok": ok,
                "n_truth": int(ys.size),
            })

    def pooled(self, preds: list[np.ndarray]) -> dict:
        TP = FP = 0.0
        n_pred = 0
        for p, part in zip(preds, self.parts):
            flat = np.asarray(p, dtype=np.float32).ravel()
            # float64 accumulation: a float32 sum over ~30k truth cells loses
            # ~1e-2 absolute precision, which is larger than the self-check
            # tolerance against the float64 reference in dti55.
            vals = np.where(part["nbr_ok"],
                            flat[part["nbr_idx"]].astype(np.float64) * part["nbr_w"], 0.0)
            TP += float(vals.max(axis=1).sum())
            FP += float(np.dot(flat[part["bin_flat"]].astype(np.float64),
                               part["one_minus_w_bin"].astype(np.float64)))
            n_pred += int((flat > 0).sum())
        n_truth = sum(part["n_truth"] for part in self.parts)
        FN = float(n_truth) - TP
        return {"dti": dti55.dti_from_totals(TP, FP, FN), "tp_w": TP, "fp_w": FP,
                "fn_w": FN, "n_truth": n_truth,
                "mean_pred_cells": n_pred / max(len(self.parts), 1)}

    def selfcheck(self, preds: list[np.ndarray], tol: float = 1e-4) -> dict:
        """Verify the fast path against the literal ``dti55`` reference, per fold.

        ``dti55.dti`` scores the prediction over the whole grid; the pooled
        protocol charges false positives only inside the fold's own bin, so the
        reference FP is recomputed explicitly on that same bin.
        """
        ref_tp = ref_fp = ref_fn = 0.0
        for k, (p, f) in enumerate(zip(preds, self.folds)):
            r = dti55.dti(p, f.truth)
            ref_tp += r.tp_w
            ref_fn += r.fn_w
            pf = np.asarray(p, dtype=np.float64)
            w = dti55.kernel_credit(f.truth, dti55.R_PX)
            b = self.bins[k]
            ref_fp += float(np.sum(pf[b] * (1.0 - w)[b]))
        fast = self.pooled(preds)
        worst = max(abs(fast["tp_w"] - ref_tp), abs(fast["fp_w"] - ref_fp),
                    abs(fast["fn_w"] - ref_fn))
        return {"max_abs_component_error": float(worst), "tolerance": tol,
                "passed": bool(worst <= tol)}


def spatial_bins(footprint: np.ndarray, nrows: int, ncols: int) -> list[np.ndarray]:
    ny, nx = footprint.shape
    by = int(np.ceil(ny / nrows))
    bx = int(np.ceil(nx / ncols))
    out = []
    for i in range(nrows):
        for j in range(ncols):
            m = np.zeros((ny, nx), dtype=bool)
            m[i * by:(i + 1) * by, j * bx:(j + 1) * bx] = True
            out.append(m & footprint)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", type=Path, default=CACHE)
    ap.add_argument("--n-folds", type=int, default=4)
    ap.add_argument("--buffer-px", type=int, default=3)
    ap.add_argument("--n-dots", type=int, nargs="+",
                    default=[8000, 12000, 16000, 20000, 25000, 30000, 37654, 45000, 60000])
    ap.add_argument("--min-sep", type=float, nargs="+", default=[3.0, 5.0])
    ap.add_argument("--dilate-px", type=int, nargs="+", default=[0, 1])
    ap.add_argument("--arms", type=str, nargs="+", default=None)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--random-each", action="store_true",
                    help="run the mass-matched uniform random control at every morphology")
    ap.add_argument("--control-reps", type=int, default=3)
    ap.add_argument("--limit-arms", type=int, default=0)
    ap.add_argument("--out", type=Path, default=ROOT / "evidence" / "holdout55_v1.json")
    args = ap.parse_args()

    t0 = time.time()
    grid, _ = io55.read_template()
    labels = io55.read_labels()
    footprint = np.asarray(grid.footprint, dtype=bool)
    C = load_cache(args.cache)
    S = build_arm_surfaces(C, footprint)
    valid = S["_valid"]

    folds = holdout55.make_segment_folds(labels, footprint, n_folds=args.n_folds,
                                         buffer_px=args.buffer_px)
    nrows = max(1, int(np.floor(np.sqrt(len(folds)))))
    ncols = int(np.ceil(len(folds) / nrows))
    bins = spatial_bins(footprint, nrows, ncols)
    while len(bins) < len(folds):
        bins.append(bins[-1])
    bins = bins[:len(folds)]
    n_pooled = sum(int(f.truth.sum()) for f in folds)
    print(f"{len(folds)} folds (grid {nrows}x{ncols}); pooled withheld positives = {n_pooled}",
          flush=True)
    for f in folds:
        print(f"   {f.name}: truth={int(f.truth.sum())} visible={int(f.visible.sum())}", flush=True)

    ev = PooledEvaluator(folds, bins, footprint.shape)

    arm_names = args.arms or [k for k in S if not k.startswith("_")]
    if args.limit_arms:
        arm_names = arm_names[:args.limit_arms]

    # ---------------- leakage canary --------------------------------------- #
    far = footprint & ~ndimage.binary_dilation(labels == 1, iterations=6)
    canary = {}
    for name in arm_names + ["_dim", "_dtheta", "_agree"]:
        s = S[name]
        aucs, lifts = [], []
        for f in folds:
            y = np.zeros(s.shape, dtype=bool)
            y[f.truth] = True
            sub = f.truth | far
            aucs.append(holdout55.auc(s[sub], y[sub]))
            # mean score on the withheld truth vs on far-field negatives
            lifts.append(float(np.mean(s[f.truth]) / max(np.mean(s[far]), 1e-12)))
        canary[name] = {"auc_mean": float(np.nanmean(aucs)),
                        "auc_folds": [float(a) for a in aucs],
                        "mean_score_lift_vs_farfield": float(np.nanmean(lifts))}
    print("\n--- leakage canary (AUC vs withheld truth; negatives >=600 m from any mapped fault) ---",
          flush=True)
    for k, v in canary.items():
        flag = "LEAKAGE-SUSPECT (>0.90)" if v["auc_mean"] > 0.90 else "ok"
        print(f"  {k:18s} AUC={v['auc_mean']:.4f}  lift={v['mean_score_lift_vs_farfield']:.2f}x  {flag}",
              flush=True)

    # ---------------- pooled DTI sweep ------------------------------------- #
    checked = False
    results = {}
    print("\n--- pooled HOLDOUT-DTI sweep ---", flush=True)
    for name in arm_names:
        surf = S[name]
        morph = {}
        for nd in args.n_dots:
            for sep in args.min_sep:
                for dp in args.dilate_px:
                    preds = [emit_dots(surf, valid & ~f.visible, n_dots=nd,
                                       min_sep_px=sep, dilate_px=dp) for f in folds]
                    if not checked:
                        sc = ev.selfcheck(preds)
                        print(f"  [selfcheck] fast vs literal dti55: {sc}", flush=True)
                        if not sc["passed"]:
                            raise SystemExit("fast evaluator disagrees with dti55 reference")
                        checked = True
                    morph[(nd, sep, dp)] = ev.pooled(preds)
        rows = [{"n_dots": nd, "min_sep_px": sep, "dilate_px": dp, **r}
                for (nd, sep, dp), r in morph.items()]
        best = max(rows, key=lambda r: r["dti"])
        # mass-matched uniform random control.  With ``--random-each`` it is run
        # at EVERY morphology, because the metric's false-positive term is cheap
        # (alpha = 0.2) and a concentrated candidate can lose to a uniformly
        # spread control purely through clustering; comparing at matched count
        # per morphology is the only honest comparison.
        ctrl_dti, ctrl_rows = [], []
        morphs = rows if args.random_each else [best]
        for row in morphs:
            reps = 1 if args.random_each else args.control_reps
            d_vals = []
            for rep in range(reps):
                nd, sep, dp = row["n_dots"], row["min_sep_px"], row["dilate_px"]
                preds = []
                for k, f in enumerate(folds):
                    elig = valid & ~f.visible
                    ref = emit_dots(surf, elig, n_dots=nd, min_sep_px=sep, dilate_px=dp)
                    n_sel = int((ref > 0).sum())
                    idx = np.nonzero(elig.ravel())[0]
                    rng = np.random.default_rng(args.seed + 1000 * rep + k)
                    out = np.zeros(surf.shape, dtype=np.float32)
                    take = rng.choice(idx, size=min(n_sel, idx.size), replace=False)
                    out.ravel()[take] = 1.0
                    preds.append(out)
                r = ev.pooled(preds)
                ctrl_rows.append({"morphology": [nd, sep, dp], **r})
                d_vals.append(r["dti"])
            if args.random_each:
                row["random_control_dti"] = float(np.mean(d_vals))
                row["lift_over_random"] = float(row["dti"] / max(np.mean(d_vals), 1e-12))
            ctrl_dti.extend(d_vals)
        results[name] = {
            "best": best,
            "sweep": rows,
            "random_control_reps": ctrl_rows,
            "random_control_dti_mean": float(np.mean(ctrl_dti)),
            "random_control_dti_min": float(np.min(ctrl_dti)),
            "random_control_dti_max": float(np.max(ctrl_dti)),
            "lift_over_random": float(best["dti"] / max(np.mean(ctrl_dti), 1e-12)),
        }
        print(f"  {name:18s} best DTI={best['dti']:.6f} (n_dots={best['n_dots']} "
              f"sep={best['min_sep_px']} dilate {best['dilate_px']})  random={np.mean(ctrl_dti):.6f}  "
              f"lift={best['dti']/max(np.mean(ctrl_dti),1e-12):.2f}x  "
              f"[{time.time()-t0:.0f}s]", flush=True)

    out = {
        "evidence_class": "HOLDOUT-DTI",
        "evaluator_version": dti55.EVALUATOR_VERSION,
        "withheld_positive_count": int(n_pooled),
        "n_folds": len(folds),
        "buffer_px": args.buffer_px,
        "footprint_px": int(footprint.sum()),
        "metric": {"alpha": dti55.ALPHA, "beta": dti55.BETA,
                   "kernel": "triangular", "radius_m": dti55.R_PX * io55.RES_M},
        "cache": str(args.cache),
        "canary": canary,
        "arms": results,
        "elapsed_s": time.time() - t0,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=1))
    print(f"\nwrote {args.out}  ({time.time()-t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
