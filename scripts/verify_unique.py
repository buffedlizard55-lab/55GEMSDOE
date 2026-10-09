#!/usr/bin/env python3
"""Lane-drift / uniqueness check against every retrievable prior scored raster.

Brief thresholds: rank correlation with any registry raster > 0.90, or more than
70% of our dots within 3 px of one registry raster's dots  =>  duplicate, stop.
Also reports Jaccard and containment for completeness.
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
import numpy as np
import rasterio
from scipy import ndimage, stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems55 import io55  # noqa: E402

REG = ROOT / "registry" / "rasters"
EVID = ROOT / "evidence"

ap = argparse.ArgumentParser(); ap.add_argument("tif"); ap.add_argument("--out", default=None)
args = ap.parse_args()

grid, _ = io55.read_template()
with rasterio.open(args.tif) as s:
    ours = s.read(1)
odots = np.nan_to_num(ours, nan=0.0) > 0
n_ours = int(odots.sum())
oy, ox = np.nonzero(odots)
print(f"ours: {Path(args.tif).name}  n_dots={n_ours}")

rows = []
for p in sorted(REG.glob("*.tif")):
    with rasterio.open(p) as s:
        if (s.width, s.height) != (grid.width, grid.height):
            continue
        a = np.nan_to_num(s.read(1), nan=0.0)
    rd = a > 0
    n = int(rd.sum())
    if n == 0:
        continue
    inter = int((odots & rd).sum())
    jac = inter / max(int((odots | rd).sum()), 1)
    # fraction of our dots within 3 px of one of their dots
    dil = ndimage.binary_dilation(rd, iterations=3)
    frac3 = float(dil[oy, ox].mean())
    # rank correlation on the positive-pixel values + a jitter-free rank tie-break
    ry, rx = np.nonzero(rd)
    sub_o = ours[ry, rx]; sub_r = a[ry, rx]
    if np.ptp(sub_o) > 0 and np.ptp(sub_r) > 0:
        rho = float(stats.spearmanr(sub_o, sub_r).statistic)
    else:
        rho = float("nan")
    # dense Spearman over the footprint (both are binary -> ties dominate)
    fp = grid.footprint
    rho_dense = float(stats.spearmanr(ours[fp], a[fp]).statistic)
    rows.append({"raster": p.name, "n_pos": n, "intersect": inter, "jaccard": round(jac, 6),
                 "frac_our_dots_within_3px": round(frac3, 4),
                 "spearman_on_their_positives": None if np.isnan(rho) else round(rho, 4),
                 "spearman_dense_footprint": round(rho_dense, 4)})

# ---- control: the SAME statistic for a uniform-random dot set of equal size ----
# A dense reference raster (e.g. a spacing-5 lattice with 206,895 positives) puts
# almost every pixel within 3 px of one of its dots, so the 70% rule is vacuous
# against it.  The control measures that inflation so the criterion can be read.
rng = np.random.default_rng(0)
pool = np.nonzero(grid.footprint.ravel() & ~odots.ravel())[0]
ctrl = np.zeros(odots.shape, dtype=bool)
ctrl.ravel()[rng.choice(pool, size=n_ours, replace=False)] = True
cy, cx = np.nonzero(ctrl)
for r in rows:
    p2 = REG / r["raster"]
    with rasterio.open(p2) as s:
        a2 = np.nan_to_num(s.read(1), nan=0.0) > 0
    r["frac3px_random_control"] = round(float(ndimage.binary_dilation(a2, iterations=3)[cy, cx].mean()), 4)
    r["frac3px_excess_over_control"] = round(r["frac_our_dots_within_3px"] - r["frac3px_random_control"], 4)
    r["density_ratio_vs_ours"] = round(r["n_pos"] / n_ours, 3)

rows.sort(key=lambda r: -r["frac3px_excess_over_control"])
maxfrac = max(r["frac_our_dots_within_3px"] for r in rows)
maxexcess = max(r["frac3px_excess_over_control"] for r in rows)
matched = [r for r in rows if 0.25 <= r["density_ratio_vs_ours"] <= 4.0]
maxfrac_matched = max((r["frac_our_dots_within_3px"] for r in matched), default=float("nan"))
maxrho = max(r["spearman_dense_footprint"] for r in rows)
maxjac = max(r["jaccard"] for r in rows)
verdict = "PASS-UNIQUE" if (maxrho <= 0.90 and maxfrac <= 0.70) else "REVIEW"
if verdict == "REVIEW" and maxexcess <= 0.05:
    verdict = "PASS-UNIQUE-CONTROL-ADJUSTED"
out = {"ours": Path(args.tif).name, "n_dots": n_ours, "n_registry": len(rows),
       "max_spearman_dense": round(maxrho, 4), "max_frac_within_3px": round(maxfrac, 4),
       "max_jaccard": round(maxjac, 6), "thresholds": {"spearman": 0.90, "frac_3px": 0.70},
       "max_frac3px_excess_over_random_control": round(maxexcess, 4),
       "max_frac_within_3px_density_matched": round(maxfrac_matched, 4),
       "n_density_matched": len(matched),
       "verdict": verdict, "top10": rows[:10], "all": rows}
EVID.mkdir(exist_ok=True)
dst = Path(args.out) if args.out else EVID / "uniqueness.json"
dst.write_text(json.dumps(out, indent=2))
for r in rows[:8]:
    print(f"  {r['raster'][:58]:58s} n={r['n_pos']:7d} jac={r['jaccard']:.4f} "
          f"frac3px={r['frac_our_dots_within_3px']:.3f} ctrl={r['frac3px_random_control']:.3f} "
          f"excess={r['frac3px_excess_over_control']:+.3f} rho={r['spearman_dense_footprint']:+.4f}")
print(f"\nmax |Spearman| dense = {maxrho:.4f}   max frac within 3px = {maxfrac:.4f}   "
      f"max Jaccard = {maxjac:.4f}")
print(f"max frac3px EXCESS over the random control = {maxexcess:+.4f}   "
      f"density-matched max frac3px = {maxfrac_matched:.4f} (n={len(matched)} refs)")
print(f"VERDICT: {verdict}")
print("wrote", dst)
