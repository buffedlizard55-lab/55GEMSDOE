"""Fail-closed regression checks for the reviewed project status and site.

The site may only offer a GeoTIFF download when *every* gate recorded in
``docs/status.json`` clears.  These tests assert the recorded state, assert the
artifact really is the recorded bytes, and assert that the caveats travel with
the download button — so a future edit that flips a gate back must either flip
the button off or break the build.
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
            self.hrefs.extend(v for k, v in attrs if k.lower() == "href" and v)


def _links(page: Path) -> list[str]:
    parser = LinkCollector()
    parser.feed(page.read_text(errors="replace"))
    return parser.hrefs


class ClearedArtifactTests(unittest.TestCase):
    """The current tensor-lane artifact is cleared, with two disclosed caveats."""

    def test_status_and_card_agree_the_artifact_is_cleared(self) -> None:
        status = json.loads((DOCS / "status.json").read_text())
        card = json.loads((DOCS / "run-card.json").read_text())
        self.assertTrue(status["download_allowed"])
        self.assertTrue(status["submit_allowed"])
        self.assertEqual(status["artifact"]["role"], "COMPETITION_SUBMISSION_CANDIDATE")
        self.assertTrue(status["artifact"]["download_link_published"])
        self.assertEqual(card["submission"]["status"], "CLEARED_TO_DOWNLOAD_AND_SUBMIT")
        self.assertTrue(card["submission"]["file_link_published"])
        self.assertEqual(card["verdict"], "PROMOTE_WITH_CAVEATS")

    def test_the_cleared_artifact_matches_its_recorded_hash(self) -> None:
        status = json.loads((DOCS / "status.json").read_text())
        card = json.loads((DOCS / "run-card.json").read_text())
        raster = ROOT / status["artifact"]["file"]
        self.assertTrue(raster.is_file())
        digest = hashlib.sha256(raster.read_bytes()).hexdigest()
        self.assertEqual(digest, status["artifact"]["sha256"])
        self.assertEqual(digest, card["raster_sha256"]["value"])
        self.assertEqual(digest, "927dc17f7f5d890b2f382e266ade5d775474631ee96674f8ff3cbc1f1b7c7693")
        self.assertEqual(raster.stat().st_size, status["artifact"]["size_bytes"])

    def test_both_caveats_are_recorded_and_shown(self) -> None:
        status = json.loads((DOCS / "status.json").read_text())
        card = json.loads((DOCS / "run-card.json").read_text())
        # caveat 1: the lane's confirmatory test failed
        self.assertEqual(status["gate_status"]["lane_confirmatory_strike_test"],
                         "FAILED_NOT_SUPPORTED")
        self.assertEqual(status["strike_test"]["verdict"], "NOT_SUPPORTED")
        self.assertIn("FAILED", card["confirmatory_strike_test"]["verdict"])
        # caveat 2: the literal uniqueness rule is breached, by coverage artefact
        self.assertEqual(status["gate_status"]["final_dot_uniqueness_literal_rule"],
                         "BREACHED_BY_COVERAGE_ARTEFACT")
        self.assertEqual(status["uniqueness_evidence"]["literal_rule_verdict"],
                         "BREACHED_BY_COVERAGE_ARTEFACT")
        self.assertLessEqual(status["uniqueness_evidence"]["max_excess_row"]["excess"], 0.5)
        # the breach must be one-sided: the reverse direction stays at or near chance
        worst = status["uniqueness_evidence"]["literal_rule_worst_case"]
        self.assertLessEqual(worst["reverse_fraction"], worst["reverse_chance"] + 0.05)
        for page_name in ("index.html", "download.html"):
            text = (DOCS / page_name).read_text().lower()
            self.assertIn("strike", text, page_name)
            self.assertIn("artefact", text, page_name)

    def test_the_chance_adjusted_uniqueness_gates_pass(self) -> None:
        status = json.loads((DOCS / "status.json").read_text())
        u = status["uniqueness_evidence"]
        # 55 sibling-repo rasters + 6 from the parallel session merged in PR #16
        self.assertEqual(u["registry_rasters_compared"], 61)
        self.assertEqual(u["parallel_session_16_rasters_added"], 6)
        self.assertLess(u["max_abs_spearman"], 0.90)
        self.assertLess(u["max_jaccard"], 0.10)
        # the decisive statistic is symmetric: close in BOTH directions = a copy
        self.assertLessEqual(u["symmetric_max_min_direction_fraction"], 0.70)
        self.assertLessEqual(u["symmetric_max_reverse_fraction"], 0.70)
        self.assertEqual(u["symmetric_rule_verdict"], "PASS-UNIQUE")
        # the literal one-sided breach must be explained by reference coverage
        worst = u["literal_rule_worst_case"]
        self.assertGreaterEqual(worst["chance"], 0.95)
        self.assertLessEqual(abs(worst["raw"] - worst["chance"]), 0.02)
        # and the parallel same-lane rasters must have been scanned, not skipped
        self.assertEqual(len(u["parallel_session_16_rows"]), 3)
        for row in u["parallel_session_16_rows"]:
            self.assertLessEqual(row["min_direction"], 0.70)
            self.assertLess(row["jaccard"], 0.05)
            self.assertLess(abs(row["spearman"]), 0.10)

    def test_holdout_number_is_labelled_and_interval_bearing(self) -> None:
        card = json.loads((DOCS / "run-card.json").read_text())
        h = card["holdout_dti"]
        self.assertEqual(h["evidence_class"], "HOLDOUT-DTI")
        self.assertTrue(h["evaluator_version"])
        self.assertEqual(h["withheld_positive_count"], 60988)
        self.assertEqual(len(h["ci95"]), 2)
        self.assertGreater(h["value"], h["random_control_mean"])
        self.assertGreater(h["ci95"][0], h["random_control_mean"])
        self.assertIn("not a leaderboard prediction", h["limitation"].lower())

    def test_no_organizer_receipt_is_claimed_anywhere(self) -> None:
        status = json.loads((DOCS / "status.json").read_text())
        card = json.loads((DOCS / "run-card.json").read_text())
        self.assertIsNone(card["submission"]["organizer_receipt"])
        self.assertIsNone(card["score_attribution"]["organizer_receipt"])
        self.assertEqual(status["gate_status"]["organizer_receipt"], "ABSENT")
        self.assertFalse(card["budget"]["weekly_slot_used"])


class DownloadAffordanceTests(unittest.TestCase):
    """A raster may be linked only when status.json says it may be."""

    def _raster_links(self) -> list[tuple[Path, str]]:
        found: list[tuple[Path, str]] = []
        for page in DOCS.rglob("*.html"):
            for href in _links(page):
                if urlsplit(href).path.lower().endswith((".tif", ".tiff", ".zip")):
                    found.append((page, href))
        return found

    def test_only_the_cleared_artifact_is_linked(self) -> None:
        status = json.loads((DOCS / "status.json").read_text())
        target = (ROOT / status["artifact"]["file"]).resolve()
        links = self._raster_links()
        self.assertTrue(links, "the cleared artifact should be linked from the site")
        for page, href in links:
            resolved = (page.parent / unquote(urlsplit(href).path)).resolve()
            self.assertEqual(resolved, target, f"{page.name} links {href}")

    def test_artifacts_under_docs_are_exactly_the_cleared_one(self) -> None:
        status = json.loads((DOCS / "status.json").read_text())
        target = (ROOT / status["artifact"]["file"]).resolve()
        published = [p.resolve() for p in DOCS.rglob("*")
                     if p.is_file() and p.suffix.lower() in {".tif", ".tiff", ".zip"}]
        self.assertEqual(sorted(published), [target])

    def test_flipping_the_status_off_removes_the_download_button(self) -> None:
        """The page generator must be fail-closed on the download permission."""
        protected = [DOCS / "status.json", DOCS / "run-card.json", DOCS / "index.html",
                     DOCS / "download.html"]
        before = [p.read_bytes() for p in protected]
        status = json.loads((DOCS / "status.json").read_text())
        try:
            status["download_allowed"] = False
            status["submit_allowed"] = False
            status["artifact"]["download_link_published"] = False
            (DOCS / "status.json").write_text(json.dumps(status, indent=1))
            result = subprocess.run([sys.executable, str(ROOT / "scripts" / "build_pages55.py")],
                                    cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            for page in ("index.html", "download.html"):
                for href in _links(DOCS / page):
                    self.assertFalse(urlsplit(href).path.lower().endswith((".tif", ".zip")),
                                     f"{page} still offers a download while forbidden")
        finally:
            for path, blob in zip(protected, before):
                path.write_bytes(blob)
            subprocess.run([sys.executable, str(ROOT / "scripts" / "build_pages55.py")],
                           cwd=ROOT, capture_output=True, text=True)


class SiteIntegrityTests(unittest.TestCase):
    def test_every_local_html_link_resolves(self) -> None:
        pages = list(DOCS.rglob("*.html")) + [ROOT / "index.html"]
        for page in pages:
            for href in _links(page):
                url = urlsplit(href)
                if url.scheme or url.netloc or not url.path:
                    continue
                self.assertTrue((page.parent / unquote(url.path)).resolve().exists(),
                                f"{page.name} -> {href}")

    def test_static_site_audit_passes(self) -> None:
        result = subprocess.run([sys.executable, str(ROOT / "scripts" / "build_site.py")],
                                cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_executive_summary_explains_the_portal_workflow(self) -> None:
        text = (DOCS / "executive-summary.html").read_text().lower()
        for phrase in ("download the geotiff", "sign in", "submit", "receipt",
                       "predicted values must be in range"):
            self.assertIn(phrase, text, phrase)
        self.assertIn("how to submit", (DOCS / "index.html").read_text().lower())

    def test_parallel_session_artifacts_are_preserved_but_unpublished(self) -> None:
        status = json.loads((DOCS / "status.json").read_text())
        block = status["parallel_session_artifacts"]
        for item in block["items"]:
            self.assertFalse(item["download_link_published"], item["file"])
            self.assertEqual(item["role"], "PARALLEL_SESSION_ARTIFACT_AUDIT_ONLY")
            path = ROOT / item["file"]
            self.assertTrue(path.is_file(), item["file"])
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), item["sha256"])
            self.assertFalse(path.parent.samefile(DOCS / "downloads"))
        # and they are inside the uniqueness registry so future scans see them
        registry = json.loads((ROOT / "registry" / "registry.json").read_text())
        self.assertGreaterEqual(
            len([k for k in registry if k.startswith("PARALLEL16__")]), 6)

    def test_historical_artifacts_stay_unlinked(self) -> None:
        status = json.loads((DOCS / "status.json").read_text())
        self.assertFalse(status["historical_raster"]["download_link_published"])
        self.assertEqual(status["historical_raster"]["role"],
                         "UNCLEARED_HISTORICAL_ARTIFACT")
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
        self.assertEqual(holdout["withheld_positive_count"], 60988)
        self.assertEqual(len(holdout["candidate"]["ci95"]), 2)

    def test_retired_h55_card_generator_still_fails_closed(self) -> None:
        protected = [DOCS / "run-card.json", DOCS / "status.json"]
        before = [p.read_bytes() for p in protected]
        result = subprocess.run([sys.executable, str(ROOT / "scripts" / "make_final_card.py")],
                                cwd=ROOT, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Retired", result.stderr)
        self.assertEqual(before, [p.read_bytes() for p in protected])

    def test_submission_notes_are_within_limit(self) -> None:
        for name in ("run-card.json", "run-card-h55-160k.json"):
            card = json.loads((DOCS / name).read_text())
            note = card["submission"]["note"]
            self.assertLessEqual(len(note), 140, name)
            self.assertEqual(card["submission"]["note_characters"], len(note), name)


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

    def test_official_range_contract_is_stated_before_the_download(self) -> None:
        # the portal rejects values outside [0,1]; every visitor must see that
        text = (DOCS / "executive-summary.html").read_text()
        self.assertIn("Predicted values must be in range", text)
        self.assertIn("[0, 1]", text)
        # the legacy submit.html is a pointer, not a second download surface
        submit = (DOCS / "submit.html").read_text()
        self.assertIn("download.html", submit)
        self.assertIn("Predicted values must be in range [0, 1]", text)
        self.assertNotIn('.tif"', submit.lower())

    def test_readme_carries_the_full_standing_brief(self) -> None:
        readme = (ROOT / "README.md").read_text()
        # the owner's rule: the whole prompt lives in the README as the recurring
        # starting point, verbatim
        self.assertIn("standing prompt, verbatim", readme)
        for phrase in ("PARALLEL-RUN PROTOCOL", "LEAKAGE CANARY", "RUN CARD",
                       "ORGANIZER-CONFIRMED", "Negative results are deliverables",
                       "Maximize P(Win)", "Own the Outcome",
                       "Predicted values must be in range"):
            self.assertIn(phrase, readme, phrase)
        # and the current gate state is stated, not implied
        self.assertIn("CLEARED TO DOWNLOAD AND SUBMIT", readme)
        self.assertIn("NOT_SUPPORTED", readme)
        self.assertIn("0.0380906", readme)


if __name__ == "__main__":
    unittest.main()
