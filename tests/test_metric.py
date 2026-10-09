import numpy as np
from gems import metric


def test_official_worked_example_arithmetic():
    # Numbers from the official scoring example (DrivenData problem description)
    assert abs(metric.dti_from_totals(3.00, 1.89, 2.00) - 0.60) < 0.005


def test_perfect_prediction_scores_one():
    gt = np.zeros((20, 20), bool); gt[10, 2:18] = True
    p = gt.astype(float)
    assert metric.dti(p, gt) > 0.999


def test_one_pixel_offset_hand_computed():
    # gt single pixel at (5,5); prediction 1 at (5,6): distance 100 m -> k = 2/3
    gt = np.zeros((11, 11), bool); gt[5, 5] = True
    p = np.zeros((11, 11)); p[5, 6] = 1.0
    c = metric.components(p, gt)
    assert abs(c["TP"] - 2 / 3) < 1e-9
    assert abs(c["FN"] - 1 / 3) < 1e-9
    assert abs(c["FP"] - 1 / 3) < 1e-9
    assert abs(metric.dti(p, gt) - (2 / 3) / (2 / 3 + 0.2 / 3 + 0.8 / 3)) < 1e-9


def test_beyond_300m_gets_no_credit():
    gt = np.zeros((11, 11), bool); gt[5, 5] = True
    p = np.zeros((11, 11)); p[5, 8] = 1.0          # 300 m away -> k = 0
    c = metric.components(p, gt)
    assert c["TP"] == 0 and abs(c["FN"] - 1) < 1e-9 and abs(c["FP"] - 1) < 1e-9


def test_kernel_support_is_three_pixels():
    offs = metric.kernel_offsets()
    assert max(abs(dy) for dy, _, _ in offs) == 2 and max(abs(dx) for _, dx, _ in offs) == 2
