"""Canonical grid paths, documented geometry, and raster I/O for DOE GEMS.

``prepare_data.py`` checks local files against this module's canonical names and
geometry plus recorded SHA-256 pins. The pins came from an owner-maintained
sibling mirror, not organizer authentication. The grid constants and content
must be rechecked against authorized organizer files before a candidate can be
called organizer-validated.

Historical Git blob SHA-1 values found in sibling repositories:
  sample_submission.tif  7d865a9921a40ed2ea4c742a6a25b1fa2f357c5a
  labels.tif             4ad3c1f3f19823e40924589bee7e51e44ae3a2e7
These hashes establish byte identity only within those Git objects, not organizer
provenance or permission to redistribute the files.

The public problem description gives the format contract: same projected CRS,
resolution, and bounds; one float32 layer; [0, 1] predictions; and null/NaN
outside the bounds. This module writes rasters; it does not certify a submission.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import Affine

REPO = Path(__file__).resolve().parents[2]
DATA = REPO / "data"

FEATURES_TIF = DATA / "gems-geodawn-numerical-features.tif"
LABELS_TIF = DATA / "labels.tif"
TEMPLATE_TIF = DATA / "sample_submission.tif"

# --- expected grid contract (synthetic or data-dependent checks in tests_numeric/test_core.py) ---
CRS_EPSG = 32611
RES_M = 100.0
WIDTH = 3292          # columns  (rasterio `width`)
HEIGHT = 3730         # rows     (rasterio `height`)
TRANSFORM = Affine(100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)
NPIX = WIDTH * HEIGHT  # 12,279,160

# The feature stack encodes missing data with the float32 sentinel, not NaN.
# This is the same rule the organiser reference solution uses
# (gems-prize-reference-solution, cell 5: `X_orig[X_orig < -1e38] = np.nan`).
FEATURE_SENTINEL = -1e38

# Official metric parameters (problem description, "Performance metric").
DTI_ALPHA = 0.2
DTI_BETA = 0.8
DTI_KERNEL_M = 300.0
DTI_KERNEL_PX = DTI_KERNEL_M / RES_M  # 3.0 pixels

# Band numbers (1-based, as rasterio counts) of the official 19-layer stack.
# Descriptions below are the `description` tags read from the file itself.
BAND_RTP_MAG = 2        # "Reduced to pole magnetic data ..."
BAND_ISO_GRAV = 13      # "Isostatic gravity anomaly - gravity after compensating ..."
BAND_TMI = 14           # "Total magnetic intensity ..."
BAND_DETRENDED_ELEV = 12
BAND_ISO_GRAV_HORIZ_GRAD = 18
BAND_TMI_VERT_GRAD = 9


@dataclass(frozen=True)
class Grid:
    """The competition grid: shape, CRS, transform and the valid footprint."""

    height: int
    width: int
    crs: int | str | None
    transform: Affine
    footprint: np.ndarray  # bool, True where a prediction is scored/expected

    @property
    def shape(self) -> tuple[int, int]:
        return (self.height, self.width)


def read_template(path: Path = TEMPLATE_TIF) -> tuple[Grid, np.ndarray]:
    """Return the grid and the organiser template array (float32, NaN outside)."""
    with rasterio.open(path) as src:
        arr = src.read(1).astype(np.float32)
        grid = Grid(
            height=src.height,
            width=src.width,
            crs=src.crs.to_epsg(),
            transform=src.transform,
            footprint=np.isfinite(arr),
        )
    return grid, arr


def read_labels(path: Path = LABELS_TIF) -> np.ndarray:
    """Catalogue fault raster: 1 = mapped fault, 0 = not mapped, -1 = outside."""
    with rasterio.open(path) as src:
        return src.read(1).astype(np.int8)


def read_band(band: int, path: Path = FEATURES_TIF) -> tuple[np.ndarray, np.ndarray]:
    """Read one float32 band and its valid mask (sentinel -> False)."""
    with rasterio.open(path) as src:
        x = src.read(band).astype(np.float32)
    valid = x > FEATURE_SENTINEL
    x = np.where(valid, x, np.nan)
    return x, valid


def band_descriptions(path: Path = FEATURES_TIF) -> dict[int, str]:
    with rasterio.open(path) as src:
        return {i: src.tags(i).get("description", "") for i in range(1, src.count + 1)}


def write_submission(
    arr: np.ndarray,
    out_path: Path,
    grid: Grid,
    *,
    outside: str = "nan",
    compress: str = "lzw",
) -> Path:
    """Write a structurally formatted single-band float32 GeoTIFF.

    ``outside='nan'`` matches the documented null/NaN treatment outside the
    footprint and is the conservative default. ``outside='zeros'`` is available
    for local diagnostics only; this writer does not establish that zero-filled
    inactive cells satisfy the organizer's exact template interpretation, nor
    does it clear scientific, leakage, uniqueness, or portal-validation gates.
    """
    a = np.asarray(arr, dtype=np.float32).copy()
    if a.shape != grid.shape:
        raise ValueError(f"array shape {a.shape} != grid shape {grid.shape}")
    if outside == "zeros":
        a[~grid.footprint] = 0.0
        if not np.all(np.isfinite(a)):
            raise ValueError("non-finite values inside the all-finite encoding")
    elif outside == "nan":
        a[~grid.footprint] = np.nan
        if not np.isfinite(a[grid.footprint]).all():
            raise ValueError("non-finite values inside the footprint")
    else:
        raise ValueError("outside must be 'zeros' or 'nan'")
    finite = a[np.isfinite(a)]
    if finite.size and (finite.min() < 0.0 or finite.max() > 1.0):
        raise ValueError(
            f"values outside [0,1]: min={finite.min():.6g} max={finite.max():.6g}"
        )
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    profile = {
        "driver": "GTiff",
        "height": grid.height,
        "width": grid.width,
        "count": 1,
        "dtype": "float32",
        "crs": rasterio.crs.CRS.from_epsg(CRS_EPSG),
        "transform": grid.transform,
        "compress": compress,
    }
    with rasterio.open(out_path, "w", **profile) as dst:
        dst.write(a, 1)
    return out_path
