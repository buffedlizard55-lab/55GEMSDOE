"""Writer and validator for the competition submission GeoTIFF.

Official format (verified 2026-10-09, DrivenData problem description):
  * projected CRS EPSG:32611 (UTM 11N), 100 m resolution, same bounds as training data
  * single layer, float32, values in [0, 1]
  * data outside the bounds/footprint must be null or NaN
Template used for footprint, CRS, transform and shape: the competition's
sample_submission.tif (NOT a fault-absence file -- see docs/irregularities.md).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import rasterio
from rasterio.crs import CRS

REQUIRED_CRS = "EPSG:32611"
REQUIRED_RES = (100.0, 100.0)


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_template(template_path: str | Path):
    with rasterio.open(template_path) as src:
        arr = src.read(1)
        meta = {"crs": src.crs, "transform": src.transform, "height": src.height,
                "width": src.width}
    footprint = np.isfinite(arr)
    return footprint, meta


def write_submission(pred: np.ndarray, footprint: np.ndarray, meta: dict, out_path: str | Path) -> dict:
    """Write float32 GeoTIFF: NaN outside footprint, probabilities clipped to [0, 1] inside."""
    assert pred.shape == footprint.shape, "prediction shape must match template"
    out = np.where(footprint, np.clip(np.nan_to_num(pred, nan=0.0), 0.0, 1.0), np.nan).astype(np.float32)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(
        out_path, "w", driver="GTiff", height=out.shape[0], width=out.shape[1], count=1,
        dtype="float32", crs=meta["crs"], transform=meta["transform"], nodata=np.nan,
        compress="deflate", predictor=3, tiled=False,
    ) as dst:
        dst.write(out, 1)
        dst.set_band_description(1, "fault_probability")
    return {"path": str(out_path), "sha256": sha256_file(out_path), "bytes": out_path.stat().st_size}


def validate(path: str | Path, footprint: np.ndarray, meta: dict) -> dict:
    """Run every official check. Returns a dict of named checks plus 'all_passed'."""
    checks = {}
    with rasterio.open(path) as src:
        checks["single_band"] = src.count == 1
        checks["dtype_float32"] = src.dtypes[0] == "float32"
        checks["crs_epsg_32611"] = src.crs == CRS.from_epsg(32611) and REQUIRED_CRS in str(src.crs)
        checks["shape_matches_template"] = (src.height, src.width) == (meta["height"], meta["width"])
        checks["transform_matches_template"] = tuple(src.transform)[:6] == tuple(meta["transform"])[:6]
        checks["resolution_100m"] = tuple(abs(v) for v in src.res) == REQUIRED_RES
        arr = src.read(1).astype(np.float64)
    inside = arr[footprint]
    outside = arr[~footprint]
    checks["no_nan_inside_footprint"] = bool(np.all(np.isfinite(inside)))
    checks["no_inf_anywhere"] = bool(not np.isinf(arr).any())
    checks["values_in_0_1_inside"] = bool(np.all((inside >= 0) & (inside <= 1))) if inside.size else False
    checks["outside_null_or_nan"] = bool(np.all(np.isnan(outside)))
    checks["footprint_inside_pixels"] = int(footprint.sum())
    checks["positive_pixels"] = int(np.sum(inside > 0)) if inside.size else 0
    checks["min_inside"] = float(np.nanmin(inside)) if inside.size else None
    checks["max_inside"] = float(np.nanmax(inside)) if inside.size else None
    bool_keys = [k for k, v in checks.items() if isinstance(v, bool)]
    checks["all_passed"] = all(checks[k] for k in bool_keys)
    checks["sha256"] = sha256_file(path)
    return checks


if __name__ == "__main__":  # CLI: python -m gems.submission <file.tif> <template.tif>
    import sys
    fp, meta = read_template(sys.argv[2])
    print(json.dumps(validate(sys.argv[1], fp, meta), indent=2, default=str))
