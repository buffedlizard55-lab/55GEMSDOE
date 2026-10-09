"""Regression checks for the published project status and site (E1 cleared state).

The 2026-10-09 E1 session generated a unique tensor-lane submission, validated it
locally, and published it for download. These tests pin the site to the truth:
  * the cleared submission file exists under docs/downloads/ and its sha256
    matches status.json, run-card.json, and the submission evidence record;
  * the site states OBVIOUSLY whether the file is OK to download and submit;
  * every score-like number keeps its evidence-class label (HOLDOUT-DTI /
    PROXY-DTI / PUBLIC-LEADERBOARD); no organizer receipt is claimed;
  * no uncleared artifact (historical H55/H56 rasters, archives) is linked.
"""
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
        if tag.lower() == "a":
            self.hrefs.extend(value for key, value in attrs if key.lower() == "href" and value)


def _submission_record() -> dict:
    subs = sorted((ROOT / "evidence").glob("submission_h55c-*.json"))
    assert subs, "no E1 submission record found"
    return json.loads(subs[-1].read_text())


class SiteStatusTests(unittest.TestCase):
    def test_current_status_and_run_card_are_cleared(self) -> None:
        status = json.loads((DOCS / "status.json").read_text())
        card = json.loads((DOCS / "run-card.json").read_text())

        self.assertTrue(status["download_allowed"])
        self.assertTrue(status["submit_allowed"])
        self.assertTrue(status["submit_recommended"])
        self.assertEqual(status["overall_status"], "CLEARED_OK_TO_DOWNLOAD_AND_SUBMIT")
        self.assertEqual(card["submission"]["status"], "CLEARED_OK_TO_DOWNLOAD_AND_SUBMIT")
        self.assertTrue(card["submission"]["file_link_published"])
        self.assertIsNone(card["submission"]["organizer_receipt"])
        self.assertFalse(card["submission"]["weekly_slot_used"])
        self.assertEqual(card["verdict"], "PROMOTE")

    def test_cleared_submission_file_exists_and_hash_matches_everywhere(self) -> None:
        status = json.loads((DOCS / "status.json").read_text())
        card = json.loads((DOCS / "run-card.json").read_text())
        record = _submission_record()
        raster = ROOT / status["submission"]["file"]
        self.assertTrue(raster.is_file(), f"missing published raster {raster}")
        self.assertEqual(raster.parent.name, "downloads")
        digest = hashlib.sha256(raster.read_bytes()).hexdigest()
        self.assertEqual(digest, status["submission"]["sha256"])
        self.assertEqual(digest, card["raster_sha256"]["value"])
        self.assertEqual(digest, record["raster"]["sha256"])
        self.assertEqual(raster.stat().st_size, status["submission"]["bytes"])
        self.assertEqual(raster.stat().st_size, record["raster"]["bytes"])
        self.assertTrue(record["cleared_for_download_and_submission"])
        self.assertEqual(record["published_copy"], status["submission"]["file"])

    def test_holdout_and_proxy_numbers_are_labeled(self) -> None:
        card = json.loads((DOCS / "run-card.json").read_text())
        hold = card["holdout_dti"]
        self.assertEqual(hold["evidence_class"], "HOLDOUT-DTI")
        self.assertTrue(hold["evaluator_version"])
        self.assertEqual(hold["withheld_positive_count"], 60988)
        self.assertIsNotNone(hold["value"])
        self.assertEqual(len(hold["ci95"]), 2)
        self.assertLess(hold["ci95"][0], hold["value"])
        self.assertLess(hold["value"], hold["ci95"][1])
        self.assertGreater(hold["value"], hold["matched_random_control"]["value"])
        self.assertEqual(hold["leakage_canary"]["verdict"], "PASS_NO_LEAKAGE")
        proxy = card["proxy_dti"]
        self.assertEqual(proxy["evidence_class"], "PROXY-DTI")
        self.assertIsNotNone(proxy["value"])
        self.assertIsNone(card["score_attribution"]["organizer_confirmed_score_for_this_submission"])

    def test_uniqueness_and_validator_gates_are_published(self) -> None:
        card = json.loads((DOCS / "run-card.json").read_text())
        reg = card["registry_comparisons"]
        self.assertEqual(reg["surface_stage"]["verdict"], "PASS-UNIQUE")
        self.assertEqual(reg["final_dot_stage"]["verdict"], "PASS-UNIQUE")
        self.assertLessEqual(reg["surface_stage"]["max_abs_spearman"], 0.90)
        self.assertLessEqual(reg["final_dot_stage"]["max_abs_spearman"], 0.90)
        self.assertLessEqual(
            reg["final_dot_stage"]["max_fraction_candidate_dots_within_euclidean_3px_binding"], 0.70)
        self.assertGreaterEqual(reg["registry_rasters_scanned"], 56)
        val = card["validator_findings"]
        self.assertEqual(val["status"], "PASS_LOCAL_VALIDATOR")
        self.assertTrue(val["all_checks_passed"])
        for check in val["checks"]:
            self.assertTrue(check["passed"], check["name"])

    def test_submission_notes_are_within_limit(self) -> None:
        for name in ("run-card.json", "run-card-h55-160k.json"):
            card = json.loads((DOCS / name).read_text())
            note = card["submission"]["note"]
            self.assertLessEqual(len(note), 140, name)
            self.assertEqual(card["submission"]["note_characters"], len(note), name)

    def test_published_site_links_only_the_cleared_raster(self) -> None:
        status = json.loads((DOCS / "status.json").read_text())
        cleared = status["submission"]["file"]  # docs/downloads/<name>.tif
        for page in DOCS.rglob("*.html"):
            parser = LinkCollector()
            parser.feed(page.read_text())
            for href in parser.hrefs:
                path = urlsplit(href).path.lower()
                if path.endswith((".tif", ".tiff", ".zip")):
                    target = (page.parent / unquote(urlsplit(href).path)).resolve()
                    self.assertEqual(
                        target, (ROOT / cleared).resolve(),
                        f"{page.relative_to(DOCS)} links non-cleared artifact {href}")
        published = [p for p in DOCS.rglob("*")
                     if p.is_file() and p.suffix.lower() in {".tif", ".tiff", ".zip"}]
        self.assertEqual(len(published), 1)
        self.assertEqual(str(published[0].relative_to(ROOT)), cleared)

    def test_landing_page_states_clearance_obviously(self) -> None:
        index = (DOCS / "index.html").read_text()
        status = json.loads((DOCS / "status.json").read_text())
        self.assertIn("CLEARED — OK TO DOWNLOAD AND SUBMIT", index)
        self.assertIn(status["submission"]["file"].split("/")[-1], index)
        self.assertIn("sign in", index.lower())
        self.assertIn("organizer receipt", index.lower())
        submit = (DOCS / "submit.html").read_text()
        self.assertIn("CLEARED — OK TO DOWNLOAD AND SUBMIT", submit)
        self.assertIn("Exactly how to make a submission", submit)
        execsum = (DOCS / "executive-summary.html").read_text()
        self.assertIn("CLEARED — OK TO DOWNLOAD AND SUBMIT", execsum)
        self.assertIn("Exactly how to make a submission", execsum)

    def test_historical_h55_card_is_also_fail_closed(self) -> None:
        status = json.loads((DOCS / "status-h55-160k.json").read_text())
        card = json.loads((DOCS / "run-card-h55-160k.json").read_text())
        self.assertFalse(status["download_allowed"])
        self.assertFalse(status["submit_allowed"])
        self.assertFalse(status["download_link_published"])
        self.assertEqual(card["submission"]["status"], "DO_NOT_DOWNLOAD_OR_SUBMIT")
        self.assertFalse(card["submission"]["file_link_published"])
        holdout = card["holdout_dti"]
        self.assertTrue(holdout["evidence_class"].startswith("HOLDOUT-DTI"))
        self.assertTrue(holdout["evaluator_version"])
        self.assertEqual(holdout["withheld_positive_count"], 60988)
        self.assertEqual(len(holdout["candidate"]["ci95"]), 2)
        self.assertEqual(status["sha256"], card["raster_sha256"]["value"])

    def test_retired_h55_card_generator_fails_closed_without_writing(self) -> None:
        protected = [DOCS / "run-card.json", DOCS / "status.json"]
        before = [path.read_bytes() for path in protected]
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "make_final_card.py")],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Retired", result.stderr)
        self.assertEqual(before, [path.read_bytes() for path in protected])

    def test_every_local_html_link_resolves(self) -> None:
        pages = list(DOCS.rglob("*.html")) + [ROOT / "index.html"]
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
        self.assertIsNone(card["score_attribution"].get("organizer_receipt"))

    def test_public_leaderboard_snapshot_is_not_h33_receipt(self) -> None:
        card = json.loads((DOCS / "run-card.json").read_text())
        status = json.loads((DOCS / "status.json").read_text())
        snapshot = json.loads((ROOT / "evidence/leaderboard_snapshot_20261009.json").read_text())
        self.assertTrue(card["score_attribution"]["evidence_class"].startswith("PUBLIC-LEADERBOARD"))
        self.assertTrue(status["leaderboard_attribution"]["evidence_class"].startswith("PUBLIC-LEADERBOARD"))
        self.assertEqual(status["leaderboard_attribution"]["h33_account_mapping"], "UNVERIFIED")
        self.assertTrue(snapshot["evidence_class"].startswith("PUBLIC-LEADERBOARD"))
        rank16 = next(row for row in snapshot["rows"] if row["rank"] == 16)
        self.assertEqual(rank16["participant"], "extradr19")
        self.assertEqual(rank16["best_public_dw_tversky"], 0.2778)

    def test_metric_correction_is_visible_on_summary_page(self) -> None:
        index = (DOCS / "index.html").read_text()
        self.assertIn("0.2*TP_w + 0.2*FP_w + 0.8*|G|", index)
        results = (DOCS / "results.html").read_text()
        self.assertIn("0.2*N + 0.8*|G|", results)
        self.assertIn("invalid", results.lower())
        self.assertIn("pooled-score contribution uncertainty", results.lower())


if __name__ == "__main__":
    unittest.main()
