#!/usr/bin/env python3
"""Fail-closed audit of the curated static site; never generates pages.

No historical TIFF or ZIP is approved for download. This check verifies that
status/run-card records remain fail-closed, no raster/archive is physically under
``docs/``, and no published HTML page contains a direct download link. It does
not validate a candidate or query the organizer.
"""
from __future__ import annotations

import json
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


class LinkAudit(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag.lower() == "a":
            href = dict(attrs).get("href")
            if href:
                self.links.append(href.lower())


def main() -> None:
    card = json.loads((DOCS / "run-card.json").read_text())
    h55_status_path = DOCS / "status-h55-160k.json"
    h55_status = json.loads(h55_status_path.read_text()) if h55_status_path.exists() else None

    checks: dict[str, bool] = {
        "current status forbids download": status.get("download_allowed") is False,
        "current status forbids submission": status.get("submit_allowed") is False,
        "current run card is do-not-download-or-submit": card.get("submission", {}).get("status") == "DO_NOT_DOWNLOAD_OR_SUBMIT",
        "run card publishes no artifact link": card.get("submission", {}).get("file_link_published") is False,
        "no valid promotion HOLDOUT-DTI is asserted": card.get("holdout_dti", {}).get("value") is None and card.get("holdout_dti", {}).get("ci95") is None,
        "registry disposition is duplicate-stop": card.get("registry_comparisons", {}).get("verdict") == "DUPLICATE_STOP",
        "historical artifact is explicitly unlinked": status.get("historical_raster", {}).get("download_link_published") is False,
        "no GeoTIFF/ZIP is physically under published docs": not any(p.is_file() and p.suffix.lower() in {".tif", ".tiff", ".zip"} for p in DOCS.rglob("*")),
    }
    if h55_status is not None:
        checks["historical H55 status forbids download"] = h55_status.get("download_allowed") is False
        checks["historical H55 status forbids submission"] = h55_status.get("submit_allowed") is False

    pages = sorted(DOCS.rglob("*.html"))
    for page in pages:
        parser = LinkAudit()
        parser.feed(page.read_text(encoding="utf-8"))
        bad = [href for href in parser.links if href.split("#", 1)[0].split("?", 1)[0].endswith((".tif", ".tiff", ".zip"))]
        checks[f"{page.relative_to(DOCS)} contains no raster/archive download links"] = not bad
        if bad:
            print(f"  {page.relative_to(DOCS)}: unsafe links: {bad}")

    landing = (DOCS / "index.html").read_text(encoding="utf-8").lower()
    checks["landing page clearly says not to download or submit"] = "not cleared — do not download or submit" in landing
    checks["landing page explains portal workflow"] = "sign in" in landing and "organizer receipt" in landing

    for name, ok in checks.items():
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    if not all(checks.values()):
        raise SystemExit("Static site audit failed; do not publish until corrected.")
    print("PASS: curated site is fail-closed. No page was generated and no submission was validated.")


if __name__ == "__main__":
    main()
