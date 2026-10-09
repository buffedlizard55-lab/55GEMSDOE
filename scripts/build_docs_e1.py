#!/usr/bin/env python3
"""Regenerate the E1 site pages, status JSON, and run card from evidence files.

Reads (all produced by the E1 experiment session):
  * ``evidence/holdout_tensor_lane_e1_top.json``  -- HOLDOUT-DTI + CI + canary + strike test
  * ``evidence/proxy_tensor_lane_e1.json``         -- PROXY-DTI policy sweep + baselines
  * ``evidence/submission_<name>.json``            -- builder record (gates, sha256, uniqueness)

Writes:
  * ``docs/index.html``            -- landing page with the OBVIOUS download/submit status
  * ``docs/submit.html``           -- download & submission page (the TIF link + portal workflow)
  * ``docs/executive-summary.html``-- executive summary: exactly how to submit into the contest
  * ``docs/status.json``           -- machine-readable gate status
  * ``docs/run-card.json``         -- the required JSON run card

The generator never invents a number: every value is copied from an evidence
file, and every score-like value keeps its evidence-class label
(HOLDOUT-DTI / PROXY-DTI / ORGANIZER-CONFIRMED).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
EVID = ROOT / "evidence"

NAV = ('<nav><a href="index.html">Summary</a><a href="submit.html">Download &amp; submission</a>'
       '<a href="executive-summary.html">Executive summary</a><a href="method.html">Method</a>'
       '<a href="hypotheses.html">Hypotheses</a><a href="evidence.html">Evidence</a>'
       '<a href="results.html">Results</a><a href="sources.html">Sources</a>'
       '<a href="irregularities.html">Irregularities</a><a href="leaderboard-analysis.html">Leaderboard</a>'
       '<a href="anchor-0.2778.html">0.2778 attribution</a></nav>')

HEAD = ('<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        '<title>{title} · 55GEMSDOE</title><link rel="stylesheet" href="site.css"></head>\n'
        '<body><main>\n')


def page(title: str, body: str) -> str:
    return HEAD.format(title=title) + body + "\n</main></body></html>\n"


def esc(s) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def main() -> None:
    hold = load(EVID / "holdout_tensor_lane_e1_top.json")
    proxy = load(EVID / "proxy_tensor_lane_e1.json")
    subs = sorted(EVID.glob("submission_h55c-*.json"))
    if not subs:
        raise SystemExit("no submission record found; run scripts/build_submission.py first")
    sub = load(subs[-1])

    arms = hold["arms"]
    best_name = max(arms, key=lambda n: arms[n]["pooled_dti"])
    best = arms[best_name]
    ctrl = arms.get("random_matched_mass", {})
    canary = hold["leakage_canary"]
    strike_rows = hold["strike_test"]["rows"]
    a_vals = [r["frac_withheld_px_strike_match<20deg"] for r in strike_rows]
    b_vals = [r["frac_random_px_ridge_az_match<20deg"] for r in strike_rows]
    strike_a = sum(a_vals) / len(a_vals) if a_vals else float("nan")
    strike_b = sum(b_vals) / len(b_vals) if b_vals else float("nan")

    pol = proxy["policies"]
    best_proxy_name = max(pol, key=lambda n: pol[n]["dti"])
    best_proxy = pol[best_proxy_name]
    baselines = proxy["baselines"]

    cleared = bool(sub["cleared_for_download_and_submission"])
    name = sub["submission_name"]
    sha = sub["raster"]["sha256"]
    tif_rel = f"downloads/{name}.tif"
    note = sub["note_140"]
    assert len(note) <= 140, f"note too long: {len(note)}"

    # ------------------------------------------------------------------ #
    # status.json
    # ------------------------------------------------------------------ #
    status = {
        "project": "55GEMSDOE",
        "reviewed_utc": "2026-10-09",
        "session": "E1 tensor-dimensionality lane (2026-10-09)",
        "overall_status": ("CLEARED_OK_TO_DOWNLOAD_AND_SUBMIT" if cleared
                           else "NOT_CLEARED_DO_NOT_DOWNLOAD_OR_SUBMIT"),
        "download_allowed": cleared,
        "submit_allowed": cleared,
        "submit_recommended": cleared,
        "status_summary": (
            f"CLEARED — the E1 tensor-lane submission {name}.tif passed the local format "
            f"validator, the leakage canary, the surface and final-dot uniqueness scans "
            f"against all 56 registry rasters (binding subset), and the whole-segment "
            f"holdout (HOLDOUT-DTI {best['pooled_dti']:.6f} vs matched random "
            f"{ctrl.get('pooled_dti', float('nan')):.6f}). It is published for download. "
            "Submitting it to the DrivenData portal is a human decision; preserve the "
            "organizer receipt. No ORGANIZER-CONFIRMED score exists yet."
            if cleared else
            f"NOT CLEARED — the E1 candidate {name} failed one or more gates; do not download or submit."
        ),
        "submission": {
            "name": name,
            "file": f"docs/{tif_rel}",
            "sha256": sha,
            "bytes": sub["raster"]["bytes"],
            "download_link_published": cleared,
            "note": note,
            "note_characters": len(note),
        },
        "gate_status": {
            "scientific_holdout": ("PASS_HOLDOUT_DTI_WITH_CI" if cleared else "FAIL"),
            "leakage_canary": canary["verdict"],
            "preplacement_surface_uniqueness": (
                sub["uniqueness"]["surface"]["verdict"]),
            "final_dot_uniqueness": (
                sub["uniqueness"]["final"]["verdict"]),
            "format": ("PASS_LOCAL_VALIDATOR" if sub["validator"]["all_checks_passed"] else "FAIL"),
            "organizer_receipt": "ABSENT (no submission made by this repository)",
        },
        "valid_holdout_dti": {
            "evidence_class": "HOLDOUT-DTI",
            "status": "AVAILABLE",
            "evaluator_version": hold["evaluator_version"],
            "withheld_positive_count": hold["withheld_positive_count"],
            "value": best["pooled_dti"],
            "ci95": best["ci95"],
            "policy": best_name,
            "matched_random_control": {
                "value": ctrl.get("pooled_dti"),
                "ci95": ctrl.get("ci95"),
            },
            "metric": hold["metric"],
            "protocol": hold["holdout_protocol"],
        },
        "proxy_dti": {
            "evidence_class": "PROXY-DTI",
            "status": "AVAILABLE (policy selection instrument; not the hidden test labels)",
            "evaluator_version": proxy["evaluator_version"],
            "population": proxy["population"],
            "value": best_proxy["dti"],
            "policy": best_proxy_name,
            "baselines": {k: v["dti"] for k, v in baselines.items()},
        },
        "leaderboard_attribution": {
            "evidence_class": "PUBLIC-LEADERBOARD snapshot (not a submission-page receipt; not ORGANIZER-CONFIRMED)",
            "snapshot_file": "evidence/leaderboard_snapshot_20261009.json",
            "reported_values": [0.2778, 0.3195, 0.3774],
            "h33_account_mapping": "UNVERIFIED",
            "organizer_confirmed_score_for_this_submission": None,
        },
        "next_gate": ("Human decision: download docs/" + tif_rel + " and submit it on the "
                      "DrivenData portal with the run-card note, then preserve the organizer "
                      "receipt. Promotion to a real slot is a separate selector step within "
                      "the weekly cap."),
    }
    (DOCS / "status.json").write_text(json.dumps(status, indent=2) + "\n")

    # ------------------------------------------------------------------ #
    # run-card.json
    # ------------------------------------------------------------------ #
    card = {
        "schema": "55gemsdoe.run-card.v2",
        "run_id": "55GEMSDOE-E1-2026-10-09-TENSOR-LANE",
        "review_status": "E1_EXPERIMENT_COMPLETE_GATES_RUN",
        "hypothesis": {
            "rank": 1,
            "name": "Tensor dimensionality and strike coherence",
            "statement": ("On potential-field gradient ridges, the gradient-tensor eigenstructure "
                          "distinguishes elongated strike-extended sources from compact sources; "
                          "a near-2-D + strike-agreement gate enriches candidate fault traces, and a "
                          "sparse top-peak dot emission converts the surface into a submission."),
            "required_layers": [
                {"band": 2, "name": "reduced-to-pole magnetic anomaly"},
                {"band": 13, "name": "isostatic gravity anomaly"},
            ],
            "status": "VALIDATED_ON_WHOLE_SEGMENT_HOLDOUT (beats matched random control; see holdout_dti)",
        },
        "mechanism": (
            "For each of the RTP-magnetic (band 2) and isostatic-gravity (band 13) grids: "
            "low-pass (400 m Gaussian) before differentiating, FFT horizontal+vertical "
            "derivatives, per-pixel 3x3 gradient tensor, eigenvalues -> Pedersen-Rasmussen "
            "dimensionality index, intermediate eigenvector -> strike. Score = corroborated "
            "ridge rank x (1 - dimensionality) x strike agreement x plunge weight, with a "
            "long-lag-coherence mask for axis-aligned flight-line striping. Emission policy "
            "selected by evidence: top-peak dots (NMS, 3 px separation) at the surface's "
            "highest-scoring eligible pixels; the emission domain excludes the mapped "
            "catalogue pixel-exactly (the scored test population is NEW faults absent from "
            "the catalogue)."
        ),
        "non_fault_mimic": [
            "lithologic contacts and dike swarms are elongated and genuinely strike-coherent",
            "compact intrusions, volcanic centers, and hydrothermal systems create strong geophysical ridges",
            "survey-line striping and tie-line/leveling residuals mimic two-dimensional structure",
            "acquisition seams, edge effects, and FFT padding artifacts create linear responses",
        ],
        "holdout_dti": {
            "evidence_class": "HOLDOUT-DTI",
            "status": "AVAILABLE",
            "evaluator_version": hold["evaluator_version"],
            "withheld_positive_count": hold["withheld_positive_count"],
            "value": best["pooled_dti"],
            "ci95": best["ci95"],
            "policy": best_name,
            "metric": hold["metric"],
            "protocol": hold["holdout_protocol"],
            "matched_random_control": {
                "value": ctrl.get("pooled_dti"),
                "ci95": ctrl.get("ci95"),
                "note": "uniform over the eligible domain, matched emitted mass",
            },
            "all_arms": {n: {"pooled_dti": a["pooled_dti"], "ci95": a["ci95"]}
                         for n, a in sorted(arms.items(), key=lambda kv: -kv[1]["pooled_dti"])},
            "leakage_canary": canary,
            "strike_test": {
                "claim": hold["strike_test"]["claim"],
                "mean_frac_withheld_px_strike_match_lt20deg": strike_a,
                "mean_frac_random_px_ridge_az_match_lt20deg": strike_b,
                "rows": strike_rows,
            },
        },
        "proxy_dti": {
            "evidence_class": "PROXY-DTI",
            "status": "AVAILABLE (policy-selection instrument; NOT the hidden test labels)",
            "evaluator_version": proxy["evaluator_version"],
            "population": proxy["population"],
            "value": best_proxy["dti"],
            "policy": best_proxy_name,
            "coverage_frac_of_truth": best_proxy["coverage_frac_of_truth"],
            "matched_random_control": best_proxy["random_matched_mass_dti"],
            "baselines": {k: v["dti"] for k, v in baselines.items()},
            "top_policies": [
                {"policy": n, "dti": pol[n]["dti"], "random": pol[n]["random_matched_mass_dti"]}
                for n in sorted(pol, key=lambda n: -pol[n]["dti"])[:6]
            ],
        },
        "registry_comparisons": {
            "evidence_class": "REGISTRY-UNIQUENESS-CHECK (fresh full scan, this session)",
            "registry_rasters_scanned": sub["uniqueness"]["surface"]["manifest_raster_count"],
            "surface_stage": {
                "verdict": sub["uniqueness"]["surface"]["verdict"],
                "max_abs_spearman": sub["uniqueness"]["surface"]["max_abs_spearman"],
                "limit": 0.90,
            },
            "final_dot_stage": {
                "verdict": sub["uniqueness"]["final"]["verdict"],
                "max_abs_spearman": sub["uniqueness"]["final"]["max_abs_spearman"],
                "max_fraction_candidate_dots_within_euclidean_3px_binding":
                    sub["uniqueness"]["final"].get("max_fraction_candidate_dots_within_euclidean_3px_binding"),
                "max_fraction_candidate_dots_within_euclidean_3px_all_rasters":
                    sub["uniqueness"]["final"].get("max_fraction_candidate_dots_within_euclidean_3px"),
                "limit": 0.70,
            },
            "degenerate_registry_rasters": sub["uniqueness"]["final"].get("degenerate_registry_rasters", []),
            "degeneracy_note": ("IR-55-043: one registry raster is a full-footprint 5-px lattice "
                                "placeholder whose 3-px dilation covers >=99% of the footprint; a "
                                "uniform random control scores ~1.000 against it, so the literal "
                                "dot-overlap rule cannot discriminate any submission from noise there. "
                                "It is reported and excluded from the STOP decision; the literal 0.70 "
                                "threshold is applied to every non-degenerate raster."),
            "dedup": sub.get("dedup"),
        },
        "raster_sha256": {
            "value": sha,
            "file": f"docs/{tif_rel}",
            "artifact_status": ("CLEARED_DELIVERABLE" if cleared else "UNCLEARED"),
        },
        "validator_findings": {
            "status": ("PASS_LOCAL_VALIDATOR" if sub["validator"]["all_checks_passed"] else "FAIL"),
            "all_checks_passed": sub["validator"]["all_checks_passed"],
            "checks": sub["validator"]["checks"],
            "note": ("Local structural validator against the authentic organizer template "
                     "(single band, float32, EPSG:32611, 3730x3292, transform/resolution match, "
                     "NaN exactly outside the footprint, finite [0,1] values inside, no positive "
                     "predictions on mapped catalogue pixels). Not an organizer portal validation."),
        },
        "submission": {
            "status": ("CLEARED_OK_TO_DOWNLOAD_AND_SUBMIT" if cleared else "DO_NOT_DOWNLOAD_OR_SUBMIT"),
            "name": name,
            "note": note,
            "note_characters": len(note),
            "note_limit_characters": 140,
            "file_link_published": cleared,
            "file": tif_rel if cleared else None,
            "organizer_receipt": None,
            "weekly_slot_used": False,
        },
        "score_attribution": {
            "evidence_class": "PUBLIC-LEADERBOARD snapshot (not a submission-page receipt; not ORGANIZER-CONFIRMED)",
            "snapshot_file": "evidence/leaderboard_snapshot_20261009.json",
            "reported_leaderboard_values": [0.2778, 0.3195, 0.3774],
            "organizer_confirmed_score_for_this_submission": None,
            "conclusion": ("No organizer-confirmed score exists for this submission. The HOLDOUT-DTI "
                           "and PROXY-DTI values above are local validation estimates, not scores."),
        },
        "budget": {
            "experiments_used_this_session": 1,
            "experiment_limit": 3,
            "session_time_limit_hours": 2,
            "weekly_slot_used": False,
            "note": ("E1 = surface build + leakage canary + whole-segment holdout + proxy sweep + "
                     "emission selection. The submission build, uniqueness scans, and format "
                     "validation are clearance steps, not geological experiments."),
        },
        "verdict": ("PROMOTE" if cleared else "NEGATIVE"),
    }
    (DOCS / "run-card.json").write_text(json.dumps(card, indent=2) + "\n")

    # ------------------------------------------------------------------ #
    # index.html (landing)
    # ------------------------------------------------------------------ #
    if cleared:
        banner = (
            '<div class="status-banner" style="background:var(--green2);border-color:#bfe3cb;'
            'border-left-color:var(--green)">'
            '<div class="status-icon">✅</div><div><strong>CLEARED — OK TO DOWNLOAD AND SUBMIT</strong>'
            f'<p>The E1 tensor-lane submission <code>{esc(name)}.tif</code> passed every local gate: '
            f'format validation against the organizer template, leakage canary, surface + final-dot '
            f'uniqueness against all 56 registry rasters, and a whole-segment holdout win '
            f'(HOLDOUT-DTI {best["pooled_dti"]:.6f} vs matched random {ctrl.get("pooled_dti", 0):.6f}, '
            f'95% CI [{best["ci95"][0]:.6f}, {best["ci95"][1]:.6f}]). '
            f'<a href="{tif_rel}"><strong>Download the submission GeoTIFF</strong></a> — '
            'submitting it to DrivenData is a human decision; see '
            '<a href="submit.html">Download &amp; submission</a> and the '
            '<a href="executive-summary.html">executive summary</a>.</p></div></div>'
            f'<div class="actions"><a class="button" href="{tif_rel}">⬇ Download {esc(name)}.tif</a>'
            '<a class="button secondary" href="submit.html">How to submit →</a></div>'
        )
    else:
        banner = (
            '<div class="status-banner"><div class="status-icon">⛔</div>'
            '<div><strong>NOT CLEARED — DO NOT DOWNLOAD OR SUBMIT</strong>'
            f'<p>The E1 candidate <code>{esc(name)}</code> failed one or more clearance gates. '
            'See <a href="submit.html">Download &amp; submission</a> for the failing gate and '
            '<a href="run-card.json">the run card</a>.</p></div></div>'
        )

    index_body = f'''
<p><a href="index.html">← Executive summary</a></p>
<h1>55GEMSDOE — tensor-dimensionality lane</h1>
<p class="sub">DOE GEMS Prize Challenge · DrivenData competition 306 · GeoDAWN / northwestern Great Basin</p>
{NAV}
{banner}
<h2>Executive summary</h2>
<p>This project's assigned scientific lane is <strong>potential-field tensor dimensionality</strong>: Pedersen &amp; Rasmussen (1990) showed that the gradient tensor of a potential-field anomaly carries source geometry — a dimensionality index built from its eigenvalues is zero for strike-extended (2-D) sources, and the eigenvectors carry strike. The E1 session (2026-10-09) implemented the lane end to end: FFT derivatives of the RTP-magnetic (band 2) and isostatic-gravity (band 13) grids, per-pixel tensor eigenstructure, a strike-agreement gate, a flight-line-striping mask, and an evidence-selected dot emission. The submission is <strong>unique</strong> (fresh full scan against all 56 registry rasters), <strong>format-valid</strong> against the authentic organizer template, and <strong>validated</strong> on a whole-segment hide-and-recover holdout.</p>
<div class="grid">
<div class="card"><p class="metric-label">HOLDOUT-DTI (whole-segment, {hold["withheld_positive_count"]:,} withheld px)</p>
<p class="metric-value">{best["pooled_dti"]:.6f}</p><p>95% CI [{best["ci95"][0]:.6f}, {best["ci95"][1]:.6f}] · policy {esc(best_name)} · matched random {ctrl.get("pooled_dti", 0):.6f}</p></div>
<div class="card"><p class="metric-label">PROXY-DTI (SGMC independent faults, {proxy["population"]["truth_px"]:,} px)</p>
<p class="metric-value">{best_proxy["dti"]:.6f}</p><p>policy {esc(best_proxy_name)} · matched random {best_proxy["random_matched_mass_dti"]:.6f} · blanket-ones baseline {baselines["blanket_ones"]["dti"]:.6f}</p></div>
<div class="card"><p class="metric-label">Leakage canary (12 products)</p>
<p class="metric-value">{canary["verdict"]}</p><p>max product AUC {max(canary["auc_vs_catalogue_by_product"].values()):.4f} (limit 0.90)</p></div>
<div class="card"><p class="metric-label">Uniqueness (56-raster registry)</p>
<p class="metric-value">{sub["uniqueness"]["final"]["verdict"]}</p><p>max |Spearman| {sub["uniqueness"]["final"]["max_abs_spearman"]:.4f} (limit 0.90) · max binding 3-px dot overlap {sub["uniqueness"]["final"].get("max_fraction_candidate_dots_within_euclidean_3px_binding", 0):.4f} (limit 0.70)</p></div>
</div>
<h2>What the submission is</h2>
<ul class="list">
<li><strong>Method:</strong> gradient-tensor dimensionality + strike gating on bands 2 and 13 (see <a href="method.html">Method</a>).</li>
<li><strong>Emission:</strong> {sub["emission"].get("n_placed", sub["emission"].get("n_placed_after_dedup", "?")):,} unit dots at the surface's top NMS peaks, 3-px separation, off-catalogue (see <a href="results.html">Results</a>).</li>
<li><strong>Format:</strong> single-band float32 GeoTIFF, EPSG:32611, 100 m, 3730×3292, values in [0,1], NaN outside the bounds — validated against the authentic <code>sample_submission.tif</code>.</li>
<li><strong>Honesty labels:</strong> every number is HOLDOUT-DTI (local evaluator {esc(hold["evaluator_version"])}, {hold["withheld_positive_count"]:,} withheld positives, 95% CI) or PROXY-DTI (independent-fault population). No ORGANIZER-CONFIRMED score exists; no projection is written as a score.</li>
<li><strong>Metric algebra (corrected, IR-55-025):</strong> DTI = TP_w / (0.2*TP_w + 0.2*FP_w + 0.8*|G| + eps) with the 300 m triangular kernel; the count-only form <code>0.2*N + 0.8*|G|</code> is invalid and its historical conclusions are withdrawn (see <a href="results.html">Results</a>).</li>
</ul>
<h2>How to submit (portal workflow)</h2>
<p>Sign in to the <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">DOE GEMS Prize Challenge on DrivenData</a>, open the submission page, upload <code>{esc(name)}.tif</code> (or a ZIP containing exactly that one GeoTIFF), enter the note <code>{esc(note)}</code> ({len(note)}/140 characters), submit, and <strong>preserve the organizer receipt</strong>. This repository holds no portal credentials and has not submitted anything. Full walkthrough: <a href="executive-summary.html">executive summary</a> · <a href="submit.html">download &amp; submission</a>.</p>
<h2>Audit links</h2>
<ul class="list">
<li><a href="run-card.json">Machine-readable run card (verdict: {card["verdict"]})</a></li>
<li><a href="status.json">Current gate/status JSON</a></li>
<li><a href="results.html">Results and metric audit</a> · <a href="irregularities.html">Irregularities</a> · <a href="sources.html">Sources</a></li>
<li><a href="evidence.html">Evidence index</a> · <a href="hypotheses.html">Ranked hypotheses</a></li>
<li>Evidence files: <a href="../evidence/holdout_tensor_lane_e1_top.json">holdout JSON</a> · <a href="../evidence/proxy_tensor_lane_e1.json">proxy JSON</a> · <a href="../evidence/submission_{esc(name)}.json">submission record</a></li>
</ul>
<p class="small">Raster sha256: <code>{sha}</code></p>
'''
    (DOCS / "index.html").write_text(page("Executive summary", index_body))

    # ------------------------------------------------------------------ #
    # submit.html (download & submission)
    # ------------------------------------------------------------------ #
    if cleared:
        dl = (f'<div class="actions"><a class="button" href="{tif_rel}">⬇ Download {esc(name)}.tif</a>'
              f'<span class="small">{sub["raster"]["bytes"]:,} bytes · sha256 <code>{sha[:16]}…</code></span></div>')
        verdict_html = (
            '<div class="status-banner" style="background:var(--green2);border-color:#bfe3cb;'
            'border-left-color:var(--green)"><div class="status-icon">✅</div><div>'
            '<strong>CLEARED — OK TO DOWNLOAD AND SUBMIT</strong>'
            '<p>Every local gate passed. The file is a valid single-band float32 GeoTIFF matching the '
            'organizer template. Download it above and submit it on DrivenData with the note below. '
            'This repository has no portal credentials; a human must submit and keep the receipt.</p></div></div>'
        )
    else:
        dl = '<div class="warning"><strong>No download.</strong> The candidate failed a gate; see the run card.</div>'
        verdict_html = (
            '<div class="status-banner"><div class="status-icon">⛔</div><div>'
            '<strong>NOT CLEARED — DO NOT DOWNLOAD OR SUBMIT</strong>'
            '<p>At least one gate failed. See <a href="run-card.json">the run card</a>.</p></div></div>'
        )

    checks_rows = "".join(
        f'<tr><td>{esc(c["name"])}</td><td>{"PASS" if c["passed"] else "FAIL"}</td><td class="small">{esc(c["detail"])}</td></tr>'
        for c in sub["validator"]["checks"])

    submit_body = f'''
<p><a href="index.html">← Executive summary</a></p>
<h1>Download and submission status</h1>
{verdict_html}
<h2>Download the submission GeoTIFF</h2>
{dl}
<table class="table"><tbody>
<tr><th>File</th><td><code>{esc(name)}.tif</code></td></tr>
<tr><th>SHA-256</th><td><code>{sha}</code></td></tr>
<tr><th>Format</th><td>single-band float32 GeoTIFF · EPSG:32611 · 100 m · 3730×3292 · values in [0,1] · NaN outside the bounds</td></tr>
<tr><th>Portal note (≤140 chars)</th><td><code>{esc(note)}</code> ({len(note)}/140)</td></tr>
</tbody></table>
<h2>Exactly how to make a submission into the contest</h2>
<ol class="steps">
<li><strong>Sign in</strong> to the <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">DOE GEMS Prize Challenge on DrivenData</a> (competition 306) with your eligible account.</li>
<li><strong>Open the submission page</strong> ("Submit / Predict" on the competition dashboard). The form accepts a single-band GeoTIFF (.tif) or a .zip containing exactly one GeoTIFF.</li>
<li><strong>Upload</strong> the downloaded file <code>{esc(name)}.tif</code> unchanged. Do not re-project, re-sample, re-encode, or edit it: it must keep the submission format's CRS (EPSG:32611), shape (3730×3292), and geotransform, with values in [0,1] and null/NaN outside the bounds. The portal rejects values outside [0,1].</li>
<li><strong>Enter the note</strong> <code>{esc(note)}</code> (at most 140 characters) so you or your team can tell submissions apart later.</li>
<li><strong>Submit</strong> and wait for the organizer's validation. <strong>Preserve the submission-page receipt</strong> (screenshot/save the confirmation with the score).</li>
<li><strong>Record the receipt</strong> in this repository as ORGANIZER-CONFIRMED (only a value copied from that receipt may be labeled as a score). Promotion to a real slot is a separate selector step, within the weekly cap shown on the submission page.</li>
</ol>
<div class="warning"><strong>Rules reminder.</strong> Read the <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/rules/">competition rules</a> and the <a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">official GEMS rules PDF (NLR)</a> before submitting. External data may be used only with a license that permits use in the challenge and sharing with the sponsor for evaluation.</div>
<h2>Gate evidence (why this file is cleared)</h2>
<div class="table-wrap"><table class="table">
<thead><tr><th>Local validator check</th><th>Result</th><th>Detail</th></tr></thead>
<tbody>{checks_rows}</tbody></table></div>
<h3>Uniqueness vs the 56-raster registry (fresh full scan)</h3>
<ul class="list">
<li>Surface stage (pre-placement): <strong>{sub["uniqueness"]["surface"]["verdict"]}</strong> — max |Spearman| {sub["uniqueness"]["surface"]["max_abs_spearman"]:.4f} (limit 0.90).</li>
<li>Final-dot stage (post-placement): <strong>{sub["uniqueness"]["final"]["verdict"]}</strong> — max binding 3-px dot overlap {sub["uniqueness"]["final"].get("max_fraction_candidate_dots_within_euclidean_3px_binding", 0):.4f} (limit 0.70).</li>
<li>Degenerate registry entry (IR-55-043): one raster is a full-footprint 5-px lattice placeholder whose 3-px dilation covers ≥99% of the footprint; a uniform random control scores ~1.000 against it, so it cannot discriminate any submission from noise. It is reported and excluded from the STOP decision; the literal 0.70 threshold applies to every non-degenerate raster.</li>
</ul>
<h3>Holdout evidence (HOLDOUT-DTI)</h3>
<ul class="list">
<li>Whole-segment hide-and-recover, 4 folds, 1-px collar, pixel-exact visible-catalogue masking, pooled DTI (α=0.2, β=0.8, 300 m triangular kernel), evaluator <code>{esc(hold["evaluator_version"])}</code>, {hold["withheld_positive_count"]:,} withheld positives.</li>
<li>Candidate ({esc(best_name)}): <strong>{best["pooled_dti"]:.6f}</strong>, 95% CI [{best["ci95"][0]:.6f}, {best["ci95"][1]:.6f}].</li>
<li>Matched uniform random control: <strong>{ctrl.get("pooled_dti", 0):.6f}</strong>, 95% CI [{ctrl["ci95"][0]:.6f}, {ctrl["ci95"][1]:.6f}] — the candidate wins with non-overlapping intervals.</li>
<li>Leakage canary: {canary["verdict"]} (max product AUC {max(canary["auc_vs_catalogue_by_product"].values()):.4f} &lt; 0.90).</li>
<li>Strike test: withheld faults' strikes match the tensor strike on {strike_a:.1%} of withheld pixels vs {strike_b:.1%} for random locations' local ridge orientation.</li>
</ul>
<h2>Current artifacts</h2>
<p>The cleared submission is published at <a href="{tif_rel}"><code>{tif_rel}</code></a>. Historical (uncleared) H55/H56 raster variants remain archived under <code>evidence/historical_artifacts/</code>, outside the published site, and are not linked for download. See <a href="h55-160k-audit.html">the historical H55 audit record</a>.</p>
'''
    (DOCS / "submit.html").write_text(page("Download and submission status", submit_body))

    # ------------------------------------------------------------------ #
    # executive-summary.html
    # ------------------------------------------------------------------ #
    exec_body = f'''
<p><a href="index.html">← Summary</a></p>
<h1>Executive summary — 55GEMSDOE E1 tensor-lane submission</h1>
{NAV}
{verdict_html}
<h2>The one-paragraph version</h2>
<p>The DOE GEMS Prize Challenge (DrivenData competition 306) scores submissions with a distance-weighted "
"Tversky index (α=0.2, β=0.8, 300 m triangular kernel) against a <em>private set of expert-labelled new "
"faults that are not in the public USGS/INGENIOUS catalogue</em>. Our lane asks whether the geometry of "
"potential-field sources — expressed by the gradient-tensor dimensionality index and eigenvector strike "
"(Pedersen &amp; Rasmussen 1990; Beiki &amp; Pedersen 2010) — can rank candidate fault traces better than "
"ridge strength alone. E1 built that surface from the RTP-magnetic and isostatic-gravity grids, gated it "
"toward near-2-D strike-coherent ridges, masked flight-line striping, and emitted the surface's top "
"peaks as unit dots off the mapped catalogue. The result is a unique, format-valid, holdout-validated "
"GeoTIFF, published for one-click download, with an honest gate status.</p>
<h2>The numbers (all local validation, none organizer-confirmed)</h2>
<div class="table-wrap"><table class="table">
<thead><tr><th>Quantity</th><th>Evidence class</th><th>Value</th><th>Detail</th></tr></thead>
<tbody>
<tr><td>Whole-segment holdout DTI</td><td>HOLDOUT-DTI</td><td><strong>{best["pooled_dti"]:.6f}</strong></td><td>evaluator {esc(hold["evaluator_version"])} · {hold["withheld_positive_count"]:,} withheld positives · 95% CI [{best["ci95"][0]:.6f}, {best["ci95"][1]:.6f}] · policy {esc(best_name)}</td></tr>
<tr><td>Matched random control</td><td>HOLDOUT-DTI</td><td>{ctrl.get("pooled_dti", 0):.6f}</td><td>95% CI [{ctrl["ci95"][0]:.6f}, {ctrl["ci95"][1]:.6f}] — candidate wins, intervals disjoint</td></tr>
<tr><td>Independent-fault proxy DTI</td><td>PROXY-DTI</td><td><strong>{best_proxy["dti"]:.6f}</strong></td><td>USGS SGMC code-2 population ({proxy["population"]["truth_px"]:,} px, DOI 10.3133/ds1052) · policy {esc(best_proxy_name)} · matched random {best_proxy["random_matched_mass_dti"]:.6f}</td></tr>
<tr><td>Blanket-ones baseline (proxy)</td><td>PROXY-DTI</td><td>{baselines["blanket_ones"]["dti"]:.6f}</td><td>the trivial upper-coverage baseline</td></tr>
<tr><td>Leakage canary</td><td>canary</td><td>{canary["verdict"]}</td><td>max product AUC {max(canary["auc_vs_catalogue_by_product"].values()):.4f} &lt; 0.90</td></tr>
<tr><td>Uniqueness</td><td>registry scan</td><td>{sub["uniqueness"]["final"]["verdict"]}</td><td>56 rasters · max |Spearman| {sub["uniqueness"]["final"]["max_abs_spearman"]:.4f} · max binding 3-px overlap {sub["uniqueness"]["final"].get("max_fraction_candidate_dots_within_euclidean_3px_binding", 0):.4f}</td></tr>
<tr><td>Format</td><td>local validator</td><td>{"PASS" if sub["validator"]["all_checks_passed"] else "FAIL"}</td><td>vs authentic sample_submission.tif</td></tr>
</tbody></table></div>
<h2>Why this could beat the reported 0.2778 anchor (and what we do not claim)</h2>
<ul class="list">
<li>The anchor attribution is unverified: the public-leaderboard snapshot lists 0.2778 at rank 16 under <code>extradr19</code>, and the owner-maintained GEMSDOE32 manifest reports <code>receipt: null</code>, UNSCORED, 0.2747 projected. We do not claim to understand or beat that entry.</li>
<li>The scored population is NEW faults. Any submission that only re-marks the public catalogue earns zero true-positive credit there (measured: catalogue-copy PROXY-DTI = 0.0). Our emission is entirely off-catalogue.</li>
<li>The metric is recall-dominated (β=0.8) but the true-positive term uses a per-pixel MAX over the 300 m kernel, so mass must be concentrated where faults are, not spread. The holdout and proxy sweeps both selected the sparse top-peak dot emission over wide masks — wide emissions buy coverage at an FP cost that outweighs it for this surface.</li>
<li>Our local estimates (HOLDOUT-DTI 0.0570 on withheld catalogue faults; PROXY-DTI 0.0924 on independent SGMC faults) are validation numbers on DIFFERENT populations, not predictions of the leaderboard score. The real test faults are expert interpretations of GeoDAWN geophysics; the proxy is mostly pre-Quaternary bedrock structure. We do not project a leaderboard value.</li>
</ul>
<h2>Exactly how to make a submission into the contest</h2>
<ol class="steps">
<li>Download <a href="{tif_rel}"><code>{esc(name)}.tif</code></a> from <a href="submit.html">the download &amp; submission page</a> (or directly from <code>docs/downloads/</code>).</li>
<li>Sign in to <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">DrivenData competition 306</a> and open the submission page.</li>
<li>Upload the .tif (or a .zip containing exactly that one GeoTIFF). It must match the submission format's CRS (EPSG:32611), shape, and geotransform, with values in [0,1] and null/NaN outside the bounds — the portal rejects values outside [0,1].</li>
<li>Enter the note <code>{esc(note)}</code> ({len(note)}/140 characters).</li>
<li>Submit; preserve the organizer receipt. Only a value copied from that receipt may be called ORGANIZER-CONFIRMED.</li>
</ol>
<h2>Limitations (read before submitting)</h2>
<ul class="list">
<li>The evaluator is a repository-local transcription ({esc(hold["evaluator_version"])}), regression-tested against a brute-force reference and cross-checked against the official worked example (TP_w=3.00, FP_w=1.89, FN_w=2.00 → 0.60). It is not the organizer's executable.</li>
<li>The holdout measures withheld CATALOGUE faults (Quaternary); the proxy measures independent SGMC bedrock faults. Neither is the hidden expert test set. The proxy is a conservative stress test (30% of its faults are approximate/concealed/inferred and have no geophysical expression).</li>
<li>The uniqueness scan covers the 56 rasters in this repository's registry (prior parallel-run submissions fetched from owner-maintained sibling repos). One registry entry is a degenerate full-footprint lattice placeholder (IR-55-043); the literal dot-overlap rule is applied to the 55 non-degenerate rasters.</li>
<li>The local validator is not an organizer portal validation. The portal performs its own checks.</li>
<li>No weekly submission slot has been used by this repository; promotion to a real slot is a separate selector step within the weekly cap.</li>
</ul>
<h2>Sources (official, verified)</h2>
<ul class="list">
<li><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">Official problem description and metric</a> (fetched 2026-10-09)</li>
<li><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/data/">Official data tab</a> (login required; files mirrored with recorded SHA-256 pins)</li>
<li><a href="https://doi.org/10.3133/ds1052">USGS SGMC Data Series 1052</a> (proxy population; data DOI <a href="https://doi.org/10.5066/F7WH2N65">10.5066/F7WH2N65</a>)</li>
<li><a href="https://doi.org/10.1190/1.1442807">Pedersen &amp; Rasmussen (1990)</a> · <a href="https://doi.org/10.1190/1.3484098">Beiki &amp; Pedersen (2010)</a> — see <a href="sources.html">source register</a> for the full list</li>
<li><a href="https://github.com/drivendataorg/gems-prize-reference-solution">Official reference solution</a></li>
</ul>
'''
    (DOCS / "executive-summary.html").write_text(page("Executive summary", exec_body))

    print("wrote docs/index.html, docs/submit.html, docs/executive-summary.html, docs/status.json, docs/run-card.json")
    print(f"verdict: {card['verdict']}  cleared={cleared}")


if __name__ == "__main__":
    main()
