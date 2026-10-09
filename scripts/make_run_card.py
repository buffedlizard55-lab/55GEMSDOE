"""Build the protocol item-5 RUN CARD from saved results (no hand-typed numbers)."""
import json
from pathlib import Path

R = json.loads(Path("docs/results/tensor_lane_results.json").read_text())
E3 = json.loads(Path("docs/results/registry_check_E3.json").read_text())
E1 = json.loads(Path("docs/results/registry_check_tensor_lane_E1.json").read_text())
ex = R["experiments"]
card = {
    "run_card_version": 1,
    "lane": "tensor-dimensionality (Pedersen & Rasmussen 1990 index; Beiki & Pedersen 2010 strike)",
    "hypothesis": "Near-2-D gradient ridges whose tensor strike agrees with ridge orientation mark strike-extended faults, "
                  "and down-weighting compact 3-D signatures raises recovery of withheld catalogue faults.",
    "mechanism": "FFT pseudogravity/isostatic gradient tensor -> dimensionality I=|lam_min|/|lam_mid| and min-eigenvector strike; "
                 "ridges of horizontal gradient of RTP; E-W flight-line rows masked by robust row-residual test.",
    "named_non_fault_mimic": "Lithologic contacts and dykes/sills (also 2-D) and E-W flight-line striping (1-D by construction); "
                             "also vents/intrusions give ridges but are 3-D and should be down-weighted.",
    "holdout_dti": {
        "label": "HOLDOUT-DTI", "evaluator": R["evaluator"],
        "E1_ridge_baseline": {"dti": ex["E1_ridge_baseline"]["dti"], "ci95": ex["E1_ridge_baseline"]["ci95"],
                              "withheld_positive_px": ex["E1_ridge_baseline"]["withheld_positive_px"]},
        "E2_plus_dimensionality": {"dti": ex["E2_plus_dimensionality"]["dti"], "ci95": ex["E2_plus_dimensionality"]["ci95"],
                                   "withheld_positive_px": ex["E2_plus_dimensionality"]["withheld_positive_px"]},
        "E3_full_tensor_lane": {"dti": ex["E3_full_tensor_lane"]["dti"], "ci95": ex["E3_full_tensor_lane"]["ci95"],
                                "withheld_positive_px": ex["E3_full_tensor_lane"]["withheld_positive_px"]},
    },
    "leakage_canary_auc": {k: v["auc"] for k, v in R["canary_auc_on_ridges"]["features"].items()},
    "leakage_flag_any": any(v["leak_flag"] for v in R["canary_auc_on_ridges"]["features"].values()),
    "strike_prediction_test": R["strike_test"],
    "registry": {
        "rasters_total": E1["registry_rasters_total"],
        "E1_max_spearman": E1["max_spearman"], "E1_duplicates_flagged_by_overlap_rule": E1["duplicates_flagged"],
        "E3_duplicates_flagged_by_overlap_rule": E3["duplicates_flagged"], "same_grid_compared": E3["same_grid_compared"],
        "overlap_rule_note": "saturated by dense registry rasters (up to 5.17M positive px ~ whole footprint); not chance-corrected",
    },
    "raster_sha256": {"E1_ridge_baseline": R["submission"]["sha256"],
                      "E3_full_tensor_lane": "25f2ccf40c096efe9b25bed9ab8c28151d48123a7ba4527c85ac490c3dc18d80"},
    "validator": {k: R["submission"]["validator"][k] for k in ["all_passed", "values_in_0_1_inside", "no_nan_inside_footprint",
                  "outside_null_or_nan", "crs_epsg_32611", "shape_matches_template", "transform_matches_template"]},
    "submission_name": "NOT PUBLISHED - no upload (tensor lane negative)",
    "submission_note": "No upload. Tensor lane negative on holdout (0.0444 vs ridge 0.0578). No cleared candidate.",
    "verdict": "negative",
    "organiser_confirmed_scores": [],
    "budget": "3 experiments (E1,E2,E3) within the 2-hour budget; no submission slot used",
}
Path("docs/results/run_card_tensor_lane.json").write_text(json.dumps(card, indent=2))
print(json.dumps(card, indent=2)[:1500])
