"""Round-trip tests for the canonical in-repository GeoTIFF writer."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gems55 import io55  # noqa: E402


def _grid():
    footprint = np.zeros((30, 40), dtype=bool)
    footprint[5:25, 5:35] = True
    return io55.Grid(
        height=30,
        width=40,
        crs=io55.CRS_EPSG,
        transform=from_origin(243350, 4508550, 100, 100),
        footprint=footprint,
    )


def test_roundtrip_writes_float32_with_nan_outside(tmp_path):
    grid = _grid()
    pred = np.random.default_rng(0).random(grid.shape).astype(np.float32)
    path = io55.write_submission(pred, tmp_path / "submission.tif", grid)
    with rasterio.open(path) as src:
        arr = src.read(1)
        assert src.count == 1
        assert src.dtypes == ("float32",)
        assert src.crs.to_epsg() == 32611
        assert tuple(src.transform)[:6] == tuple(grid.transform)[:6]
        assert np.isfinite(arr[grid.footprint]).all()
        assert arr[grid.footprint].min() >= 0.0
        assert arr[grid.footprint].max() <= 1.0
        assert np.array_equal(np.isnan(arr), ~grid.footprint)


def test_writer_rejects_out_of_range_values_inside_footprint(tmp_path):
    grid = _grid()
    pred = np.full(grid.shape, 0.5, dtype=np.float32)
    pred[10, 10] = 1.7
    with pytest.raises(ValueError, match=r"\[0,1\]"):
        io55.write_submission(pred, tmp_path / "bad.tif", grid)


def test_writer_rejects_nan_inside_footprint(tmp_path):
    grid = _grid()
    pred = np.full(grid.shape, 0.5, dtype=np.float32)
    pred[10, 10] = np.nan
    with pytest.raises(ValueError, match="non-finite"):
        io55.write_submission(pred, tmp_path / "nan.tif", grid)
