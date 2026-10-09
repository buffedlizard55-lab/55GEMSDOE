#!/usr/bin/env python3
"""Forensics on the ORGANIZER-CONFIRMED anchors we can actually read.

Two scored anchors have their rasters in registry/rasters:
    h33-2-b2            GEMSDOE32  ...e5eb6e7e-nan.tif   -> 0.2778
    poisson300m-offcat  GEMSDOE30  ...91eae1ca           -> 0.2600
    efd28-repro         GEMSDOE29  ...1cc7dc534d51       -> (a third-party reproduction of d28)

For each we measure the dot statistics, score it against the *visible* catalogue
with the exact official evaluator, and then solve for the hidden-test truth size
|G| that makes the algebra DTI = TP_w/(0.2 N + 0.8 |G|) reproduce the confirmed
score.  Everything printed is a measurement or an algebraic solution; nothing is
a projection dressed as a score.
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

ANCHORS = {
    "h33-2-b2 (0.2778)": ("registry/rasters/GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-nan.tif", 0.2778),
    "poisson300m-offcat (0.2600)": ("registry/rasters/GEMSDOE30__gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca-nanoutside.tif", 0.2600),
    "efd28-repro (unconfirmed)": ("registry/rasters/GEMSDOE29__gems29-refd28-repro-20261003-1cc7dc534d51-nan.tif", None),
}
ALPHA, BETA = dti55.ALPHA, dti55.BETA

grid, template = io55.read_template()
H, W = template.shape
footprint = np.isfinite(template)
labels = io55.read_labels()
truth = (labels == 1)
G_cat = int(truth.sum())
F = int(footprint.sum())

# kernel credit of a truth pixel set: w(x) = max_g k(d(g,x))
w_cat = dti55.kernel_credit(truth)

out = {"grid": {"shape": [H, W], "footprint_px": F, "catalogue_px": G_cat,
                "sum_kernel_credit": float(w_cat.sum())}, "anchors": {}}
rng = np.random.default_rng(0)

for name, (path, confirmed) in ANCHORS.items():
    with rasterio.open(ROOT / path) as src:
        a = src.read(1).astype(np.float32)
    finite = np.isfinite(a)
    pos = finite & (a > 0)
    N = int(pos.sum())
    on_cat = int((pos & truth).sum())
    # how much of the catalogue's kernel credit is actually harvested
    tpw = float(w_cat[pos].sum())
    dti_cat = tpw / (ALPHA * N + BETA * G_cat)

    # nearest-neighbour spacing among the dots -> reveals lattice vs clustered vs Poisson
    ys, xs = np.nonzero(pos)
    NSUB = 3000  # 20000 would need a 3.2 GB float64 distance matrix
    sub = rng.choice(N, size=min(N, NSUB), replace=False) if N > NSUB else np.arange(N)
    pts = np.stack([ys[sub], xs[sub]], 1).astype(np.float64)
    d = np.hypot(pts[:, None, 0] - pts[None, :, 0], pts[:, None, 1] - pts[None, :, 1])
    np.fill_diagonal(d, np.inf)
    nn = d.min(1)
    # value distribution
    vals = a[pos]
    # coverage: fraction of catalogue truth pixels with any dot within 3 px
    near = ndimage.maximum_filter(pos.astype(np.uint8), size=7) > 0   # any dot within 3 px
    covered = int((near & truth).sum())

    rec = {
        "n_dots": N,
        "mean_value": float(vals.mean()), "max_value": float(vals.max()),
        "min_value": float(vals.min()),
        "n_distinct_values": int(np.unique(np.round(vals, 6)).size),
        "dots_on_catalogue_px": on_cat,
        "catalogue_truth_covered_within_3px_frac": covered / G_cat,
        "TP_w_vs_visible_catalogue": tpw,
        "mean_credit_per_dot": tpw / N,
        "catalogue_proxy_DTI": dti_cat,
        "organizer_confirmed_DTI": confirmed,
        "nn_px_mean": float(nn.mean()), "nn_px_p10": float(np.percentile(nn, 10)),
        "nn_px_p90": float(np.percentile(nn, 90)),
    }
    if confirmed:
        # solve 0.2N + 0.8|G| = TP_w_scaled / DTI for |G|, using the ratio
        # (private TP_w) / (catalogue-proxy TP_w) = r, unknown.  Report |G| for r=1.
        rec["implied_G_if_private_credit_equals_proxy"] = (tpw / confirmed - ALPHA * N) / BETA
        rec["inflation_factor_vs_proxy"] = confirmed / dti_cat
    out["anchors"][name] = rec
    del a, d, pts
    print(f"{name}: N={N} distinct_vals={rec['n_distinct_values']} "
          f"proxyDTI={dti_cat:.4f} confirmed={confirmed} nn_mean={rec['nn_px_mean']:.2f}px")

# uniform-random controls at the same N, for the calibration ratio
ctrl = {}
for N in (37654, 44090):
    idx = rng.choice(F, size=N, replace=False)
    flat = np.zeros(H * W, np.float32); flat[idx] = 1.0
    p = flat.reshape(H, W)
    tpw = float(w_cat[p > 0].sum())
    ctrl[N] = {"TP_w": tpw, "catalogue_proxy_DTI": tpw / (ALPHA * N + BETA * G_cat),
               "mean_credit_per_dot": tpw / N}
    print(f"random N={N}: proxyDTI={ctrl[N]['catalogue_proxy_DTI']:.4f} "
          f"mean_credit_per_dot={ctrl[N]['mean_credit_per_dot']:.5f}")
out["random_controls"] = ctrl

Path(ROOT / "evidence/anchor_forensics.json").write_text(json.dumps(out, indent=2))
print("wrote evidence/anchor_forensics.json")
