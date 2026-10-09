#!/usr/bin/env python3
"""Experiment 9 (E2 of this session): distance-banded segment holdout for H-A.

WHY THIS EXPERIMENT EXISTS.  exp8 showed the two holdouts disagree for a reason
that is structural, not a finding about faults:

  * Q4 (quadrants): held-out catalogue lies a median 180-700 px (18-70 km) from
    any visible catalogue.  A proximity prior has nothing to find there.
  * S10 (10 scattered segment folds, buffer 3 px): held-out catalogue lies a
    median 3.6 px from visible catalogue (78-81 % within 5 px), because segments
    are cut from the same continuous traces.  A proximity prior looks strong.

The real task sits between these.  Hidden faults are not catalogue pixels, and
their distance to the mapped network is unknown.  So we control the gap: withhold
whole segments as in S10, but remove from the visible set every catalogue pixel
within a Euclidean distance B of the withheld truth.  B is then the minimum
truth-to-visible distance, a controlled "distance band".

PRE-REGISTERED (written before the first run of this file):
  Bands B in {3, 15, 30} px  (~0.3, 1.5, 3 km at 100 m).  PRIMARY band: B = 15 px.
  Protocol: 10 seeded whole-segment folds (holdout55.make_segment_folds, seed 0);
            visible = catalogue minus truth minus {distance to truth <= B} (exact EDT).
            Emission: footprint & ~striping & ~visible (never the truth region).
            Scoring: each fold's dots against that fold's truth over the whole
            footprint (official dti55, alpha 0.2, beta 0.8, R 3 px); fold-pooled.
  Arms: random (control), tensor_full (lane, catalogue-free), H-A-500, H-A-1500.
  Verdict per band: H-A-500 "beats" if mean paired fold difference vs random > 0
  with exact sign-flip two-sided p < 0.05 AND beats tensor_full.
  Leakage canary: per-fold AUC of each feature alone; > 0.90 flagged.
  Decision use: the file to ship is the arm with the highest PRIMARY-band
  fold-pooled DTI among non-control arms.  No arm is promoted unless the
  verdict above holds at the primary band.
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
sys.path.insert(0, str(ROOT / "scripts"))

from gems55 import dti55, holdout55, io55  # noqa: E402
from exp8_visible_prior_gate import aggregate, sign_flip_p  # noqa: E402

CACHE = ROOT / "data" / "cache"
EVID = ROOT / "evidence"


def banded_folds(labels, footprint, buffer_px: float):
    """Whole-segment folds with an EXACT Euclidean exclusion of radius buffer_px."""
    base = holdout55.make_segment_folds(labels, footprint, n_folds=10, buffer_px=1, split_px=20, seed=0)
    cat = labels == 1
    out = []
    for f in base:
        d_truth = ndimage.distance_transform_edt(~f.truth)
        visible = cat & ~f.truth & (d_truth > buffer_px)
        out.append(holdout55.Fold(name=f.name, withheld=footprint.copy(), visible=visible, truth=f.truth))
    return out


def run_band(B, folds, arrays, n_total, min_sep, footprint, striping, cat):
    score, ridge, dim, agree, plunge = arrays
    base_elig = footprint & ~striping
    arms = ["random", "tensor_full", "H-A-500", "H-A-1500"]
    per = {a: [] for a in arms}
    canary = []
    rng = np.random.default_rng(7)
    n_per = max(1, n_total // len(folds))
    for k, f in enumerate(folds):
        elig = base_elig & f.withheld & ~f.visible
        dv = ndimage.distance_transform_edt(~f.visible).astype(np.float32)
        p5 = np.exp(-dv / 5.0).astype(np.float32)
        p15 = np.exp(-dv / 15.0).astype(np.float32)
        surf = {"tensor_full": score, "H-A-500": (score * p5).astype(np.float32),
                "H-A-1500": (score * p15).astype(np.float32)}
        for a in arms:
            if a == "random":
                dots = holdout55.emit_dots(score, elig, n_per, min_sep_px=min_sep, seed=1234 + k, random=True)
            else:
                dots = holdout55.emit_dots(surf[a], elig, n_per, min_sep_px=min_sep, seed=1234 + k)
            per[a].append(dti55.dti(dots.astype(np.float32), f.truth, mask=f.withheld).as_dict()
                          | {"n_dots": int(dots.sum())})
        pos = f.truth
        pool = np.nonzero((elig & ~cat).ravel())[0]
        take = rng.choice(pool, size=int(min(200_000, pool.size)), replace=False)
        negm = np.zeros(score.shape, dtype=bool)
        negm.ravel()[take] = True
        y = np.concatenate([np.ones(int(pos.sum())), np.zeros(int(negm.sum()))])
        row = {"fold": k}
        for nm, arr in {"tensor_full_score": score, "ridge": ridge,
                        "one_minus_dim": (1 - dim).astype(np.float32),
                        "strike_agree": agree, "neg_visible_distance": (-dv).astype(np.float32)}.items():
            row[nm] = holdout55.auc(np.concatenate([arr[pos], arr[negm]]).astype(np.float64), y)
        canary.append(row)

    summ = {}
    rand = np.array([p["dti"] for p in per["random"]])
    for a in arms:
        agg = aggregate(per[a])
        if a != "random":
            diffs = np.array([p["dti"] for p in per[a]]) - rand
            m, p = sign_flip_p(diffs)
            agg["diff_vs_random_mean"] = m
            agg["diff_vs_random_signflip_p_two_sided"] = p
            agg["folds_beating_random"] = f"{int((diffs > 0).sum())}/{diffs.size}"
        summ[a] = agg
    cmax = {c: float(np.max([r[c] for r in canary])) for c in canary[0] if c != "fold"}
    cmean = {c: float(np.mean([r[c] for r in canary])) for c in canary[0] if c != "fold"}
    med_truth_dist = []
    for f in folds:
        dv = ndimage.distance_transform_edt(~f.visible)
        med_truth_dist.append(float(np.median(dv[f.truth])))
    return {
        "buffer_px": B,
        "buffer_m": B * 100.0,
        "median_truth_to_visible_px_per_fold": med_truth_dist,
        "arms": summ,
        "canary_auc_max": cmax,
        "canary_auc_mean": cmean,
        "canary_flag_gt_0p90": sorted(c for c, v in cmax.items() if v > 0.90),
        "verdict_H-A-500_beats_random_and_lane": bool(
            summ["H-A-500"]["diff_vs_random_mean"] > 0
            and summ["H-A-500"]["diff_vs_random_signflip_p_two_sided"] < 0.05
            and summ["H-A-500"]["fold_pooled_dti"] > summ["tensor_full"]["fold_pooled_dti"]),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="v1")
    ap.add_argument("--n-dots", type=int, default=40000)
    ap.add_argument("--min-sep", type=float, default=3.0)
    ap.add_argument("--bands", default="3,15,30")
    args = ap.parse_args()
    t0 = time.time()
    z = np.load(CACHE / f"lane_{args.tag}.npz")
    score = z["score"].astype(np.float32)
    arrays = (score, z["ridge"].astype(np.float32), z["dim"].astype(np.float32),
              z["agree"].astype(np.float32), z["plunge"].astype(np.float32))
    striping = z["striping"].astype(bool)
    labels = z["labels"]
    footprint = z["footprint"].astype(bool)
    z.close()
    grid, _ = io55.read_template()
    assert np.array_equal(footprint, grid.footprint)
    cat = labels == 1
    res = {"experiment": "exp9_distance_band (E2)",
           "label": "HOLDOUT-DTI (distance-banded whole-segment folds; dti55 exact official metric)",
           "primary_band_px": 15, "bands": {}}
    for B in [float(b) for b in args.bands.split(",")]:
        folds = banded_folds(labels, footprint, B)
        print(f"B={B:g}px folds={len(folds)} visible_px={[int(f.visible.sum()) for f in folds][:3]}...", flush=True)
        r = run_band(B, folds, arrays, args.n_dots, args.min_sep, footprint, striping, cat)
        res["bands"][str(int(B))] = r
        print(f"  B={int(B)}px  " + "  ".join(f"{a}={v['fold_pooled_dti']:.4f}" for a, v in r["arms"].items())
              + f"  | H-A-500 vs random p={r['arms']['H-A-500']['diff_vs_random_signflip_p_two_sided']:.3f}"
              + f"  | canary max={max(r['canary_auc_max'].values()):.3f}", flush=True)
    res["seconds"] = round(time.time() - t0, 1)
    out = EVID / "exp9_distance_band_v1_n40000.json"
    out.write_text(json.dumps(res, indent=2))
    print("wrote", out, f"{res['seconds']} s")


if __name__ == "__main__":
    main()
