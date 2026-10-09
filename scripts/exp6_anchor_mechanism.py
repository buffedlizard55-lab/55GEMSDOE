#!/usr/bin/env python3
"""What is the 0.2778 anchor actually targeting?

exp5 established the surprising fact: the h33 raster harvests almost no kernel
credit from the visible catalogue (proxy DTI 0.0049, i.e. 3.4x BELOW a uniform
random scatter of the same size), and yet it is one of the best-scoring
submissions.  So the hidden truth is systematically disjoint from the visible
catalogue, and h33 is finding it some other way.

Here we ask what.  We test the h33 dot mask against every band of the official
19-layer stack, against our own lane surface, and against simple ridge masks, and
report point-biserial correlation and lift.  Nothing here is a score.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
import rasterio
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems55 import dti55, io55  # noqa: E402

H33 = "registry/rasters/GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-nan.tif"
OURS = "docs/downloads/h55-tensor2d-strikegate-40000dots-20261009T052235Z-zeros.tif"

grid, template = io55.read_template()
H, W = template.shape
footprint = np.isfinite(template)
truth = io55.read_labels() == 1
G = int(truth.sum()); F = int(footprint.sum())
w_cat = dti55.kernel_credit(truth)
near_cat = ndimage.maximum_filter(truth.astype(np.uint8), size=7) > 0   # within 3 px


def load(p):
    with rasterio.open(ROOT / p) as s:
        a = s.read(1).astype(np.float32)
    return np.nan_to_num(a, nan=0.0, posinf=0.0, neginf=0.0) > 0


def describe(mask, name, out):
    N = int(mask.sum())
    idx = np.flatnonzero(mask.ravel())
    # anti-catalogue index: dots within 3px of a visible fault vs the random expectation
    frac_near = float(near_cat.ravel()[idx].mean())
    exp_near = float(near_cat[footprint].sum()) / F
    # dispersion
    sub = np.random.default_rng(1).choice(N, size=min(N, 3000), replace=False)
    ys, xs = np.unravel_index(idx[sub], (H, W))
    d = np.hypot(ys[:, None] - ys[None, :], xs[:, None] - xs[None, :]).astype(np.float32)
    np.fill_diagonal(d, np.inf)
    out[name] = {
        "n_dots": N,
        "catalogue_proxy_DTI": float(w_cat.ravel()[idx].sum()) / (dti55.ALPHA * N + dti55.BETA * G),
        "frac_dots_within_3px_of_visible_fault": frac_near,
        "random_expectation_of_that_fraction": exp_near,
        "anti_catalogue_index": exp_near / max(frac_near, 1e-12),
        "nn_px_mean": float(np.percentile(d.min(1), 50)),
        "n_dots_on_visible_fault_px": int(truth.ravel()[idx].sum()),
    }
    print(f"{name}: N={N} proxyDTI={out[name]['catalogue_proxy_DTI']:.4f} "
          f"nearFault={frac_near:.4f} (rand {exp_near:.4f}, index "
          f"{out[name]['anti_catalogue_index']:.2f}x)")


rng = np.random.default_rng(7)
res = {"grid": {"footprint": F, "catalogue_px": G,
                "frac_footprint_within_3px_of_fault": float(near_cat[footprint].mean())},
       "rasters": {}}
fp_idx = np.flatnonzero(footprint.ravel())
rand = np.zeros(H * W, bool); rand[rng.choice(fp_idx, size=44090, replace=False)] = True
describe(rand, "uniform_random_44090", res["rasters"])
describe(load(H33), "h33_2_b2_SCORED_0.2778", res["rasters"])
describe(load(OURS), "ours_h55_40000", res["rasters"])

# --- what does h33 correlate with? -------------------------------------------------
h33 = load(H33)
hb = h33 & footprint
names = io55.band_descriptions()
rows = []
h33v = hb.ravel()
for b in sorted(names):
    band, valid = io55.read_band(b)
    x = np.where(valid & footprint, band, np.nan)
    xr = x.ravel()
    m = np.isfinite(xr)
    a1 = xr[m]; a0 = h33v[m]
    if a0.sum() < 100 or (~a0).sum() < 100:
        continue
    lift = a1[a0].mean() / a1[~a0].mean() if a1[~a0].mean() != 0 else float("nan")
    # rank correlation on a subsample (full-array Spearman on 5M pts is fine but slow)
    s = np.random.default_rng(3).choice(a1.size, size=min(a1.size, 400000), replace=False)
    from scipy.stats import rankdata
    r = np.corrcoef(rankdata(a1[s]), rankdata(a0[s].astype(np.float64)))[0, 1]
    rows.append({"band": b, "name": names[b], "mean_on_dot": float(a1[a0].mean()),
                 "mean_off_dot": float(a1[~a0].mean()), "lift": float(lift),
                 "spearman": float(r)})
    print(f"  band {b:2d} {names[b][:38]:38s} lift={lift:6.3f} rho={r:+.4f}")
    del band, valid, x
rows.sort(key=lambda d: -abs(d["spearman"]))
res["h33_vs_bands"] = rows

Path(ROOT / "evidence/anchor_mechanism.json").write_text(json.dumps(res, indent=2))
print("top correlates:", [(r["band"], round(r["spearman"], 4)) for r in rows[:4]])
