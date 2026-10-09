#!/usr/bin/env python3
"""EXPERIMENT 2 -- placement strategy at matched mass (the density side of DTI).

Experiment 1 showed the tensor surface beats the null on *strike* but lost to
uniform placement on *DTI*, because top-N-by-score piles the dots into a few
extreme-gradient zones.  This experiment isolates placement from ranking: the
same priors are emitted three ways (clustered top-N, and greedy expected-credit
coverage), and the catalogue-annulus prior is measured as the strong reference.
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
N_DOTS = int(sys.argv[1]) if len(sys.argv) > 1 else 40000
TAG = sys.argv[2] if len(sys.argv) > 2 else "v1"

t0 = time.time()
z = np.load(CACHE / f"lane_{TAG}.npz")
score, ridge, dim, agree = z["score"], z["ridge"], z["dim"], z["agree"]
striping, labels, footprint = z["striping"], z["labels"], z["footprint"]
z.close()
cat = labels == 1
folds = holdout55.make_folds(labels, footprint, grid=(2, 2), buffer_px=3)

def t_ci95(values):
    values = np.asarray(values, dtype=np.float64)
    mean = float(values.mean())
    half = float(student_t.ppf(0.975, len(values) - 1) * values.std(ddof=1) / np.sqrt(len(values)))
    return [mean - half, mean + half]

def run(prior_fn, mode, n=N_DOTS):
    union = np.zeros(labels.shape, dtype=bool); per = []
    for f in folds:
        elig = footprint & f.withheld & ~f.visible      # striping NOT hard-masked
        pri = prior_fn(f)
        if mode == "random":
            d = holdout55.emit_dots(pri, elig, n // len(folds), random=True, seed=11)
        elif mode == "topn":
            d = holdout55.emit_dots(pri, elig, n // len(folds), min_sep_px=3.0)
        elif mode == "greedy":
            d, _ = holdout55.greedy_cover(pri, elig, n // len(folds), r_px=3.0)
        union |= d
        per.append(dti55.dti(d.astype(np.float32), f.truth, mask=f.withheld).dti)
    r = dti55.dti(union.astype(np.float32), cat)
    return {
        "evidence_class": "HOLDOUT-DTI",
        "evaluator_version": "src/gems55/dti55.py",
        "withheld_positive_count": int(cat.sum()),
        "pooled": r.as_dict(),
        "per_fold_dti": per,
        "ci95": t_ci95(per),
        "ci95_method": f"Student-t 95% interval across {len(per)} fold DTI values (df={len(per)-1}); pooled-components DTI is the point estimate.",
        "folds": [round(x, 4) for x in per],
        "wbar": round(r.tp_w / max(r.n_pred_pos, 1), 5),
    }

def cat_annulus(f):
    d = ndimage.distance_transform_edt(~f.visible)
    w = np.clip(1.0 - d / 3.0, 0.0, 1.0).astype(np.float32)
    return np.where(f.visible, 0.0, w)

flat = lambda f: np.ones(labels.shape, dtype=np.float32)
res = {
    "n_dots_target": N_DOTS,
    "tag": TAG,
    "evidence_class": "HOLDOUT-DTI",
    "evaluator_version": "src/gems55/dti55.py",
    "withheld_positive_count": int(cat.sum()),
    "metric_parameters": {"alpha": 0.2, "beta": 0.8, "kernel_radius_m": 300},
    "protocol": "Four whole-quadrant hide-and-recover folds with 3 px buffer; visible faults excluded per fold.",
    "arms": {},
}
ARMS = [
    ("flat_random",        flat, "random"),
    ("flat_greedy",        flat, "greedy"),
    ("ridge_topn",         lambda f: ridge, "topn"),
    ("ridge_greedy",       lambda f: ridge, "greedy"),
    ("tensor_topn",        lambda f: score, "topn"),
    ("tensor_greedy",      lambda f: score, "greedy"),
    ("catann_greedy",      cat_annulus, "greedy"),
    ("tensor_x_catann",    lambda f: (score * cat_annulus(f)).astype(np.float32), "greedy"),
    ("ridge_x_catann",     lambda f: (ridge * cat_annulus(f)).astype(np.float32), "greedy"),
]
for name, fn, mode in ARMS:
    r = run(fn, mode)
    res["arms"][name] = r
    print(f"[{time.time()-t0:7.1f}s] {name:18s} {mode:6s} pooled DTI={r['pooled']['dti']:.4f} "
          f"TP={r['pooled']['tp_w']:8.1f} N={r['pooled']['n_pred_pos']:6d} wbar={r['wbar']:.4f} folds={r['folds']}", flush=True)

EVID.mkdir(exist_ok=True)
(EVID / f"exp2_placement_n{N_DOTS}.json").write_text(json.dumps(res, indent=2))
print("wrote", EVID / f"exp2_placement_n{N_DOTS}.json")
