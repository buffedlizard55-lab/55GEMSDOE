#!/usr/bin/env python3
"""Experiment 10 (E3 of this session, the LAST experiment in the budget): dot-mass sweep.

WHY.  The official metric is DTI = TP_w / (0.2 N + 0.8 |G|) on a dot raster, so the
dot count N is itself a decision.  A dot raises DTI when its expected kernel credit
exceeds the break-even alpha*DTI/(1+alpha*DTI) (dti55.breakeven_credit).  At holdout
DTI of 0.008 that bar is ~0.0016 credit per dot; at 0.07 it is ~0.014.  So the best
N is not obvious and must be measured, not guessed from leaderboard rows.

PRE-REGISTERED (written before the first run):
  N in {20000, 40000, 80000, 160000} total dots, split equally over folds.
  Arms: random (control) and tensor_full (the lane; the only non-control arm that
        was not refuted in E1/E2 relative to random at the primary band).
  Protocols: Q4 (quadrants, PRIMARY) and B=15 px distance-banded segments (SECONDARY).
  Metric and visibility: identical to exp8/exp9 (fold-pooled DTI, per-fold visible).
  Decision rule for the FILE TO SHIP:
    N* = argmax_N of tensor_full fold-pooled DTI on the PRIMARY protocol (Q4).
    The file is labelled POSITIVE only if tensor_full(N*) beats random(N*) on Q4 with
    exact sign-flip two-sided p < 0.05 AND on B=15. Otherwise NEGATIVE.
    The label is HOLDOUT-DTI in every case.
"""
from __future__ import annotations

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
from exp9_distance_band import banded_folds  # noqa: E402

CACHE = ROOT / "data" / "cache"
EVID = ROOT / "evidence"
NS = [20000, 40000, 80000, 160000]


def run(folds, score, striping, footprint, n_total, min_sep=3.0):
    base_elig = footprint & ~striping
    n_per = n_total // len(folds)
    rows = {"random": [], "tensor_full": []}
    for k, f in enumerate(folds):
        elig = base_elig & f.withheld & ~f.visible
        for arm in rows:
            dots = holdout55.emit_dots(score, elig, n_per, min_sep_px=min_sep, seed=1234 + k,
                                       random=(arm == "random"))
            rows[arm].append(dti55.dti(dots.astype(np.float32), f.truth, mask=f.withheld).as_dict()
                             | {"n_dots": int(dots.sum())})
    rnd = np.array([p["dti"] for p in rows["random"]])
    tns = np.array([p["dti"] for p in rows["tensor_full"]])
    m, p = sign_flip_p(tns - rnd)
    return {
        "N_requested": n_total,
        "random": aggregate(rows["random"]),
        "tensor_full": aggregate(rows["tensor_full"]),
        "tensor_minus_random_mean": m,
        "tensor_minus_random_signflip_p_two_sided": p,
        "tensor_folds_beating_random": f"{int((tns - rnd > 0).sum())}/{tns.size}",
    }


def main() -> None:
    t0 = time.time()
    z = np.load(CACHE / "lane_v1.npz")
    score = z["score"].astype(np.float32)
    striping = z["striping"].astype(bool)
    labels = z["labels"]
    footprint = z["footprint"].astype(bool)
    z.close()
    from gems55 import io55 as _io
    grid, _ = _io.read_template()
    assert np.array_equal(footprint, grid.footprint)

    q4 = holdout55.make_folds(labels, footprint, grid=(2, 2), buffer_px=3)
    b15 = banded_folds(labels, footprint, 15.0)
    res = {"experiment": "exp10_mass_sweep (E3, last)",
           "label": "HOLDOUT-DTI (fold-pooled, per-fold visible-only; dti55 exact metric)",
           "protocols": {"Q4_primary": {}, "B15_secondary": {}}}
    for N in NS:
        r = run(q4, score, striping, footprint, N)
        res["protocols"]["Q4_primary"][str(N)] = r
        print(f"Q4  N={N:6d}  tensor={r['tensor_full']['fold_pooled_dti']:.4f}  "
              f"random={r['random']['fold_pooled_dti']:.4f}  diff={r['tensor_minus_random_mean']:+.4f} "
              f"p={r['tensor_minus_random_signflip_p_two_sided']:.3f}", flush=True)
    for N in NS:
        r = run(b15, score, striping, footprint, N)
        res["protocols"]["B15_secondary"][str(N)] = r
        print(f"B15 N={N:6d}  tensor={r['tensor_full']['fold_pooled_dti']:.4f}  "
              f"random={r['random']['fold_pooled_dti']:.4f}  diff={r['tensor_minus_random_mean']:+.4f} "
              f"p={r['tensor_minus_random_signflip_p_two_sided']:.3f}", flush=True)

    q = res["protocols"]["Q4_primary"]
    n_star = max(q, key=lambda n: q[n]["tensor_full"]["fold_pooled_dti"])
    star = q[n_star]
    b = res["protocols"]["B15_secondary"][n_star]
    positive = (star["tensor_minus_random_mean"] > 0 and star["tensor_minus_random_signflip_p_two_sided"] < 0.05
                and b["tensor_minus_random_mean"] > 0 and b["tensor_minus_random_signflip_p_two_sided"] < 0.05)
    res["decision"] = {"N_star_by_Q4_tensor_full": int(n_star),
                       "label": "POSITIVE" if positive else "NEGATIVE",
                       "reason": "tensor_full(N*) must beat random(N*) on Q4 and on B15 with p<0.05"}
    res["seconds"] = round(time.time() - t0, 1)
    out = EVID / "exp10_mass_sweep_v1.json"
    out.write_text(json.dumps(res, indent=2))
    print("decision", res["decision"], "wrote", out, f"{res['seconds']} s")


if __name__ == "__main__":
    main()
