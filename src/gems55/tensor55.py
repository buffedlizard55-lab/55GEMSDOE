"""FFT gradient tensor, dimensionality index and strike (the tensor-dimensionality lane).

Physics
-------
For a source-free potential field V (reduced-to-pole magnetic anomaly, or the
isostatic gravity anomaly) observed on a horizontal plane, the gradient tensor

    T = [[Txx, Txy, Txz],
         [Txy, Tyy, Tyz],
         [Txz, Tyz, Tzz]]

has six independent components and, because V is harmonic, ``trace(T) = 0``.
In the 2-D Fourier domain with angular wavenumbers (kx, ky) and |k| = hypot(kx, ky),
taking z positive *downward* and using the upward-continuation operator
``exp(-|k| dz)``:

    d/dx    <-> i kx
    d/dy    <-> i ky
    d/dz    <-> |k|
    Txx = d2V/dx2  <-> -kx^2   V^
    Tyy = d2V/dy2  <-> -ky^2   V^
    Txy = d2V/dxdy <-> -kx ky  V^
    Tzz = d2V/dz2  <-> +|k|^2  V^      (= -(kx^2+ky^2) V^, so trace(T) = 0 exactly)
    Txz = d2V/dxdz <-> +i kx |k| V^
    Tyz = d2V/dydz <-> +i ky |k| V^

Because Tzz is *derived* from the horizontal wavenumbers, the tensor is exactly
traceless by construction; synthetic regression tests live in ``tests_numeric/``.

References
----------
* Pedersen, L. B., and T. M. Rasmussen, 1990, The gradient tensor of potential
  field anomalies; some implications on data collection and data processing of
  maps: Geophysics, 55(12), 1558-1566. https://doi.org/10.1190/1.1442807
  (dimensionality concept: the tensor's eigenvalues carry source dimensionality)
* Beiki, M., and L. B. Pedersen, 2010, Eigenvector analysis of gravity gradient
  tensor to locate geologic bodies: Geophysics, 75(6), I37-I49.
  https://doi.org/10.1190/1.3484098
  (the largest-eigenvalue eigenvector points toward the causative body; for
  quasi-2-D bodies an eigenvector gives the strike)
* Karimi, K., and G. Kletetschka, 2024, Subsurface geology detection from
  application of the gravity-related dimensionality constraint: Sci. Rep. 14:2440.
  https://doi.org/10.1038/s41598-024-52843-5 (open access; restates the
  Pedersen-Rasmussen dimensionality indicator I, 0 for pure 2-D and 1 for pure 3-D)
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

__all__ = [
    "angular_wavenumbers",
    "gradient_tensor",
    "sym3_eigh",
    "dimensionality_invariant",
    "dimensionality_eigratio",
    "strike_eigenvector",
    "gaussian_lowpass",
    "bandpass",
    "destripe",
    "pseudogravity",
]


# --------------------------------------------------------------------------- #
# Fourier-domain derivatives
# --------------------------------------------------------------------------- #
def angular_wavenumbers(shape: tuple[int, int], res_m: float) -> tuple[np.ndarray, np.ndarray]:
    """Angular wavenumbers (rad/m) on the FFT grid, ``ky`` first (row axis = y)."""
    ny, nx = shape
    ky = 2.0 * np.pi * np.fft.fftfreq(ny, d=res_m)
    kx = 2.0 * np.pi * np.fft.fftfreq(nx, d=res_m)
    return kx, ky


def _pad_mirror(a: np.ndarray, pad: int) -> np.ndarray:
    return np.pad(a, pad, mode="reflect")


def gradient_tensor(
    field: np.ndarray,
    res_m: float,
    *,
    lowpass_m: float | None = 400.0,
    highpass_m: float | None = 6000.0,
    taper_pad_frac: float = 0.25,
    components: tuple[str, ...] = ("Txx", "Tyy", "Txy", "Tzz", "Txz", "Tyz", "gx", "gy", "gz", "bp"),
    workers: int = -1,
) -> dict[str, np.ndarray]:
    """Six independent gradient-tensor components from a gridded potential field.

    ``lowpass_m`` / ``highpass_m`` are Gaussian sigma values in metres applied in
    the wavenumber domain *before* differentiation (derivative operators amplify
    high-k noise by |k| and |k|^2, so this is mandatory).  ``highpass_m`` removes
    the regional trend.  The field is mirror-padded to suppress FFT wrap-around.

    Returns a dict with keys ``Txx, Tyy, Txy, Tzz, Txz, Tyz`` plus the first-order
    gradients ``gx, gy`` and the vertical derivative ``gz``.
    """
    import scipy.fft as sfft

    a = np.asarray(field, dtype=np.float32)
    ny, nx = a.shape
    pad = int(round(max(ny, nx) * taper_pad_frac))
    ap = _pad_mirror(a.astype(np.float32), pad)

    kx, ky = angular_wavenumbers(ap.shape, res_m)
    KX, KY = np.meshgrid(kx.astype(np.float32), ky.astype(np.float32))
    K = np.hypot(KX, KY)

    # Gaussian filters: response exp(-0.5 (K sigma)^2) is the Fourier transform
    # of a Gaussian with spatial standard deviation ``sigma`` metres.
    filt = np.ones_like(K)
    if highpass_m:  # kill the regional trend (long wavelengths)
        filt = filt * (1.0 - np.exp(-0.5 * (K * highpass_m) ** 2))
    if lowpass_m:  # suppress high-k noise before differentiating
        filt = filt * np.exp(-0.5 * (K * lowpass_m) ** 2)

    # complex64 throughout: half the memory of numpy's complex128 default.
    F = sfft.fft2(ap.astype(np.complex64), workers=workers, overwrite_x=True)
    F *= filt.astype(np.complex64)
    del ap, filt

    k2 = (KX * KX + KY * KY).astype(np.float32)

    def inv(mult):
        g = sfft.ifft2(F * mult, workers=workers).real
        return np.ascontiguousarray(g[pad : pad + ny, pad : pad + nx].astype(np.float32))

    out: dict[str, np.ndarray] = {}
    if "Txx" in components:
        out["Txx"] = inv(-(KX * KX))
    if "Tyy" in components:
        out["Tyy"] = inv(-(KY * KY))
    if "Txy" in components:
        out["Txy"] = inv(-(KX * KY))
    if "Tzz" in components:
        # trace(T) = 0 for a harmonic potential, so Tzz = -(Txx + Tyy) exactly.
        # Deriving it avoids a seventh inverse transform and enforces Laplace.
        need_x = "Txx" not in out
        need_y = "Tyy" not in out
        txx = inv(-(KX * KX)) if need_x else out["Txx"]
        tyy = inv(-(KY * KY)) if need_y else out["Tyy"]
        out["Tzz"] = np.ascontiguousarray(-(txx + tyy))
    if "Txz" in components:
        out["Txz"] = inv(1j * KX * K)
    if "Tyz" in components:
        out["Tyz"] = inv(1j * KY * K)
    if "gx" in components:
        out["gx"] = inv(1j * KX)
    if "gy" in components:
        out["gy"] = inv(1j * KY)
    if "gz" in components:
        out["gz"] = inv(K)
    if "bp" in components:
        out["bp"] = inv(np.ones_like(K))
    return out


def pseudogravity(
    field: np.ndarray,
    res_m: float,
    *,
    pad_frac: float = 0.05,
    workers: int = -1,
) -> np.ndarray:
    """Baranov/Gunn pseudogravity transform: vertical integration of a magnetic field.

    For an RTP (reduced-to-pole) magnetic anomaly ``T`` the magnetisation and the
    inducing field are, by construction, vertical, so ``T`` is proportional to the
    *vertical derivative* of the magnetic scalar potential ``V``.  ``V`` is
    therefore recovered (up to a multiplicative constant that cancels in every
    normalised product downstream) by dividing the spectrum by ``|k|``:

        V^ (kx, ky) = T^ (kx, ky) / |k|      (|k| = hypot(kx, ky), V^(0) = 0)

    The result plays exactly the role of a gravity potential, so the Marussi
    tensor built from it (``gradient_tensor``) is the quantity analysed by
    Pedersen & Rasmussen (1990) and Beiki & Pedersen (2010).  Operating on ``T``
    directly instead would build a *third*-derivative tensor: it is still
    traceless and still has a vanishing intermediate eigenvalue for a 2-D source,
    but it is not the published quantity and it weights short wavelengths one
    extra power of ``|k|``.

    Sign convention: ``gradient_tensor`` uses z positive downward and maps
    ``d/dz -> +|k|``.  Writing ``T = dV/dz`` under that same convention gives
    ``V^ = T^/|k|`` with a *positive* sign, which is what this routine returns.
    Every downstream product (eigenvalues, |strike| azimuth) is invariant to a
    global sign flip of the potential, so the choice is immaterial for the lane;
    it only matters that the convention is stated.
    """
    import scipy.fft as sfft

    a = np.asarray(field, dtype=np.float32)
    ny, nx = a.shape
    pad = int(round(max(ny, nx) * pad_frac))
    ap = _pad_mirror(a, pad)
    kx, ky = angular_wavenumbers(ap.shape, res_m)
    KY, KX = np.meshgrid(ky.astype(np.float32), kx.astype(np.float32), indexing="ij")
    K = np.hypot(KX, KY)
    with np.errstate(divide="ignore", invalid="ignore"):
        inv_k = np.where(K > 0, 1.0 / K, 0.0).astype(np.float32)
    F = sfft.fft2(ap.astype(np.complex64), workers=workers, overwrite_x=True)
    F *= inv_k
    F[0, 0] = 0.0
    del ap, inv_k, K, KX, KY
    out = sfft.ifft2(F, workers=workers, overwrite_x=True).real
    return np.ascontiguousarray(out[pad : pad + ny, pad : pad + nx].astype(np.float32))


def gaussian_lowpass(field: np.ndarray, sigma_m: float, res_m: float) -> np.ndarray:
    """Gaussian low-pass in the wavenumber domain (mirror-padded)."""
    a = np.asarray(field, dtype=np.float64)
    ny, nx = a.shape
    pad = int(round(max(ny, nx) * 0.25))
    ap = _pad_mirror(a, pad)
    kx, ky = angular_wavenumbers(ap.shape, res_m)
    KX, KY = np.meshgrid(kx, ky)
    K = np.hypot(KX, KY)
    F = np.fft.fft2(ap) * np.exp(-0.5 * (K * sigma_m) ** 2)
    out = np.real(np.fft.ifft2(F))
    return out[pad : pad + ny, pad : pad + nx]


def bandpass(field: np.ndarray, res_m: float, low_m: float, high_m: float, pad_frac: float = 0.25) -> np.ndarray:
    """Gaussian band-pass: keep wavelengths between ``high_m`` (long) and ``low_m`` (short)."""
    import scipy.fft as sfft

    a = np.asarray(field, dtype=np.float32)
    ny, nx = a.shape
    pad = int(round(max(ny, nx) * pad_frac))
    ap = _pad_mirror(a, pad)
    kx, ky = angular_wavenumbers(ap.shape, res_m)
    KX, KY = np.meshgrid(kx.astype(np.float32), ky.astype(np.float32))
    K = np.hypot(KX, KY)
    resp = (np.exp(-0.5 * (K * low_m) ** 2) * (1.0 - np.exp(-0.5 * (K * high_m) ** 2))).astype(np.complex64)
    F = sfft.fft2(ap.astype(np.complex64), workers=-1, overwrite_x=True)
    F *= resp
    out = sfft.ifft2(F, workers=-1, overwrite_x=True).real
    return np.ascontiguousarray(out[pad : pad + ny, pad : pad + nx].astype(np.float32))


# --------------------------------------------------------------------------- #
# Destriping / acquisition-block levelling
# --------------------------------------------------------------------------- #
def destripe(field: np.ndarray, along_axis: int, valid: np.ndarray, min_count: int = 40) -> np.ndarray:
    """Remove the survey-striping component: the along-track median profile.

    An airborne line artefact is constant along the flight-line direction and
    varies only across it, so its footprint is a *profile* indexed by the
    cross-track coordinate.  Subtracting the robust (median) along-track profile
    is the standard micro-levelling step and is what the lane means by "work
    within each acquisition block separately".

    ``along_axis`` is the numpy axis that runs *along* the flight lines
    (axis=1 for east-west lines, axis=0 for north-south lines).
    """
    a = np.array(field, dtype=np.float64)
    m = np.asarray(valid, dtype=bool)
    work = np.where(m, a, np.nan)
    profile = np.nanmedian(work, axis=along_axis)
    cnt = np.sum(m, axis=along_axis)
    profile = np.where(cnt >= min_count, profile, 0.0)
    shape = [1, 1]
    shape[1 - along_axis] = profile.size
    return a - profile.reshape(shape)


# --------------------------------------------------------------------------- #
# Eigen-analysis of the symmetric 3x3 tensor (vectorised, closed form)
# --------------------------------------------------------------------------- #
def sym3_eigh(T: dict[str, np.ndarray], *, chunk: int = 400_000) -> tuple[np.ndarray, np.ndarray]:
    """Eigenvalues (descending) and the null/intermediate eigenvector, vectorised.

    Uses the trigonometric closed form for a symmetric 3x3 matrix (Smith 1961;
    the standard "eigenvalues of a symmetric 3x3 matrix" algorithm), which is
    orders of magnitude faster and far more memory-frugal than
    ``numpy.linalg.eigh`` over ~5.2 M matrices. ``tests_numeric/test_core.py`` checks
    it against ``numpy.linalg.eigh`` on random tensors.

    Returns
    -------
    lam : (N, 3) float32, ``lam[:,0] >= lam[:,1] >= lam[:,2]``
    e2  : (N, 3) float32, unit eigenvector of ``lam[:,1]`` (the "null" direction
          for a strike-extended source), plus a validity flag in column 3 of
          ``e2`` -- no, validity is returned separately by :func:`strike_eigenvector`.
    """
    shape = T["Txx"].shape
    n = int(np.prod(shape))
    if n > chunk:
        lams = np.empty((n, 3), dtype=np.float32)
        e2s = np.empty((n, 3), dtype=np.float32)
        for s in range(0, n, chunk):
            e = min(s + chunk, n)
            keys = ("Txx", "Tyy", "Tzz", "Txy", "Txz", "Tyz")
            sub = {k: np.asarray(T[k]).ravel()[s:e] for k in keys}
            lams[s:e], e2s[s:e] = sym3_eigh(sub, chunk=chunk)
        return lams, e2s
    txx = T["Txx"].ravel().astype(np.float64)
    tyy = T["Tyy"].ravel().astype(np.float64)
    tzz = T["Tzz"].ravel().astype(np.float64)
    txy = T["Txy"].ravel().astype(np.float64)
    txz = T["Txz"].ravel().astype(np.float64)
    tyz = T["Tyz"].ravel().astype(np.float64)

    p1 = txy**2 + txz**2 + tyz**2
    q = (txx + tyy + tzz) / 3.0
    p2 = (txx - q) ** 2 + (tyy - q) ** 2 + (tzz - q) ** 2 + 2.0 * p1
    p = np.sqrt(p2 / 6.0)

    with np.errstate(invalid="ignore", divide="ignore"):
        # B = (T - q I)/p ; r = det(B)/2
        b11 = (txx - q) / p
        b22 = (tyy - q) / p
        b33 = (tzz - q) / p
        b12 = txy / p
        b13 = txz / p
        b23 = tyz / p
        detB = (
            b11 * (b22 * b33 - b23 * b23)
            - b12 * (b12 * b33 - b23 * b13)
            + b13 * (b12 * b23 - b22 * b13)
        )
        r = np.clip(detB / 2.0, -1.0, 1.0)
        phi = np.arccos(r) / 3.0
        l1 = q + 2.0 * p * np.cos(phi)
        l3 = q + 2.0 * p * np.cos(phi + 2.0 * np.pi / 3.0)
        l2 = 3.0 * q - l1 - l3

    degenerate = ~(p > 0)
    if degenerate.any():
        d = np.stack([txx, tyy, tzz], axis=1)
        ds = -np.sort(-d, axis=1)
        l1 = np.where(degenerate, ds[:, 0], l1)
        l2 = np.where(degenerate, ds[:, 1], l2)
        l3 = np.where(degenerate, ds[:, 2], l3)

    lam = np.stack([l1, l2, l3], axis=1).astype(np.float32)

    # Eigenvector of the intermediate eigenvalue l2.
    # (T - l1 I)(T - l3 I) is proportional to e2 e2^T, so any non-null column
    # of that product, normalised, is e2.
    M = _outer_project(txx, tyy, tzz, txy, txz, tyz, l1, l3)  # (N,3,3)
    nrm = np.sqrt((M**2).sum(axis=1))  # (N,3): norm of each column
    col = np.argmax(nrm, axis=1)  # (N,)
    e2 = M[np.arange(n), :, col]  # (N,3)
    norm = np.linalg.norm(e2, axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        e2 = e2 / np.maximum(norm, 1e-300)[:, None]
    e2 = np.where(norm[:, None] > 1e-30, e2, 0.0)
    return lam, e2.astype(np.float32)


def _outer_project(txx, tyy, tzz, txy, txz, tyz, la, lb):
    """Column-wise (T - la I)(T - lb I) as an (N,3,3) array of the 3 columns."""
    n = txx.size
    a11 = txx - la
    a22 = tyy - la
    a33 = tzz - la
    b11 = txx - lb
    b22 = tyy - lb
    b33 = tzz - lb
    M = np.empty((n, 3, 3), dtype=np.float64)
    # (A B)[:, j] = A @ B[:, j]
    B0 = np.stack([b11, txy, txz], axis=1)
    B1 = np.stack([txy, b22, tyz], axis=1)
    B2 = np.stack([txz, tyz, b33], axis=1)
    for j, B in enumerate((B0, B1, B2)):
        M[:, 0, j] = a11 * B[:, 0] + txy * B[:, 1] + txz * B[:, 2]
        M[:, 1, j] = txy * B[:, 0] + a22 * B[:, 1] + tyz * B[:, 2]
        M[:, 2, j] = txz * B[:, 0] + tyz * B[:, 1] + a33 * B[:, 2]
    return M


# --------------------------------------------------------------------------- #
# Dimensionality and strike
# --------------------------------------------------------------------------- #
def dimensionality_invariant(lam: np.ndarray) -> np.ndarray:
    """Pedersen-Rasmussen dimensionality indicator, normalised to [0, 1].

    Scale-free function of the eigenvalue triple.  With the tensor invariants

        e2 = l1 l2 + l1 l3 + l2 l3        (<= 0 whenever trace = 0)
        e3 = l1 l2 l3                     (= det T)

    the indicator is

        I = 27 e3^2 / (4 (-e2)^3)

    Endpoints (verified analytically in ``tests_numeric/test_tensor.py``):

      * strike-extended 2-D source, l = (a, 0, -a):  e3 = 0          -> I = 0
      * equidimensional 3-D source, l = (2a, -a, -a): I              -> 1
      * 1-D sheet,                  l = (a, a, -2a): I              -> 1

    This is the algebraic form of the indicator reported by Karimi & Kletetschka
    (2024, Eq. 4) after Pedersen & Rasmussen (1990), written so that the two
    documented endpoints are exact.  See docs/irregularities.md IR-55-03 for the
    transcription caveat.
    """
    l1 = lam[:, 0].astype(np.float64)
    l2 = lam[:, 1].astype(np.float64)
    l3 = lam[:, 2].astype(np.float64)
    e2 = l1 * l2 + l1 * l3 + l2 * l3
    e3 = l1 * l2 * l3
    num = 27.0 * e3**2
    den = 4.0 * (-e2) ** 3
    with np.errstate(invalid="ignore", divide="ignore"):
        I = np.where(den > 0, num / den, 1.0)
    return np.clip(np.nan_to_num(I, nan=1.0, posinf=1.0, neginf=0.0), 0.0, 1.0).astype(np.float32)


def dimensionality_eigratio(lam: np.ndarray) -> np.ndarray:
    """Eigenvalue-ratio dimensionality D = -l2/l1, clipped to [0, 1].

    0 for a strike-extended 2-D source (l2 = 0); 0.5 for a point mass.  Reported
    alongside :func:`dimensionality_invariant` because the two orderings are not
    identical and the holdout decides which one gates better.
    """
    l1 = lam[:, 0].astype(np.float64)
    l2 = lam[:, 1].astype(np.float64)
    with np.errstate(invalid="ignore", divide="ignore"):
        D = np.where(np.abs(l1) > 1e-30, -l2 / np.maximum(l1, 1e-30), 1.0)
    return np.clip(np.nan_to_num(D, nan=1.0, posinf=1.0, neginf=0.0), 0.0, 1.0).astype(np.float32)


def strike_eigenvector(e2: np.ndarray) -> np.ndarray:
    """Geographic strike azimuth (degrees, 0-180 from north) of the null eigenvector.

    Axes are (east, north, down) = (x, y, z).  The strike is the horizontal
    projection of ``e2``; where the projection is degenerate the azimuth is 0 and
    the caller should weight it out with :func:`strike_plunge_weight`.
    """
    ex = e2[:, 0].astype(np.float64)
    ey = e2[:, 1].astype(np.float64)
    az = np.degrees(np.arctan2(ex, ey)) % 180.0
    return az.astype(np.float32)


def strike_plunge_weight(e2: np.ndarray) -> np.ndarray:
    """How horizontal the null eigenvector is: 1 = perfectly horizontal (strike-able)."""
    h = np.sqrt(e2[:, 0] ** 2 + e2[:, 1] ** 2)
    return np.clip(h, 0.0, 1.0).astype(np.float32)


def angular_difference_deg(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Smallest angle between two undirected (mod 180) azimuths, in [0, 90]."""
    d = np.abs(np.asarray(a, dtype=np.float64) - np.asarray(b, dtype=np.float64)) % 180.0
    return np.minimum(d, 180.0 - d).astype(np.float32)


@dataclass
class TensorProducts:
    """Container for the per-pixel tensor products used downstream."""

    dim_inv: np.ndarray
    dim_eig: np.ndarray
    strike: np.ndarray
    plunge_w: np.ndarray
    lam: np.ndarray
