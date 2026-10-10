"""Synthetic tests for the single in-repo tensor implementation."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gems55 import holdout55, tensor55  # noqa: E402


def test_dimensionality_endpoints_and_null_vector_strike():
    lam = np.array([[1.0, 0.0, -1.0], [2.0, -1.0, -1.0]], dtype=np.float32)
    index = tensor55.dimensionality_invariant(lam)
    assert index == pytest.approx([0.0, 1.0], abs=1e-12)

    # Axes are east, north, down; strike is axial and measured clockwise from north.
    vectors = np.array([[0.0, 1.0, 0.0], [1.0, 0.0, 0.0], [0.0, -1.0, 0.0]])
    azimuth = tensor55.strike_eigenvector(vectors)
    assert azimuth == pytest.approx([0.0, 90.0, 0.0], abs=1e-6)
    assert tensor55.strike_plunge_weight(vectors) == pytest.approx([1.0, 1.0, 1.0])


def test_auc_helper_has_correct_ordering_and_tie_behavior():
    assert holdout55.auc(np.array([3.0, 4.0, 1.0, 2.0]), np.array([1, 1, 0, 0])) == pytest.approx(1.0)
    assert holdout55.auc(np.array([1.0, 2.0, 3.0, 4.0]), np.array([1, 1, 0, 0])) == pytest.approx(0.0)
    assert holdout55.auc(np.array([1.0, 1.0]), np.array([1, 0])) == pytest.approx(0.5)
