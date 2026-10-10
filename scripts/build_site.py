#!/usr/bin/env python3
"""Build the auditable GitHub Pages site from the current run card/evidence.

The page is intentionally fail-closed: format-valid does not become
submit-cleared when the strict registry gate or the holdout promotion gate
fails.  No leaderboard value is inferred from a local holdout.

Everything on the overview and submission pages is read from the committed
``docs/run-card.json`` and ``docs/status.json`` plus the evidence JSON they
reference, so the site cannot drift from the measured artifacts.  The banner
states in one line whether the published TIF is OK to download and OK to
submit, and the submission page carries the step-by-step upload instructions.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
EVID = ROOT / "evidence"
DOWNLOADS = DOCS / "downloads"

GRID = "3292 × 3730 (columns × rows), EPSG:32611, 100 m, transform (100, 0, 243350, 0, −100, 4508550)"

CSS = """
:root{--ink:#14271f;--muted:#5a6b62;--paper:#f5f7f2;--card:#fff;--line:#dce5dc;--green:#176747;--green2:#e5f3ea;--red:#9e332d;--redbg:#fff0ed;--amber:#8d5a10;--amberbg:#fff7e7;--shadow:0 12px 35px rgba(20,39,31,.08)}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.62 system-ui,-apple-system,Segoe UI,sans-serif}a{color:#126244;text-underline-offset:3px}a:hover{color:#093e2a}a:focus-visible{outline:3px solid #d7962d;outline-offset:3px}.wrap{max-width:1120px;margin:0 auto;padding:0 24px}.top{background:#10271e;color:#e8f3eb}.topin{min-height:70px;display:flex;align-items:center;justify-content:space-between;gap:20px}.brand{color:#fff;text-decoration:none;font-weight:800;font-size:19px}.nav{display:flex;gap:15px;flex-wrap:wrap}.nav a{color:#d5e7da;text-decoration:none;font-size:14px}.hero{padding:58px 0 38px;background:linear-gradient(140deg,#edf5ee,#f5f7f2 65%,#e9f0e8);border-bottom:1px solid var(--line)}.eyebrow{font-size:12px;letter-spacing:.13em;text-transform:uppercase;font-weight:800;color:var(--green)}h1,h2,h3{line-height:1.18;letter-spacing:-.03em}h1{font-size:clamp(34px,5vw,54px);margin:12px 0 16px;max-width:850px}h2{font-size:clamp(24px,3vw,32px);margin:0 0 14px}h3{font-size:19px;margin:0 0 9px}.lead{font-size:18px;color:#334b3e;max-width:820px}.section{padding:42px 0}.section+.section{padding-top:10px}.banner{display:flex;gap:14px;padding:19px 21px;margin:22px 0;background:var(--redbg);border:1px solid #efc5bc;border-left:6px solid var(--red);border-radius:14px;box-shadow:var(--shadow)}.banner strong{display:block;color:#79211c;font-size:19px}.banner p{margin:4px 0;color:#633632}.banner.ok{background:var(--green2);border-color:#bfe0cb;border-left-color:var(--green)}.banner.ok strong{color:#0d4a30}.banner.ok p{margin:4px 0;color:#24503a}.audit{padding:21px;background:var(--amberbg);border:1px solid #ecd9ad;border-radius:14px;margin:22px 0}.audit strong{color:#6e4809}.audit.ok{background:var(--green2);border-color:#bfe0cb}.audit.ok strong{color:#0d4a30}.actions{display:flex;gap:10px;flex-wrap:wrap;margin:18px 0}.button{display:inline-flex;align-items:center;padding:11px 16px;border-radius:9px;background:var(--green);color:#fff;text-decoration:none;font-weight:800}.button.secondary{background:#fff;color:var(--green);border:1px solid var(--green)}.button.warn{background:#8d5a10;color:#fff}.grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px;box-shadow:0 5px 20px rgba(20,39,31,.035)}.card p{color:var(--muted);margin:0}.label{font-size:12px;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);font-weight:800}.value{font-weight:800;font-size:21px;margin-top:6px}.tablewrap{overflow:auto;border:1px solid var(--line);border-radius:12px;background:#fff}.table{border-collapse:collapse;width:100%;min-width:700px}.table th,.table td{text-align:left;padding:11px 13px;border-bottom:1px solid var(--line);vertical-align:top}.table th{background:#edf3ed;font-size:13px}.table tr:last-child td{border-bottom:0}.tag{display:inline-block;padding:3px 9px;border-radius:999px;font-size:12px;font-weight:800;background:var(--green2);color:#28533c}.tag.red{background:#ffe2dc;color:#832d27}.tag.amber{background:#fff0ce;color:#765010}pre,code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace}pre{background:#14221b;color:#e8f3eb;padding:14px;border-radius:9px;overflow:auto;font-size:13px}code{background:#edf2ee;border-radius:4px;padding:2px 5px;font-size:.92em}.small{font-size:13px;color:var(--muted)}.two{display:grid;grid-template-columns:1.2fr .8fr;gap:18px}.list li{margin:8px 0}.footer{background:#10271e;color:#d2e2d7;padding:28px 0;margin-top:30px}.footer a{color:#bde8cf}.md{white-space:pre-wrap;background:#fff;border:1px solid var(--line);border-radius:12px;padding:18px;overflow:auto}@media(max-width:850px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}.two{grid-template-columns:1fr}.topin{align-items:flex-start;flex-direction:column;padding:17px 0}}@media(max-width:520px){.wrap{padding:0 16px}.grid{grid-template-columns:1fr}.hero{padding-top:42px}}
"""

NAV = [
    ("index.html", "Overview"),
    ("download.html", "Download"),
    ("submit.html", "Submission steps"),
    ("results.html", "Results"),
    ("hypotheses.html", "Hypotheses"),
    ("method.html", "Method"),
    ("evidence.html", "Evidence"),
    ("leaderboard-analysis.html", "Anchor analysis"),
    ("sources.html", "Sources"),
    ("irregularities.html", "Irregularities"),
    ("h55-160k-audit.html", "h55 audit (DO NOT SUBMIT)"),  # written by scripts/build_h55_audit_page.py, run after this
]


def load(name: str) -> dict:
    p = EVID / name
    return json.loads(p.read_text()) if p.exists() else {}


def page(title: str, body: str) -> str:
    nav = " ".join(f'<a href="{h}">{t}</a>' for h, t in NAV)
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)} · 55GEMSDOE</title><style>{CSS}</style></head><body><header class="top"><div class="wrap topin"><a class="brand" href="index.html">55GEMSDOE · tensor lane</a><nav class="nav">{nav}</nav></div></header>{body}<footer class="footer"><div class="wrap"><p>Generated by <code>scripts/build_site.py</code> from the committed run card and evidence JSON.</p><p>Every scientific number is labelled HOLDOUT-DTI or ORGANIZER-CONFIRMED; this run has no organizer-confirmed score.</p></div></footer></body></html>'''


def hero(title: str, subtitle: str, body: str = "") -> str:
    return f'<section class="hero"><div class="wrap"><div class="eyebrow">DOE GEMS · competition 306</div><h1>{title}</h1><p class="lead">{subtitle}</p>{body}</div></section>'


def esc(x) -> str:
    return html.escape(str(x))


def status_banner(status: dict, card: dict) -> str:
    """State plainly whether the audit file can be downloaded and submitted."""
    if status.get("submit_allowed"):
        return f'''<div class="banner ok"><div aria-hidden="true">✅</div><div><strong>DOWNLOAD FOR AUDIT: YES · OK TO SUBMIT</strong><p>{esc(status.get("why_submission_is_allowed", ""))}</p></div></div>'''
    if status.get("download_allowed"):
        heading = "DOWNLOAD FOR AUDIT: YES · NOT CLEARED TO SUBMIT"
    else:
        heading = "DOWNLOAD: NO · NOT CLEARED TO SUBMIT"
    return f'''<div class="banner"><div aria-hidden="true">⛔</div><div><strong>{esc(heading)}</strong><p>{esc(status.get("why_submission_is_blocked", "The current gates have not all passed; see the run card."))}</p></div></div>'''


def download_box(status: dict, card: dict) -> str:
    sub = card.get("submission", {})
    tif = Path(status.get("submission_tif", "")).name
    zipf = Path(sub.get("zip", "")).name if sub.get("zip") else ""
    zerosf = Path(sub.get("zeros_variant", "")).name if sub.get("zeros_variant") else ""
    sha = status.get("sha256", "")
    note = sub.get("note", "")
    ok = bool(status.get("submit_allowed"))
    cls = "audit ok" if ok else "audit"
    btn = "button" if ok else "button warn"
    label = "Download submission .tif" if ok else "Download audit NaN-outside .tif"
    links = f'<a class="{btn}" href="downloads/{esc(tif)}" download>{esc(label)}</a>'
    if zipf:
        links += f'<a class="button secondary" href="downloads/{esc(zipf)}" download>NaN-outside single-TIF ZIP</a>'
    if zerosf:
        links += f'<a class="button secondary" href="downloads/{esc(zerosf)}" download>Zeros-outside diagnostic (fails strict format check)</a>'
    uniqueness = card.get("correlation_overlap_vs_registry", {}).get("strict_verdict", "NOT CHECKED")
    scientific = str(card.get("verdict", "NOT RUN")).upper()
    disposition = ("Ready to submit to DrivenData competition 306." if ok else
                   f"Audit-only. Strict uniqueness is {uniqueness}; HOLDOUT-DTI verdict is {scientific}. Do not submit.")
    return f'''<div class="{cls}"><strong>{esc(tif)}</strong><p>{esc(disposition)}</p><div class="actions">{links}</div><p class="small">SHA-256: <code>{esc(sha)}</code><br>Portal note: <code>{esc(note)}</code></p></div>'''


def fmt(x, nd=5):
    try:
        return f"{float(x):.{nd}f}"
    except (TypeError, ValueError):
        return "—"


def main() -> None:
    status = json.loads((DOCS / "status.json").read_text())
    card = json.loads((DOCS / "run-card.json").read_text())
    sub = card.get("submission", {})
    hd = card.get("holdout_dti", {})
    uniq = card.get("correlation_overlap_vs_registry", {})
    val = card.get("validator_output", {})
    ho = hd.get("value")
    ci = hd.get("ci95", [None, None])
    best = hd.get("current_best_comparator", {})
    rnd = hd.get("matched_random_control", {})
    tif_name = Path(status.get("submission_tif", "")).name
    zeros_name = Path(sub.get("zeros_variant", "")).name if sub.get("zeros_variant") else ""

    # ---- overview / executive summary --------------------------------------
    body = hero(
        "A transparent fault-discovery submission — tensor dimensionality, flank-gated",
        "Potential-field gradient-tensor dimensionality separates strike-extended structures "
        "from compact bodies. The H57 NaN-outside TIF is audit-only: the expanded strict "
        "scan covers 66 rasters and returns DUPLICATE-STOP at 0.76 overlap (>0.70).",
    )
    body += '<main class="wrap">' + status_banner(status, card) + download_box(status, card)
    body += f'''<section class="section"><h2>Executive summary</h2><p>{esc(card.get("hypothesis", ""))}</p><p>{esc(card.get("mechanism", ""))}</p><p><b>Result (HOLDOUT-DTI, not a leaderboard score):</b> candidate <b>{fmt(ho)}</b> with 95% CI [{fmt(ci[0])}, {fmt(ci[1])}], {int(hd.get("withheld_positive_count", 0)):,} withheld positives; matched random control {fmt(rnd.get("value"))}; current best comparator ({esc(hd.get("current_best_comparator", {}).get("name", ""))}) {fmt(best.get("value"))}. Verdict: <b>{esc(card.get("verdict", ""))}</b>.</p></section>'''
    body += f'''<section class="section"><h2>Four decisions at a glance</h2><div class="grid"><div class="card"><div class="label">Format</div><div class="value"><span class="tag">{int(val.get("checks_passed", 0))}/{int(val.get("checks_passed", 0)) + int(val.get("checks_failed", 0))} PASS</span></div><p>NaN-outside float32 GeoTIFF, finite footprint values in [0,1], exact template geometry, no mapped-catalogue hit. The zeros-outside twin fails the strict null/NaN footprint check.</p></div><div class="card"><div class="label">Science</div><div class="value"><span class="tag{"" if card.get("verdict") == "promote" else " red"}">{esc(card.get("verdict", "").upper())}</span></div><p>HOLDOUT-DTI {fmt(ho)} vs comparator {fmt(best.get("value"))} and random {fmt(rnd.get("value"))}.</p></div><div class="card"><div class="label">Uniqueness</div><div class="value"><span class="tag{"" if uniq.get("strict_verdict") == "PASS-UNIQUE" else " amber"}">{esc(uniq.get("strict_verdict", ""))}</span></div><p>Max surface Spearman {fmt(uniq.get("max_abs_surface_spearman"), 4)}; max final-dot overlap {fmt(uniq.get("max_final_dot_overlap_within_3px"), 4)} vs 0.70 stop. {esc(uniq.get("degenerate_row_disclosure", ""))}</p></div><div class="card"><div class="label">Organizer score</div><div class="value">None</div><p>No submission-page receipt exists in this repository; every leaderboard value quoted anywhere is a user/sibling claim.</p></div></div></section>'''
    body += f'''<section class="section"><div class="two"><div><h2>What the metric rewards</h2><p>The official distance-weighted Tversky metric uses alpha 0.2, beta 0.8, and a 300 m triangular kernel. False negatives cost more than false positives, so coverage near real structure matters more than density. A local holdout on mapped faults is only a proxy for the organizer's hidden new-fault labels.</p><pre>DTI = TP_w / (TP_w + 0.2 FP_w + 0.8 FN_w)</pre><h2>Grid contract</h2><p>{GRID}<br>5,167,373 valid footprint pixels · 60,988 mapped catalogue pixels · {int(sub.get("n_dots", 0)):,} candidate dots.</p></div><div><h2>Submission decision</h2><p><b>Do not upload the current TIF.</b> It is downloadable for audit, but the expanded strict uniqueness scan is DUPLICATE-STOP and matched-mass HOLDOUT-DTI is negative. No weekly slot was used. For a future promoted artifact, follow the <a href="submit.html">step-by-step submission page</a> and record the organizer receipt; local format checks alone do not clear a submission.</p></div></div></section></main>'''
    (DOCS / "index.html").write_text(page("Executive summary", body))
    (DOCS / "executive-summary.html").write_text(page("Executive summary", body))

    # ---- submission steps ----------------------------------------------------
    gate_rows = [
        ("Format validator", "PASS" if val.get("status") == "PASS" else "FAIL",
         f"Primary NaN-outside TIF: {int(val.get('checks_passed', 0))}/{int(val.get('checks_passed', 0)) + int(val.get('checks_failed', 0))} strict checks; zeros-outside diagnostic: {int(val.get('zeros_variant_checks_passed', 0))}/{int(val.get('zeros_variant_checks_passed', 0)) + int(val.get('zeros_variant_checks_failed', 0))}, failing the null/NaN outside-footprint rule."),
        ("Continuous surface uniqueness", "PASS" if (uniq.get("max_abs_surface_spearman") or 1) <= 0.90 else "FAIL",
         f"max absolute Spearman {fmt(uniq.get('max_abs_surface_spearman'), 4)} across {int(uniq.get('comparison_rasters_scanned', 0))}/{int(uniq.get('comparison_rasters_total', 0))} registry + local historical rasters (stop above 0.90)."),
        ("Final-dot uniqueness", uniq.get("strict_verdict", ""),
         f"max one-sided overlap within 3 px = {fmt(uniq.get('max_final_dot_overlap_within_3px'), 4)} (literal stop above 0.70); {int(uniq.get('strict_duplicate_rows', 0))} duplicate rows across {int(uniq.get('comparison_rasters_scanned', 0))}/{int(uniq.get('comparison_rasters_total', 0))} comparisons. {uniq.get('degenerate_row_disclosure', '')}"),
        ("Holdout promotion", "PASS" if card.get("verdict") == "promote" else "FAIL",
         f"candidate {fmt(ho)} vs comparator {fmt(best.get('value'))} and random {fmt(rnd.get('value'))} (HOLDOUT-DTI, {int(hd.get('withheld_positive_count', 0)):,} withheld positives)."),
        ("Organizer receipt", "None", "No submission-page receipt exists in this repository. A local validator is not an organizer receipt."),
    ]
    rows_html = "".join(
        f'<tr><td>{esc(g)}</td><td><span class="tag{" red" if s in ("FAIL", "DUPLICATE-STOP") else ""}">{esc(s)}</span></td><td>{esc(d)}</td></tr>'
        for g, s, d in gate_rows
    )
    submit = hero("How to enter a submission", "The exact steps to upload the published TIF to DrivenData competition 306, and the gate checklist it must pass.")
    submit += '<main class="wrap">' + status_banner(status, card) + download_box(status, card)
    submit += f'''<section class="section"><h2>Current gate checklist</h2><div class="tablewrap"><table class="table"><tr><th>Gate</th><th>Measured state</th><th>Evidence</th></tr>{rows_html}</table></div></section>'''
    submit += f'''<section class="section"><h2>Submission steps</h2><p><b>These upload steps are conditional on the banner saying OK TO DOWNLOAD AND SUBMIT. The current banner says NOT CLEARED; do not upload the current audit TIF.</b></p><ol class="list"><li>Check the banner above. If it says NOT CLEARED, stop. No competition slot should be used.</li><li>Only after a future file is cleared, download the exact <code>-nan.tif</code> named on the overview and verify its SHA-256. The current NaN-outside TIF passes 11/11 local checks. The <code>-zeros.tif</code> diagnostic fails the strict null/NaN outside-footprint check and is not an upload candidate.</li><li>Run <code>scripts/validate_submission.py</code> against the official template and check the run card's final-dot uniqueness and matched-mass holdout gates.</li><li>Sign in to <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">DrivenData competition 306</a> (this repository never stores credentials).</li><li>Upload one single-band GeoTIFF (or a .zip containing one GeoTIFF). It must match the official CRS (EPSG:32611), 100 m resolution, shape (3730 × 3292), geotransform, value range [0,1], and the organizer's outside-footprint null/NaN rule.</li><li>Paste the portal note from the run card into the optional note field. The official rules require a narrative explaining the extent of generative-AI use and how it contributed; this project used an AI coding/research agent, so any future prize package must disclose that use accurately.</li><li>Use at most three submissions per week for feedback; before the deadline, select one final submission to count for both prize phases, as stated in the official rules. This site never uses a weekly slot.</li><li>Save the submission-page receipt. Until a receipt exists, no score is ORGANIZER-CONFIRMED.</li></ol></section></main>'''
    (DOCS / "submit.html").write_text(page("Submission steps", submit))

    # ---- download / artifact status -----------------------------------------
    download = hero("Download and submission status", "Audit download is available. The current candidate is not cleared to upload.")
    download += '<main class="wrap">' + status_banner(status, card) + download_box(status, card)
    download += f'''<section class="section"><h2>Current gates</h2><div class="tablewrap"><table class="table"><tr><th>Gate</th><th>Measured result</th></tr><tr><td>Primary format</td><td>NaN outside the footprint; {int(val.get("checks_passed", 0))}/{int(val.get("checks_passed", 0)) + int(val.get("checks_failed", 0))} strict local checks pass.</td></tr><tr><td>Zeros diagnostic</td><td>{int(val.get("zeros_variant_checks_passed", 0))}/{int(val.get("zeros_variant_checks_passed", 0)) + int(val.get("zeros_variant_checks_failed", 0))} checks pass; fails the null/NaN outside-footprint rule. Not an upload candidate.</td></tr><tr><td>Expanded strict uniqueness</td><td><b>{esc(uniq.get("strict_verdict", ""))}</b>; {int(uniq.get("comparison_rasters_scanned", 0))}/{int(uniq.get("comparison_rasters_total", 0))} comparisons, max one-sided 3-pixel overlap {fmt(uniq.get("max_final_dot_overlap_within_3px"), 2)} (literal limit 0.70).</td></tr><tr><td>HOLDOUT-DTI promotion</td><td><b>{esc(card.get("verdict", "").upper())}</b>; candidate {fmt(ho)} vs matched random {fmt(rnd.get("value"))} and best comparator {fmt(best.get("value"))}.</td></tr><tr><td>Organizer receipt / score</td><td>None; no upload was made and no weekly slot was used.</td></tr></table></div><p><b>Decision: download for audit YES; submit NO.</b> A strict uniqueness failure and negative HOLDOUT-DTI independently block submission. A local format pass or symmetric/chance-adjusted comparison does not waive the literal one-sided overlap threshold. See <a href="results.html">full results</a>, <a href="submit.html">submission steps</a>, and the <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">official problem page</a>.</p></section></main>'''
    (DOCS / "download.html").write_text(page("Download and status", download))

    # ---- results -------------------------------------------------------------
    hold_name = hd.get("evidence_file", "")
    hold = load(Path(hold_name).name) if hold_name else {}
    results = hero("Results and evidence", "Every score below is HOLDOUT-DTI from the shared evaluator, not a leaderboard result.")
    results += '<main class="wrap">' + status_banner(status, card)
    results += f'''<section class="section"><h2>HOLDOUT-DTI results</h2><p>Evaluator <code>{esc(hd.get("evaluator_version", ""))}</code>; alpha=0.2, beta=0.8, 300 m triangular kernel; {esc(hd.get("protocol", ""))}. Withheld positives: {int(hd.get("withheld_positive_count", 0)):,}. 95% CI from 4,000 resamples of the five fold DTI values.</p>'''
    if hold:
        arms_order = ["random", "ridge_only", "ridge_x_dim", "ridge_x_agree", "tensor_full", "flank_only", "tensor_flank"]
        labels = {
            "random": "Uniform random control (all-registry-budgeted matched null)",
            "ridge_only": "Ridge only (budgeted)",
            "ridge_x_dim": "Ridge × dimensionality (budgeted)",
            "ridge_x_agree": "Ridge × strike agreement (budgeted; lane best surface)",
            "tensor_full": "Full tensor lane (budgeted)",
            "flank_only": "Off-catalogue flank prior alone (budgeted; diagnostic)",
            "tensor_flank": "H57-A candidate: tensor × flank (budgeted)",
        }
        results += '<div class="tablewrap"><table class="table"><tr><th>Arm</th><th>HOLDOUT-DTI</th><th>95% CI</th><th>Interpretation</th></tr>'
        for arm in arms_order:
            if arm not in hold:
                continue
            r = hold[arm]
            p = r["pooled"]["dti"]
            c = r["fold_ci95"]
            interp = labels.get(arm, arm)
            if arm == "tensor_flank":
                interp += " — CANDIDATE"
            results += f'<tr><td>{esc(labels.get(arm, arm))}</td><td><b>{p:.5f}</b></td><td>[{c[0]:.5f}, {c[1]:.5f}]</td><td>{esc(interp)}</td></tr>'
        results += "</table></div>"
        can = hold.get("leakage_canary", {})
        if can:
            results += f'''<h2>Leakage canary</h2><p>Maximum single-feature AUC was <b>{max(v["auc_mean"] for v in can.values()):.4f}</b>, below the preregistered 0.90 leakage threshold. Per feature: '''
            results += "; ".join(f"{esc(k)} {v['auc_mean']:.3f}" for k, v in sorted(can.items()))
            results += ". This is a diagnostic, not a performance score.</p>"
        st = hold.get("strike_test", {})
        if st:
            results += f'''<h2>Strike diagnostic</h2><p>On the catalogue proxy, {int(st.get("n_withheld_segments", 0))} connected segments were tested ({int(st.get("n_withheld_pixel_samples", 0))} pixel samples): {100 * st.get("frac_within_20deg_withheld", 0):.1f}% within 20° versus {100 * st.get("frac_within_20deg_random", 0):.1f}% for {int(st.get("n_random_ridge_samples", 0))} sampled random-ridge pixels. Diagnostic only, not a score.</p>'''
    results += "</section>"
    duplicate_names = ", ".join(uniq.get("strict_duplicate_raster_names", [])) or "none"
    results += f'''<section class="section"><h2>Format and strict uniqueness audit</h2><p>Primary NaN-outside TIF: <b>{int(val.get("checks_passed", 0))}/{int(val.get("checks_passed", 0)) + int(val.get("checks_failed", 0))} local checks PASS</b>. The zeros-outside diagnostic fails {int(val.get("zeros_variant_checks_failed", 0))} strict check(s): null/NaN exactly outside the template footprint.</p><p>Comparison coverage: {int(uniq.get("comparison_rasters_scanned", 0))}/{int(uniq.get("comparison_rasters_total", 0))} total (62 registry + 4 local historical) rasters; max |surface Spearman| {fmt(uniq.get("max_abs_surface_spearman"), 4)}; max one-sided overlap within 3 px <b>{fmt(uniq.get("max_final_dot_overlap_within_3px", 0), 2)}</b> against the literal 0.70 stop. Verdict: <b>{esc(uniq.get("strict_verdict", ""))}</b>; duplicate rows: <code>{esc(duplicate_names)}</code>. Random-control overlap is diagnostic only and cannot waive the stated threshold.</p><p><b>Download for audit: YES. Submit: NO.</b> Neither a local format pass nor a chance-adjusted comparison clears this candidate.</p></section></main>'''
    (DOCS / "results.html").write_text(page("Results", results))

    # ---- hypotheses ----------------------------------------------------------
    hypotheses_md = (DOCS / "hypotheses.md").read_text()
    hyp = hero("Hypotheses before implementation", "Preregistered candidates inside the tensor-dimensionality lane, ranked before any result was seen.")
    hyp += '<main class="wrap"><section class="section"><h2>Preregistered shortlist</h2><div class="md">' + html.escape(hypotheses_md) + '</div></section></main>'
    (DOCS / "hypotheses.html").write_text(page("Hypotheses", hyp))

    # ---- method --------------------------------------------------------------
    method = hero("Method and reproducibility", "A single canonical stack feeds the evaluator, writer, validator, and registry checker. The current artifact is audit-only and fails the strict uniqueness gate.")
    method += f'''<main class="wrap"><section class="section"><h2>H57-A pipeline (negative; audit-only raster)</h2><ol class="list"><li>Use measured competition bands 2 (RTP magnetic) and 13 (isostatic gravity), with the canonical sample footprint. Local payload hashes are pinned through a sibling GitHub bridge; they are not claimed as organizer-authenticated bytes.</li><li>Reuse the one-scale cached stack: nearest-valid fill, robust line-axis leveling, low-pass before mirror-padded FFT derivatives, symmetric 3×3 tensor eigendecomposition, dimensionality, intermediate-eigenvector strike, plunge and magnetic+gravity ridge corroboration. Flight-line striping is hard-masked.</li><li>H57-A multiplies the tensor score by a 15-pixel quadratic flank prior derived only from VISIBLE catalogue faults. The sensitivity run uses the cached tensor factors without the normal six-pixel footprint erosion; this raises FFT boundary-ringing risk.</li><li>The already-completed five-fold holdout used 200 dots (40 per fold), a 3-pixel buffer, exact visible-fault masking and matched mass. It is negative: candidate {fmt(ho)} vs random {fmt(rnd.get("value"))}, ridge×strike {fmt(hold.get("ridge_x_agree", dict()).get("pooled", dict()).get("dti"))}, and full tensor {fmt(hold.get("tensor_full", dict()).get("pooled", dict()).get("dti"))}. Do not rerun the holdout; the three-experiment budget is spent.</li><li>The pre-placement surface scan covered 66/66 comparisons and passed at max |Spearman| {fmt(uniq.get("max_abs_surface_spearman"), 4)}. The final-dot scan also covered 66/66 (62 registry + 4 local historical rasters) and returned <b>DUPLICATE-STOP</b>: one-sided 3-pixel overlap {fmt(uniq.get("max_final_dot_overlap_within_3px"), 2)} exceeds the literal 0.70 limit. Two PARALLEL16 NaN/zeros variants each trigger the stop; the random-control overlap is diagnostic only and does not change the verdict.</li><li>The primary <code>{esc(tif_name)}</code> is NaN outside the footprint and passes {int(val.get("checks_passed", 0))}/{int(val.get("checks_passed", 0)) + int(val.get("checks_failed", 0))} strict local format checks. The <code>{esc(zeros_name)}</code> variant fails the null/NaN outside-footprint check and is diagnostic only.</li><li>Disposition: audit download YES; submit NO. No organizer receipt or score exists, and no weekly slot was used.</li></ol><h2>Recheck the retained artifact (no holdout rerun)</h2><pre>.venv/bin/python scripts/validate_submission.py docs/downloads/{esc(tif_name)}
# Expected to fail: zeros-outside diagnostic violates the strict footprint rule.
.venv/bin/python scripts/validate_submission.py docs/downloads/{esc(zeros_name)}
# Expected exit 2 with DUPLICATE-STOP; the random-control metric is diagnostic only.
.venv/bin/python scripts/verify_unique.py docs/downloads/{esc(tif_name)} \
  --surface data/cache/h57_tensor_flank_surface.tif \
  --additional evidence/historical_artifacts/audit-h55-160k/h55-tensor2d-strikegate-160000dots-20261009T164334Z-zeros.tif \
  --additional evidence/historical_artifacts/h55-tensor2d-strikegate-40000dots-20261009T052235Z-zeros.tif \
  --additional evidence/historical_artifacts/h56-multiscale-tensor-persistence-40000dots-20261009T162812Z-zeros.tif \
  --additional evidence/historical_artifacts/gems55-tensor_full-n16000-sep3-20261009T211747Z-nan.tif \
  --out /tmp/uniqueness_h57_review.json</pre><h2>Important boundaries</h2><p><b>Striping-axis caveat:</b> USGS metadata describes E–W flight lines, but the local spectral and coherence diagnostics do not agree on the observed striping axis. The flight-path payload could not be downloaded here, so the current hard mask is not independently verified as targeting the E–W line direction.</p><p>The official GeoDAWN release includes four acquisition blocks and flight-path archives. This sandbox could read the public catalog entry but could not fetch the non-allowlisted ScienceBase file payloads, so true per-block FFT has not been run. Direct RTP tensor differentiation is a proxy; no explicit magnetization-direction pseudogravity transform is claimed.</p><p>The strict local validator requires NaN exactly outside the footprint: the primary NaN TIF passes, while the zeros variant fails one check. A local pass is not organizer portal clearance. This candidate remains DO NOT SUBMIT because the final-dot uniqueness gate and holdout both fail.</p></section></main>'''
    (DOCS / "method.html").write_text(page("Method", method))

    # ---- sources -------------------------------------------------------------
    sources = hero("Verified sources", "Primary sources are separated from local measurements and user-reported leaderboard claims.")
    sources += '''<main class="wrap"><section class="section"><div class="tablewrap"><table class="table"><tr><th>Source</th><th>What was verified</th><th>Boundary</th></tr><tr><td><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">DrivenData problem description</a></td><td>Task, provided features, DTI formula, alpha/beta, 300 m kernel, and GeoTIFF contract.</td><td>Login-gated tabs (data, submissions) are not reachable from the sandbox.</td></tr><tr><td><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">DrivenData official rules</a></td><td>Competition rules and submission format.</td><td>—</td></tr><tr><td><a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">GEMS prize rules PDF (docs.nlr.gov)</a></td><td>At most three submissions per week for feedback; choose one final submission by the deadline for both prize phases; explain the extent and manner of generative-AI use in the narrative.</td><td>Eligibility and final package must be completed by the registered competitor.</td></tr><tr><td><a href="https://github.com/drivendataorg/gems-prize-reference-solution">Official reference solution</a></td><td>Baseline approach and payload conventions (sentinel encoding).</td><td>—</td></tr><tr><td><a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and">USGS GeoDAWN overview</a></td><td>Four acquisition blocks, E–W flight lines and N–S tie lines, survey specifications, tie-line leveling and micro-leveling.</td><td>True block-local FFT is not implemented.</td></tr><tr><td><a href="https://www.sciencebase.gov/catalog/item/657e1d85d34e23d3533209f7">USGS ScienceBase GeoDAWN release, DOI 10.5066/P93LGLVQ</a></td><td>Public catalog lists flight-path archives (<code>area1_flight_path.zip</code> 32.11 MB, <code>area2_flight_path.zip</code> 291.55 MB), survey outlines, geophysical grids and CC0 rights.</td><td>Catalog page was reachable; binary downloads were not available under this sandbox's outbound host allowlist, so block geometry was not locally verified/aligned.</td></tr><tr><td><a href="https://doi.org/10.1190/1.1442807">Pedersen &amp; Rasmussen (1990), Geophysics</a></td><td>Gradient-tensor dimensionality index; strike from eigenvectors.</td><td>—</td></tr><tr><td><a href="https://doi.org/10.1190/1.3484098">Beiki &amp; Pedersen (2010), Geophysics</a></td><td>Eigenvector source-location methods.</td><td>—</td></tr><tr><td><a href="https://doi.org/10.1190/1.3555343">Beiki, Pedersen &amp; Nazi (2011)</a></td><td>Aeromagnetic pseudogravity extension (conditional on magnetization direction).</td><td>—</td></tr><tr><td><a href="https://pmc.ncbi.nlm.nih.gov/articles/PMC11333590/">Karimi &amp; Kletetschka (2024), Scientific Reports</a></td><td>Open-access dimensionality-invariant discussion.</td><td>—</td></tr><tr><td><a href="https://epsg.io/32611">EPSG:32611</a></td><td>CRS definition (UTM zone 11N).</td><td>—</td></tr><tr><td><a href="https://en.wikipedia.org/wiki/Tversky_index">Tversky index</a></td><td>Metric background.</td><td>The official formula is the problem-description transcription in <code>src/gems55/dti55.py</code>.</td></tr><tr><td><a href="anchor-0.2778.html">Reported 0.2778 / H33 attribution</a></td><td>The owner-maintained H33 manifest has no receipt and labels 0.2747 as projected; no verified mapping ties the public 0.2778 row to H33. Earlier local anchor-proxy DTI and causal conclusions are withdrawn under the corrected metric.</td><td>No submission-page receipt or verified file/account mapping; local proxy analysis is not a score.</td></tr></table></div></section></main>'''
    (DOCS / "sources.html").write_text(page("Sources", sources))

    # ---- irregularities ------------------------------------------------------
    irr = hero("Irregularities and review flags", "These are explicit blockers or caveats, not hidden assumptions.")
    irr += '''<main class="wrap"><section class="section"><ol class="list"><li><b>No organizer submission receipt is available.</b> A saved public-page leaderboard snapshot lists 0.2778, 0.3195, 0.3774, and other values, but it is not a submission-page receipt and does not tie a score to a raster hash. Treat all such rows as PUBLIC-LEADERBOARD only until receipt-backed. The public 0.2778 entry is not tied by a receipt or verified mapping to H33; the separate 0.2747 owner-manifest value is labelled projected. Earlier anchor-proxy conclusions are withdrawn (IR-55-051; <a href="anchor-0.2778.html">corrected analysis</a>).</li><li><b>Dense lattice constrains unique submission size (IR-55-035).</b> The spacing-5 lattice raster covers about 99.87% of the footprint within a 3-pixel Euclidean distance. No registry row is excluded. The final H57 map has 200 dots; the expanded 66-raster scan returns 0.76 overlap against two PARALLEL16 NaN/zeros variants, exceeding the literal 0.70 stop. No registry row is excluded; random-control similarity is diagnostic only.</li><li><b>Registry random-control metric fixed (IR-55-036).</b> The earlier control used a 4-connected dilation, not the gate's Euclidean distance. <code>verify_unique.py</code> now uses the same Euclidean <=3 px distance-transform mask for both observed and random-control overlap.</li><li><b>Registry geometry alignment (IR-55-039).</b> One prior raster has the competition shape and CRS but an incorrect origin (500000, 4500000). It is reprojected to the official template with nearest-neighbor resampling before uniqueness scoring. The holdout budgeted 56 rows; the later strict uniqueness audit scanned all 62 current registry rasters.</li><li><b>Holdout correction.</b> The evaluator is the required whole-segment hide-and-recover design (five seeded segment/lattice folds, 3 px buffer, per-fold visible-fault masking, pooled DTI). The historical quadrant evaluator is retired.</li><li><b>H57 holdout/write alignment (IR-55-037).</b> This H57 candidate uses the same hard striping mask, un-eroded tensor-factor sensitivity surface, visible-catalogue flank prior, min-sep, 56-row registry budget at holdout time, and total dot mass in the holdout evaluator and writer. The five holdout folds receive 40 dots each. All arms were mass-matched. Earlier archived experiments had mismatches and are not used for this verdict.</li><li><b>Data provenance.</b> The competition rasters are absent from the current checkout, so no current payload pin check or data download was performed. Historical owner-mirror hash matches are secondary integrity evidence only, not organizer provenance. The DrivenData data tab is login-gated here; do not redistribute mirror payloads.</li><li><b>Acquisition blocks.</b> USGS documents four blocks and publicly lists area1/area2 flight-path archives (32.11 MB / 291.55 MB) in the CC0 ScienceBase release. The catalog is reachable, but binary payload downloads are blocked by this sandbox's outbound host allowlist; true block-separated FFT processing is not claimed.</li><li><b>Pseudogravity wording.</b> The direct RTP tensor is a constrained proxy; the full magnetic-to-pseudogravity transform needs an explicit magnetization-direction convention and remains unimplemented (H57-E/H5 blocked).</li><li><b>Strict outside-footprint encoding (IR-55-049).</b> The NaN-outside primary passes 11/11 strict local checks. The all-finite <code>-zeros.tif</code> diagnostic passes 10/11 and fails the exact null/NaN outside-footprint check. The local format pass is not organizer clearance; H57 remains DO NOT SUBMIT because uniqueness and holdout fail.</li><li><b>Feature-file naming (IR-55-034).</b> The active downloader and preparation check use the canonical <code>gems-geodawn-numerical-features.tif</code> path from <code>src/gems55/io55.py</code>. A legacy <code>training_features.tif</code> alias alone is not sufficient for the cached pipeline. The optional mirror downloader remains disabled unless explicitly opted into and does not establish organizer provenance.</li><li><b>Generative-AI disclosure (IR-55-045).</b> The September 2026 rules require describing generative-AI use, its extent and contribution in any prize narrative. This repo used an AI coding/research agent; disclose that accurately in a future package.</li><li><b>Final selection and eligibility (IR-55-046).</b> Up to three weekly feedback submissions are allowed, but one final submission must be selected by the deadline for both prize phases. Eligibility and final certifications belong to the registered competitor; this agent did not submit or certify.</li><li><b>Expanded strict uniqueness audit (IR-55-048).</b> The final comparison covers all 62 registry rasters plus four local historical TIFs (66/66). Max one-sided 3-pixel overlap is 0.76, above the literal 0.70 limit, against both NaN/zeros PARALLEL16 variants. Both rows count; chance-adjusted/control similarity cannot waive DUPLICATE-STOP. Expanded final max surface |Spearman| is 0.245 (pre-placement report 0.2443), both below 0.90. No candidate submission is cleared.</li><li><b>Random-control support fix (IR-55-050).</b> The old unbudgeted <code>emit_dots(random=True)</code> path sampled only score-positive pixels. The shared emitter now draws uniformly from the eligible set. H57 used the registry-budgeted emitter for every arm and is unaffected; historical exp8/exp9 control values were not rerun and are not used for the current H57 decision.</li><li><b>IR-55-051 (High; withdrawn). Earlier H33 anchor forensics used a prediction-side kernel sum as TP_w and an invalid count-only DTI denominator. The resulting proxy DTI, hidden-truth-size, ratio, and causal claims are withdrawn and must not be used as scores or promotion evidence. See the corrected formula and receipt boundary on <a href="anchor-0.2778.html">the anchor page</a>.</li></ol></section></main>'''
    (DOCS / "irregularities.html").write_text(page("Irregularities", irr))

    # ---- leaderboard analysis -------------------------------------------------
    leader = hero("Leaderboard claims and the 0.2778 anchor", "A score shown in a sibling report is not an organizer-confirmed receipt.")
    leader += '''<main class="wrap"><section class="section"><p>The saved PUBLIC-LEADERBOARD snapshot lists 0.2778 at rank 17 under <code>extradr19</code>, but there is no submission-page receipt or verified file/account mapping tying that row to H33. The owner-maintained H33 manifest separately marks its artifact UNSCORED and labels 0.2747 projected. Earlier local anchor-proxy DTI values, hidden-truth-size calculations, and causal explanations were withdrawn because they used the wrong metric algebra; they do not explain any leaderboard value. No claim that a candidate beats a leaderboard entry is supported.</p><p>See the <a href="anchor-0.2778.html">corrected 0.2778/H33 attribution review</a>, the dated <a href="leaderboard-review-20261009.md">leaderboard evidence record</a>, and the official <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">metric definition</a>.</p></section></main>'''
    (DOCS / "leaderboard-analysis.html").write_text(page("Leaderboard analysis", leader))

    # ---- evidence index --------------------------------------------------------
    evidence = hero("Evidence index", "Machine-readable artifacts are kept beside the code so every claim can be rerun or challenged.")
    evidence += '<main class="wrap"><section class="section"><h2>Current H57 review</h2><ul class="list">'
    legacy = []
    for p in sorted(EVID.glob("*.json")):
        if any(k in p.name for k in ("h55", "h56", "holdout_v1", "holdout_baseline", "exp", "runcard", "uniqueness.json", "uniqueness_160000", "uniqueness_h56", "anchor", "striping", "submission_h5", "exploratory_invalid")):
            legacy.append(p)
            continue
        evidence += f'<li><a href="../evidence/{html.escape(p.name)}"><code>{html.escape(p.name)}</code></a></li>'
    evidence += '</ul><h2>Historical / retired artifacts</h2><p class="small">These files are retained for audit provenance only. They are not the current candidate, are not submission receipts, and must not be read as current H57 results.</p><ul class="list">'
    for p in legacy:
        evidence += f'<li><span class="tag amber">ARCHIVED</span> <a href="../evidence/{html.escape(p.name)}"><code>{html.escape(p.name)}</code></a></li>'
    evidence += '</ul></section></main>'
    (DOCS / "evidence.html").write_text(page("Evidence", evidence))

    # data_dictionary.html is maintained from the committed, source-backed
    # dictionary page. Do not replace it with a reduced placeholder when data are absent.


if __name__ == "__main__":
    main()
