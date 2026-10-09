#!/usr/bin/env python3
"""Experiment 8 (this session's single candidate experiment): H-A visible-catalogue prior x tensor lane.

PRE-REGISTERED before this file was first run (see docs/hypotheses.md, section H-A):

  Hypothesis H-A.  Unmapped faults cluster with mapped faults at the 0.5-1.5 km
  scale, so the lane score (ridge x 2-D gate x strike agreement x plunge, the
  one part of the lane that is catalogue-free) multiplied by a proximity prior
  built ONLY from the visible catalogue of each fold should beat both the lane
  alone and uniform random placement at matched mass.

  Arms (matched N per protocol):
    random       uniform over the eligible set                 (control)
    tensor_full  lane score alone                              (reference, prior run 0.0667)
    H-A-500      lane score x exp(-d_vis / 5 px)     PRIMARY candidate
    H-A-1500     lane score x exp(-d_vis / 15 px)    secondary
    prox-500     exp(-d_vis / 5 px) alone            ablation (no tensor gate)
    prox-1500    exp(-d_vis / 15 px) alone           ablation

  Protocols (both fold-wise, every feature recomputed from that fold's visible set):
    Q4  contiguous quadrants (shared template protocol, holdout55.make_folds)  PRIMARY PROTOCOL
    S10 whole-segment scattered withholding, 10 folds (holdout55.make_segment_folds)  secondary

  Metric.  Each fold's dots are scored ONLY against that fold's own withheld
  truth, inside its withheld mask, with the official distance-weighted Tversky
  index (dti55.dti).  Folds are aggregated as sum(TP_w) / sum(TP_w + a FP_w + b FN_w).
  The union-across-folds ("pooled") score used by evaluate_holdout.py is NOT used
  for the catalogue-prior arms: a fold-k dot placed next to fold-j traces would be
  credited against fold-j truth that was visible when the dot was chosen (leak).

  Decision rule (pre-registered).  H-A-500 is PROMOTED to a submission candidate
  only if, in BOTH protocols, its mean per-fold DTI minus random's is > 0 AND the
  exact sign-flip test on paired fold differences has two-sided p < 0.05 AND it
  beats the tensor_full reference.  Otherwise the verdict is NEGATIVE and the
  file is still written, labelled negative.  The labels are HOLDOUT-DTI.

  Leakage canary: each feature alone, AUC per fold against that fold's truth
  (own visible set); AUC > 0.90 means leakage until proven otherwise.

  Run log (kept for audit).
    run 1: S10 emission region was truth|buffer (oracle).  Result discarded:
           random control scored 0.326 on S10 against 0.074 on Q4.  Output kept as
           evidence/exp8_RUN1_DISCARDED_oracle_S10_v1_n40000.json.  See IR-55-018.
    run 2: holdout55.make_segment_folds now returns withheld = footprint.  Reported.
"""
from __future__ import annotations

import argparse
import itertools
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems55 import dti55, holdout55, io55  # noqa: E402

CACHE = ROOT / "data" / "cache"
EVID = ROOT / "evidence"


def fold_dti(dots: np.ndarray, f) -> dict:
    r = dti55.dti(dots.astype(np.float32), f.truth, mask=f.withheld)
    return r.as_dict() | {"n_dots": int(dots.sum())}


def aggregate(per_fold: list[dict]) -> dict:
    tp = sum(p["tp_w"] for p in per_fold)
    fp = sum(p["fp_w"] for p in per_fold)
    fn = sum(p["fn_w"] for p in per_fold)
    d = [p["dti"] for p in per_fold]
    return {
        "fold_pooled_dti": tp / (tp + dti55.ALPHA * fp + dti55.BETA * fn + dti55.EPS),
        "fold_mean_dti": float(np.mean(d)),
        "per_fold_dti": [round(x, 6) for x in d],
        "n_withheld_truth": int(sum(p["n_truth"] for p in per_fold)),
        "n_dots": int(sum(p["n_dots"] for p in per_fold)),
    }


def sign_flip_p(diffs: np.ndarray) -> tuple[float, float]:
    """Exact two-sided sign-flip test on paired fold differences; returns (mean, p)."""
    d = np.asarray(diffs, dtype=np.float64)
    obs = abs(d.mean())
    k = d.size
    if k <= 16:
        signs = np.array(list(itertools.product([-1.0, 1.0], repeat=k)))
        stats = np.abs((signs * d).mean(axis=1))
    else:
        rng = np.random.default_rng(0)
        signs = rng.choice([-1.0, 1.0], size=(200_000, k))
        stats = np.abs((signs * d).mean(axis=1))
    return float(d.mean()), float((stats >= obs - 1e-15).mean())


def run_protocol(name, folds, arrays, n_total, min_sep, footprint, striping, cat):
    score, ridge, dim, agree, plunge = arrays
    base_elig = footprint & ~striping
    lane = score
    arms = {}
    per_arm_folds: dict[str, list[dict]] = {a: [] for a in ["random", "tensor_full", "H-A-500", "H-A-1500", "prox-500", "prox-1500"]}
    canary_rows: list[dict] = []
    rng = np.random.default_rng(7)
    n_per = max(1, n_total // len(folds))
    for k, f in enumerate(folds):
        elig = base_elig & f.withheld & ~f.visible
        dv = ndimage.distance_transform_edt(~f.visible).astype(np.float32)  # own visible set only
        p5 = np.exp(-dv / 5.0).astype(np.float32)
        p15 = np.exp(-dv / 15.0).astype(np.float32)
        surfaces = {
            "tensor_full": lane,
            "H-A-500": (lane * p5).astype(np.float32),
            "H-A-1500": (lane * p15).astype(np.float32),
            "prox-500": p5,
            "prox-1500": p15,
        }
        for arm in per_arm_folds:
            if arm == "random":
                dots = holdout55.emit_dots(lane, elig, n_per, min_sep_px=min_sep, seed=1234 + k, random=True)
            else:
                dots = holdout55.emit_dots(surfaces[arm], elig, n_per, min_sep_px=min_sep, seed=1234 + k)
            per_arm_folds[arm].append(fold_dti(dots, f))

        # leakage canary: each feature alone, AUC on this fold, own visible set
        pos = f.truth
        neg_pool = np.nonzero((elig & ~cat).ravel())[0]
        take = rng.choice(neg_pool, size=int(min(200_000, neg_pool.size)), replace=False)
        negm = np.zeros(score.shape, dtype=bool)
        negm.ravel()[take] = True
        y = np.concatenate([np.ones(int(pos.sum())), np.zeros(int(negm.sum()))])
        feats = {
            "tensor_full_score": lane,
            "ridge": ridge,
            "one_minus_dim": (1.0 - dim).astype(np.float32),
            "strike_agree": agree,
            "neg_visible_distance": (-dv).astype(np.float32),
        }
        row = {"fold": k}
        for fn_name, arr in feats.items():
            s = np.concatenate([arr[pos], arr[negm]]).astype(np.float64)
            row[fn_name] = holdout55.auc(s, y)
        canary_rows.append(row)
        print(f"  [{name}] fold {k}: truth={int(pos.sum())} elig={int(elig.sum())}", flush=True)

    summary = {}
    rand = np.array([p["dti"] for p in per_arm_folds["random"]])
    for arm, pf in per_arm_folds.items():
        agg = aggregate(pf)
        if arm != "random":
            diffs = np.array([p["dti"] for p in pf]) - rand
            mean_d, pval = sign_flip_p(diffs)
            agg["diff_vs_random_mean"] = mean_d
            agg["diff_vs_random_signflip_p_two_sided"] = pval
            agg["folds_beating_random"] = f"{int((diffs > 0).sum())}/{diffs.size}"
        summary[arm] = agg
        print(f"  [{name}] {arm:12s} fold-pooled DTI={agg['fold_pooled_dti']:.4f} "
              f"fold-mean={agg['fold_mean_dti']:.4f} dots={agg['n_dots']}", flush=True)
    canary_mean = {c: float(np.mean([r[c] for r in canary_rows])) for c in canary_rows[0] if c != "fold"}
    canary_max = {c: float(np.max([r[c] for r in canary_rows])) for c in canary_rows[0] if c != "fold"}
    return {
        "protocol": name,
        "n_folds": len(folds),
        "n_total_dots": n_total,
        "arms": summary,
        "leakage_canary_auc_mean": canary_mean,
        "leakage_canary_auc_max": canary_max,
        "leakage_canary_rows": canary_rows,
        "leakage_flag_gt_0p90": sorted(k for k, v in canary_max.items() if v > 0.90),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="v1")
    ap.add_argument("--n-dots", type=int, default=40000)
    ap.add_argument("--min-sep", type=float, default=3.0)
    ap.add_argument("--out", default=str(EVID / "exp8_visible_prior_gate_v1_n40000.json"))
    args = ap.parse_args()
    t0 = time.time()

    z = np.load(CACHE / f"lane_{args.tag}.npz")
    score = z["score"].astype(np.float32)
    ridge = z["ridge"].astype(np.float32)
    dim = z["dim"].astype(np.float32)
    agree = z["agree"].astype(np.float32)
    plunge = z["plunge"].astype(np.float32)
    striping = z["striping"].astype(bool)
    labels = z["labels"]
    footprint = z["footprint"].astype(bool)
    z.close()
    grid, _ = io55.read_template()
    assert footprint.shape == grid.shape and np.array_equal(footprint, grid.footprint)
    cat = labels == 1
    arrays = (score, ridge, dim, agree, plunge)

    q4 = holdout55.make_folds(labels, footprint, grid=(2, 2), buffer_px=3)
    s10 = holdout55.make_segment_folds(labels, footprint, n_folds=10, buffer_px=3, split_px=20, seed=0)
    print(f"Q4 folds={len(q4)} truth={[int(f.truth.sum()) for f in q4]}")
    print(f"S10 folds={len(s10)} truth={[int(f.truth.sum()) for f in s10]}", flush=True)

    res = {
        "experiment": "exp8_visible_prior_gate",
        "label": "HOLDOUT-DTI (per-fold visible-only features; dti55 exact official metric)",
        "evaluator": "src/gems55/dti55.py alpha=0.2 beta=0.8 R=3px (300 m triangular kernel)",
        "n_catalogue_px": int(cat.sum()),
        "protocols": {},
    }
    res["protocols"]["Q4"] = run_protocol("Q4", q4, arrays, args.n_dots, args.min_sep, footprint, striping, cat)
    res["protocols"]["S10"] = run_protocol("S10", s10, arrays, args.n_dots, args.min_sep, footprint, striping, cat)

    # ---- verdict under the pre-registered rule -------------------------------
    verdict = {}
    for pname, pr in res["protocols"].items():
        a = pr["arms"]["H-A-500"]
        ok = (
            a["diff_vs_random_mean"] > 0
            and a["diff_vs_random_signflip_p_two_sided"] < 0.05
            and a["fold_pooled_dti"] > pr["arms"]["tensor_full"]["fold_pooled_dti"]
        )
        verdict[pname] = {"H-A-500_beats_random_and_lane_with_p_lt_0.05": bool(ok)}
    res["pre_registered_verdict"] = verdict
    res["promote"] = all(v["H-A-500_beats_random_and_lane_with_p_lt_0.05"] for v in verdict.values())
    res["seconds"] = round(time.time() - t0, 1)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, indent=2))
    print(json.dumps({k: v for k, v in res.items() if k != "protocols"}, indent=2))
    for pname, pr in res["protocols"].items():
        print(pname, {a: round(v["fold_pooled_dti"], 4) for a, v in pr["arms"].items()})
        print(pname, "canary max AUC", {c: round(v, 3) for c, v in pr["leakage_canary_auc_max"].items()})
    print("wrote", out, f"({res['seconds']} s)")


if __name__ == "__main__":
    main()
