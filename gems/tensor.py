"""Tensor-dimensionality lane: gradient tensor by FFT, dimensionality index, strike, ridges.

Method (sources verified 2026-10-09):
  * Pedersen & Rasmussen (1990) dimensionality indicator, 0 = pure 2-D, 1 = pure 3-D;
    Beiki & Pedersen (2010, Geophysics 75, I37-I49) eigenvector analysis: for a quasi-2-D body the
    eigenvector of the MINIMUM eigenvalue gives strike.  Sources: ResearchGate abstract
    https://www.researchgate.net/publication/228794726_Eigenvector_analysis_of_gravity_gradient_tensor_to_locate_geologic_bodies
    ASEG 2012 extended abstract (dimensionality threshold 0.5, PGGT strike):
    https://www.tandfonline.com/doi/pdf/10.1071/ASEG2012ab057
  * Index used here: I = |lambda_min| / |lambda_mid| (eigenvalues ordered by absolute value), clipped to
    [0, 1].  The ratio of smallest to intermediate eigenvalue is the form given in Beiki's TSVD paper
    (ScienceDirect abstract https://www.sciencedirect.com/science/article/abs/pii/S0926985113000062).
    NOTE: the exact 1990 normalisation was not retrievable from this sandbox; flagged for review.
  * Magnetic data: pseudogravity transform  F_pg = F_RTP / |k|  (Fourier domain), then the tensor.
    Isostatic gravity: tensor of the isostatic anomaly directly.
  * Tensor from FFT:  T_ab = IFFT( s_a s_b F ) with s_x = i kx, s_y = i ky, s_z = -|k|.
    Traceless by construction (Laplace).  Strike = horizontal part of the eigenvector of min |lambda|.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage

PAD = 64
TINY = 1e-30


def fill_and_lowpass(field: np.ndarray, footprint: np.ndarray, sigma_px: float = 2.0):
    """Fill NaN/outside-footprint with the footprint mean, low-pass (Gaussian, 200 m), mirror-pad."""
    mean = float(field[footprint & np.isfinite(field)].mean())
    f = np.where(footprint & np.isfinite(field), field, mean).astype(np.float64)
    f = ndimage.gaussian_filter(f, sigma_px, mode="nearest")
    return np.pad(f, PAD, mode="reflect")


def derivatives(padded: np.ndarray, pseudogravity: bool, dx: float = 100.0):
    """Return dict of 6 tensor components and the two horizontal first derivatives, all cropped."""
    H, W = padded.shape
    kx = 2 * np.pi * np.fft.fftfreq(W, d=dx)
    ky = 2 * np.pi * np.fft.fftfreq(H, d=dx)
    KX, KY = np.meshgrid(kx, ky)
    K = np.hypot(KX, KY)
    F = np.fft.fft2(padded)
    if pseudogravity:
        with np.errstate(divide="ignore", invalid="ignore"):
            F = np.where(K > 0, F / np.where(K > 0, K, 1.0), 0.0)
    sx, sy, sz = 1j * KX, 1j * KY, -K
    crop = (slice(PAD, H - PAD), slice(PAD, W - PAD))
    sym = {"x": sx, "y": sy, "z": sz}
    out = {}
    for a, b in [("x", "x"), ("y", "y"), ("z", "z"), ("x", "y"), ("x", "z"), ("y", "z")]:
        out[a + b] = np.real(np.fft.ifft2(F * sym[a] * sym[b]))[crop].astype(np.float32)
    out["gx"] = np.real(np.fft.ifft2(F * sx))[crop].astype(np.float32)
    out["gy"] = np.real(np.fft.ifft2(F * sy))[crop].astype(np.float32)
    return out


def dimensionality_and_strike(T: dict, chunk: int = 256):
    """Per-pixel dimensionality index I in [0,1], strike azimuth (deg, mod 180, from north),
    and confidence = horizontal length of the min-|lambda| eigenvector (0 = vertical/undefined)."""
    H, W = T["xx"].shape
    I = np.empty((H, W), np.float32)
    az = np.empty((H, W), np.float32)
    conf = np.empty((H, W), np.float32)
    for r0 in range(0, H, chunk):
        r1 = min(H, r0 + chunk)
        n = r1 - r0
        M = np.empty((n, W, 3, 3), np.float64)
        M[..., 0, 0] = T["xx"][r0:r1]; M[..., 1, 1] = T["yy"][r0:r1]; M[..., 2, 2] = T["zz"][r0:r1]
        M[..., 0, 1] = M[..., 1, 0] = T["xy"][r0:r1]
        M[..., 0, 2] = M[..., 2, 0] = T["xz"][r0:r1]
        M[..., 1, 2] = M[..., 2, 1] = T["yz"][r0:r1]
        w, v = np.linalg.eigh(M)
        aw = np.abs(w)
        order = np.argsort(aw, axis=-1)
        ia = order[..., 0]
        ib = order[..., 1]
        a = np.take_along_axis(aw, ia[..., None], axis=-1)[..., 0]
        b = np.take_along_axis(aw, ib[..., None], axis=-1)[..., 0]
        Ii = np.where(b > TINY, np.clip(a / np.maximum(b, TINY), 0.0, 1.0), 1.0)
        idx = np.broadcast_to(ia[..., None, None], ia.shape + (3, 1))
        va = np.take_along_axis(v, idx, axis=-1)[..., 0]          # eigenvector, shape (n, W, 3)
        vx, vy = va[..., 0], va[..., 1]
        I[r0:r1] = Ii
        # grid rows increase SOUTH, so north = -y.  Azimuth from north, clockwise, mod 180.
        az[r0:r1] = np.mod(np.degrees(np.arctan2(vx, -vy)), 180.0)
        conf[r0:r1] = np.hypot(vx, vy)
    return I, az, conf


def ridges(gx: np.ndarray, gy: np.ndarray, footprint: np.ndarray, pct: float = 80.0):
    """Non-maximum-suppressed ridges of the horizontal-gradient magnitude.
    Returns (ridge_mask, ridge_azimuth_deg_mod180, G)."""
    G = np.hypot(gx, gy).astype(np.float64)
    th = np.arctan2(gy, gx)
    H, W = G.shape
    yy, xx = np.mgrid[0:H, 0:W]
    dy = np.rint(np.sin(th)).astype(int)
    dx = np.rint(np.cos(th)).astype(int)
    n1 = G[np.clip(yy + dy, 0, H - 1), np.clip(xx + dx, 0, W - 1)]
    n2 = G[np.clip(yy - dy, 0, H - 1), np.clip(xx - dx, 0, W - 1)]
    thr = np.percentile(G[footprint], pct)
    rm = (G >= n1) & (G >= n2) & (G > thr) & footprint
    # ridge runs perpendicular to the gradient. In north-up azimuth the ridge direction is (E,N)=(-gy,-gx),
    # so azimuth = atan2(gy, gx) mod 180 (grid rows increase south).
    az_r = np.mod(np.degrees(np.arctan2(gy, gx)), 180.0)
    return rm, az_r.astype(np.float32), G.astype(np.float32)


def angle_diff180(a, b):
    d = np.abs(np.mod(a - b, 180.0))
    return np.minimum(d, 180.0 - d)


def stripe_rows(rtp: np.ndarray, footprint: np.ndarray, z_thr: float = 4.0):
    """Flag E-W flight-line striping: rows whose median high-pass residual is a robust outlier.
    Striping is one-dimensional along E-W lines, i.e. constant along x within a row."""
    filled = fill_and_lowpass(rtp, footprint, sigma_px=0.0001)[PAD:-PAD, PAD:-PAD]
    hp = filled - ndimage.gaussian_filter(filled, 5, mode="nearest")
    hp = np.where(footprint, hp, np.nan)
    with np.errstate(all="ignore"):
        med = np.nanmedian(hp, axis=1)
    ok = np.isfinite(med)
    base = np.nanmedian(med[ok])
    mad = 1.4826 * np.nanmedian(np.abs(med[ok] - base)) + TINY
    z = np.where(ok, (med - base) / mad, 0.0)
    flagged = np.abs(z) > z_thr
    return flagged, z
