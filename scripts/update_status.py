#!/usr/bin/env python3
"""Verify and refresh the current fail-closed site status.

This script deliberately reads the current H56 evidence, not the retired H55
quadrant-run files. It will not turn a format-valid audit artifact into a submit
recommendation when strict uniqueness or the same-evaluator promotion gate fails.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
EVID = ROOT / "evidence"


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    status_path = DOCS / "status.json"
    card_path = DOCS / "run-card.json"
    status = load(status_path)
    card = load(card_path)
    holdout = load(EVID / "holdout_h56_ms300_900_n40000.json")
    baseline = load(EVID / "holdout_baseline_segment_n40000.json")
    unique = load(EVID / "uniqueness_h56_strict.json")

    rel = Path(card["submission"]["file"])
    tif = ROOT / rel
    if not tif.exists():
        raise SystemExit(f"published candidate is missing: {tif}")
    digest = sha256(tif)
    if digest != card["raster_sha256"]:
        raise SystemExit(f"SHA-256 mismatch: {digest} != {card['raster_sha256']}")

    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate_submission.py"), str(tif)],
        capture_output=True,
        text=True,
    )
    if result.returncode:
        print(result.stdout, end="")
        raise SystemExit("published candidate no longer passes the local validator")
    checks_passed = result.stdout.count("[PASS]")
    checks_failed = result.stdout.count("[FAIL]")
    if checks_failed:
        raise SystemExit("published candidate has validator failures")

    h56 = holdout["tensor_full"]["pooled"]["dti"]
    best = baseline["ridge_x_agree"]["pooled"]["dti"]
    strict_block = unique["strict_verdict"] == "DUPLICATE-STOP"
    negative = h56 <= best
    status.update(
        {
            "overall_status": "format_valid_uniqueness_blocked_negative" if strict_block and negative else "needs_review",
            "submission_tif": str(rel),
            "download_allowed": True,
            "submit_allowed": not strict_block and not negative,
            "submit_recommended": not strict_block and not negative,
            "sha256": digest,
            "organizer_confirmed_score": None,
            "holdout_dti": {
                "evidence_class": "HOLDOUT-DTI",
                "evaluator_version": "src/gems55/dti55.py; exact published DTI formula, alpha=0.2, beta=0.8, R=300 m",
                "withheld_positive_count": holdout["tensor_full"]["pooled"]["n_truth"],
                "multiscale_tensor_full": h56,
                "multiscale_tensor_full_ci95": holdout["tensor_full"]["fold_ci95"],
                "matched_random_control": holdout["random"]["pooled"]["dti"],
                "matched_random_control_ci95": holdout["random"]["fold_ci95"],
                "current_best_one_scale_arm": best,
                "current_best_one_scale_arm_name": "ridge_x_agree (ablation/control, not the full tensor candidate)",
                "current_best_one_scale_arm_ci95": baseline["ridge_x_agree"]["fold_ci95"],
            },
            "reason": "Audit download is permitted; strict uniqueness and promotion gates are independently enforced.",
        }
    )
    status_path.write_text(json.dumps(status, indent=2) + "\n")

    card["raster_sha256"] = digest
    card["status"] = status["overall_status"]
    card["validator_output"].update(
        {"status": "PASS", "checks_passed": checks_passed, "checks_failed": checks_failed}
    )
    card["submission"]["submit_allowed"] = status["submit_allowed"]
    card_path.write_text(json.dumps(card, indent=2) + "\n")
    print(f"verified {rel}: {checks_passed} PASS / {checks_failed} FAIL; status={status['overall_status']}")


if __name__ == "__main__":
    main()
