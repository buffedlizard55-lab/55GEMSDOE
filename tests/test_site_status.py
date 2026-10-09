"""Fail-closed regression tests for the reviewed project status and site."""
from __future__ import annotations

import hashlib
import json
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


class LinkCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag.lower() == "a":
            self.hrefs.extend(value for key, value in attrs if key.lower() == "href" and value)


class SiteStatusTests(unittest.TestCase):
    def test_status_and_run_card_are_fail_closed(self) -> None:
        status = json.loads((DOCS / "status.json").read_text())
        card = json.loads((DOCS / "run-card.json").read_text())

        self.assertFalse(status["download_allowed"])
        self.assertFalse(status["submit_allowed"])
        self.assertFalse(status["submit_recommended"])
        self.assertEqual(card["submission"]["status"], "DO_NOT_DOWNLOAD_OR_SUBMIT")
        self.assertFalse(card["submission"]["file_link_published"])
        self.assertIsNone(card["submission"]["organizer_receipt"])
        self.assertIsNone(card["holdout_dti"]["value"])
        self.assertIsNone(card["holdout_dti"]["ci95"])
        self.assertEqual(card["budget"]["experiments_used_recorded"], 3)
        self.assertEqual(card["budget"]["new_experiments_run_in_review"], 0)
        self.assertFalse(card["budget"]["weekly_slot_used"])

    def test_historical_raster_hash_is_audit_only(self) -> None:
        status = json.loads((DOCS / "status.json").read_text())
        card = json.loads((DOCS / "run-card.json").read_text())
        raster = ROOT / status["historical_raster"]["file"]
        self.assertTrue(raster.is_file())
        digest = hashlib.sha256(raster.read_bytes()).hexdigest()
        self.assertEqual(digest, status["historical_raster"]["sha256"])
        self.assertEqual(digest, card["raster_sha256"]["value"])
        self.assertEqual(status["historical_raster"]["role"], "UNCLEARED_HISTORICAL_ARTIFACT")
        self.assertFalse(status["historical_raster"]["download_link_published"])

    def test_submission_note_is_within_limit(self) -> None:
        card = json.loads((DOCS / "run-card.json").read_text())
        note = card["submission"]["note"]
        self.assertLessEqual(len(note), 140)
        self.assertEqual(card["submission"]["note_characters"], len(note))

    def test_site_has_no_raster_or_archive_download_cta(self) -> None:
        for page in DOCS.glob("*.html"):
            parser = LinkCollector()
            parser.feed(page.read_text())
            for href in parser.hrefs:
                path = urlsplit(href).path.lower()
                self.assertFalse(path.endswith((".tif", ".tiff", ".zip")),
                                 f"{page.name} links uncleared artifact {href}")
        index = (DOCS / "index.html").read_text().lower()
        self.assertIn("not cleared — do not download or submit", index)
        self.assertIn("no project file is currently approved", index)
        self.assertIn("sign in", index)
        self.assertIn("organizer receipt", index)

    def test_every_local_html_link_resolves(self) -> None:
        pages = list(DOCS.glob("*.html")) + [ROOT / "index.html"]
        for page in pages:
            parser = LinkCollector()
            parser.feed(page.read_text())
            for href in parser.hrefs:
                url = urlsplit(href)
                if url.scheme or url.netloc or not url.path:
                    continue
                target = (page.parent / unquote(url.path)).resolve()
                self.assertTrue(target.exists(), f"{page.relative_to(ROOT)} -> {href}")

    def test_run_card_has_complete_scientific_claim_fields(self) -> None:
        card = json.loads((DOCS / "run-card.json").read_text())
        self.assertTrue(card["hypothesis"]["name"])
        self.assertTrue(card["mechanism"])
        self.assertTrue(card["non_fault_mimic"])
        self.assertIn("verdict", card)
        self.assertEqual(card["registry_comparisons"]["verdict"], "DUPLICATE_STOP")
        self.assertEqual(card["validator_findings"]["format_gate"], "NOT_CLEARED")
        self.assertIsNone(card["score_attribution"].get("organizer_receipt"))

    def test_metric_correction_is_visible_on_summary_page(self) -> None:
        index = (DOCS / "index.html").read_text()
        self.assertIn("0.2*TP_w + 0.2*FP_w + 0.8*|G|", index)
        self.assertIn("withdrawn", index.lower())
        results = (DOCS / "results.html").read_text()
        self.assertIn("0.2*N + 0.8*|G|", results)
        self.assertIn("invalid", results.lower())


if __name__ == "__main__":
    unittest.main()
