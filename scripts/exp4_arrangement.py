#!/usr/bin/env python3
"""EXPERIMENT 4 -- arrangement (spread) at matched mass, leakage-free holdout.

Exp 1 showed the tensor surface loses to uniform placement at N=40k because
top-N-by-score piles dots into a few extreme-gradient zones.  DTI =
TP/(0.2N + 0.8|G|), so *coverage* is what pays.  This sweeps the NMS separation,
which is the arrangement knob, on the contiguous-quadrant holdout where the
catalogue-annulus prior is structurally unavailable (no leakage).
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems55 import dti55, holdout55, io55  # noqa: E402
CACHE = ROOT/"data"/"cache"; EVID = ROOT/"evidence"
TAG = sys.argv[1] if len(sys.argv) > 1 else "v1"
N = int(sys.argv[2]) if len(sys.argv) > 2 else 40000

z = np.load(CACHE/f"lane_{TAG}.npz")
score, ridge, dim, striping = z["score"], z["ridge"], z["dim"], z["striping"]
labels, footprint = z["labels"], z["footprint"]; z.close()
cat = labels == 1
folds = holdout55.make_folds(labels, footprint, grid=(2,2), buffer_px=3)
t0 = time.time(); res = {"tag": TAG, "n_target": N, "runs": {}}
SURF = {"flat": ridge*0+1e-6, "ridge": ridge, "tensor": score,
        "tensor_2d": (ridge*(1.0-dim)).astype(np.float32)}
for name, surf in SURF.items():
    for sep in (3.0, 6.0, 10.0, 16.0, 24.0):
        union = np.zeros(labels.shape, dtype=bool)
        for f in folds:
            elig = footprint & f.withheld & ~f.visible
            if name == "flat":
                d = holdout55.emit_dots(surf, elig, N//len(folds), random=True, seed=5)
            else:
                d = holdout55.emit_dots(surf, elig, N//len(folds), min_sep_px=sep)
            union |= d
        r = dti55.dti(union.astype(np.float32), cat)
        key = f"{name}_sep{sep:g}"
        res["runs"][key] = r.as_dict() | {"wbar": round(r.tp_w/max(r.n_pred_pos,1),5)}
        print(f"[{time.time()-t0:6.1f}s] {key:20s} DTI={r.dti:.4f} TP={r.tp_w:8.1f} N={r.n_pred_pos:6d} "
              f"wbar={r.tp_w/max(r.n_pred_pos,1):.4f}", flush=True)
        if name == "flat":
            break
EVID.mkdir(exist_ok=True); (EVID/f"exp4_arrangement_n{N}.json").write_text(json.dumps(res, indent=2))
b = max(res["runs"].items(), key=lambda kv: kv[1]["dti"]); print("BEST:", b[0], round(b[1]["dti"],4))
