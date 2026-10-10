"""The tensor-dimensionality lane.

Pipeline
--------
1. Read the official RTP-magnetic (band 2) and isostatic-gravity (band 13) grids.
2. NaN-fill and subtract the configured along-axis profile, then band-pass to the
   structural wavelength band. The later robust normalization uses fixed-size
   pixels; these are not verified acquisition-block polygons.
3. Form the FFT gradient tensor (horizontal + vertical derivatives) of each grid.
   For the magnetic grid this is a direct-RTP tensor proxy only. No pseudogravity
   transform for a known magnetization direction is established by this code.
4. Per pixel: eigenvalues -> dimensionality index; intermediate eigenvector -> strike.
5. Gradient ridges from the horizontal-gradient magnitude; the ridge's own
   orientation comes from the gradient azimuth rotated by 90 degrees.
6. Keep ridges that are near-2-D *and* whose eigenvector strike agrees with the
   ridge's own orientation; down-weight compact 3-D signatures; mask the
   survey-line (striping) direction measured from the data.
"""

from __future__ import annotations

from dataclasses import dataclass, field as dc_field, replace

import numpy as np
from scipy import ndimage

__all__ = ["TensorLane", "LaneConfig", "build_lane", "build_multiscale_lane"]

from . import fields55, tensor55


@dataclass
class LaneConfig:
    res_m: float = 100.0
    lowpass_m: float = 400.0       # Gaussian sigma, pre-differentiation
    highpass_m: float = 6000.0     # remove the regional trend
    block_px: int = 64             # fixed normalization tile; not an official block polygon
    striping_lag_px: int = 60      # long-lag coherence lag (6 km)
    striping_thresh: float = 0.55  # coherence above this = survey artefact
    striping_tol_deg: float = 20.0
    strike_sigma_deg: float = 25.0
    dim_power: float = 1.0
    dim_variant: str = "invariant"  # 'invariant' | 'eigratio'
    combine: str = "corroborated"   # 'corroborated' | 'max' | 'mag' | 'grav'
    erode_px: int = 6              # drop this many pixels off the footprint edge
    pad_frac: float = 0.10         # mirror-pad fraction for the FFT derivatives
    eig_chunk: int = 400_000       # pixels per closed-form eigen-decomposition chunk


def _robust_block_norm(x: np.ndarray, valid: np.ndarray, block: int) -> np.ndarray:
    """Per fixed-size pixel-tile robust z-score; tiles are not acquisition polygons."""
    ny, nx = x.shape
    out = np.zeros_like(x)
    for y0 in range(0, ny, block):
        for x0 in range(0, nx, block):
            sl = (slice(y0, min(y0 + block, ny)), slice(x0, min(x0 + block, nx)))
            v = valid[sl]
            if v.sum() < 25:
                continue
            vals = x[sl][v]
            med = np.median(vals)
            mad = np.median(np.abs(vals - med)) * 1.4826
            out[sl] = np.where(v, (x[sl] - med) / max(mad, 1e-12), 0.0)
    return out


def _rank01(x: np.ndarray, valid: np.ndarray) -> np.ndarray:
    """Percentile-rank the valid pixels into [0, 1]."""
    out = np.zeros_like(x, dtype=np.float64)
    idx = np.nonzero(valid.ravel())[0]
    vals = x.ravel()[idx]
    order = np.argsort(vals, kind="stable")
    ranks = np.empty_like(order, dtype=np.float64)
    ranks[order] = np.arange(vals.size, dtype=np.float64)
    ranks /= max(vals.size - 1, 1)
    out.ravel()[idx] = ranks
    return out


@dataclass
class TensorLane:
    cfg: LaneConfig
    footprint: np.ndarray
    # per-field products
    ridge: np.ndarray                 # corroborated ridge rank in [0,1]
    dim: np.ndarray                   # dimensionality index in [0,1]
    strike_agree: np.ndarray          # weight in [0,1]
    plunge_w: np.ndarray
    striping_mask: np.ndarray         # bool, True = survey-line artefact
    strike: np.ndarray                # tensor strike azimuth, deg
    ridge_az: np.ndarray              # ridge tangent azimuth, deg
    score: np.ndarray                 # final continuous surface in [0,1]
    products: dict = dc_field(default_factory=dict)


def _field_products(raw: np.ndarray, valid: np.ndarray, cfg: LaneConfig, along_axis: int) -> dict:
    """All per-field products, computed and then pruned to what downstream needs."""
    import gc

    bp, _ = fields55.prepare_field(
        raw, valid, cfg.res_m, along_axis=along_axis,
        lowpass_m=cfg.lowpass_m, highpass_m=cfg.highpass_m,
    )
    T = tensor55.gradient_tensor(
        bp, cfg.res_m, lowpass_m=None, highpass_m=None,
        taper_pad_frac=cfg.pad_frac,
        components=("Txx", "Tyy", "Txy", "Tzz", "Txz", "Tyz", "gx", "gy"),
    )
    hg = np.hypot(T["gx"], T["gy"]).astype(np.float32)
    ridge_az = ((np.degrees(np.arctan2(T["gx"], T["gy"])) + 90.0) % 180.0).astype(np.float32)
    del T["gx"], T["gy"]
    lam, e2 = tensor55.sym3_eigh(T, chunk=cfg.eig_chunk)
    del T
    gc.collect()
    shape = hg.shape
    dim_inv = tensor55.dimensionality_invariant(lam).reshape(shape)
    dim_eig = tensor55.dimensionality_eigratio(lam).reshape(shape)
    del lam
    strike = tensor55.strike_eigenvector(e2).reshape(shape)
    plunge = tensor55.strike_plunge_weight(e2).reshape(shape)
    del e2
    gc.collect()
    return {
        "bp": bp.astype(np.float32),
        "hg": hg,
        "dim_inv": dim_inv.astype(np.float32),
        "dim_eig": dim_eig.astype(np.float32),
        "strike": strike.astype(np.float32),
        "plunge": plunge.astype(np.float32),
        "ridge_az": ridge_az,
    }


def _long_lag_coherence_map(bp: np.ndarray, valid: np.ndarray, lag: int, axis: int) -> np.ndarray:
    """Local Pearson coherence of the band-passed field at lag ``lag`` along ``axis``.

    Computed in a sliding 31-px window via box-filtered moments so it is a map,
    not a single number.  float32 throughout: this is called four times and the
    grid has 12.28 M cells, so float64 temporaries would not fit in memory.
    """
    a = fields55.fill_nan_nearest(bp, valid).astype(np.float32)
    if axis == 1:
        b = np.roll(a, -lag, axis=1)
        b[:, -lag:] = a[:, -lag:]
    else:
        b = np.roll(a, -lag, axis=0)
        b[-lag:, :] = a[-lag:, :]
    w = 31
    sx = ndimage.uniform_filter(a, w).astype(np.float32)
    sy = ndimage.uniform_filter(b, w).astype(np.float32)
    sxx = ndimage.uniform_filter(a * a, w).astype(np.float32)
    syy = ndimage.uniform_filter(b * b, w).astype(np.float32)
    sxy = ndimage.uniform_filter(a * b, w).astype(np.float32)
    del a, b
    cov = sxy - sx * sy
    vx = np.maximum(sxx - sx * sx, 1e-12)
    vy = np.maximum(syy - sy * sy, 1e-12)
    del sxx, syy, sxy
    c = cov / np.sqrt(vx * vy, dtype=np.float32)
    del cov, vx, vy, sx, sy
    return np.clip(np.nan_to_num(c, nan=0.0), -1.0, 1.0).astype(np.float32)


def _score_products(
    Pm: dict[str, np.ndarray],
    Pg: dict[str, np.ndarray],
    valid: np.ndarray,
    footprint: np.ndarray,
    cfg: LaneConfig,
) -> dict[str, np.ndarray]:
    """Turn two field-product dictionaries into one lane score.

    This helper is shared by the one-scale and multi-scale builders.  Keeping the
    ridge, dimensionality, strike, plunge, and stripe equations in one place is
    important: a scale-persistence experiment must change only the preregistered
    scale aggregation, not silently create a second scoring implementation.
    """
    rm = _rank01(np.clip(_robust_block_norm(Pm["hg"], valid, cfg.block_px), 0, None), valid)
    rg = _rank01(np.clip(_robust_block_norm(Pg["hg"], valid, cfg.block_px), 0, None), valid)
    if cfg.combine == "corroborated":
        ridge = np.sqrt(np.clip(rm, 0, 1) * np.clip(rg, 0, 1))
    elif cfg.combine == "max":
        ridge = np.maximum(rm, rg)
    elif cfg.combine == "mag":
        ridge = rm
    elif cfg.combine == "grav":
        ridge = rg
    else:
        raise ValueError(cfg.combine)

    key = "dim_inv" if cfg.dim_variant == "invariant" else "dim_eig"
    dim = 0.5 * (Pm[key] + Pg[key])
    dth_m = tensor55.angular_difference_deg(Pm["strike"], Pm["ridge_az"])
    dth_g = tensor55.angular_difference_deg(Pg["strike"], Pg["ridge_az"])
    dth = 0.5 * (dth_m + dth_g)
    agree = np.exp(-((dth / cfg.strike_sigma_deg) ** 2))
    plunge = 0.5 * (Pm["plunge"] + Pg["plunge"])

    coh_m_x = _long_lag_coherence_map(Pm["bp"], valid, cfg.striping_lag_px, 1)
    coh_m_y = _long_lag_coherence_map(Pm["bp"], valid, cfg.striping_lag_px, 0)
    coh_g_x = _long_lag_coherence_map(Pg["bp"], valid, cfg.striping_lag_px, 1)
    coh_g_y = _long_lag_coherence_map(Pg["bp"], valid, cfg.striping_lag_px, 0)
    coh_x = np.maximum(coh_m_x, coh_g_x)
    coh_y = np.maximum(coh_m_y, coh_g_y)
    strike_mean = np.where(agree > 0.5, Pm["strike"], Pg["strike"])
    ew_like = tensor55.angular_difference_deg(strike_mean, np.full_like(strike_mean, 90.0)) < cfg.striping_tol_deg
    ns_like = tensor55.angular_difference_deg(strike_mean, np.zeros_like(strike_mean)) < cfg.striping_tol_deg
    striping = ((coh_x > cfg.striping_thresh) & ew_like) | ((coh_y > cfg.striping_thresh) & ns_like)

    w2d = np.clip(1.0 - dim, 0.0, 1.0) ** cfg.dim_power
    score = ridge * w2d * agree * plunge
    score = np.where(striping, 0.0, score)
    if cfg.erode_px > 0:
        fp_er = ndimage.binary_erosion(footprint, iterations=cfg.erode_px)
        score = np.where(fp_er, score, 0.0)
    score = np.where(valid, np.clip(score, 0.0, 1.0), 0.0).astype(np.float32)
    return {
        "ridge": ridge.astype(np.float32),
        "dim": dim.astype(np.float32),
        "agree": agree.astype(np.float32),
        "plunge": plunge.astype(np.float32),
        "striping": striping,
        "score": score,
        "strike": strike_mean.astype(np.float32),
        "ridge_az": (0.5 * (Pm["ridge_az"] + Pg["ridge_az"])).astype(np.float32),
        "ridge_mag": rm.astype(np.float32),
        "ridge_grav": rg.astype(np.float32),
        "dim_inv": (0.5 * (Pm["dim_inv"] + Pg["dim_inv"])).astype(np.float32),
        "dim_eig": (0.5 * (Pm["dim_eig"] + Pg["dim_eig"])).astype(np.float32),
        "dtheta": dth.astype(np.float32),
        "coh_x": coh_x.astype(np.float32),
        "coh_y": coh_y.astype(np.float32),
    }


def build_lane(
    rtp: np.ndarray,
    rtp_valid: np.ndarray,
    grav: np.ndarray,
    grav_valid: np.ndarray,
    footprint: np.ndarray,
    cfg: LaneConfig | None = None,
    along_axis: int = 0,
) -> TensorLane:
    cfg = cfg or LaneConfig()
    valid = footprint & rtp_valid & grav_valid

    Pm = _field_products(rtp, valid, cfg, along_axis)
    Pg = _field_products(grav, valid, cfg, along_axis)

    products = _score_products(Pm, Pg, valid, footprint, cfg)
    return TensorLane(
        cfg=cfg,
        footprint=footprint,
        ridge=products["ridge"],
        dim=products["dim"],
        strike_agree=products["agree"],
        plunge_w=products["plunge"],
        striping_mask=products["striping"],
        strike=products["strike"],
        ridge_az=products["ridge_az"],
        score=products["score"],
        products={k: products[k] for k in (
            "ridge_mag", "ridge_grav", "dim_inv", "dim_eig", "dtheta", "coh_x", "coh_y"
        )},
    )


def build_multiscale_lane(
    rtp: np.ndarray,
    rtp_valid: np.ndarray,
    grav: np.ndarray,
    grav_valid: np.ndarray,
    footprint: np.ndarray,
    cfg: LaneConfig | None = None,
    along_axis: int = 0,
    scales_m: tuple[float, ...] = (300.0, 900.0),
) -> TensorLane:
    """Build a preregistered scale-persistent tensor surface.

    Each scale runs the exact same field preparation and tensor score.  The final
    surface is the geometric mean of the scale scores, so a response that exists
    at only one scale is down-weighted.  Dimensionality, agreement, ridge rank,
    and plunge are aggregated with the same rule; the striping mask is the union
    of the scale masks.  No label-derived quantity enters this operation.
    """
    import gc

    cfg = cfg or LaneConfig()
    scales = tuple(float(s) for s in scales_m)
    if len(scales) < 2 or any(s <= 0 for s in scales):
        raise ValueError("scales_m must contain at least two positive scales")
    valid = footprint & rtp_valid & grav_valid
    acc: dict[str, np.ndarray] | None = None
    for scale in scales:
        scfg = replace(cfg, lowpass_m=scale)
        Pm = _field_products(rtp, valid, scfg, along_axis)
        Pg = _field_products(grav, valid, scfg, along_axis)
        cur = _score_products(Pm, Pg, valid, footprint, scfg)
        if acc is None:
            acc = {k: v.copy() if isinstance(v, np.ndarray) else v for k, v in cur.items()}
        else:
            # Geometric means implement persistence for nonnegative scores and
            # weights; arithmetic means preserve interpretable angles/indices.
            for key in ("score", "ridge", "agree"):
                acc[key] = np.sqrt(np.maximum(acc[key], 0.0) * np.maximum(cur[key], 0.0)).astype(np.float32)
            for key in ("dim", "plunge", "ridge_mag", "ridge_grav", "dim_inv", "dim_eig", "dtheta", "coh_x", "coh_y"):
                acc[key] = (0.5 * (acc[key] + cur[key])).astype(np.float32)
            acc["striping"] = np.asarray(acc["striping"], dtype=bool) | np.asarray(cur["striping"], dtype=bool)
            # Undirected azimuths are only used for diagnostics downstream; the
            # score itself uses the scale-specific angular difference above.
            acc["strike"] = np.where(acc["agree"] >= cur["agree"], acc["strike"], cur["strike"])
            acc["ridge_az"] = np.where(acc["agree"] >= cur["agree"], acc["ridge_az"], cur["ridge_az"])
        del Pm, Pg, cur
        gc.collect()
    assert acc is not None
    return TensorLane(
        cfg=replace(cfg, lowpass_m=float(scales[0])),
        footprint=footprint,
        ridge=acc["ridge"],
        dim=acc["dim"],
        strike_agree=acc["agree"],
        plunge_w=acc["plunge"],
        striping_mask=acc["striping"],
        strike=acc["strike"],
        ridge_az=acc["ridge_az"],
        score=np.where(valid, np.clip(acc["score"], 0.0, 1.0), 0.0).astype(np.float32),
        products={k: acc[k] for k in (
            "ridge_mag", "ridge_grav", "dim_inv", "dim_eig", "dtheta", "coh_x", "coh_y"
        )},
    )
