"""Tests for the H57 emission helpers: flank prior, registry budgets, budgeted emission.

Run with ``.venv/bin/python -m pytest -q tests_numeric``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gems55 import holdout55, io55, registry55  # noqa: E402


# --------------------------------------------------------------------------- #
# flank_weight
# --------------------------------------------------------------------------- #
def test_flank_weight_decays_and_is_zero_on_catalogue():
    cat = np.zeros((60, 60), dtype=bool)
    cat[30, 10:50] = True  # an E-W mapped trace
    w = holdout55.flank_weight(cat, support_px=15.0)
    assert w.shape == cat.shape
    assert w.dtype == np.float32
    assert np.all(w[cat] == 0.0)
    assert w[29, 30] == pytest.approx((1.0 - 1.0 / 15.0) ** 2, rel=1e-6)
    assert w[30 - 7, 30] == pytest.approx((1.0 - 7.0 / 15.0) ** 2, rel=1e-6)
    assert w[30 - 15, 30] == pytest.approx(0.0, abs=1e-7)
    assert w[30 - 16, 30] == pytest.approx(0.0, abs=1e-7)
    assert w[0, 0] == pytest.approx(0.0, abs=1e-7)
    assert np.all((w >= 0.0) & (w <= 1.0))


def test_flank_weight_neutral_when_no_visible_catalogue():
    w = holdout55.flank_weight(np.zeros((20, 20), dtype=bool), support_px=15.0)
    assert np.all(w == 1.0)


# --------------------------------------------------------------------------- #
# emit_dots_budgeted
# --------------------------------------------------------------------------- #
def _surface_with_two_blobs(shape=(120, 120)):
    rng = np.random.default_rng(0)
    score = rng.random(shape).astype(np.float32) * 0.01
    yy, xx = np.mgrid[0 : shape[0], 0 : shape[1]]
    score += (np.exp(-(((yy - 30) ** 2 + (xx - 30) ** 2) / 20.0))).astype(np.float32)
    score += (np.exp(-(((yy - 90) ** 2 + (xx - 90) ** 2) / 20.0))).astype(np.float32)
    return score


def test_budgeted_emission_respects_every_cap_and_minimum_separation():
    score = _surface_with_two_blobs()
    elig = np.ones(score.shape, dtype=bool)
    left = np.zeros(score.shape, dtype=bool)
    left[:, : score.shape[1] // 2] = True
    right = np.zeros(score.shape, dtype=bool)
    right[:, score.shape[1] // 2 :] = True
    n_dots = 400
    dots = holdout55.emit_dots_budgeted(
        score, elig, n_dots, min_sep_px=3.0, cover_masks=[left, right], max_overlap=0.68
    )
    n = int(dots.sum())
    assert n == n_dots
    assert (dots & left).sum() / n <= 0.68 + 1e-12
    assert (dots & right).sum() / n <= 0.68 + 1e-12
    from scipy import spatial

    py, px = np.nonzero(dots)
    d, _ = spatial.cKDTree(np.stack([py, px], axis=1)).query(
        np.stack([py, px], axis=1), k=2
    )
    assert d[:, 1].min() > 3.0


def test_budgeted_emission_impossible_everywhere_mask_fails_closed():
    score = _surface_with_two_blobs()
    elig = np.ones(score.shape, dtype=bool)
    everywhere = np.ones(score.shape, dtype=bool)
    dots = holdout55.emit_dots_budgeted(
        score, elig, 200, min_sep_px=3.0, cover_masks=[everywhere], max_overlap=0.10
    )
    assert int(dots.sum()) == 0


def test_budgeted_emission_without_masks_returns_requested_separated_count():
    score = _surface_with_two_blobs()
    elig = np.ones(score.shape, dtype=bool)
    dots = holdout55.emit_dots_budgeted(score, elig, 300, min_sep_px=3.0, seed=5)
    assert int(dots.sum()) == 300
    from scipy import spatial

    py, px = np.nonzero(dots)
    d, _ = spatial.cKDTree(np.stack([py, px], axis=1)).query(
        np.stack([py, px], axis=1), k=2
    )
    assert d[:, 1].min() > 3.0


def test_budgeted_emission_random_arm_obeys_registry_budget():
    score = _surface_with_two_blobs()
    elig = np.ones(score.shape, dtype=bool)
    everywhere = np.ones(score.shape, dtype=bool)
    dots = holdout55.emit_dots_budgeted(
        score, elig, 100, cover_masks=[everywhere], max_overlap=0.10, seed=3, random=True
    )
    assert int(dots.sum()) == 0


def test_budgeted_emission_repair_guarantees_overlap_below_target_mass():
    score = _surface_with_two_blobs()
    elig = np.ones(score.shape, dtype=bool)
    mostly = np.ones(score.shape, dtype=bool)
    mostly[100:, 100:] = False
    dots = holdout55.emit_dots_budgeted(
        score, elig, 400, min_sep_px=3.0, cover_masks=[mostly], max_overlap=0.68
    )
    n = int(dots.sum())
    assert n < 400
    assert n == 0 or (dots & mostly).sum() / n <= 0.68 + 1e-12


def test_budgeted_emission_repair_keeps_separation():
    score = _surface_with_two_blobs()
    elig = np.ones(score.shape, dtype=bool)
    mostly = np.ones(score.shape, dtype=bool)
    mostly[100:, 100:] = False
    dots = holdout55.emit_dots_budgeted(
        score, elig, 400, min_sep_px=3.0, cover_masks=[mostly], max_overlap=0.68
    )
    from scipy import spatial

    py, px = np.nonzero(dots)
    if py.size > 1:
        d, _ = spatial.cKDTree(np.stack([py, px], axis=1)).query(
            np.stack([py, px], axis=1), k=2
        )
        assert d[:, 1].min() > 3.0


# --------------------------------------------------------------------------- #
# registry mask construction and raster alignment
# --------------------------------------------------------------------------- #
def test_registry_cover_masks_includes_every_same_grid_raster(tmp_path):
    rasterio = pytest.importorskip("rasterio")
    from rasterio.transform import Affine

    shape = (40, 50)
    transform = Affine(100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)
    profile = {
        "driver": "GTiff",
        "height": shape[0],
        "width": shape[1],
        "count": 1,
        "dtype": "float32",
        "crs": "EPSG:32611",
        "transform": transform,
    }
    a = np.zeros(shape, dtype=np.float32)
    a[20, 25] = 1.0
    b = np.ones(shape, dtype=np.float32)
    with rasterio.open(tmp_path / "A_registry.tif", "w", **profile) as dst:
        dst.write(a, 1)
    with rasterio.open(tmp_path / "B_lattice-s5_degenerate.tif", "w", **profile) as dst:
        dst.write(b, 1)

    names, masks = holdout55.registry_cover_masks(tmp_path, shape)
    assert names == ["A_registry.tif", "B_lattice-s5_degenerate.tif"]
    assert len(masks) == 2
    m = masks[0]
    assert m[20, 25]
    assert m[20, 28] and m[23, 25]
    assert not m[20, 29] and not m[24, 25]
    assert m[22, 23]
    assert not m[23, 23]
    assert int(m.sum()) == 29
    assert masks[1].all()


def test_registry_reader_reprojects_shifted_transform_to_template(tmp_path):
    rasterio = pytest.importorskip("rasterio")
    from rasterio.transform import Affine

    shape = (40, 50)
    official = Affine(100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)
    shifted = Affine(100.0, 0.0, 243450.0, 0.0, -100.0, 4508550.0)
    grid = io55.Grid(height=shape[0], width=shape[1], crs=32611,
                     transform=official, footprint=np.ones(shape, dtype=bool))
    arr = np.zeros(shape, dtype=np.float32)
    arr[20, 25] = 1.0
    profile = {
        "driver": "GTiff", "height": shape[0], "width": shape[1],
        "count": 1, "dtype": "float32", "crs": "EPSG:32611", "transform": shifted,
    }
    path = tmp_path / "shifted.tif"
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(arr, 1)
    aligned, was_warped = registry55.read_on_grid(path, grid)
    assert was_warped
    assert aligned[20, 26] == 1.0  # one 100 m source-grid shift becomes one template pixel
    assert aligned[20, 25] == 0.0
