#!/usr/bin/env python3
"""Create the final H57 run card and fail-closed site status from measured evidence.

No score is typed by hand.  HOLDOUT-DTI comes from the canonical evaluator JSON;
format checks are re-run against both written TIFFs; SHA-256 is recomputed from
bytes; surface and dot uniqueness are read from the strict current-registry plus local
historical-raster check. A format-valid audit raster is not cleared to submit if
uniqueness fails or the holdout is negative.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import validate_submission as vs  # noqa: E402

DOCS = ROOT / "docs"
EVID = ROOT / "evidence"
HOLD_NAME = "holdout_h57_unique_n200.json"
EVALUATOR = "src/gems55/dti55.py (local published-formula transcription, gems55.dti55/2.0-local; alpha=0.2, beta=0.8, R=300 m; not organizer-executable)"


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    hold = load(EVID / HOLD_NAME)
    uniq = load(EVID / "uniqueness_h57_final.json")
    pre = load(EVID / "uniqueness_h57_surface_preplacement.json")
    submission_json = sorted(EVID.glob("submission_h57-tensor-flank-*.json"))
    if len(submission_json) != 1:
        raise SystemExit(f"expected exactly one H57 sidecar, found {len(submission_json)}")
    sub = load(submission_json[0])
    name = sub["name"]
    tif = ROOT / "docs" / "downloads" / f"{name}-nan.tif"
    zeros_variant = ROOT / "docs" / "downloads" / f"{name}-zeros.tif"
    zip_path = ROOT / "docs" / "downloads" / f"{name}-nan.zip"
    zeros_zip = ROOT / "docs" / "downloads" / f"{name}-zeros.zip"
    for path in (tif, zeros_variant, zip_path, zeros_zip):
        if not path.exists():
            raise SystemExit(f"missing written artifact: {path}")

    recorded_hashes = sub.get("sha256", {})
    for artifact in (tif, zeros_variant, zip_path, zeros_zip):
        expected = recorded_hashes.get(artifact.name)
        if expected is None or sha256(artifact) != expected:
            raise SystemExit(f"artifact SHA-256 mismatch or missing sidecar hash: {artifact.name}")
    digest = sha256(tif)

    nan_ok, nan_checks = vs.validate(tif)
    nan_pass = sum(1 for _, ok, _ in nan_checks if ok)
    nan_fail = sum(1 for _, ok, _ in nan_checks if not ok)
    zeros_ok, zeros_checks = vs.validate(zeros_variant)
    zeros_pass = sum(1 for _, ok, _ in zeros_checks if ok)
    zeros_fail = sum(1 for _, ok, _ in zeros_checks if not ok)
    zero_failed_checks = [name for name, ok, _ in zeros_checks if not ok]
    if not nan_ok or nan_fail:
        raise SystemExit("the NaN-outside audit TIF failed scripts/validate_submission.py")
    if zeros_ok or zero_failed_checks != ["null/NaN exactly outside template footprint"]:
        raise SystemExit(f"unexpected zeros-variant validator result: {zero_failed_checks}")
    if zeros_fail != 1:
        raise SystemExit(f"expected the zeros diagnostic to fail exactly one strict check, got {zeros_fail}")
    with ZipFile(zip_path) as archive:
        if archive.namelist() != [tif.name]:
            raise SystemExit("NaN ZIP must contain exactly the validated NaN-outside TIF")
    with ZipFile(zeros_zip) as archive:
        if archive.namelist() != [zeros_variant.name]:
            raise SystemExit("diagnostic zeros ZIP must contain exactly its zeros-outside TIF")

    cand = hold["tensor_flank"]
    best = max(("tensor_full", hold["tensor_full"]), ("ridge_x_agree", hold["ridge_x_agree"]),
               key=lambda item: item[1]["pooled"]["dti"])
    random = hold["random"]
    n_truth = int(cand["pooled"]["n_truth"])
    candidate_folds = [float(x["dti"]) for x in cand["per_fold"]]
    best_folds = [float(x["dti"]) for x in best[1]["per_fold"]]
    folds_beating_best = sum(a > b for a, b in zip(candidate_folds, best_folds))
    mass_matched = bool(hold.get("all_arms_mass_matched")) and all(
        hold[k]["mass_matched"] for k in ("random", "ridge_x_agree", "tensor_full", "tensor_flank")
    )

    unique_ok = (
        uniq.get("strict_verdict") == "PASS-UNIQUE"
        and uniq.get("registry_rasters_total") == uniq.get("registry_rasters_scanned") == 62
        and uniq.get("registry_rasters_incompatible") == 0
        and uniq.get("local_historical_rasters_total") == uniq.get("local_historical_rasters_scanned") == 4
        and uniq.get("local_historical_rasters_incompatible") == 0
        and uniq.get("comparison_rasters_total") == uniq.get("comparison_rasters_scanned") == 66
        and pre.get("registry_rasters_total") == pre.get("registry_rasters_scanned") == 62
        and pre.get("local_historical_rasters_total") == pre.get("local_historical_rasters_scanned") == 4
        and pre.get("local_historical_rasters_incompatible") == 0
        and pre.get("comparison_rasters_total") == pre.get("comparison_rasters_scanned") == 66
        and (uniq.get("max_abs_surface_spearman") is not None)
        and uniq["max_abs_surface_spearman"] <= 0.90
        and (uniq.get("max_final_dot_overlap_within_3px") is not None)
        and uniq["max_final_dot_overlap_within_3px"] <= 0.70
        and pre.get("strict_verdict") == "PASS-SURFACE-UNIQUE"
    )
    leak = hold["leakage_canary"]
    max_auc = max(float(v["auc_mean"]) for v in leak.values())
    leakage_ok = not bool(hold.get("leakage_flagged_gt_0p90")) and max_auc <= 0.90
    holdout_positive = (
        mass_matched
        and cand["pooled"]["dti"] > best[1]["pooled"]["dti"]
        and cand["pooled"]["dti"] > random["pooled"]["dti"]
        and folds_beating_best >= 4
        and leakage_ok
    )
    verdict = "promote" if holdout_positive else "negative"
    # A weekly slot is still a separate selector step.  This card never submits.
    submit_allowed = bool(nan_ok and unique_ok and holdout_positive)
    note = sub["portal_note"]
    if len(note) > 140:
        raise SystemExit(f"portal note is over 140 chars ({len(note)})")

    reprojected = [r["raster"] for r in uniq["rows"] if r.get("reprojected_to_template")]
    card = {
        "schema": "55gemsdoe.run-card.v2",
        "run_id": "55GEMSDOE-H57-TENSOR-FLANK-2026-10-09",
        "status": "format_valid_duplicate_stop_holdout_negative_audit_only",
        "hypothesis": (
            "A potential-field gradient ridge cannot distinguish an elongated fault/contact from a compact "
            "intrusion/vent. The RTP-magnetic (band 2) and isostatic-gravity (band 13) gradient tensors encode "
            "dimensionality and a candidate strike. A near-2-D, strike-concordant ridge should preferentially "
            "retain fault-like structure. H57-A adds a 15-pixel off-catalogue flank prior built only from the "
            "VISIBLE catalogue during holdout, based on the measured adjacency pattern in the local anchor "
            "forensics. It was tested as a new-fault prediction, not assumed to be a leaderboard improvement."
        ),
        "mechanism": (
            "Use the existing one-scale cached stack (band 2 RTP magnetic + band 13 isostatic gravity); "
            "nearest-valid fill, robust line-axis leveling, low-pass before mirror-padded FFT derivatives, "
            "closed-form symmetric 3x3 tensor eigendecomposition, dimensionality invariant, intermediate "
            "eigenvector strike, strike agreement, plunge weight, corroborated ridge rank. H57 holdout and final "
            "writer use the same cached tensor factors and a 15-pixel quadratic off-catalogue flank prior; "
            "the candidate sensitivity run removes the cached 6-pixel footprint erosion (un-eroded edge score) "
            "to test whether a dense 5-pixel lattice registry raster leaves any unique feasible pixels. Flight-line "
            "striping is hard-masked. At run time the final 200 binary dots were placed with 3-pixel minimum "
            "separation and 56 registry cover masks, including one misregistered raster reprojected to the official "
            "grid, under a 0.68 cap. A later audit added six parallel-session registry variants and four local "
            "historical candidates; the current 66-raster strict scan finds 0.76 overlap with two PARALLEL16 twins, "
            "so this raster is not unique under the literal rule."
        ),
        "named_non_fault_mimic": (
            "Lithologic contacts, dikes, intrusive sheets, basin-margin alluvial edges, and acquisition/FFT edge "
            "artifacts can all produce long, near-2-D responses without being faults. Flight-line striping and "
            "tie-line/leveling residuals are additional potential mimics. The un-eroded footprint-edge sensitivity "
            "increases FFT boundary-ringing risk and is a reason this raster remains audit-only."
        ),
        "holdout_dti": {
            "status": "RUN",
            "evidence_class": "HOLDOUT-DTI",
            "evidence_file": HOLD_NAME,
            "evaluator_version": EVALUATOR,
            "parameters": {
                "alpha": 0.2, "beta": 0.8, "kernel_radius_m": 300,
                "n_dots_total": 200, "dots_per_fold": 40, "min_sep_px": 3.0,
                "flank_support_px": 15.0, "un_eroded_edge_score": True,
                "registry_rasters_budgeted_at_holdout_time": 56,
                "current_registry_rasters_in_uniqueness_audit": 62,
                "local_historical_rasters_in_uniqueness_audit": 4,
                "total_uniqueness_comparisons": 66,
                "current_max_dot_overlap": uniq["max_final_dot_overlap_within_3px"],
                "registry_max_dot_overlap_at_holdout_time": 0.68,
            },
            "withheld_positive_count": n_truth,
            "protocol": (
                "Five whole-segment/lattice hide-and-recover folds, 3-pixel buffer, per-fold visible faults "
                "masked pixel-exactly; flank prior recomputed from VISIBLE faults only; all 56 registry rasters "
                "budgeted after alignment to EPSG:32611 template; 40 dots per fold; pooled TP/FP/FN DTI; 95% CI "
                "is a 4,000-resample bootstrap of the five fold DTI values. All candidate and comparator arms "
                "returned the same requested mass. The holdout used the 56 registry rows present at run time; "
                "the later strict uniqueness audit includes 62 registry rows plus four local historical rasters. "
                "No holdout was rerun after the three-experiment budget was exhausted."
            ),
            "value": cand["pooled"]["dti"],
            "ci95": cand["fold_ci95"],
            "candidate_dots": cand["pooled"]["n_pred_pos"],
            "matched_random_control": {
                "value": random["pooled"]["dti"], "ci95": random["fold_ci95"],
                "dots": random["pooled"]["n_pred_pos"],
            },
            "current_best_comparator": {
                "name": best[0], "value": best[1]["pooled"]["dti"],
                "ci95": best[1]["fold_ci95"], "dots": best[1]["pooled"]["n_pred_pos"],
            },
            "other_arms": {
                "ridge_x_agree": {"value": hold["ridge_x_agree"]["pooled"]["dti"],
                                  "ci95": hold["ridge_x_agree"]["fold_ci95"]},
                "tensor_full": {"value": hold["tensor_full"]["pooled"]["dti"],
                                "ci95": hold["tensor_full"]["fold_ci95"]},
                "flank_only": {"value": hold["flank_only"]["pooled"]["dti"],
                               "ci95": hold["flank_only"]["fold_ci95"]},
            },
            "mass_matched": mass_matched,
            "folds_beating_best_comparator": folds_beating_best,
            "folds_beating_best_comparator_of": len(candidate_folds),
            "promotion_rule": "candidate must beat tensor_full, ridge_x_agree, and random, and beat the best surface in >=4/5 folds; all arms must be mass-matched",
            "projection_written_as_score": False,
        },
        "leakage_canary": {
            "evidence_class": "HOLDOUT-DTI diagnostic",
            "features_tested_alone": sorted(leak),
            "max_auc": max_auc,
            "auc_by_feature": {k: float(v["auc_mean"]) for k, v in leak.items()},
            "threshold": 0.90,
            "flagged": sorted(hold.get("leakage_flagged_gt_0p90", [])),
            "note": "The visible-catalogue flank AUC is 0.8933, close to (but below) 0.90; it is catalogue autocorrelation, not hidden-label leakage, and is not a DTI score.",
        },
        "strike_diagnostic": {
            "evidence_class": "HOLDOUT-DTI diagnostic",
            "withheld_connected_segments_tested": hold["strike_test"]["n_withheld_segments"],
            "withheld_pixel_samples": hold["strike_test"]["n_withheld_pixel_samples"],
            "random_ridge_pixel_samples": hold["strike_test"]["n_random_ridge_samples"],
            "withheld_match_rate_within_20deg": hold["strike_test"]["frac_within_20deg_withheld"],
            "random_ridge_match_rate_within_20deg": hold["strike_test"]["frac_within_20deg_random"],
            "mean_difference_ci95_deg": hold["strike_test"]["mean_diff_ci95"],
            "note": "Auxiliary catalogue-proxy strike diagnostic; not a performance score. Counts were corrected under IR-55-041.",
        },
        "correlation_overlap_vs_registry": {
            "evidence_class": "REGISTRY-AND-LOCAL-HISTORICAL-MEASURED",
            "registry_rasters_total": uniq["registry_rasters_total"],
            "registry_rasters_scanned": uniq["registry_rasters_scanned"],
            "registry_rasters_reprojected_to_template": uniq["registry_rasters_reprojected"],
            "reprojected_rasters": reprojected,
            "registry_rasters_incompatible": uniq["registry_rasters_incompatible"],
            "local_historical_rasters_total": uniq["local_historical_rasters_total"],
            "local_historical_rasters_scanned": uniq["local_historical_rasters_scanned"],
            "local_historical_rasters_reprojected": uniq["local_historical_rasters_reprojected"],
            "local_historical_rasters_incompatible": uniq["local_historical_rasters_incompatible"],
            "comparison_rasters_total": uniq["comparison_rasters_total"],
            "comparison_rasters_scanned": uniq["comparison_rasters_scanned"],
            "max_final_dot_overlap_within_3px_all_comparisons": uniq["max_final_dot_overlap_within_3px"],
            "degenerate_row_disclosure": "Literal >0.70 stop applies without chance adjustment. The max 0.76 overlap is against two zero/NaN variants of the same PARALLEL16 continuous raster; both rows are retained and both count toward DUPLICATE-STOP.",
            "strict_duplicate_raster_names": [r["raster"] for r in uniq["rows"] if r["strict_duplicate_flag"]],
            "max_abs_surface_spearman": uniq["max_abs_surface_spearman"],
            "max_abs_final_binary_spearman": uniq["max_abs_final_binary_spearman"],
            "max_final_dot_overlap_within_3px": uniq["max_final_dot_overlap_within_3px"],
            "threshold_surface_spearman": 0.90,
            "threshold_final_dot_overlap": 0.70,
            "strict_verdict": uniq["strict_verdict"],
            "strict_duplicate_rows": uniq["strict_duplicate_rows"],
            "lattice_overlap": next(r["final_dot_overlap_within_3px"] for r in uniq["rows"] if "lattice-s5" in r["raster"]),
            "lattice_random_control_overlap": next(r["random_control_overlap_within_3px"] for r in uniq["rows"] if "lattice-s5" in r["raster"]),
            "random_control_uses_same_euclidean_3px_metric": True,
        },
        "raster_sha256": digest,
        "validator_output": {
            "evidence_class": "FORMAT-VALIDATION",
            "status": "PASS",
            "tool": "scripts/validate_submission.py; independent rasterio re-read",
            "checks_passed": nan_pass,
            "checks_failed": nan_fail,
            "primary_encoding": "NaN exactly outside the template footprint",
            "zeros_variant_checks_passed": zeros_pass,
            "zeros_variant_checks_failed": zeros_fail,
            "zeros_variant_fails_null_nan_outside_rule": not zeros_ok,
            "no_nan_inside_footprint": True,
            "values_in_0_1_inside_footprint": True,
            "single_band_float32": True,
            "crs_matches": True,
            "shape_matches": True,
            "transform_matches": True,
            "nan_outside_footprint": True,
            "positive_pixels": sub["n_dots"],
            "dots_on_mapped_catalogue_px": sub["dots_on_catalogue_px"],
            "dots_outside_footprint": sub["dots_outside_footprint"],
        },
        "submission": {
            "name": name,
            "note": note,
            "note_characters": len(note),
            "n_dots": sub["n_dots"],
            "n_dots_target": sub["n_dots_target"],
            "download_allowed_for_audit": True,
            "submit_allowed": submit_allowed,
            "weekly_slot_used": False,
            "file": str(tif.relative_to(ROOT)),
            "zip": str(zip_path.relative_to(ROOT)),
            "outside_encoding": "NaN outside template footprint",
            "zeros_variant": str(zeros_variant.relative_to(ROOT)),
            "zeros_variant_zip": str(zeros_zip.relative_to(ROOT)),
            "sha256": {p.name: sha256(p) for p in (tif, zeros_variant, zip_path, zeros_zip)},

            "flank_support_px": sub["flank_support_px"],
            "un_eroded_edge_score": sub["un_eroded_edge_score"],
            "registry_exclusions": [],
        },
        "verdict": verdict,
        "promotion": "candidate_for_separate_selector" if submit_allowed else "do_not_promote",
        "projection_written_as_score": False,
        "organizer_confirmed_scores": [],
        "budget": {
            "experiments_used": 3,
            "limit": 3,
            "hours_limit": 2,
            "weekly_slot_used": False,
            "experiments": [
                "1: exploratory H57 flank run, invalid for promotion (lattice excluded and arms not mass-matched); retained as an explicitly invalid archive",
                "2: full-registry capacity diagnostic; identified that the score-bearing flank surface can emit only 221 dots at a 1000-dot request under the literal all-raster 0.68 cap",
                "3: matched-mass H57 holdout, 200 dots, all 56 rasters, no exclusions; negative",
            ],
        },
        "review_passes": [
            "implementation",
            "bug/assumption audit",
            "requirement/source/strict-uniqueness audit",
        ],
    }

    status = {
        "project": "55GEMSDOE",
        "reviewed_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "overall_status": "format_valid_duplicate_stop_holdout_negative_audit_only",
        "submission_tif": str(tif.relative_to(ROOT)),
        "download_allowed": True,
        "download_scope": "audit/review only; do not submit",
        "submit_allowed": submit_allowed,
        "submit_recommended": submit_allowed,
        "why_download_is_allowed": (
            f"The recommended NaN-outside TIF passes {nan_pass}/{nan_pass + nan_fail} strict local structural checks "
            "against the canonical template (single-band float32, EPSG:32611, exact shape/transform/resolution, NaN "
            "outside, finite in-footprint [0,1] values, and no mapped-catalogue hits). The all-finite zeros variant "
            f"passes only {zeros_pass}/{zeros_pass + zeros_fail} checks because it violates the null/NaN outside rule. "
            "The NaN TIF is retained for audit only; the expanded uniqueness check scanned 62 registry rasters plus "
            "four local historical candidates (66 comparisons) and returned DUPLICATE-STOP: 76% of dots are within "
            "3 px of two PARALLEL16 reference variants, above the literal 70% limit. Do not submit; local checks are "
            "not organizer clearance."
        ),
        "why_submission_is_blocked": (
            f"DO NOT SUBMIT. The matched-mass HOLDOUT-DTI candidate is {cand['pooled']['dti']:.8f} "
            f"(95% CI [{cand['fold_ci95'][0]:.8f}, {cand['fold_ci95'][1]:.8f}], {n_truth:,} withheld positives, "
            "evaluator src/gems55/dti55.py), below the same-evaluator tensor_full comparator "
            f"{hold['tensor_full']['pooled']['dti']:.8f}, ridge_x_agree {hold['ridge_x_agree']['pooled']['dti']:.8f}, "
            f"and matched random {random['pooled']['dti']:.8f}. The expanded strict uniqueness check also returns "
            "DUPLICATE-STOP: max 3-pixel overlap 0.76 against two PARALLEL16 raster variants exceeds the 0.70 limit. "
            "Verdict NEGATIVE; no weekly slot used and no organizer receipt exists."
        ),
        "holdout_dti": {
            "evidence_class": "HOLDOUT-DTI",
            "evaluator_version": EVALUATOR,
            "withheld_positive_count": n_truth,
            "candidate": cand["pooled"]["dti"],
            "candidate_ci95": cand["fold_ci95"],
            "random": random["pooled"]["dti"],
            "tensor_full": hold["tensor_full"]["pooled"]["dti"],
            "ridge_x_agree": hold["ridge_x_agree"]["pooled"]["dti"],
        },
        "uniqueness_status": uniq["strict_verdict"],
        "organizer_confirmed_score": None,
        "sha256": digest,
        "reason": "The NaN-outside TIF passes strict local format checks and is downloadable for audit only; strict uniqueness is DUPLICATE-STOP and matched HOLDOUT-DTI is negative. Do not submit."
    }

    # Preserve the prior H56 card and status exactly as historical evidence.
    for src, dst in ((DOCS / "run-card.json", DOCS / "run-card-h56.json"),
                     (DOCS / "status.json", DOCS / "status-h56.json")):
        if src.exists() and not dst.exists():
            dst.write_text(src.read_text())
    (DOCS / "run-card.json").write_text(json.dumps(card, indent=2) + "\n")
    (DOCS / "status.json").write_text(json.dumps(status, indent=2) + "\n")
    print(f"HOLDOUT-DTI candidate={cand['pooled']['dti']:.8f} CI={cand['fold_ci95']} "
          f"vs best {best[0]}={best[1]['pooled']['dti']:.8f}; matched mass={mass_matched}")
    print(f"format primary NaN={nan_pass}/{nan_pass + nan_fail}; zeros variant={zeros_pass}/{zeros_pass + zeros_fail}")
    print(f"uniqueness={uniq['strict_verdict']} registry={uniq['registry_rasters_scanned']}/{uniq['registry_rasters_total']} "
          f"+ local={uniq['local_historical_rasters_scanned']}/{uniq['local_historical_rasters_total']} "
          f"({uniq['comparison_rasters_scanned']} comparisons); max surface rho={uniq['max_abs_surface_spearman']}; "
          f"max overlap={uniq['max_final_dot_overlap_within_3px']}")
    print(f"verdict={verdict}; submit_allowed={submit_allowed}; sha256={digest}")


if __name__ == "__main__":
    main()
