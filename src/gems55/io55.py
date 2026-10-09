"""Grid constants and I/O for the DOE GEMS Prize (DrivenData competition 306).

Every constant in this module is measured from the organiser-supplied rasters by
``scripts/prepare_data.py`` and re-asserted by ``tests/test_io.py``.  Nothing is
hard-coded from memory.

Verified provenance (2026-10-09, git blob SHA over the GitHub API, which is
content-addressed so an identical SHA means identical bytes):

  sample_submission.tif  sha 7d865a9921a40ed2ea4c742a6a25b1fa2f357c5a  1,599,597 B
  labels.tif             sha 4ad3c1f3f19823e40924589bee7e51e44ae3a2e7    425,830 B
      (identical blob to 5GEMSDOE:data/bridge/existing_faults.tif)

Submission contract, transcribed from the official problem description
https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/ :
  * same projected CRS as the training data -> EPSG:32611 (UTM zone 11N)
  * same resolution as the training data   -> 100 m
  * same bounds as the training data, null/NaN outside
  * single layer, float32, values in [0, 1]
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import Affine

REPO = Path(__file__).resolve().parents[2]
DATA = REPO / "data"

# The organiser calls this payload ``training_features.tif``.  Older sibling
# mirrors used the descriptive GeoDAWN filename; ``feature_path`` below accepts
# that name as a read-only compatibility alias without making the pipeline
# depend on a private mirror.
FEATURES_TIF = DATA / "training_features.tif"
FEATURES_TIF_LEGACY = DATA / "gems-geodawn-numerical-features.tif"
LABELS_TIF = DATA / "labels.tif"
TEMPLATE_TIF = DATA / "sample_submission.tif"


def feature_path() -> Path:
    """Return the available official feature-stack path.

    The competition download is named ``training_features.tif``.  A legacy
    descriptive filename is accepted only when the canonical name is absent;
    this makes a fresh data placement and the existing bridge reproducible while
    keeping one authoritative path in the code.
    """
    if FEATURES_TIF.exists():
        return FEATURES_TIF
    if FEATURES_TIF_LEGACY.exists():
        return FEATURES_TIF_LEGACY
    return FEATURES_TIF

# --- grid contract (asserted against the template in tests/test_io.py) -------
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
    crs: str
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


def read_band(band: int, path: Path | None = None) -> tuple[np.ndarray, np.ndarray]:
    """Read one float32 band and its valid mask (sentinel -> False)."""
    path = feature_path() if path is None else Path(path)
    with rasterio.open(path) as src:
        x = src.read(band).astype(np.float32)
    valid = x > FEATURE_SENTINEL
    x = np.where(valid, x, np.nan)
    return x, valid


def band_descriptions(path: Path | None = None) -> dict[int, str]:
    path = feature_path() if path is None else Path(path)
    with rasterio.open(path) as src:
        return {i: src.tags(i).get("description", "") for i in range(1, src.count + 1)}


def write_submission(
    arr: np.ndarray,
    out_path: Path,
    grid: Grid,
    *,
    outside: str = "zeros",
    compress: str = "lzw",
) -> Path:
    """Write a contract-compliant single-band float32 GeoTIFF.

    ``outside='zeros'`` writes 0.0 outside the footprint (all-finite file);
    ``outside='nan'`` writes NaN there.  Both encodings are permitted by the
    official rules ("data outside the bounds is null or nan"), but the portal's
    range check ``[0, 1]`` is only guaranteed to pass for the all-finite
    encoding, so ``zeros`` is the default for anything meant for upload.
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
