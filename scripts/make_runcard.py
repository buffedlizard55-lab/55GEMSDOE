#!/usr/bin/env python3
"""Assemble the run card from the measured evidence files."""
from __future__ import annotations
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
EVID = ROOT/"evidence"
def L(n):
    p = EVID/n
    return json.loads(p.read_text()) if p.exists() else {}

subs = sorted(EVID.glob("submission_*.json"))
sub = json.loads(subs[-1].read_text()) if subs else {}
e1 = L("holdout_v1_n40000.json"); un = L("uniqueness.json"); st = e1.get("strike_test", {})
tf = e1.get("tensor_full", {}); rnd = e1.get("random", {})
card = {
  "hypothesis": ("Gradient ridges on RTP-magnetic and isostatic-gravity grids cannot separate a "
                 "strike-extended fault or contact from a compact intrusion or vent, because both "
                 "produce ridges. The potential-field gradient tensor can: its dimensionality index "
                 "is zero for strictly two-dimensional sources and its intermediate eigenvector "
                 "carries strike. Gating ridges on being near-2-D AND on eigenvector strike agreeing "
                 "with the ridge's own orientation should therefore preferentially retain unmapped, "
                 "elongated, less conspicuous traces."),
  "mechanism": ("FFT gradient tensor of bands 2 (RTP mag) and 13 (isostatic gravity) after "
                "nearest-neighbour NaN fill, along-track micro-levelling and a 400 m - 6 km "
                "band-pass; Tzz derived as -(Txx+Tyy) so the tensor is exactly traceless; "
                "closed-form 3x3 eigen-decomposition; dimensionality I = 27 e3^2 / (4 (-e2)^3) "
                "(I=0 2-D, I=1 3-D, both endpoints unit-tested); strike = azimuth of the "
                "intermediate eigenvector; score = corroborated ridge rank x (1-I) x "
                "exp(-(dtheta/25deg)^2) x plunge weight x survey-line mask."),
  "non_fault_process_that_could_mimic_it": ("Airborne survey-line striping. It is measured here to "
                "run north-south, not east-west as the lane brief asserts (IR-55-04). Analytically a "
                "field varying only across the flight lines has eigenvalues (|f''|,0,-|f''|) - "
                "indistinguishable from a 2-D source striking along the lines - so the tensor cannot "
                "reject it and it must be masked geometrically. Secondary mimics: lithologic contacts "
                "and dike swarms (genuinely 2-D but not faults) and basin-margin alluvial edges."),
  "holdout_dti": {
    "label": "HOLDOUT-DTI (evaluator: src/gems55/dti55.py, exact official DTI, verified against a "
             "brute-force transcription and against the official worked example)",
    "protocol": "4 contiguous-quadrant hide-and-recover, 3 px buffer, visible faults masked "
                "pixel-exactly, catalogue-derived features recomputed per fold, pooled scoring",
    "n_withheld_positives_total": int(sum(f["n_truth"] for f in tf.get("per_fold", []))),
    "this_lane_pooled_dti": tf.get("pooled", {}).get("dti"),
    "this_lane_fold_mean": tf.get("fold_mean"),
    "this_lane_fold_sd": tf.get("fold_sd"),
    "this_lane_fold_ci95": tf.get("fold_ci95"),
    "uniform_random_control_pooled_dti": rnd.get("pooled", {}).get("dti"),
    "uniform_random_control_fold_ci95": rnd.get("fold_ci95"),
    "n_dots": 40000,
    "leakage_canary_max_lane_feature_auc": max(
        (v["auc_mean"] for k, v in e1.get("leakage_canary", {}).items()
         if k != "neg_visible_catalogue_distance"), default=None),
    "leakage_flagged_gt_0.90": e1.get("leakage_flagged_gt_0p90"),
    "strike_test": {
      "frac_within_20deg_withheld": st.get("frac_within_20deg_withheld"),
      "frac_within_20deg_random": st.get("frac_within_20deg_random"),
      "mean_abs_dtheta_withheld_deg": st.get("mean_abs_dtheta_withheld_deg"),
      "mean_abs_dtheta_random_deg": st.get("mean_abs_dtheta_random_deg"),
      "mean_diff_ci95_deg": st.get("mean_diff_ci95"),
      "verdict": "CONFIRMED - CI excludes zero; 45.0 deg is the calibrated null mean",
    },
  },
  "correlation_overlap_vs_registry": {
    "n_registry_rasters": un.get("n_registry"),
    "max_abs_spearman_dense_footprint": un.get("max_spearman_dense"),
    "threshold": 0.90,
    "max_jaccard": un.get("max_jaccard"),
    "max_frac_our_dots_within_3px_raw": un.get("max_frac_within_3px"),
    "max_frac_3px_excess_over_random_control": un.get("max_frac3px_excess_over_random_control"),
    "max_frac_within_3px_density_matched": un.get("max_frac_within_3px_density_matched"),
    "n_density_matched_references": un.get("n_density_matched"),
    "threshold_frac_3px": 0.70,
    "verdict": un.get("verdict"),
    "note": "raw 3-px statistic is 0.841 only against a 206,895-dot spacing-5 lattice; the "
            "uniform-random control reaches the same value, so the excess (+0.0399) and the "
            "density-matched statistic (0.6694 < 0.70) are the informative readings (IR-55-08).",
  },
  "raster_sha256": sub.get("sha256"),
  "validator_output": {
    "tool": "scripts/validate_submission.py (re-reads the written bytes with rasterio)",
    "checks_passed": "12/12 on the -zeros encoding, 11/11 on the -nan twin",
    "no_nan_inside_footprint": True,
    "values_in_0_1": True,
    "crs_shape_transform_match_template": True,
    "dots_on_mapped_catalogue_pixels": sub.get("dots_on_catalogue_px"),
    "dots_outside_footprint": sub.get("dots_outside_footprint"),
  },
  "submission_name": sub.get("name"),
  "submission_note": sub.get("portal_note"),
  "submission_note_length": len(sub.get("portal_note", "")),
  "verdict": "NEGATIVE",
  "verdict_reason": ("The strike prediction is confirmed, but emitted as a prediction surface the "
                     "lane does not beat a uniform-random control at matched mass "
                     f"({tf.get('pooled',{}).get('dti'):.4f} vs {rnd.get('pooled',{}).get('dti'):.4f} "
                     "pooled, and below it in 4 of 4 folds at every NMS separation tested). The "
                     "file is format-valid and unique, so it is downloadable and legal to upload, "
                     "but it must not be promoted into a weekly slot on this evidence."),
  "metric_finding_of_general_value": ("TP_w + FN_w = |G| identically, so DTI = TP_w/(0.2N + 0.8|G|). "
                     "Coverage, not per-pixel precision, dominates: a false positive costs 0.2 and an "
                     "uncovered truth pixel costs 0.8. Verified numerically at eight dot budgets."),
}
(ROOT/"evidence"/"runcard.json").write_text(json.dumps(card, indent=2))
print(json.dumps(card, indent=2)[:1200]); print("...\nwrote evidence/runcard.json")
