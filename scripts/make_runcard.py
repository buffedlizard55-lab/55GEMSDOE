#!/usr/bin/env python3
"""Retired generator: validate the reviewed JSON run card without rewriting it.

The previous generator copied incomplete experiment evidence into publication
fields. The reviewed source of truth is docs/run-card.json; this utility now
checks required fields and fail-closed status only.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CARD_PATH = ROOT / "docs" / "run-card.json"


def main() -> None:
    card = json.loads(CARD_PATH.read_text())
    required = {
        "hypothesis": card.get("hypothesis", {}).get("name"),
        "mechanism": card.get("mechanism"),
        "non_fault_mimic": card.get("non_fault_mimic"),
        "holdout_dti": card.get("holdout_dti"),
        "registry_comparisons": card.get("registry_comparisons"),
        "raster_sha256": card.get("raster_sha256"),
        "validator_findings": card.get("validator_findings"),
        "submission": card.get("submission"),
        "verdict": card.get("verdict"),
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        raise SystemExit(f"Missing required run-card fields: {missing}")

    submission = card["submission"]
    checks = {
        "submission note is within 140 characters": len(submission["note"]) <= 140,
        "recorded note length is accurate": submission["note_characters"] == len(submission["note"]),
        "submission is not cleared": submission["status"] == "DO_NOT_DOWNLOAD_OR_SUBMIT",
        "no organizer receipt is asserted": submission.get("organizer_receipt") is None,
        "no valid promotion holdout score or CI is asserted": (
            card["holdout_dti"].get("value") is None and card["holdout_dti"].get("ci95") is None
        ),
        "artifact is explicitly uncleared": str(card["raster_sha256"].get("artifact_status", "")).startswith("UNCLEARED"),
    }
    for name, passed in checks.items():
        print(f"  [{'PASS' if passed else 'FAIL'}] {name}")
    if not all(checks.values()):
        raise SystemExit("Run-card validation failed; no file was written.")
    print(f"PASS: {CARD_PATH.relative_to(ROOT)} is complete and fail-closed. No file was written.")


if __name__ == "__main__":
    main()
