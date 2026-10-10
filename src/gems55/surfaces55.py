"""Shared tensor-lane surface composition for evaluator, writer, and preflight checks.

Keeping the edge sensitivity, stripe mask, flank prior, footprint and catalogue
exclusion in one function prevents holdout and final-writer surfaces from quietly
drifting apart.
"""
from __future__ import annotations

import numpy as np

from . import holdout55


def tensor_surface(
    *,
    cached_score: np.ndarray,
    ridge: np.ndarray,
    dimensionality: np.ndarray,
    strike_agreement: np.ndarray,
    plunge_weight: np.ndarray,
    striping: np.ndarray,
    footprint: np.ndarray,
    catalogue: np.ndarray | None = None,
    flank_support_px: float = 0.0,
    un_eroded: bool = False,
) -> np.ndarray:
    """Compose the submission surface from cached tensor products.

    ``un_eroded=True`` removes only the builder's 6-pixel footprint erosion and
    recomputes the same tensor formula from its cached factors.  It is an
    edge-artifact sensitivity option, not the default scientific surface.
    Striping is hard-masked (as required by the lane prompt); mapped catalogue
    pixels and outside-footprint pixels are never eligible.  The flank prior, if
    requested, is computed from the catalogue array passed by the caller (visible
    faults only during holdout, all currently known faults during final inference).
    """
    arrays = [cached_score, ridge, dimensionality, strike_agreement, plunge_weight,
              striping, footprint]
    shape = np.asarray(footprint).shape
    if any(np.asarray(a).shape != shape for a in arrays):
        raise ValueError("all cached products and masks must share the footprint shape")
    if catalogue is not None and np.asarray(catalogue).shape != shape:
        raise ValueError("catalogue mask must match footprint shape")
    if flank_support_px < 0:
        raise ValueError("flank_support_px must be nonnegative")

    if un_eroded:
        surface = (
            np.asarray(ridge, dtype=np.float32)
            * (1.0 - np.asarray(dimensionality, dtype=np.float32))
            * np.asarray(strike_agreement, dtype=np.float32)
            * np.asarray(plunge_weight, dtype=np.float32)
        )
    else:
        surface = np.asarray(cached_score, dtype=np.float32).copy()
    surface = np.nan_to_num(surface, nan=0.0, posinf=0.0, neginf=0.0)
    valid = np.asarray(footprint, dtype=bool)
    cat = np.zeros(shape, dtype=bool) if catalogue is None else np.asarray(catalogue, dtype=bool)
    surface[~valid] = 0.0
    surface[np.asarray(striping, dtype=bool)] = 0.0
    if flank_support_px > 0:
        if catalogue is None:
            raise ValueError("flank prior requires a visible/final catalogue mask")
        surface *= holdout55.flank_weight(cat, flank_support_px)
    surface[cat] = 0.0
    return np.clip(surface, 0.0, 1.0).astype(np.float32)
