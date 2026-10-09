"""Regression checks for honest download/submit status and local site links."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
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
        current = status["current_checkout_revalidation"]
        self.assertEqual(current["status"], "STATIC_TIF_CHECKS_PASS_FULL_GATES_BLOCKED")
        self.assertEqual(current["static_tif_check"], "PASS")
        self.assertIn("full_template_match", current)
        self.assertEqual(current["holdout_rerun"], "BLOCKED_MISSING_FEATURE_CACHE_AND_LABELS")
        self.assertEqual(current["registry_uniqueness_rerun"], "BLOCKED_MISSING_REGISTRY_RASTERS")
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
        # H56 is committed prior-run evidence, not rerun in this checkout. Every
        # reported DTI arm shares the exact evaluator/positive-count metadata and CI.
        card = json.loads((DOCS / "run-card.json").read_text())
        holdout = card["holdout_dti"]
        self.assertEqual(holdout["evidence_class"], "HOLDOUT-DTI")
        self.assertEqual(holdout["status"], "RUN")
        self.assertTrue(holdout["evaluator_version"])
        self.assertIsInstance(holdout["withheld_positive_count"], int)
        arms = [holdout, holdout["matched_random_control"], holdout["current_best_comparator"]]
        arms.extend(holdout["other_arms"].values())
        for arm in arms:
            self.assertIn("value", arm)
            self.assertEqual(len(arm["ci95"]), 2)
            self.assertLessEqual(arm["ci95"][0], arm["value"])
            self.assertLessEqual(arm["value"], arm["ci95"][1])
        self.assertEqual(card["current_checkout_revalidation"]["status"],
                         "STATIC_TIF_CHECKS_PASS_FULL_GATES_BLOCKED")
        self.assertFalse(card["submission"]["submit_allowed"])
        self.assertFalse(card["organizer_confirmed_scores"])
        snapshot = card["public_leaderboard_snapshot"]
        self.assertEqual(snapshot["evidence_class"], "PUBLIC-LEADERBOARD-SNAPSHOT_NOT_SUBMISSION_PAGE_RECEIPT")
        self.assertFalse(snapshot["h33_artifact_mapping_verified"])

    def test_h55_archived_dti_scores_and_sweep_ci_metadata(self) -> None:
        card = json.loads((DOCS / "run-card-h55-160k.json").read_text())
        h = card["holdout_dti"]
        self.assertEqual(h["evidence_class"], "HOLDOUT-DTI")
        self.assertTrue(h["evaluator_version"])
        self.assertEqual(h["withheld_positive_count"], 60988)
        arms = [h, h["uniform_random_control"], h["B15_secondary"]["tensor_full"],
                h["B15_secondary"]["random"]]
        for arm in arms:
            self.assertIn("value", arm)
            self.assertEqual(len(arm["ci95"]), 2)

        for name in ("exp9_distance_band_v1_n40000.json", "exp10_mass_sweep_v1.json"):
            evidence = json.loads((ROOT / "evidence" / name).read_text())
            meta = evidence["review_metadata"]
            self.assertEqual(meta["evidence_class"], "HOLDOUT-DTI")
            self.assertTrue(meta["evaluator_version"])
            self.assertEqual(meta["withheld_positive_count"], 60988)
            def check_fold_scores(x):
                if isinstance(x, dict):
                    if "per_fold_dti" in x:
                        self.assertEqual(len(x["ci95"]), 2)
                        self.assertIn("ci95_method", x)
                    for value in x.values():
                        check_fold_scores(value)
                elif isinstance(x, list):
                    for value in x:
                        check_fold_scores(value)
            check_fold_scores(evidence)

    def test_retired_h55_card_generator_fails_closed(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/make_final_card.py")],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("is retired", result.stderr)
        self.assertIn("must not overwrite", result.stderr)


if __name__ == "__main__":
    unittest.main()
