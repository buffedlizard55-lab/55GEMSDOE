"""Fail-closed regression checks for the reviewed project status and site."""
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


class SiteStatusTests(unittest.TestCase):
    def test_current_status_and_run_card_are_fail_closed(self) -> None:
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

    def test_current_historical_raster_hash_is_archival_only(self) -> None:
        status = json.loads((DOCS / "status.json").read_text())
        card = json.loads((DOCS / "run-card.json").read_text())
        raster = ROOT / status["historical_raster"]["file"]
        self.assertTrue(raster.is_file())
        digest = hashlib.sha256(raster.read_bytes()).hexdigest()
        self.assertEqual(digest, status["historical_raster"]["sha256"])
        self.assertEqual(digest, card["raster_sha256"]["value"])
        self.assertEqual(status["historical_raster"]["role"], "UNCLEARED_HISTORICAL_ARTIFACT")
        self.assertFalse(status["historical_raster"]["download_link_published"])
        for item in status["historical_artifacts"]:
            self.assertFalse(item["download_link_published"])
            self.assertTrue((ROOT / item["primary_file"]).is_file())

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

    def test_submission_notes_are_within_limit(self) -> None:
        for name in ("run-card.json", "run-card-h55-160k.json"):
            card = json.loads((DOCS / name).read_text())
            note = card["submission"]["note"]
            self.assertLessEqual(len(note), 140, name)
            self.assertEqual(card["submission"]["note_characters"], len(note), name)

    def test_every_published_score_record_has_evaluator_count_and_interval(self) -> None:
        card = json.loads((DOCS / "run-card.json").read_text())
        rows = card["holdout_dti"]["historical_records_not_for_promotion"]
        self.assertGreaterEqual(len(rows), 4)
        for row in rows:
            self.assertTrue(row["evidence_class"].startswith("HOLDOUT-DTI"))
            self.assertTrue(row["evaluator_version"])
            self.assertGreater(row["withheld_positive_count"], 0)
            if "tensor_full_value" in row:
                self.assertEqual(len(row["tensor_full_ci95"]), 2)
            if "candidate_value" in row:
                self.assertEqual(len(row["ci95"]), 2)
            for result in row.get("results", []):
                self.assertIn("value", result)
                self.assertEqual(len(result["ci95"]), 2)

    def test_published_site_has_no_raster_or_archive_download_cta(self) -> None:
        for page in DOCS.rglob("*.html"):
            parser = LinkCollector()
            parser.feed(page.read_text())
            for href in parser.hrefs:
                path = urlsplit(href).path.lower()
                self.assertFalse(path.endswith((".tif", ".tiff", ".zip")),
                                 f"{page.relative_to(DOCS)} links uncleared artifact {href}")
        published_artifacts = [p for p in DOCS.rglob("*") if p.is_file() and p.suffix.lower() in {".tif", ".tiff", ".zip"}]
        self.assertEqual(published_artifacts, [])
        index = (DOCS / "index.html").read_text().lower()
        self.assertIn("not cleared — do not download or submit", index)
        self.assertIn("no project file is currently approved", index)
        self.assertIn("sign in", index)
        self.assertIn("organizer receipt", index)
        audit = (DOCS / "h55-160k-audit.html").read_text().lower()
        self.assertIn("not cleared — do not download or submit", audit)
        self.assertIn("deliberately not linked", audit)

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
        self.assertEqual(card["registry_comparisons"]["verdict"], "DUPLICATE_STOP")
        self.assertEqual(card["validator_findings"]["format_gate"], "NOT_CLEARED")
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
        self.assertIn("withdrawn", index.lower())
        results = (DOCS / "results.html").read_text()
        self.assertIn("0.2*N + 0.8*|G|", results)
        self.assertIn("invalid", results.lower())
        self.assertIn("pooled-score contribution uncertainty", results.lower())


    def test_session_run_card_is_negative_blocked_and_fail_closed(self) -> None:
        card = json.loads((DOCS / "run-card-session-20261009.json").read_text())
        self.assertEqual(card["verdict"], "NEGATIVE_BLOCKED")
        self.assertEqual(card["submission"]["status"], "DO_NOT_DOWNLOAD_OR_SUBMIT")
        self.assertFalse(card["submission"]["file_link_published"])
        self.assertIsNone(card["submission"]["organizer_receipt"])
        self.assertIsNone(card["submission"]["note"])
        self.assertFalse(card["raster"]["generated"])
        self.assertIsNone(card["raster"]["sha256"])
        self.assertIsNone(card["holdout_dti"]["value"])
        self.assertIsNone(card["holdout_dti"]["ci95"])
        self.assertEqual(card["budget"]["new_experiments_run_in_session"], 0)
        self.assertFalse(card["budget"]["weekly_slot_used"])
        self.assertIn("null or NaN", card["validator_findings"]["official_format_contract"])
        self.assertTrue(all(src.startswith("https://") for src in card["sources"]))

    def test_session_leaderboard_capture_is_labelled_and_consistent(self) -> None:
        capture = json.loads((ROOT / "evidence/leaderboard_capture_20261009_live.json").read_text())
        self.assertTrue(capture["evidence_class"].startswith("PUBLIC-LEADERBOARD"))
        self.assertIn("NOT ORGANIZER-CONFIRMED", capture["evidence_class"])
        ranks = [row["rank"] for row in capture["rows"]]
        self.assertEqual(ranks, list(range(1, len(ranks) + 1)))
        scores = [row["best_public_dw_tversky"] for row in capture["rows"]]
        self.assertEqual(scores, sorted(scores, reverse=True))
        top = capture["rows"][0]
        self.assertEqual((top["participant"], top["best_public_dw_tversky"]), ("xiaofanhu", 0.3774))
        ext = next(row for row in capture["rows"] if row["participant"] == "extradr19")
        self.assertEqual((ext["rank"], ext["best_public_dw_tversky"]), (17, 0.2778))

    def test_submit_page_states_official_range_contract_without_download_link(self) -> None:
        page = (DOCS / "submit.html").read_text()
        self.assertIn("between 0 and 1", page)
        self.assertIn("null</code> or <code>NaN", page)
        self.assertIn("Predicted values must be in range [0, 1]", page)
        self.assertIn("NOT CLEARED — DO NOT DOWNLOAD OR SUBMIT", page)
        self.assertNotIn(".tif\"", page.lower())

    def test_readme_carries_user_brief_and_blockers(self) -> None:
        readme = (ROOT / "README.md").read_text()
        self.assertIn("## User brief", readme)
        self.assertIn("**BLOCKED.**", readme)
        self.assertIn("session-20261009-verification.md", readme)
        self.assertIn("IR-55-048", (DOCS / "irregularities.md").read_text())


if __name__ == "__main__":
    unittest.main()
