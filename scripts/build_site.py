#!/usr/bin/env python3
"""Fail-closed audit of the curated static site; never generates pages.

The audit is *state-dependent*, not static.  If ``docs/status.json`` forbids
download, no page may carry a GeoTIFF/ZIP link and no GeoTIFF/ZIP may sit under
``docs/``.  If it allows download, the link must resolve to a file whose SHA-256
matches the hash recorded in ``status.json``, and the page carrying it must also
carry the disclosed caveats.  Either way a mismatch fails the build.
"""
from __future__ import annotations

import hashlib
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


class LinkCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag.lower() == "a":
            self.links.extend(v for k, v in attrs if k.lower() == "href")


def main() -> int:
    status = json.loads((DOCS / "status.json").read_text())
    card = json.loads((DOCS / "run-card.json").read_text())
    allowed = status.get("download_allowed") is True

    checks: dict[str, bool] = {}
    checks["status and run card agree on download permission"] = (
        status.get("submit_allowed") is allowed
        and card["submission"].get("file_link_published") is allowed
    )
    checks["submission note within 140 characters"] = (
        len(card["submission"]["note"]) <= 140
        and card["submission"]["note_characters"] == len(card["submission"]["note"])
    )
    checks["run card names the evaluator and counts"] = bool(
        card["holdout_dti"]["evaluator_version"]
        and card["holdout_dti"]["withheld_positive_count"] > 0
        and len(card["holdout_dti"]["ci95"]) == 2
    )
    checks["no organizer receipt is claimed"] = (
        card["score_attribution"].get("organizer_receipt") is None
        and card["submission"].get("organizer_receipt") is None
    )
    checks["historical artifact is explicitly unlinked"] = (
        status.get("historical_raster", {}).get("download_link_published") is False
    )

    links: list[tuple[Path, str]] = []
    for page in sorted(DOCS.rglob("*.html")):
        parser = LinkCollector()
        parser.feed(page.read_text())
        for href in parser.links:
            path = urlsplit(href).path
            if path.lower().endswith((".tif", ".tiff", ".zip")):
                links.append((page, href))

    if allowed:
        artifact = ROOT / status["artifact"]["file"]
        digest = hashlib.sha256(artifact.read_bytes()).hexdigest() if artifact.is_file() else ""
        checks["the linked artifact exists"] = artifact.is_file()
        checks["the linked artifact matches the recorded sha256"] = (
            digest == status["artifact"]["sha256"] == card["raster_sha256"]["value"]
        )
        rel = "/" + Path(status["artifact"]["file"]).as_posix()
        checks["exactly the recorded artifact is linked"] = links and all(
            (page.parent / unquote(urlsplit(h).path)).resolve() == artifact.resolve()
            for page, h in links
        ) and rel.endswith(artifact.name)
        carry = " ".join(sorted({p.name for p, _ in links})).lower()
        checks["the download page discloses both caveats"] = (
            "strike" in (DOCS / "download.html").read_text().lower()
            and "artefact" in (DOCS / "download.html").read_text().lower()
            and bool(carry)
        )
    else:
        checks["no GeoTIFF/ZIP is linked when download is forbidden"] = not links
        checks["no GeoTIFF/ZIP is physically under published docs"] = not any(
            p.is_file() and p.suffix.lower() in {".tif", ".tiff", ".zip"} for p in DOCS.rglob("*")
        )

    for name, ok in sorted(checks.items()):
        print(f"[{'PASS' if ok else 'FAIL'}] {name}")
    if not all(checks.values()):
        print("\nStatic site audit failed; do not publish until corrected.")
        return 1
    print("\nStatic site audit passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
