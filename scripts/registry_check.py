"""Uniqueness check against every earlier raster (PARALLEL-RUN PROTOCOL item 1).

Metrics per registry raster (same grid only):
  * Spearman rank correlation on the scored footprint (subsampled, fixed seed)
  * dot overlap: % of candidate positive pixels within 3 px (300 m) of a registry positive pixel
  * exact sha256 match
Drift thresholds from the protocol: rank corr > 0.90 OR overlap > 70%  -> duplicate, stop.

Usage: python scripts/registry_check.py <candidate.tif> <registry_dir> <out.json>
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage
from scipy.stats import spearmanr


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def main(cand, regdir, out, spearman=True):
    with rasterio.open(cand) as s:
        c = s.read(1).astype(np.float64)
        shape = s.shape
        crs = str(s.crs)
        tr = tuple(s.transform)[:6]
    cfin = np.isfinite(c)
    cpos = cfin & (c > 0)
    rng = np.random.default_rng(0)
    rows = []
    _ = spearman
    for p in sorted(Path(regdir).rglob("*.tif")):
        try:
            with rasterio.open(p) as s:
                if s.shape != shape or str(s.crs) != crs or tuple(s.transform)[:6] != tr or s.count != 1:
                    continue
                r = s.read(1).astype(np.float64)
        except Exception as e:  # noqa: BLE001
            rows.append({"file": str(p), "error": str(e)})
            continue
        rfin = np.isfinite(r)
        both = cfin & rfin
        idx = np.flatnonzero(both)
        if idx.size > 300000:
            idx = rng.choice(idx, 300000, replace=False)
        rho = float(spearmanr(c.ravel()[idx], r.ravel()[idx]).statistic) if (spearman and idx.size > 10) else float("nan")
        rpos = rfin & (r > 0)
        dist = ndimage.distance_transform_edt(~rpos) if rpos.any() else np.full(shape, np.inf)
        cd = dist[cpos]
        overlap = float(np.mean(cd <= 3.0)) if cd.size else float("nan")
        rows.append({"file": str(p.relative_to(regdir)), "sha256": sha(p), "spearman_footprint": round(rho, 4) if rho == rho else None,
                     "dot_overlap_within_3px": round(overlap, 4), "registry_positive_px": int(rpos.sum()),
                     "duplicate_flag": bool((rho > 0.90) or (overlap > 0.70)) if spearman else bool(overlap > 0.70),
                     "identical_bytes": False})
    cand_sha = sha(cand)
    for row in rows:
        if row.get("sha256") == cand_sha:
            row["identical_bytes"] = True
    summary = {"candidate": str(cand), "candidate_sha256": cand_sha, "candidate_positive_px": int(cpos.sum()),
               "registry_rasters_total": len(list(Path(regdir).rglob('*.tif'))),
               "same_grid_compared": sum(1 for r in rows if 'dot_overlap_within_3px' in r),
               "max_spearman": max([r["spearman_footprint"] for r in rows if r.get("spearman_footprint") is not None] or [None], key=lambda v: -9 if v is None else v),
               "max_dot_overlap": max([r["dot_overlap_within_3px"] for r in rows if 'dot_overlap_within_3px' in r] or [None], key=lambda v: -9 if v is None else v),
               "duplicates_flagged": sum(1 for r in rows if r.get("duplicate_flag")),
               "identical_bytes_found": sum(1 for r in rows if r.get("identical_bytes")),
               "rows": sorted([r for r in rows if 'dot_overlap_within_3px' in r], key=lambda r: -r['dot_overlap_within_3px'])[:25]}
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(summary, indent=2))
    print(json.dumps({k: v for k, v in summary.items() if k != "rows"}, indent=2))
    print("top rows:")
    for r in summary["rows"][:8]:
        print(r["spearman_footprint"], r["dot_overlap_within_3px"], r["registry_positive_px"], r["file"])


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3], spearman="--no-spearman" not in sys.argv)
