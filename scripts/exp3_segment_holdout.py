#!/usr/bin/env python3
"""EXPERIMENT 3 -- the decisive holdout: segment-level hide-and-recover.

Protocol per the run brief: withhold whole fault segments with a buffer, derive
every catalogue-based feature only from the visible faults, mask visible faults
pixel-exactly, score the pooled official DTI.
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path
import numpy as np
from scipy import ndimage
from scipy.stats import t as student_t

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems55 import dti55, holdout55, io55  # noqa: E402

CACHE = ROOT / "data" / "cache"; EVID = ROOT / "evidence"
TAG = sys.argv[1] if len(sys.argv) > 1 else "v1"
DOTS = [int(x) for x in (sys.argv[2].split(",") if len(sys.argv) > 2 else ["24000", "40000", "60000"])]

t0 = time.time()
z = np.load(CACHE / f"lane_{TAG}.npz")
score, ridge, dim, agree, plunge = z["score"], z["ridge"], z["dim"], z["agree"], z["plunge"]
striping, labels, footprint = z["striping"], z["labels"], z["footprint"]
z.close()
folds = holdout55.make_segment_folds(labels, footprint, n_folds=5, buffer_px=3, split_px=20, seed=0)

def t_ci95(values):
    values = np.asarray(values, dtype=np.float64)
    mean = float(values.mean())
    half = float(student_t.ppf(0.975, len(values) - 1) * values.std(ddof=1) / np.sqrt(len(values)))
    return [mean - half, mean + half]

print(f"[{time.time()-t0:.1f}s] {len(folds)} segment folds; truth px per fold = "
      f"{[int(f.truth.sum()) for f in folds]}", flush=True)

def cat_credit(f):
    """Kernel-credit field of the VISIBLE catalogue, zeroed on visible pixels."""
    d = ndimage.distance_transform_edt(~f.visible)
    return np.where(f.visible, 0.0, np.clip(1.0 - d / 3.0, 0.0, 1.0)).astype(np.float32)

PRIORS = {
    "flat":            lambda f: np.ones(labels.shape, dtype=np.float32),
    "ridge":           lambda f: ridge,
    "tensor_full":     lambda f: score,
    "tensor_x_2d":     lambda f: (ridge * (1.0 - dim)).astype(np.float32),
    "catann":          cat_credit,
    "tensor_x_catann": lambda f: (score * cat_credit(f)).astype(np.float32),
    "ridge_x_catann":  lambda f: (ridge * cat_credit(f)).astype(np.float32),
    "2d_x_catann":     lambda f: ((1.0 - dim) * cat_credit(f)).astype(np.float32),
}
res = {
    "tag": TAG,
    "n_folds": len(folds),
    "evidence_class": "HOLDOUT-DTI",
    "evaluator_version": "src/gems55/dti55.py",
    "withheld_positive_count": int(np.count_nonzero(labels == 1)),
    "metric_parameters": {"alpha": 0.2, "beta": 0.8, "kernel_radius_m": 300},
    "protocol": "Whole-segment folds, 3 px buffer, per-fold visible-fault masking, pooled components.",
    "truth_per_fold": [int(f.truth.sum()) for f in folds],
    "runs": {},
}

for N in DOTS:
    for name, fn in PRIORS.items():
        for mode in ("greedy", "topn") if name != "flat" else ("random",):
            union = np.zeros(labels.shape, dtype=bool); per = []
            for f in folds:
                elig = footprint & ~f.visible
                pri = fn(f)
                n = N // len(folds)
                if mode == "random":
                    d = holdout55.emit_dots(pri, elig, n, random=True, seed=5)
                elif mode == "topn":
                    d = holdout55.emit_dots(pri, elig, n, min_sep_px=3.0)
                else:
                    d, _ = holdout55.greedy_cover(pri, elig, n, r_px=3.0)
                union |= d
                per.append(dti55.dti(d.astype(np.float32), f.truth, mask=f.truth | f.withheld).dti)
            r = dti55.dti(union.astype(np.float32), np.zeros(labels.shape, dtype=bool) | np.logical_or.reduce([f.truth for f in folds]))
            key = f"n{N}_{name}_{mode}"
            res["runs"][key] = {
                "evidence_class": "HOLDOUT-DTI",
                "evaluator_version": "src/gems55/dti55.py",
                "withheld_positive_count": int(r.n_truth),
                "pooled": r.as_dict(),
                "per_fold_dti": per,
                "ci95": t_ci95(per),
                "ci95_method": f"Student-t 95% interval across {len(per)} fold DTI values (df={len(per)-1}); pooled-components DTI is the point estimate.",
                "folds": [round(x, 4) for x in per],
                "wbar": round(r.tp_w / max(r.n_pred_pos, 1), 5),
            }
            print(f"[{time.time()-t0:7.1f}s] {key:26s} DTI={r.dti:.4f} TP={r.tp_w:8.1f} "
                  f"N={r.n_pred_pos:6d} wbar={r.tp_w/max(r.n_pred_pos,1):.4f}", flush=True)

EVID.mkdir(exist_ok=True)
(EVID / f"exp3_segment_holdout_{TAG}.json").write_text(json.dumps(res, indent=2))
best = max(res["runs"].items(), key=lambda kv: kv[1]["pooled"]["dti"])
print("BEST:", best[0], round(best[1]["pooled"]["dti"], 4))
