"""Regression checks for honest download/submit status and local site links."""
from __future__ import annotations

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
        if tag == "a":
            self.hrefs.extend(value for key, value in attrs if key == "href" and value)


class SiteStatusTests(unittest.TestCase):
    def test_status_and_run_card_are_fail_closed(self) -> None:
        status = json.loads((DOCS / "status.json").read_text())
        card = json.loads((DOCS / "run-card.json").read_text())

        self.assertEqual(status["overall_status"], "not_cleared")
        self.assertFalse(status["download_allowed"])
        self.assertFalse(status["submit_allowed"])
        self.assertIsNone(status["submission_tif"])
        self.assertEqual(card["verdict"], "negative")
        self.assertFalse(card["submission"]["download_allowed"])
        self.assertFalse(card["submission"]["weekly_slot_used"])
        self.assertIsNone(card["raster_sha256"])
        self.assertEqual(card["validator_output"]["status"], "NOT_RUN_NO_RASTER")

    def test_submission_note_is_within_project_limit(self) -> None:
        card = json.loads((DOCS / "run-card.json").read_text())
        note = card["submission"]["note"]
        self.assertLessEqual(len(note), 140)
        self.assertEqual(card["submission"]["note_characters"], len(note))

    def test_no_fake_tiff_or_download_link_is_published(self) -> None:
        self.assertFalse((DOCS / "downloads").exists())
        tiffs = list(DOCS.rglob("*.tif")) + list(DOCS.rglob("*.tiff"))
        self.assertEqual(tiffs, [])
        for page in (DOCS / "index.html", DOCS / "executive-summary.html"):
            parser = LinkCollector()
            parser.feed(page.read_text())
            linked_tiffs = [href for href in parser.hrefs if urlsplit(href).path.lower().endswith((".tif", ".tiff"))]
            self.assertEqual(linked_tiffs, [], f"Unexpected candidate TIFF download link in {page.name}")
        for page in (DOCS / "index.html", DOCS / "executive-summary.html"):
            text = page.read_text().lower()
            self.assertTrue("do not submit" in text or "do not download or submit" in text)
        index = (DOCS / "index.html").read_text().lower()
        self.assertIn("no tiff available", index)

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

    def test_run_card_labels_unrun_evaluation(self) -> None:
        card = json.loads((DOCS / "run-card.json").read_text())
        holdout = card["holdout_dti"]
        self.assertEqual(holdout["evidence_class"], "HOLDOUT-DTI")
        self.assertEqual(holdout["status"], "NOT_RUN")
        self.assertIsNone(holdout["evaluator_version"])
        self.assertIsNone(holdout["withheld_positive_count"])
        self.assertIsNone(holdout["ci95"])


if __name__ == "__main__":
    unittest.main()
