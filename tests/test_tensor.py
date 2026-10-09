import numpy as np
from gems import tensor


def _grid(n=256):
    y, x = np.mgrid[0:n, 0:n].astype(float)
    return x, y


def _run(field, pseudo=False):
    fp = np.ones(field.shape, bool)
    padded = tensor.fill_and_lowpass(field, fp, sigma_px=0.0001)
    T = tensor.derivatives(padded, pseudogravity=pseudo)
    return T, tensor.dimensionality_and_strike(T)


def test_traceless_tensor():
    x, y = _grid()
    f = -np.log((x - 128) ** 2 + 30.0 ** 2)          # 2-D line source (harmonic in x-z plane)
    T, _ = _run(f)
    tr = T["xx"] + T["yy"] + T["zz"]
    assert np.abs(tr[70:-70, 70:-70]).max() < 1e-3 * np.abs(T["zz"]).max()


def test_two_d_source_has_zero_dimensionality_and_ns_strike():
    x, y = _grid()
    f = -np.log((x - 128) ** 2 + 30.0 ** 2)          # varies only with x -> strike along y (north)
    T, (I, az, conf) = _run(f)
    core = (slice(100, 156), slice(100, 156))
    assert np.median(I[core]) < 0.02
    d = tensor.angle_diff180(az[core], 0.0)
    assert np.median(d) < 2.0


def test_point_source_is_more_three_dimensional_than_line():
    x, y = _grid()
    f2 = -np.log((x - 128) ** 2 + 30.0 ** 2)
    f3 = 1.0 / np.sqrt((x - 128) ** 2 + (y - 128) ** 2 + 30.0 ** 2)
    _, (I2, _, _) = _run(f2)
    _, (I3, _, _) = _run(f3)
    core = (slice(110, 146), slice(110, 146))
    assert np.median(I3[core]) > np.median(I2[core]) + 0.2


def test_auc_helper():
    from gems.holdout import auc
    assert abs(auc(np.array([3., 4.]), np.array([1., 2.])) - 1.0) < 1e-12
    assert abs(auc(np.array([1.]), np.array([1.])) - 0.5) < 1e-12


def test_strike_is_north_convention_and_not_mirrored():
    # 2-D source striking NW-SE: strike azimuth (from north, clockwise) = 135 deg.
    n = 256
    rows, cols = np.mgrid[0:n, 0:n].astype(float)
    E = cols - 128; N = -(rows - 128)                     # north-up coordinates; rows increase south
    s = (E + N) / np.sqrt(2)
    f = -np.log(s ** 2 + 30.0 ** 2)
    T, (I, az, conf) = _run(f)
    core = (slice(100, 156), slice(100, 156))
    assert tensor.angle_diff180(np.median(az[core]), 135.0) < 2.0


def test_ridge_azimuth_north_convention():
    # gradient pointing east (gx>0, gy=0) => contact runs north-south => azimuth 0
    n = 64
    gx = np.ones((n, n)); gy = np.zeros((n, n))
    fp = np.ones((n, n), bool)
    _, az_r, _ = tensor.ridges(gx, gy, fp)
    assert tensor.angle_diff180(float(np.median(az_r)), 0.0) < 1e-3
