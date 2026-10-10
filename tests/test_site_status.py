"""Regression checks for honest download/submit status and local site links.

Revised 2026-10-10 (expanded H57 audit). The tests ensure the site agrees with the
run card, the NaN-outside primary exists and matches its recorded SHA-256, the strict
validator record is truthful about the zeros diagnostic, and download/submit status
is unmistakable. If a card ever clears submission, its uniqueness evidence must
support that decision.
"""
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
    """Guardrails for honest download/submit status."""

    def test_status_and_run_card_agree_with_the_published_raster(self) -> None:
        status = json.loads((DOCS / "status.json").read_text())
        card = json.loads((DOCS / "run-card.json").read_text())

        # download is always allowed for a published, validated artifact
        self.assertTrue(status["download_allowed"])
        self.assertIsNone(status["organizer_confirmed_score"])
        self.assertNotIn("organizer_confirmed_score", card)
        self.assertEqual(card["submission"]["weekly_slot_used"], False)
        self.assertTrue(card["submission"]["download_allowed_for_audit"])
        self.assertFalse(status["submit_allowed"])
        self.assertFalse(card["submission"]["submit_allowed"])
        self.assertTrue(status["submission_tif"].endswith("-nan.tif"))
        self.assertTrue(card["submission"]["zeros_variant"].endswith("-zeros.tif"))

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
        self.assertEqual(vout["checks_passed"], 11)
        self.assertEqual(vout["checks_failed"], 0)
        self.assertEqual(vout["primary_encoding"], "NaN exactly outside the template footprint")
        self.assertEqual(vout["zeros_variant_checks_passed"], 10)
        self.assertEqual(vout["zeros_variant_checks_failed"], 1)
        self.assertTrue(vout["zeros_variant_fails_null_nan_outside_rule"])

        uniq = card["correlation_overlap_vs_registry"]
        self.assertEqual(uniq["strict_verdict"], "DUPLICATE-STOP")
        self.assertEqual(uniq["registry_rasters_scanned"], 62)
        self.assertEqual(uniq["local_historical_rasters_scanned"], 4)
        self.assertEqual(uniq["comparison_rasters_scanned"], 66)
        self.assertEqual(uniq["max_final_dot_overlap_within_3px"], 0.76)
        self.assertEqual(uniq["strict_duplicate_rows"], 2)

        # status and card must agree on the submit decision
        self.assertEqual(bool(status["submit_allowed"]), bool(card["submission"]["submit_allowed"]))
        self.assertEqual(status["submit_recommended"], status["submit_allowed"])
        self.assertIn("DUPLICATE-STOP", status["why_download_is_allowed"])
        self.assertIn("DUPLICATE-STOP", status["why_submission_is_blocked"])
        self.assertIn("NEGATIVE", status["why_submission_is_blocked"])

    def test_submit_clearance_is_supported_by_the_gates(self) -> None:
        """A submit-cleared card must carry passing gate evidence, not just a label."""
        card = json.loads((DOCS / "run-card.json").read_text())
        if not card["submission"]["submit_allowed"]:
            return  # fail-closed states need no further proof
        hd = card["holdout_dti"]
        uniq = card["correlation_overlap_vs_registry"]
        # holdout promotion: candidate above both comparators
        self.assertGreater(hd["value"], hd["current_best_comparator"]["value"])
        self.assertGreaterEqual(hd["folds_beating_best_comparator"], 4)
        # surface uniqueness below the 0.90 stop
        self.assertLessEqual(uniq["max_abs_surface_spearman"], 0.90)
        # literal final-dot rule against every budgeted registry raster
        self.assertLessEqual(uniq["max_final_dot_overlap_within_3px"], 0.70)
        # any degenerate registry row must be disclosed, not hidden
        self.assertIn("degenerate_row_disclosure", uniq)
        self.assertTrue(uniq["degenerate_row_disclosure"])

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
        recorded.update(card["submission"].get("sha256", {}).values())
        downloads = DOCS / "downloads"
        published_tifs = ([*downloads.glob("*-zeros.tif"), *downloads.glob("*-nan.tif")]
                          if downloads.exists() else [])
        self.assertTrue(published_tifs, "no audit TIF is published")
        for p in published_tifs:
            self.assertIn(hashlib.sha256(p.read_bytes()).hexdigest(), recorded,
                          f"{p.name} is served but its SHA-256 is not in the run card")
        # every download link on the index must point at a file that exists
        index = (DOCS / "index.html").read_text()
        low_index = index.lower()
        self.assertIn("download audit nan-outside .tif", low_index)
        self.assertIn("zeros-outside diagnostic (fails strict format check)", low_index)
        self.assertIn("duplicate-stop", low_index)
        self.assertIn("0.76", low_index)
        parser = LinkCollector()
        parser.feed(index)
        for href in parser.hrefs:
            if href.lower().endswith((".tif", ".zip")):
                self.assertTrue((DOCS / href).exists(), f"index links a missing download: {href}")

    def test_site_states_plainly_whether_it_is_ok_to_submit(self) -> None:
        """The owner's requirement: it must be OBVIOUS whether the file may be submitted."""
        index = (DOCS / "index.html").read_text()
        low = index.lower()
        status = json.loads((DOCS / "status.json").read_text())
        if status["submit_allowed"]:
            self.assertIn("ok to submit", low)
            self.assertIn("download submission .tif", low)
        else:
            self.assertIn("download for audit: yes", low)
            self.assertIn("not cleared to submit", low)
        # Current strict uniqueness and format verdicts must be explicit.
        self.assertIn("duplicate-stop", low)
        self.assertIn("11/11", low)
        self.assertIn("pass", low)

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
        # Every holdout number must carry its label, evaluator, withheld-positive
        # count and CI, and must not be presented as an organiser score.
        card = json.loads((DOCS / "run-card.json").read_text())
        holdout = card["holdout_dti"]
        self.assertEqual(holdout["evidence_class"], "HOLDOUT-DTI")
        self.assertEqual(holdout["status"], "RUN")
        self.assertTrue(holdout["evaluator_version"])
        self.assertIsInstance(holdout["withheld_positive_count"], int)
        self.assertGreater(holdout["withheld_positive_count"], 0)
        self.assertEqual(len(holdout["ci95"]), 2)
        self.assertLessEqual(holdout["ci95"][0], holdout["value"])
        self.assertLessEqual(holdout["value"], holdout["ci95"][1])
        self.assertFalse(card["projection_written_as_score"])
        self.assertEqual(card["organizer_confirmed_scores"], [])


if __name__ == "__main__":
    unittest.main()
