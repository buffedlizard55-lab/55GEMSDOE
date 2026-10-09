#!/usr/bin/env python3
"""Shared holdout evaluator for the tensor-dimensionality lane.

Protocol
--------
5-fold *whole-segment* spatial CV ("hide and recover"):

* the catalogue is split into whole connected traces and 20-pixel lattice
  segments; a seeded assignment withholds complete segments and buffers them by
  3 px.  No withheld segment is used as a visible catalogue feature.
* each fold emits ``n_dots / 5`` unit dots over the full scored footprint, while
  all visible catalogue pixels are masked pixel-exactly.  The held-out segment
  truth is the only positive set for that fold.
* fold TP/FP/FN contributions are pooled before taking one official DTI.  This
  mirrors the organiser's pooled aggregation and avoids averaging fold ratios.
* a matched uniform-random arm is evaluated with the identical eligible mask.

Arms at matched mass:
  random        uniform over the eligible set (the null)
  ridge_only    horizontal-gradient ridge rank, no tensor gating
  ridge_x_dim   ridge x (1 - dimensionality)
  ridge_x_agree ridge x strike-agreement
  tensor_full   the whole lane score (ridge x 2-D gate x strike agreement x plunge)

Also runs the leakage canary (single-feature AUC against the hidden truth) and
the strike test (withheld-fault strike vs the tensor strike).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems55 import dti55, holdout55, io55, tensor55  # noqa: E402

CACHE = ROOT / "data" / "cache"
EVID = ROOT / "evidence"


def bootstrap_ci(x: np.ndarray, n: int = 2000, seed: int = 0) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    if x.size == 0:
        return (float("nan"), float("nan"))
    idx = rng.integers(0, x.size, size=(n, x.size))
    m = x[idx].mean(axis=1)
    return (float(np.quantile(m, 0.025)), float(np.quantile(m, 0.975)))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="v1")
    ap.add_argument("--n-dots", type=int, default=40000)
    ap.add_argument("--min-sep", type=float, default=3.0)
    ap.add_argument("--out", default=None)
    ap.add_argument("--arms", default="random,ridge_only,ridge_x_dim,ridge_x_agree,tensor_full")
    args = ap.parse_args()

    t0 = time.time()
    z = np.load(CACHE / f"lane_{args.tag}.npz")
    score = z["score"]
    ridge = z["ridge"]
    dim = z["dim"]
    agree = z["agree"]
    plunge = z["plunge"]
    striping = z["striping"]
    labels = z["labels"]
    footprint = z["footprint"]
    z.close()

    grid, _ = io55.read_template()
    assert footprint.shape == grid.shape
    folds = holdout55.make_segment_folds(
        labels, footprint, n_folds=5, buffer_px=3, split_px=20, seed=0
    )
    if len(folds) < 2:
        raise RuntimeError("segment holdout needs at least two non-empty folds")
    cat = labels == 1

    base_elig = footprint & ~striping
    surfaces = {
        "random": score,  # unused, but keeps the dict uniform
        "ridge_only": ridge,
        "ridge_x_dim": (ridge * (1.0 - dim)).astype(np.float32),
        "ridge_x_agree": (ridge * agree).astype(np.float32),
        "tensor_full": score,
    }
    arms = [a for a in args.arms.split(",") if a]

    res: dict = {"config": vars(args), "n_folds": len(folds), "n_truth_total": int(cat.sum())}
    for arm in arms:
        # Each fold has its own information set.  Do not union the predictions
        # before scoring: a pixel masked as visible in one fold is not the same
        # information state as that pixel in another fold.  Pool the exact
        # TP/FP/FN totals instead, as the organiser does for the leaderboard.
        per_fold = []
        totals = {"tp_w": 0.0, "fp_w": 0.0, "fn_w": 0.0, "n_pred_pos": 0, "n_truth": 0}
        for fold_i, f in enumerate(folds):
            # Predictions may occur anywhere in the footprint.  Only visible
            # catalogue pixels are forbidden; otherwise this is a true
            # hide-and-recover test rather than a quadrant placement test.
            elig = base_elig & ~f.visible
            n = args.n_dots // len(folds)
            surf = surfaces[arm]
            dots = holdout55.emit_dots(
                surf, elig, n, min_sep_px=args.min_sep,
                seed=1234 + fold_i, random=(arm == "random")
            )
            c = dti55.dti(dots.astype(np.float32), f.truth, mask=footprint)
            record = c.as_dict() | {"n_dots": int(dots.sum()), "n_truth": int(f.truth.sum())}
            per_fold.append(record)
            for key in ("tp_w", "fp_w", "fn_w", "n_pred_pos", "n_truth"):
                totals[key] += record[key]
        pooled = dti55.DTIResult(
            dti=dti55.dti_from_totals(totals["tp_w"], totals["fp_w"], totals["fn_w"]),
            tp_w=totals["tp_w"], fp_w=totals["fp_w"], fn_w=totals["fn_w"],
            n_pred_pos=int(totals["n_pred_pos"]), n_truth=int(totals["n_truth"]),
        )
        fd = np.array([p["dti"] for p in per_fold])
        res[arm] = {
            "pooled": pooled.as_dict(),
            "per_fold": per_fold,
            "fold_mean": float(fd.mean()),
            "fold_sd": float(fd.std(ddof=1)) if fd.size > 1 else 0.0,
            "fold_ci95": bootstrap_ci(fd, n=4000),
        }
        print(
            f"[{time.time()-t0:6.1f}s] {arm:14s} pooled DTI={pooled.dti:.4f} "
            f"(dots={pooled.n_pred_pos}) folds={np.round(fd,4).tolist()}",
            flush=True,
        )

    # ---------------- leakage canary -----------------------------------------
    rng = np.random.default_rng(7)
    canary = {}
    zc = np.load(CACHE / f"lane_{args.tag}.npz")
    dim_inv = zc["dim_inv"]
    zc.close()
    feats = {
        "tensor_full_score": score,
        "ridge": ridge,
        "one_minus_dim": (1.0 - dim).astype(np.float32),
        "strike_agree": agree,
        "plunge": plunge,
        "dim_inv_raw": dim_inv,
    }
    for name, arr in feats.items():
        aucs = []
        for f in folds:
            # The negative sample is drawn from the same fold's eligible
            # information state.  No distance-to-visible-fault channel is
            # invented here; catalogue-derived controls must be recomputed per
            # fold, not borrowed from fold zero.
            pos = f.truth
            neg = base_elig & ~f.visible & ~f.truth
            nidx = np.nonzero(neg.ravel())[0]
            take = rng.choice(nidx, size=int(min(200_000, nidx.size)), replace=False)
            negm = np.zeros(grid.shape, dtype=bool)
            negm.ravel()[take] = True
            y = np.concatenate([np.ones(int(pos.sum())), np.zeros(int(negm.sum()))])
            s = np.concatenate([arr[pos], arr[negm]]).astype(np.float64)
            aucs.append(holdout55.auc(s, y))
        canary[name] = {"auc_per_fold": [float(a) for a in aucs], "auc_mean": float(np.mean(aucs))}
    res["leakage_canary"] = canary
    res["leakage_flagged_gt_0p90"] = sorted(
        k for k, v in canary.items() if v["auc_mean"] > 0.90
    )

    # ---------------- strike test --------------------------------------------
    z2 = np.load(CACHE / f"lane_{args.tag}.npz")
    strike = z2["strike"]
    dtheta = z2["dtheta"]
    z2.close()
    d_with, d_rand = [], []
    for f in folds:
        segs = holdout55.strike_of_segments(f.truth, min_px=25)
        ridge_px = base_elig & f.withheld & (score > np.quantile(score[base_elig & f.withheld], 0.98))
        ry, rx = np.nonzero(ridge_px)
        for s in segs:
            cy, cx = int(round(s["cy"])), int(round(s["cx"]))
            win = (slice(max(0, cy - 4), cy + 5), slice(max(0, cx - 4), cx + 5))
            seg_px = f.truth[win]
            if seg_px.sum() < 5:
                continue
            sy, sx = np.nonzero(seg_px)
            vals = strike[win][sy, sx]
            d_with.extend(tensor55.angular_difference_deg(np.full(vals.shape, s["azimuth_deg"]), vals).tolist())
        if ry.size:
            pick = rng.choice(ry.size, size=int(min(20000, ry.size)), replace=False)
            rr = rng.random(pick.size) * 180.0
            d_rand.extend(tensor55.angular_difference_deg(rr, strike[ry[pick], rx[pick]]).tolist())
    dw = np.array(d_with, dtype=np.float64)
    dr = np.array(d_rand, dtype=np.float64)
    res["strike_test"] = {
        "n_withheld_segments": int(dw.size),
        "n_random_ridge": int(dr.size),
        "mean_abs_dtheta_withheld_deg": float(dw.mean()),
        "mean_abs_dtheta_random_deg": float(dr.mean()),
        "frac_within_20deg_withheld": float((dw <= 20).mean()),
        "frac_within_20deg_random": float((dr <= 20).mean()),
        "mean_diff_ci95": bootstrap_ci(dw - dr.mean()),
        "lift_fraction_points": float((dw <= 20).mean() - (dr <= 20).mean()),
    }
    print("[strike]", json.dumps(res["strike_test"], indent=2), flush=True)

    EVID.mkdir(parents=True, exist_ok=True)
    out = Path(args.out) if args.out else EVID / f"holdout_{args.tag}_n{args.n_dots}.json"
    out.write_text(json.dumps(res, indent=2))
    print("wrote", out, f"({time.time()-t0:.1f}s)")


if __name__ == "__main__":
    main()
