#!/usr/bin/env python3
"""Fail-closed audit of the curated static site; no longer regenerates pages.

The former builder generated unsupported score, metric, format, and download
claims from historical evidence. Pages are now curated from the audited sources.
This command verifies that the published site and JSON status remain fail-closed.
"""
from __future__ import annotations

import json
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


class LinkAudit(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "a":
            return
        href = dict(attrs).get("href")
        if href:
            self.links.append(href.lower())


def main() -> None:
    status = json.loads((DOCS / "status.json").read_text())
    card = json.loads((DOCS / "run-card.json").read_text())
    checks = {
        "status download_allowed is false": status.get("download_allowed") is False,
        "status submit_allowed is false": status.get("submit_allowed") is False,
        "run-card submission status is do-not-download-or-submit": card.get("submission", {}).get("status") == "DO_NOT_DOWNLOAD_OR_SUBMIT",
        "valid promotion HOLDOUT-DTI is null": card.get("holdout_dti", {}).get("value") is None and card.get("holdout_dti", {}).get("ci95") is None,
        "registry disposition is duplicate-stop": card.get("registry_comparisons", {}).get("verdict") == "DUPLICATE_STOP",
    }
    for page in sorted(DOCS.glob("*.html")):
        parser = LinkAudit()
        parser.feed(page.read_text())
        bad = [h for h in parser.links if h.endswith((".tif", ".tiff", ".zip")) or ".tif?" in h]
        checks[f"{page.name} has no raster download link"] = not bad
        if bad:
            print(f"  {page.name}: unsafe links: {bad}")

    for name, ok in checks.items():
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    if not all(checks.values()):
        raise SystemExit("Static site audit failed; do not publish until corrected.")
    print("PASS: site remains fail-closed. This script does not rebuild pages or validate a submission.")


if __name__ == "__main__":
    main()
