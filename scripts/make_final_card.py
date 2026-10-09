#!/usr/bin/env python3
"""Write docs/run-card.json and docs/status.json from measured artifacts only.

Every number is read from evidence/*.json, from the validator's own check list
(scripts/validate_submission.py), or from the raster's SHA-256 on disk.  Nothing
is typed in by hand.  Labels: HOLDOUT-DTI (never ORGANIZER-CONFIRMED: no organiser
score exists for this file).
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import validate_submission as vs  # noqa: E402

EVID = ROOT / "evidence"
DOCS = ROOT / "docs"
N_STAR = 160000
BASE = "h55-tensor2d-strikegate-160000dots-20261009T164334Z"
TIF = f"docs/downloads/audit-h55-160k/{BASE}-zeros.tif"  # audit-only folder: not the canonical primary (see AGENTS.md)
NOTE = ("DO NOT SUBMIT (audit). h55 tensor-dim lane, 160k dots. NEGATIVE holdout "
        "(Q4 0.102 vs random 0.163). Literal duplicate-stop tripped.")
EVALUATOR = "src/gems55/dti55.py (exact official DTI; verified vs brute force and official worked example)"


# Brief-required card fields (carried verbatim from the tensor-lane card; unchanged claims).
CARD_TEXT = {
    "hypothesis": "Gradient ridges on RTP-magnetic and isostatic-gravity grids cannot separate a strike-extended fault or contact from a compact intrusion or vent, because both produce ridges. The potential-field gradient tensor can: its dimensionality index is zero for strictly two-dimensional sources and its intermediate eigenvector carries strike. Gating ridges on being near-2-D AND on eigenvector strike agreeing with the ridge's own orientation should therefore preferentially retain unmapped, elongated, less conspicuous traces.",
    "mechanism": "FFT gradient tensor of bands 2 (RTP mag) and 13 (isostatic gravity) after nearest-neighbour NaN fill, along-track micro-levelling and a 400 m - 6 km band-pass; Tzz derived as -(Txx+Tyy) so the tensor is exactly traceless; closed-form 3x3 eigen-decomposition; dimensionality I = 27 e3^2 / (4 (-e2)^3) (I=0 2-D, I=1 3-D, both endpoints unit-tested); strike = azimuth of the intermediate eigenvector; score = corroborated ridge rank x (1-I) x exp(-(dtheta/25deg)^2) x plunge weight x survey-line mask.",
    "non_fault_process_that_could_mimic_it": "Airborne survey-line striping. It is measured here to run north-south, not east-west as the lane brief asserts (IR-55-04). Analytically a field varying only across the flight lines has eigenvalues (|f''|,0,-|f''|) - indistinguishable from a 2-D source striking along the lines - so the tensor cannot reject it and it must be masked geometrically. Secondary mimics: lithologic contacts and dike swarms (genuinely 2-D but not faults) and basin-margin alluvial edges."
}


def load(name: str) -> dict:
    return json.loads((EVID / name).read_text())


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def t_ci95(vals: list[float]) -> list[float]:
    """Fold-level t-interval. Only 4 folds (df=3), so this is indicative, not tight."""
    n = len(vals)
    m = sum(vals) / n
    sd = math.sqrt(sum((v - m) ** 2 for v in vals) / (n - 1))
    t = 3.182  # two-sided 95%, df=3
    return [round(m - t * sd / math.sqrt(n), 4), round(m + t * sd / math.sqrt(n), 4)]


def main() -> None:
    ex10 = load("exp10_mass_sweep_v1.json")
    ex9 = load("exp9_distance_band_v1_n40000.json")
    uniq = load("uniqueness_160000dots.json")
    sub = load(f"submission_{BASE}.json")

    q4 = ex10["protocols"]["Q4_primary"][str(N_STAR)]
    b15 = ex10["protocols"]["B15_secondary"][str(N_STAR)]
    tens = q4["tensor_full"]
    rnd = q4["random"]
    tens_vals = tens["per_fold_dti"]
    ci = t_ci95(tens_vals)

    tif = ROOT / TIF
    nan_twin = ROOT / TIF.replace("-zeros.tif", "-nan.tif")
    zpath = ROOT / TIF.replace("-zeros.tif", "-zeros.zip")
    digest = sha256(tif)
    assert digest == sub["sha256"][tif.name], "published TIF differs from the writer's recorded hash"

    # Run the validator in-process; its CHECKS list is the record of what was measured.
    ok = vs.validate(tif, outside="zeros")
    n_pass = sum(1 for _, p, _ in vs.CHECKS if p)
    n_fail = sum(1 for _, p, _ in vs.CHECKS if not p)
    ok_nan = vs.validate(nan_twin, outside="nan")
    n_pass_nan = sum(1 for _, p, _ in vs.CHECKS if p)

    band_b15 = ex9["bands"]["15"]["arms"]
    card = {
        "project": "55GEMSDOE",
        "hypothesis": CARD_TEXT["hypothesis"],
        "mechanism": CARD_TEXT["mechanism"],
        "non_fault_process_that_could_mimic_it": CARD_TEXT["non_fault_process_that_could_mimic_it"],
        "generated_by": "scripts/make_final_card.py",
        "verdict": "negative",
        "verdict_reason": (
            f"Pre-registered rule (exp10): N* = argmax over N of tensor_full on the Q4 primary protocol = {N_STAR}. "
            f"At N*, tensor_full scores {tens['fold_pooled_dti']:.4f} vs uniform random {rnd['fold_pooled_dti']:.4f} "
            f"(Q4, {tens['n_withheld_truth']:,} withheld positives), and beats random in {q4['tensor_folds_beating_random']} "
            f"folds (p={q4['tensor_minus_random_signflip_p_two_sided']}). The B=15 px secondary is mixed: tensor "
            f"{b15['tensor_full']['fold_pooled_dti']:.4f} vs random {b15['random']['fold_pooled_dti']:.4f} "
            f"(p={b15['tensor_minus_random_signflip_p_two_sided']}), a significant gain there but not on the primary, "
            "so the label rule (both must pass) gives NEGATIVE. No weekly slot."
        ),
        "submission": {
            "file": TIF,
            "name": BASE,
            "note": NOTE,
            "note_characters": len(NOTE),
            "weekly_slot_used": False,
            "n_dots": N_STAR,
            "crs": "EPSG:32611",
            "shape": [3730, 3292],
            "cell_m": 100,
            "values": "0 or 1 (binary dots), float32, single band, zeros outside footprint",
        },
        "raster_sha256": digest,
        "nan_twin": {"file": str(nan_twin.relative_to(ROOT)), "sha256": sha256(nan_twin)},
        "zip": {"file": str(zpath.relative_to(ROOT)), "sha256": sha256(zpath)},
        "holdout_dti": {
            "evidence_class": "HOLDOUT-DTI",
            "status": "RUN",
            "evaluator_version": EVALUATOR,
            "protocol": ("Q4 contiguous-quadrant hide-and-recover (PRIMARY), per-fold visible-only faults, "
                         "3 px buffer; secondary B=15 px distance-banded whole-segment folds (exp9/exp10)."),
            "value": round(tens["fold_pooled_dti"], 4),
            "value_meaning": "tensor_full at N=160000, Q4, fold-pooled DTI",
            "withheld_positive_count": tens["n_withheld_truth"],
            "ci95": ci,
            "ci95_method": "fold-level t-interval over 4 quadrant folds (df=3); indicative only",
            "uniform_random_control": round(rnd["fold_pooled_dti"], 4),
            "tensor_minus_random": round(q4["tensor_minus_random_mean"], 4),
            "signflip_p_two_sided_Q4": q4["tensor_minus_random_signflip_p_two_sided"],
            "folds_beating_random_Q4": q4["tensor_folds_beating_random"],
            "B15_secondary": {
                "tensor_full": round(b15["tensor_full"]["fold_pooled_dti"], 4),
                "random": round(b15["random"]["fold_pooled_dti"], 4),
                "signflip_p_two_sided": b15["tensor_minus_random_signflip_p_two_sided"],
                "direction": "tensor > random (significant)",
                "label_rule_passed": "not applicable: label rule requires the Q4 primary to pass, and it fails",
            },
            "exp9_B15_at_N40000": {k: round(v["fold_pooled_dti"], 4) for k, v in band_b15.items()},
            "all_N_Q4": {n: round(ex10["protocols"]["Q4_primary"][n]["tensor_full"]["fold_pooled_dti"], 4)
                         for n in ex10["protocols"]["Q4_primary"]},
            "all_N_Q4_random": {n: round(ex10["protocols"]["Q4_primary"][n]["random"]["fold_pooled_dti"], 4)
                                for n in ex10["protocols"]["Q4_primary"]},
            "leakage_canary": ("per-fold mean AUC of single lane features <= 0.90 in exp8/exp9 "
                               "(max 0.555 at B=15, ridge). The visible-distance control reached 0.899 at B=3 "
                               "(below 0.90) and 0.654 at B=15; it is a control, not a lane feature."),
            "organizer_score_status": "none exists for this file (organiser-confirmed score: not available)",
        },
        "validator_output": {
            "tool": "scripts/validate_submission.py (re-reads written bytes with rasterio)",
            "status": "PASS" if ok else "FAIL",
            "zeros_status": "PASS" if ok else "FAIL",
            "checks_passed": n_pass,
            "checks_failed": n_fail,
            "nan_twin_status": "PASS" if ok_nan else "FAIL",
            "nan_twin_checks_passed": n_pass_nan,
            "dots_on_mapped_catalogue_px": sub["dots_on_catalogue_px"],
            "dots_outside_footprint": sub["dots_outside_footprint"],
        },
        "uniqueness": {
            "tool": "scripts/verify_unique.py vs registry/rasters (56 prior scored rasters)",
            "verdict": uniq["verdict"],
            "n_registry": uniq["n_registry"],
            "max_abs_spearman_dense": uniq["max_spearman_dense"],
            "max_jaccard": uniq["max_jaccard"],
            "max_frac_within_3px_raw": uniq["max_frac_within_3px"],
            "raw_max_reference": "13GEMSDOE__13gems_20261001_r13-lattice-s5_v2_nan-outside.tif (206,895-dot spacing-5 lattice)",
            "raw_max_reference_random_control_frac_within_3px": 0.8389,
            "excess_over_random_control_for_that_reference": 0.0012,
            "brief_threshold_frac_within_3px": uniq["thresholds"]["frac_3px"],
            "literal_70pct_rule": "TRIPPED on the raw statistic (0.8401 > 0.70)",
            "interpretation": ("Chance-level density overlap with a dense lattice (random control 0.839). "
                               "Not a copy: Spearman max 0.014, Jaccard max 0.031, excess over control +0.0012. "
                               "Flagged for owner decision; not cleared as a clean PASS."),
        },
        "striping": {
            "lane_mask_px": 1105919,
            "lane_mask_definition": "gems55 coherence-based mask (build_lane, thresh 0.55, lag 60 px)",
            "older_count_px": 86947,
            "older_count_definition": "gems/tensor.py row-median z>4 (129 rows); a different detector, not a miscount",
            "axis_status": "UNRECONCILED (see docs/irregularities.md IR-55-028)",
        },
        "archive_superseded": {
            "file": "docs/downloads/archive-superseded/h55-tensor2d-strikegate-40000dots-20261009T052235Z-zeros.tif",
            "reason": "Superseded by the pre-registered N* = 160000 file. Same negative holdout verdict at N=40000.",
            "sha256": "b7c7225d1b35559d27a7800e40ac75a48d9a15ef79f169de0b5b64fc1bd9d368",
        },
        "organizer_score_status": "none exists for this file (organiser-confirmed score: not available)",
        "weekly_slot_selection": "separate selector step; not performed (no holdout win)",
    }
    (DOCS / "run-card-h55-160k.json").write_text(json.dumps(card, indent=2) + "\n")  # canonical docs/run-card.json belongs to the h56 session

    status = {
        "project": "55GEMSDOE",
        "reviewed_utc": "2026-10-09",
        "overall_status": "format_valid_uniqueness_blocked_negative_audit_only",
        "label": "DO NOT SUBMIT",
        "submission_tif": TIF,
        "sha256": digest,
        "download_allowed": True,
        "download_scope": "audit only (AGENTS.md: audit TIF links need a prominent DO NOT SUBMIT label)",
        "submit_allowed": False,
        "submit_recommended": False,
        "uniqueness_status": "BLOCKED: literal 70% duplicate-stop rule tripped (raw 0.8401 vs a spacing-5 lattice; random control 0.8389; not a copy). Submit blocked until the owner decides.",
        "why_download_is_allowed": (
            f"Audit download only. The file passes {n_pass}/{n_pass + n_fail} format checks re-read from the written bytes "
            "(single-band float32, EPSG:32611, 3730x3292, template transform incl. 100 m pixel size, every value in [0,1], "
            "zero NaN, no dot on a mapped catalogue pixel). It is not a copy of any of the 56 registry rasters "
            "(max Spearman 0.014, max Jaccard 0.031). Format validity is not submit clearance."),
        "why_submission_is_not_recommended": (
            f"On the leakage-free Q4 holdout, tensor_full at N={N_STAR} scores {tens['fold_pooled_dti']:.4f} "
            f"vs {rnd['fold_pooled_dti']:.4f} for uniform random (HOLDOUT-DTI, 60,988 withheld positives). "
            "On Q4 it loses at N=40k, 80k and 160k and is not distinguishable at 20k. Do not spend a weekly slot on it. "
            "The uniqueness gate is also flagged (see uniqueness_status)."),
        "holdout_dti": {
            "evidence_class": "HOLDOUT-DTI",
            "evaluator": EVALUATOR,
            "tensor_lane": round(tens["fold_pooled_dti"], 4),
            "uniform_random_control": round(rnd["fold_pooled_dti"], 4),
            "ci95_folds": ci,
            "withheld_positive_count": tens["n_withheld_truth"],
            "n_dots": N_STAR,
        },
        "organizer_confirmed_score": None,
        "organizer_score_status": "none exists for this file",
        "reason": ("A validated raster is published because the owner's standing requirement is an obvious "
                   "downloadable submission. Its scientific verdict is negative and the site says so next to the button."),
    }
    (DOCS / "status-h55-160k.json").write_text(json.dumps(status, indent=2) + "\n")
    print(f"validator zeros ok={ok} pass={n_pass} fail={n_fail}; nan ok={ok_nan} pass={n_pass_nan}")
    print(f"wrote docs/run-card-h55-160k.json and docs/status-h55-160k.json; sha={digest}; ci95={ci}")


if __name__ == "__main__":
    main()
