#!/usr/bin/env python3
"""Final forensic verdict on the 0.2778 anchor.

Corrections over exp5/exp6, both of which are superseded by this file:
  * exp5 drew its random control over ALL H*W cells instead of the footprint,
    diluting it by ~2.4x.  Fixed: controls are drawn from footprint cells only.
  * exp5/exp6 estimated nearest-neighbour spacing from a 3,000-point subsample,
    which inflates NN by sqrt(44090/3000) ~ 3.8x.  Fixed: exact NN via cKDTree on
    the full dot set.

Facts taken from GEMSDOE32's own audit manifest
(docs/downloads/submissions_manifest.json, generated 2026-10-04T15:27:17Z by
scripts/audit_shipped.py), fetched read-only from api.github.com.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
import rasterio
from scipy import ndimage
from scipy.spatial import cKDTree
from scipy.stats import rankdata

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems55 import dti55, io55  # noqa: E402

MANIFEST = {  # verbatim from GEMSDOE32 submissions_manifest.json
    "h33-2-b2": {"proxy_DTI_author": 0.0067, "credit_per_dot_author": 0.0100,
                 "dots": 37654, "dots_on_catalogue": 0, "receipt": None,
                 "author_note": ("flank B=2 prune on the 0.2708 base: 37,654 dots, "
                                 "0 within 200 m of the catalogue; live-mirror "
                                 "+0.00487 in 4/4 folds, safety 2.08, "
                                 "projected 0.2747; UNSCORED")},
    "d28/0.2600-anchor": {"proxy_DTI_author": 0.1618, "credit_per_dot_author": 0.2154,
                          "dots": 44090, "dots_on_catalogue": 0, "receipt": None},
}
FILES = {
    "h33_2_b2": "registry/rasters/GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-nan.tif",
    "d28_0.2600_anchor": "registry/rasters/GEMSDOE30__gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca-nanoutside.tif",
    "ours_h55": "docs/downloads/h55-tensor2d-strikegate-40000dots-20261009T052235Z-zeros.tif",
}
A, B = dti55.ALPHA, dti55.BETA

grid, template = io55.read_template()
H, W = template.shape
footprint = np.isfinite(template)
truth = io55.read_labels() == 1
G, F = int(truth.sum()), int(footprint.sum())
w_cat = dti55.kernel_credit(truth)
dt_cat = ndimage.distance_transform_edt(~truth)          # px to nearest mapped fault
fp_idx = np.flatnonzero(footprint.ravel())
names = io55.band_descriptions()
rng = np.random.default_rng(11)


def load(p):
    with rasterio.open(ROOT / p) as s:
        a = s.read(1).astype(np.float32)
    return np.nan_to_num(a, nan=0.0, posinf=0.0, neginf=0.0) > 0


def measure(mask, key):
    idx = np.flatnonzero(mask.ravel())
    N = int(idx.size)
    tpw = float(w_cat.ravel()[idx].sum())
    ys, xs = np.unravel_index(idx, (H, W))
    nn = cKDTree(np.stack([ys, xs], 1).astype(np.float64)).query(
        np.stack([ys, xs], 1).astype(np.float64), k=2)[0][:, 1]
    dist = dt_cat.ravel()[idx]
    rec = {
        "n_dots": N,
        "TP_w_vs_visible_catalogue": tpw,
        "credit_per_dot": tpw / N,
        "catalogue_proxy_DTI": tpw / (A * N + B * G),
        "dots_on_visible_fault_px": int(truth.ravel()[idx].sum()),
        "min_distance_to_mapped_fault_px": float(dist.min()),
        "median_distance_to_mapped_fault_px": float(np.median(dist)),
        "frac_dots_within_300m_of_a_mapped_fault": float((dist <= 3).mean()),
        "nn_px_mean": float(nn.mean()), "nn_px_p10": float(np.percentile(nn, 10)),
    }
    # top band correlates
    rows = []
    h = mask.ravel()
    for b in sorted(names):
        band, valid = io55.read_band(b)
        xr = np.where(valid & footprint, band, np.nan).ravel()
        m = np.isfinite(xr)
        a1, a0 = xr[m], h[m]
        if a0.sum() < 100 or (~a0).sum() < 100:
            del band, valid; continue
        s = rng.choice(a1.size, size=min(a1.size, 400000), replace=False)
        rows.append((b, float(np.corrcoef(rankdata(a1[s]), rankdata(a0[s].astype(float)))[0, 1])))
        del band, valid, xr
    rows.sort(key=lambda t: -abs(t[1]))
    rec["top_band_correlates"] = [{"band": b, "spearman": round(r, 4)} for b, r in rows[:4]]
    rec["max_abs_band_spearman"] = abs(rows[0][1])
    return rec


res = {"grid": {"footprint_px": F, "catalogue_px": G,
                "sum_kernel_credit": float(w_cat.sum())},
       "rasters": {}, "random_controls_footprint_restricted": {},
       "manifest_facts": MANIFEST,
       "algebra": {"identity": "TP_w + FN_w = |G|  =>  DTI = TP_w/(0.2N + 0.8|G|)",
                   "upper_bound": "DTI <= |G| / (0.2N + 0.8|G|) since each truth pixel can contribute at most 1.0"}}

for key, path in FILES.items():
    res["rasters"][key] = measure(load(path), key)
    r = res["rasters"][key]
    print(f"{key:20s} N={r['n_dots']:6d} proxy={r['catalogue_proxy_DTI']:.4f} "
          f"cr/dot={r['credit_per_dot']:.4f} minDist={r['min_distance_to_mapped_fault_px']:.0f}px "
          f"medDist={r['median_distance_to_mapped_fault_px']:.1f}px "
          f"nn={r['nn_px_mean']:.2f}px maxrho={r['max_abs_band_spearman']:.4f}")

for N in (37654, 40000, 44090):
    idx = rng.choice(fp_idx, size=N, replace=False)
    m = np.zeros(H * W, bool); m[idx] = True
    tpw = float(w_cat.ravel()[idx].sum())
    res["random_controls_footprint_restricted"][N] = {
        "TP_w": tpw, "credit_per_dot": tpw / N,
        "catalogue_proxy_DTI": tpw / (A * N + B * G)}
    print(f"random N={N}: proxy={res['random_controls_footprint_restricted'][N]['catalogue_proxy_DTI']:.4f} "
          f"cr/dot={tpw/N:.4f}")

# what does a target score require?
req = {}
for target in (0.2600, 0.2708, 0.2747, 0.2778, 0.3195, 0.3774):
    for N in (37654, 44090):
        gmin = target * A * N / (1 - target * B)
        req[f"{target}@N={N}"] = {"min_abs_G_for_any_placement": round(gmin, 1),
                                  "required_TP_w_per_dot_at_that_G": round(gmin * target / N, 4)}
res["what_a_target_score_requires"] = req
print()
for k, v in req.items():
    print(f"  {k}: |G| >= {v['min_abs_G_for_any_placement']:.0f} px and "
          f"TP_w/dot >= {v['required_TP_w_per_dot_at_that_G']:.4f}")

Path(ROOT / "evidence/anchor_verdict.json").write_text(json.dumps(res, indent=2))
print("\nwrote evidence/anchor_verdict.json")
