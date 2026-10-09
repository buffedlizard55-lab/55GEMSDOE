"""Field preparation: NaN filling, destriping, and survey-line diagnostics."""

from __future__ import annotations

import numpy as np
from scipy import ndimage

from . import tensor55

__all__ = ["fill_nan_nearest", "prepare_field", "measure_striping_axis", "power_spectrum_azimuth_energy"]


def fill_nan_nearest(a: np.ndarray, valid: np.ndarray | None = None) -> np.ndarray:
    """Replace NaN with the value of the nearest valid pixel (exact nearest neighbour)."""
    a = np.asarray(a, dtype=np.float64)
    if valid is None:
        valid = np.isfinite(a)
    if valid.all():
        return np.where(valid, a, 0.0)
    idx = ndimage.distance_transform_edt(~valid, return_distances=False, return_indices=True)
    return a[tuple(idx)]


def prepare_field(
    field: np.ndarray,
    valid: np.ndarray,
    res_m: float,
    *,
    along_axis: int,
    lowpass_m: float = 400.0,
    highpass_m: float = 6000.0,
    destripe: bool = True,
    pad_frac: float = 0.10,
) -> tuple[np.ndarray, np.ndarray]:
    """NaN-fill, level (destripe) and band-pass a potential-field grid.

    Returns ``(prepared_field, filled_valid)``.  The band-passed field is what the
    gradient tensor is built from; the returned ``prepared_field`` is that
    band-passed product.
    """
    filled = fill_nan_nearest(field, valid)
    if destripe:
        filled = tensor55.destripe(filled, along_axis=along_axis, valid=valid)
        filled = fill_nan_nearest(np.where(valid, filled, np.nan), valid)
    bp = tensor55.bandpass(filled, res_m, low_m=lowpass_m, high_m=highpass_m, pad_frac=pad_frac)
    return bp, valid


def power_spectrum_azimuth_energy(
    field: np.ndarray, lam_lo_m: float, lam_hi_m: float, res_m: float, n_bins: int = 180
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Azimuthal distribution of spectral power inside a wavelength annulus.

    Returns ``(azimuth_deg, energy, wavelengths_m)``.  A spectral maximum at
    azimuth ``psi`` means structure elongated along ``psi + 90 deg``.
    """
    a = fill_nan_nearest(field)
    F = np.fft.fftshift(np.fft.fft2(a))
    P = np.abs(F) ** 2
    ny, nx = P.shape
    ky = np.fft.fftshift(np.fft.fftfreq(ny, d=res_m))
    kx = np.fft.fftshift(np.fft.fftfreq(nx, d=res_m))
    KX, KY = np.meshgrid(kx, ky)
    K = np.hypot(KX, KY)
    with np.errstate(invalid="ignore", divide="ignore"):
        lam = np.where(K > 0, 1.0 / K, np.inf)
    sel = (lam >= lam_lo_m) & (lam <= lam_hi_m)
    az = (np.degrees(np.arctan2(KX, KY)) % 180.0)[sel]  # direction of the k-vector, from north
    w = P[sel]
    bins = np.linspace(0, 180.0, n_bins + 1)
    hist, _ = np.histogram(az, bins=bins, weights=w)
    centres = 0.5 * (bins[:-1] + bins[1:])
    # fold the 180-ambiguity: azimuth and azimuth+180 are the same line
    return centres, hist, np.array([lam_lo_m, lam_hi_m])


def measure_striping_axis(field: np.ndarray, valid: np.ndarray, res_m: float) -> dict:
    """Decide, from the data, which axis the airborne line artefact runs along.

    Flight-line striping is *constant along* the flight lines, so the field it
    produces carries spectral energy only in the direction *perpendicular* to the
    lines.  We compare the fraction of band-passed power whose wavevector lies
    within +-7.5 deg of north (=> structure elongated east-west => east-west
    flight lines) with the fraction within +-7.5 deg of east.
    """
    filled = fill_nan_nearest(field, valid)
    centres, energy, _ = power_spectrum_azimuth_energy(filled, 1000.0, 20000.0, res_m)
    ew = energy[(centres >= 82.5) & (centres <= 97.5)].sum()  # k along E-W -> lines run N-S
    ns = energy[(centres <= 7.5) | (centres >= 172.5)].sum()  # k along N-S -> lines run E-W
    tot = energy.sum()
    # profile variance test: striping makes the along-track profile the dominant
    # signal, so the cross-track profile explains most of the variance.
    row_prof = np.nanmean(np.where(valid, filled, np.nan), axis=1)  # mean along x (E-W)
    col_prof = np.nanmean(np.where(valid, filled, np.nan), axis=0)  # mean along y (N-S)
    vr = np.nanvar(row_prof)
    vc = np.nanvar(col_prof)
    along_axis = 1 if ns >= ew else 0  # axis along the flight lines
    return {
        "spectral_power_k_east_west": float(ew / tot),
        "spectral_power_k_north_south": float(ns / tot),
        "variance_of_east_west_mean_profile": float(vr),
        "variance_of_north_south_mean_profile": float(vc),
        "profile_variance_ratio_ns_over_ew": float(vc / max(vr, 1e-30)),
        "flight_line_axis_numpy": int(along_axis),
        "flight_line_direction": "east-west" if along_axis == 1 else "north-south",
        "spectral_azimuth_deg": centres.tolist(),
        "spectral_energy": energy.tolist(),
    }
