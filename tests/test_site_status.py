"""Regression checks for honest download/submit status and local site links."""
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
        if tag == "a":
            self.hrefs.extend(value for key, value in attrs if key == "href" and value)


class SiteStatusTests(unittest.TestCase):
    """Guardrails for honest download/submit status.

    Revised 2026-10-09.  The previous version asserted that no TIF may exist, which
    was correct for a session that produced no raster but contradicts the owner's
    standing requirement for an obvious, downloadable, validated submission.  The
    intent is kept and strengthened: any published TIF must exist on disk, must
    match the SHA-256 in the run card, must have passed the validator, and the site
    must state plainly whether it is OK to download and submit.
    """

    def test_status_and_run_card_agree_with_the_published_raster(self) -> None:
        status = json.loads((DOCS / "status.json").read_text())
        card = json.loads((DOCS / "run-card.json").read_text())

        self.assertEqual(status["overall_status"], "format_valid_uniqueness_blocked_negative")
        self.assertEqual(card["verdict"], "negative")
        self.assertFalse(card["submission"]["weekly_slot_used"])
        self.assertFalse(card["submission"]["submit_allowed"])
        # An audit download is allowed, but format validity is not submit clearance.
        self.assertTrue(status["download_allowed"])
        self.assertFalse(status["submit_recommended"])
        self.assertFalse(status["submit_allowed"])
        self.assertIsNone(status["organizer_confirmed_score"])

        rel = status["submission_tif"]
        tif = (ROOT / rel)
        self.assertTrue(tif.exists(), f"status.json advertises a missing file: {rel}")
        digest = hashlib.sha256(tif.read_bytes()).hexdigest()
        self.assertEqual(card["raster_sha256"], digest)
        self.assertEqual(status["sha256"], digest)
        self.assertEqual(card["submission"]["file"], rel)

        vout = card["validator_output"]
        self.assertEqual(vout["status"], "PASS")
        self.assertEqual(vout["checks_failed"], 0)
        self.assertGreaterEqual(vout["checks_passed"], 12)

    def test_submission_note_is_within_project_limit(self) -> None:
        card = json.loads((DOCS / "run-card.json").read_text())
        note = card["submission"]["note"]
        self.assertLessEqual(len(note), 140)
        self.assertEqual(card["submission"]["note_characters"], len(note))

    def test_every_published_tif_is_validated_and_disclosed(self) -> None:
        """No TIF may be served unless its hash is on record and the site says what it is."""
        card = json.loads((DOCS / "run-card.json").read_text())
        status = json.loads((DOCS / "status.json").read_text())
        recorded = {card["raster_sha256"]}
        downloads = DOCS / "downloads"
        primaries = [p for p in downloads.glob("*-zeros.tif")] if downloads.exists() else []
        self.assertTrue(primaries, "no primary submission TIF is published")
        for p in primaries:
            self.assertIn(hashlib.sha256(p.read_bytes()).hexdigest(), recorded,
                          f"{p.name} is served but its SHA-256 is not in the run card")
        # every download link on the index must point at a file that exists
        index = (DOCS / "index.html").read_text()
        parser = LinkCollector()
        parser.feed(index)
        for href in parser.hrefs:
            if href.lower().endswith((".tif", ".zip")):
                self.assertTrue((DOCS / href).exists(), f"index links a missing download: {href}")

    def test_site_states_plainly_whether_it_is_ok_to_submit(self) -> None:
        """The owner's requirement: it must be OBVIOUS whether the file may be submitted."""
        index = (DOCS / "index.html").read_text()
        low = index.lower()
        self.assertIn("not cleared to submit", low)
        self.assertIn("do not spend a drivendata slot", low)
        self.assertIn("download audit .tif", low)
        self.assertIn("negative", low)
        # the format verdict and the strict uniqueness/science verdict must both appear
        self.assertIn("12/12 pass", low)
        self.assertIn("duplicate-stop", low)

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

    def test_run_card_labels_holdout_evaluation(self) -> None:
        # Updated 2026-10-09: the holdout HAS run (negative). Every number must carry its label, evaluator,
        # withheld-positive count and CI, and must not be presented as an organiser score.
        card = json.loads((DOCS / "run-card.json").read_text())
        holdout = card["holdout_dti"]
        self.assertEqual(holdout["evidence_class"], "HOLDOUT-DTI")
        self.assertEqual(holdout["status"], "RUN")
        self.assertTrue(holdout["evaluator_version"])
        self.assertIsInstance(holdout["withheld_positive_count"], int)
        self.assertEqual(len(holdout["ci95"]), 2)
        self.assertLessEqual(holdout["ci95"][0], holdout["value"])
        self.assertLessEqual(holdout["value"], holdout["ci95"][1])
        self.assertNotIn("organizer_confirmed_score", card)


if __name__ == "__main__":
    unittest.main()
