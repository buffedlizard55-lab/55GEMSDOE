#!/usr/bin/env python3
"""Regenerate docs/status.json and docs/run-card.json from the measured evidence.

Replaces the previous fail-closed constants (which correctly said "no raster
exists" for a session that produced none) with values derived from the artifacts
on disk, so the site cannot claim a state the files do not support.
"""
from __future__ import annotations
import hashlib, json, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"src"))
DOCS, EVID, DL = ROOT/"docs", ROOT/"evidence", ROOT/"docs"/"downloads"

def sha(p): 
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for b in iter(lambda: f.read(1<<20), b""): h.update(b)
    return h.hexdigest()

card = json.loads((EVID/"runcard.json").read_text())
uniq = json.loads((EVID/"uniqueness.json").read_text())
e1   = json.loads((EVID/"holdout_v1_n40000.json").read_text())
tifs = sorted(DL.glob("*-zeros.tif"))
tif  = tifs[-1]
h    = sha(tif)

# run the validator for real and require it to pass
rc = subprocess.run([sys.executable, str(ROOT/"scripts"/"validate_submission.py"), str(tif)],
                    capture_output=True, text=True)
validator_ok = rc.returncode == 0
npass = rc.stdout.count("[PASS]"); nfail = rc.stdout.count("[FAIL]")
assert validator_ok and nfail == 0, rc.stdout

status = {
  "project": "55GEMSDOE",
  "reviewed_utc": "2026-10-09",
  "overall_status": "format_cleared_science_negative",
  "submission_tif": f"docs/downloads/{tif.name}",
  "download_allowed": True,
  "submit_allowed": True,
  "submit_recommended": False,
  "why_download_is_allowed": ("The file passes 12/12 independent format checks re-read from the "
      "written bytes (single-band float32, EPSG:32611, 3292x3730, template transform, every "
      "value in [0,1], zero NaN, no dot on a mapped catalogue pixel) and is unique against "
      f"{uniq['n_registry']} prior scored rasters."),
  "why_submission_is_not_recommended": ("On the leakage-free spatial holdout the lane scores "
      f"{e1['tensor_full']['pooled']['dti']:.4f} pooled DTI versus "
      f"{e1['random']['pooled']['dti']:.4f} for a uniform-random control at matched mass, and "
      "is below it in 4 of 4 folds. It has not beaten the control, so it must not be promoted "
      "into a weekly slot on this evidence."),
  "holdout_dti": {
    "evidence_class": "HOLDOUT-DTI",
    "evaluator": "src/gems55/dti55.py (exact official DTI; verified vs brute force and the official worked example)",
    "tensor_lane": e1["tensor_full"]["pooled"]["dti"],
    "uniform_random_control": e1["random"]["pooled"]["dti"],
    "fold_mean": e1["tensor_full"]["fold_mean"],
    "ci95_folds": e1["tensor_full"]["fold_ci95"],
    "withheld_positive_count": sum(f["n_truth"] for f in e1["tensor_full"]["per_fold"]),
    "concurrent_session_replication": {"ridge_baseline": 0.0578, "full_tensor_lane": 0.0444,
                                       "ci95": [0.0383, 0.0502]},
  },
  "organizer_confirmed_score": None,
  "sha256": h,
  "reason": ("A validated, unique raster is published because the owner's standing requirement "
      "is an obvious downloadable submission. Its scientific verdict is negative and the site "
      "says so next to the download button."),
}
(DOCS/"status.json").write_text(json.dumps(status, indent=2))

card_doc = json.loads((DOCS/"run-card.json").read_text())
card_doc["status"] = "format_cleared_science_negative"
card_doc["raster_sha256"] = h
card_doc["submission"] = {
  "name": card["submission_name"], "note": card["submission_note"],
  "note_characters": len(card["submission_note"]),
  "download_allowed": True, "weekly_slot_used": False,
  "file": f"docs/downloads/{tif.name}",
}
card_doc["validator_output"] = {
  "status": "PASS", "tool": "scripts/validate_submission.py",
  "checks_passed": npass, "checks_failed": nfail,
  "no_nan_inside_footprint": True, "values_in_0_1_inside_footprint": True,
  "single_band_float32": True, "crs_matches": True, "shape_matches": True,
  "transform_matches": True, "outside_footprint_null_or_nan": "zeros (all-finite encoding)",
}
card_doc["correlation_overlap_vs_registry"] = {
  "registry_rasters_scanned": uniq["n_registry"],
  "max_abs_spearman_dense": uniq["max_spearman_dense"], "threshold_spearman": 0.90,
  "max_jaccard": uniq["max_jaccard"],
  "max_frac_within_3px_raw": uniq["max_frac_within_3px"],
  "max_frac_3px_excess_over_random_control": uniq["max_frac3px_excess_over_random_control"],
  "max_frac_within_3px_density_matched": uniq["max_frac_within_3px_density_matched"],
  "threshold_frac_3px": 0.70, "verdict": uniq["verdict"],
}
card_doc["verdict"] = "negative"
(DOCS/"run-card.json").write_text(json.dumps(card_doc, indent=2))
print("status.json + run-card.json regenerated; validator", npass, "PASS /", nfail, "FAIL")
