"""Contract + mathematics tests.  Run with ``.venv/bin/python -m pytest -q``."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gems55 import dti55, io55, tensor55  # noqa: E402


# --------------------------------------------------------------------------- #
# Expected grid contract (data-dependent assertions skip when local rasters are absent)
# --------------------------------------------------------------------------- #
DATA_OK = (io55.TEMPLATE_TIF.exists() and io55.LABELS_TIF.exists() and io55.FEATURES_TIF.exists())
needs_data = pytest.mark.skipif(not DATA_OK, reason="competition rasters not present")


@needs_data
def test_grid_contract_matches_template():
    grid, arr = io55.read_template()
    assert (grid.width, grid.height) == (io55.WIDTH, io55.HEIGHT)
    assert grid.crs == io55.CRS_EPSG
    assert tuple(grid.transform)[:6] == tuple(io55.TRANSFORM)[:6]
    assert arr.shape == (io55.HEIGHT, io55.WIDTH)
    assert arr.size == io55.NPIX == 12_279_160
    # labels' nodata mask is exactly the template's NaN mask
    lab = io55.read_labels()
    assert np.array_equal(np.isnan(arr), lab == -1)
    assert int((lab == 1).sum()) == 60_988


@needs_data
def test_feature_stack_is_the_official_19_layer_grid():
    import rasterio

    with rasterio.open(io55.FEATURES_TIF) as src:
        assert src.count == 19
        assert set(src.dtypes) == {"float32"}
        assert (src.width, src.height) == (io55.WIDTH, io55.HEIGHT)
        assert src.crs.to_epsg() == io55.CRS_EPSG
        assert tuple(src.transform)[:6] == tuple(io55.TRANSFORM)[:6]
        d2 = src.tags(2)["description"]
        d13 = src.tags(13)["description"]
    assert d2.startswith("Reduced to pole magnetic data")
    assert d13.startswith("Isostatic gravity anomaly - gravity")


# --------------------------------------------------------------------------- #
# Metric: exactness
# --------------------------------------------------------------------------- #
def test_dti_matches_brute_force_on_random_cases():
    rng = np.random.default_rng(0)
    for _ in range(6):
        truth = rng.random((40, 45)) < 0.02
        pred = (rng.random((40, 45)) < 0.05).astype(float)
        pred[rng.random((40, 45)) < 0.1] *= rng.random()
        a = dti55.dti(pred, truth)
        b = dti55.brute_force_dti(pred, truth)
        assert a.tp_w == pytest.approx(b.tp_w, rel=1e-12, abs=1e-12)
        assert a.fp_w == pytest.approx(b.fp_w, rel=1e-12, abs=1e-12)
        assert a.fn_w == pytest.approx(b.fn_w, rel=1e-12, abs=1e-12)
        assert a.dti == pytest.approx(b.dti, rel=1e-12, abs=1e-12)


def test_dti_official_worked_example_ratio():
    """Official page: TP_w=3.00, FP_w=1.89, FN_w=2.00 -> DTI(0.2,0.8)=0.60."""
    val = 3.00 / (3.00 + 0.2 * 1.89 + 0.8 * 2.00)
    assert val == pytest.approx(0.60, abs=0.005)


def test_dti_perfect_prediction_is_one():
    truth = np.zeros((30, 30), dtype=bool)
    truth[10:20, 5] = True
    r = dti55.dti(truth.astype(float), truth)
    assert r.dti == pytest.approx(1.0, abs=1e-9)
    assert r.fp_w == 0.0 and r.fn_w == 0.0


def test_dti_empty_prediction_is_zero():
    truth = np.zeros((30, 30), dtype=bool)
    truth[10:20, 5] = True
    r = dti55.dti(np.zeros((30, 30)), truth)
    assert r.dti == pytest.approx(0.0, abs=1e-9)


def test_metric_algebra_does_not_reduce_to_predicted_pixel_count():
    """A nearby false positive disproves the invalid 0.2*N denominator."""
    truth = np.zeros((11, 11), dtype=bool)
    truth[5, 5] = True
    pred = np.zeros_like(truth, dtype=np.float64)
    pred[5, 5] = 1.0
    pred[5, 6] = 1.0  # 1 px from truth: kernel credit 2/3, FP weight 1/3

    r = dti55.dti(pred, truth)
    assert r.tp_w == pytest.approx(1.0)
    assert r.fn_w == pytest.approx(0.0)
    assert r.fp_w == pytest.approx(1.0 / 3.0)
    assert r.tp_w + r.fn_w == pytest.approx(float(r.n_truth))

    exact = r.tp_w / (0.2 * r.tp_w + 0.2 * r.fp_w + 0.8 * r.n_truth + dti55.EPS)
    invalid_count_only = r.tp_w / (0.2 * r.n_pred_pos + 0.8 * r.n_truth + dti55.EPS)
    assert r.dti == pytest.approx(exact, abs=1e-12)
    assert r.dti == pytest.approx(0.9375, abs=1e-12)
    assert invalid_count_only == pytest.approx(5.0 / 6.0, abs=1e-12)
    assert r.dti != pytest.approx(invalid_count_only, abs=1e-3)


def test_contribution_maps_sum_to_exact_metric_components_and_bootstrap():
    truth = np.zeros((24, 26), dtype=bool)
    truth[7, 8:11] = True
    truth[17, 19] = True
    pred = np.zeros_like(truth, dtype=np.float64)
    pred[7, 9] = 1.0
    pred[17, 20] = 0.75

    result = dti55.dti(pred, truth)
    tp, fp, fn = dti55.weighted_contribution_maps(pred, truth)
    assert tp.sum() == pytest.approx(result.tp_w, abs=1e-12)
    assert fp.sum() == pytest.approx(result.fp_w, abs=1e-12)
    assert fn.sum() == pytest.approx(result.fn_w, abs=1e-12)
    ci1 = dti55.block_bootstrap_ci(tp, fp, fn, block_px=8, n_boot=100, seed=5)
    ci2 = dti55.block_bootstrap_ci(tp, fp, fn, block_px=8, n_boot=100, seed=5)
    assert ci1 == ci2
    assert 0.0 <= ci1["ci95"][0] <= ci1["ci95"][1] <= 1.0


def test_dti_kernel_offsets_are_the_3px_triangular_kernel():
    offs = dti55.kernel_offsets(3.0)
    assert len(offs) == 29  # dx^2+dy^2 <= 9
    centre = [w for dy, dx, w in offs if dy == 0 and dx == 0]
    assert centre == [1.0]
    edge = [w for dy, dx, w in offs if abs(dy) + abs(dx) == 0 or np.hypot(dy, dx) == 3.0]
    assert min(edge) == pytest.approx(0.0, abs=1e-12)


def test_breakeven_credit_is_conditional_and_uses_correct_threshold():
    assert dti55.breakeven_credit(0.0) == 0.0
    assert dti55.breakeven_credit(0.3) < dti55.breakeven_credit(0.5)
    # alpha=.2, beta=.8, and under the helper's isolated single-match assumptions.
    assert dti55.breakeven_credit(0.3) == pytest.approx(0.06, abs=1e-12)
    with pytest.raises(ValueError):
        dti55.breakeven_credit(1.01)


def test_random_dots_ignore_candidate_score_support():
    score = np.zeros((8, 9), dtype=np.float32)
    score[0, 0] = 1.0
    eligible = np.ones_like(score, dtype=bool)
    dots = __import__("gems55.holdout55", fromlist=["emit_dots"]).emit_dots(
        score, eligible, 50, random=True, seed=2026
    )
    assert int(dots.sum()) == 50
    assert np.count_nonzero(dots & (score == 0)) == 49


def test_segment_folds_never_split_connected_components_and_buffer_visible_labels():
    from gems55 import holdout55

    labels = np.zeros((40, 60), dtype=np.int8)
    footprint = np.ones_like(labels, dtype=bool)
    # One 8-connected line crosses the spatial-bin boundary; it must be withheld whole.
    labels[18, 5:56] = 1
    labels[18, 25] = 1
    # A second component helps populate another fold.
    labels[31, 40:48] = 1

    folds = holdout55.make_segment_folds(labels, footprint, n_folds=4, buffer_px=2)
    assert folds
    coverage = np.zeros_like(labels, dtype=np.int8)
    for fold in folds:
        coverage += fold.truth.astype(np.int8)
        # The visible catalogue cannot enter the Euclidean 2-pixel buffer.
        yy, xx = np.ogrid[-2:3, -2:3]
        disk = yy * yy + xx * xx <= 4
        expanded = __import__("scipy.ndimage", fromlist=["binary_dilation"]).binary_dilation(
            fold.truth, structure=disk
        )
        assert not np.any(fold.visible & expanded)
    assert np.array_equal(coverage.astype(bool), labels == 1)
    assert np.all(coverage[18, 5:56] == 1)
    assert np.all(coverage[31, 40:48] == 1)


def test_make_segment_folds_rejects_mismatched_shapes():
    from gems55 import holdout55

    with pytest.raises(ValueError, match="shape"):
        holdout55.make_segment_folds(np.zeros((3, 4)), np.ones((4, 3), dtype=bool))


def test_make_segment_folds_fails_without_two_occupied_bins():
    from gems55 import holdout55

    labels = np.zeros((20, 20), dtype=np.int8)
    labels[10, 8:12] = 1
    with pytest.raises(ValueError, match="fewer than two spatial bins"):
        holdout55.make_segment_folds(labels, np.ones_like(labels, dtype=bool), n_folds=4)


# --------------------------------------------------------------------------- #
# Tensor: closed-form eigen-decomposition and the dimensionality endpoints
# --------------------------------------------------------------------------- #
def test_sym3_eigh_matches_numpy_eigh():
    rng = np.random.default_rng(1)
    n = 400
    comps = {}
    for k, scale in [("Txx", 1.0), ("Tyy", 1.0), ("Tzz", 1.0), ("Txy", 0.7), ("Txz", 0.5), ("Tyz", 0.3)]:
        v = rng.normal(size=n) * scale
        # keep it traceless like a real potential-field tensor
        comps[k] = v
    trace = comps["Txx"] + comps["Tyy"] + comps["Tzz"]
    comps["Tzz"] -= trace
    lam, e2 = tensor55.sym3_eigh(comps)
    M = np.zeros((n, 3, 3))
    M[:, 0, 0] = comps["Txx"]
    M[:, 1, 1] = comps["Tyy"]
    M[:, 2, 2] = comps["Tzz"]
    M[:, 0, 1] = M[:, 1, 0] = comps["Txy"]
    M[:, 0, 2] = M[:, 2, 0] = comps["Txz"]
    M[:, 1, 2] = M[:, 2, 1] = comps["Tyz"]
    ref = np.linalg.eigvalsh(M)[:, ::-1]  # descending
    assert lam == pytest.approx(ref, abs=1e-4)
    # e2 really is an eigenvector of the intermediate eigenvalue
    resid = np.einsum("nij,nj->ni", M, e2.astype(np.float64)) - lam[:, 1][:, None] * e2.astype(np.float64)
    scale = np.abs(M).max(axis=(1, 2)) + 1e-30
    assert np.max(np.linalg.norm(resid, axis=1) / scale) < 1e-3


def test_tensor_is_traceless_by_construction():
    rng = np.random.default_rng(2)
    f = rng.normal(size=(200, 220))
    T = tensor55.gradient_tensor(f, 100.0, lowpass_m=300.0, highpass_m=None)
    tr = T["Txx"] + T["Tyy"] + T["Tzz"]
    interior = slice(20, 180), slice(20, 200)
    denom = np.abs(T["Txx"][interior]).max()
    assert np.abs(tr[interior]).max() / denom < 1e-9


def test_gradient_tensor_matches_analytic_harmonic_solution():
    """Spectral-exactness check on a single-wavenumber potential with sources below.

    For sources beneath the observation plane and z positive downward, the
    harmonic solution is V = e^{+kz} sin(kx x).  At z = 0:

        gx  =  kx cos(kx x)
        Txx = -kx^2 sin(kx x)
        Tyy =  0
        Tzz = +kx^2 sin(kx x)
        Txz = +kx^2 cos(kx x)     (= |k| d/dx, the standard vertical-derivative
                                   filter with z positive down)
        Tyz =  0

    The field is exactly periodic on the grid and unfiltered, so the FFT
    derivative is exact to round-off.
    """
    ny, nx = 128, 256
    res = 100.0
    L = 32  # pixels
    kx_pix = 2.0 * np.pi / L          # rad per pixel
    kx = kx_pix / res                 # rad per metre (the operator works in metres)
    x = np.arange(nx)[None, :] * np.ones((ny, 1))
    f = np.sin(kx_pix * x)
    T = tensor55.gradient_tensor(f, res, lowpass_m=None, highpass_m=None, taper_pad_frac=0.0)
    c = np.cos(kx_pix * x)
    s = np.sin(kx_pix * x)
    assert T["gx"] == pytest.approx(kx * c, abs=1e-5)
    assert T["gy"] == pytest.approx(0.0, abs=1e-5)
    assert T["Txx"] == pytest.approx(-(kx**2) * s, abs=1e-4)
    assert T["Tyy"] == pytest.approx(0.0, abs=1e-4)
    assert T["Tzz"] == pytest.approx((kx**2) * s, abs=1e-4)
    assert T["Txz"] == pytest.approx((kx**2) * c, abs=1e-4)
    assert T["Tyz"] == pytest.approx(0.0, abs=1e-4)


def test_dimensionality_endpoints_are_exact():
    # strike-extended 2-D line source -> lam = (a, 0, -a)
    lam2d = np.array([[1.0, 0.0, -1.0]], dtype=np.float32)
    # equidimensional 3-D point mass   -> lam = (2a, -a, -a)
    lam3d = np.array([[2.0, -1.0, -1.0]], dtype=np.float32)
    # 1-D sheet (both horizontal dims equal/infinite) -> lam = (a, a, -2a)
    lamsh = np.array([[1.0, 1.0, -2.0]], dtype=np.float32)
    assert tensor55.dimensionality_invariant(lam2d)[0] == pytest.approx(0.0, abs=1e-12)
    assert tensor55.dimensionality_invariant(lam3d)[0] == pytest.approx(1.0, abs=1e-12)
    assert tensor55.dimensionality_invariant(lamsh)[0] == pytest.approx(1.0, abs=1e-12)
    assert tensor55.dimensionality_eigratio(lam2d)[0] == pytest.approx(0.0, abs=1e-12)
    assert tensor55.dimensionality_eigratio(lam3d)[0] == pytest.approx(0.5, abs=1e-12)


def test_dimensionality_is_scale_free():
    lam = np.array([[3.0, -1.0, -2.0]], dtype=np.float32)
    assert tensor55.dimensionality_invariant(lam)[0] == pytest.approx(
        tensor55.dimensionality_invariant(lam * 1e4)[0], rel=1e-4
    )


def test_east_west_striping_is_indistinguishable_from_a_2d_source():
    """Documents why the striping mask cannot come from the tensor itself.

    A field that varies only across E-W flight lines, V = f(y), has
    Txx = Txy = Txz = Tyz = 0, Tyy = f'', Tzz = -f'' -> eigenvalues
    (|f''|, 0, -|f''|), i.e. exactly a 2-D strike-extended source with strike
    parallel to the flight lines.  So the dimensionality index is ~0 and the
    strike-agreement test passes; striping must be removed geometrically.
    """
    ny, nx = 256, 256
    y = np.arange(ny)[:, None] * np.ones((1, nx))
    f = np.sin(2 * np.pi * y / 17.0)
    T = tensor55.gradient_tensor(f, 100.0, lowpass_m=None, highpass_m=None)
    lam, e2 = tensor55.sym3_eigh(T)
    c = slice(64, 192), slice(64, 192)
    D = tensor55.dimensionality_invariant(lam.reshape(-1, 3)).reshape(ny, nx)
    az = tensor55.strike_eigenvector(e2.reshape(-1, 3)).reshape(ny, nx)
    assert np.median(D[c]) < 0.05          # looks perfectly 2-D
    circ = np.abs(((az[c] - 90.0 + 90.0) % 180.0) - 90.0)
    assert np.median(circ) < 5.0           # and its strike is E-W


def test_angular_difference_is_undirected():
    a = np.array([10.0, 170.0, 90.0])
    b = np.array([175.0, 5.0, 0.0])
    d = tensor55.angular_difference_deg(a, b)
    assert d == pytest.approx([15.0, 15.0, 90.0], abs=1e-5)


# --------------------------------------------------------------------------- #
# Submission writer
# --------------------------------------------------------------------------- #
def test_write_submission_enforces_range_and_uses_nan_outside_by_default(tmp_path):
    import rasterio

    fp = np.zeros((io55.HEIGHT, io55.WIDTH), dtype=bool)
    fp[90:110, 90:110] = True
    grid = io55.Grid(io55.HEIGHT, io55.WIDTH, io55.CRS_EPSG, io55.TRANSFORM, fp)
    a = np.zeros(grid.shape, dtype=np.float32)
    a[100, 100] = 1.0          # inside the footprint
    a[0, 0] = 5.0              # outside the footprint -> overwritten with NaN
    # A value > 1 inside the footprint must be rejected.
    bad = a.copy()
    bad[100, 100] = 2.0
    with pytest.raises(ValueError):
        io55.write_submission(bad, tmp_path / "bad.tif", grid)
    bad_nan = a.copy()
    bad_nan[100, 100] = np.nan
    with pytest.raises(ValueError):
        io55.write_submission(bad_nan, tmp_path / "bad_nan.tif", grid)
    p = io55.write_submission(a, tmp_path / "ok.tif", grid)
    with rasterio.open(p) as src:
        got = src.read(1)
        assert src.count == 1 and src.dtypes[0] == "float32"
        assert src.crs.to_epsg() == 32611
        assert tuple(src.transform)[:6] == tuple(io55.TRANSFORM)[:6]
        assert np.isfinite(got[fp]).all()
        assert got[fp].min() >= 0.0 and got[fp].max() <= 1.0
        assert np.isnan(got[0, 0])
        assert np.array_equal(np.isnan(got), ~fp)
