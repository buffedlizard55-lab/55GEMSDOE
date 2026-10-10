"""Exact DTI regression checks for the single canonical local evaluator."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gems55 import dti55  # noqa: E402


def test_official_worked_example_arithmetic():
    assert dti55.dti_from_totals(3.00, 1.89, 2.00) == pytest.approx(0.60, abs=0.005)


def test_perfect_prediction_scores_one():
    gt = np.zeros((20, 20), bool)
    gt[10, 2:18] = True
    result = dti55.dti(gt.astype(float), gt)
    assert result.dti == pytest.approx(1.0, abs=1e-12)


def test_one_pixel_offset_hand_computed():
    # One-pixel offset: k=2/3; FP complement is 1/3.
    gt = np.zeros((11, 11), bool)
    gt[5, 5] = True
    pred = np.zeros((11, 11))
    pred[5, 6] = 1.0
    result = dti55.dti(pred, gt)
    assert result.tp_w == pytest.approx(2 / 3)
    assert result.fn_w == pytest.approx(1 / 3)
    assert result.fp_w == pytest.approx(1 / 3)
    assert result.dti == pytest.approx((2 / 3) / (2 / 3 + 0.2 / 3 + 0.8 / 3))


def test_beyond_300m_gets_no_credit():
    gt = np.zeros((11, 11), bool)
    gt[5, 5] = True
    pred = np.zeros((11, 11))
    pred[5, 8] = 1.0
    result = dti55.dti(pred, gt)
    assert result.tp_w == 0.0
    assert result.fn_w == pytest.approx(1.0)
    assert result.fp_w == pytest.approx(1.0)
    assert result.dti == pytest.approx(0.0)


def test_nonzero_kernel_offsets_have_strictly_positive_credit():
    positive = [(dy, dx, w) for dy, dx, w in dti55.kernel_offsets() if w > 0.0]
    assert max(abs(dy) for dy, _, _ in positive) == 2
    assert max(abs(dx) for _, dx, _ in positive) == 2
