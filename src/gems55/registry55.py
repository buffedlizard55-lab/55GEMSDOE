"""Registry-raster alignment and cover masks shared by the writer and uniqueness gate.

Prior candidate GeoTIFFs are not guaranteed to carry the official submission
transform even when their array shape matches.  This module aligns each prior
raster to the measured competition grid before pixelwise uniqueness checks.  The
reprojection is nearest-neighbor because the registry products are binary/continuous
predictions and the protocol's 3-pixel overlap is defined on the final template grid.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import rasterio
from rasterio.crs import CRS
from rasterio.warp import Resampling, reproject
from scipy import ndimage

from .io55 import Grid


def read_on_grid(path: str | Path, grid: Grid) -> tuple[np.ndarray, bool]:
    """Read a single-band registry raster reprojected to ``grid``.

    Returns ``(float32_array, was_reprojected)``.  Source cells that are NaN,
    infinite, or declared nodata do not become positive predictions.  A source
    with a missing CRS or multiple bands raises instead of being silently skipped.
    """
    path = Path(path)
    with rasterio.open(path) as src:
        if src.count != 1:
            raise ValueError(f"registry raster {path.name} must be single-band (found {src.count})")
        if src.crs is None:
            raise ValueError(f"registry raster {path.name} has no CRS; cannot align safely")
        same_grid = (
            (src.height, src.width) == grid.shape
            and src.crs.to_epsg() == grid.crs
            and tuple(src.transform)[:6] == tuple(grid.transform)[:6]
        )
        raw = src.read(1).astype(np.float32, copy=False)
        nodata = src.nodata
        if same_grid:
            out = np.array(raw, dtype=np.float32, copy=True)
            if nodata is not None and np.isfinite(nodata):
                out[out == np.float32(nodata)] = 0.0
            return np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0), False

        # Reproject the numeric prediction to the official template.  Explicitly
        # zero invalid source cells so a NaN sentinel cannot contaminate warp logic.
        src_arr = np.nan_to_num(raw, nan=0.0, posinf=0.0, neginf=0.0).copy()
        src_nodata = nodata if nodata is not None else None
        if src_nodata is not None and np.isfinite(src_nodata):
            src_arr[src_arr == np.float32(src_nodata)] = 0.0
            src_nodata = 0.0
        dst = np.zeros(grid.shape, dtype=np.float32)
        reproject(
            source=src_arr,
            destination=dst,
            src_transform=src.transform,
            src_crs=src.crs,
            src_nodata=src_nodata,
            dst_transform=grid.transform,
            dst_crs=CRS.from_epsg(int(grid.crs)),
            dst_nodata=0.0,
            resampling=Resampling.nearest,
            init_dest_nodata=True,
        )
    return np.nan_to_num(dst, nan=0.0, posinf=0.0, neginf=0.0), True


def cover_mask(path: str | Path, grid: Grid, max_dist_px: float = 3.0) -> tuple[np.ndarray, bool]:
    """Pixels within ``max_dist_px`` Euclidean pixels of a prior positive dot."""
    raster, warped = read_on_grid(path, grid)
    pos = raster > 0
    if not pos.any():
        return np.zeros(grid.shape, dtype=bool), warped
    return ndimage.distance_transform_edt(~pos) <= max_dist_px, warped


def cover_masks(registry_dir: str | Path, grid: Grid, max_dist_px: float = 3.0):
    """Load every ``*.tif`` in a registry directory onto ``grid``; never exclude one.

    Returns ``(names, masks, reprojected_names)`` so the run card can disclose any
    registry geometry correction.  A corrupt/unreferenced raster raises and stops.
    """
    names: list[str] = []
    masks: list[np.ndarray] = []
    warped_names: list[str] = []
    for path in sorted(Path(registry_dir).glob("*.tif")):
        mask, warped = cover_mask(path, grid, max_dist_px=max_dist_px)
        names.append(path.name)
        masks.append(mask)
        if warped:
            warped_names.append(path.name)
    return names, masks, warped_names
