#!/usr/bin/env python3
"""Build the auditable GitHub Pages site from the current run card/evidence.

The page is intentionally fail-closed: format-valid does not become
submit-cleared when the strict registry gate or the holdout promotion gate fails.
No leaderboard value is inferred from a local holdout.
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
TIF = "h56-multiscale-tensor-persistence-40000dots-20261009T162812Z-zeros.tif"
ZIP = "h56-multiscale-tensor-persistence-40000dots-20261009T162812Z-zeros.zip"
NAN = "h56-multiscale-tensor-persistence-40000dots-20261009T162812Z-nan.tif"
NOTE = "tensor-dim lane: FFT grad-tensor RTP-mag+iso-grav, 2-D/strike-gated ridges, 40000 dots"

CSS = """
:root{--ink:#14271f;--muted:#5a6b62;--paper:#f5f7f2;--card:#fff;--line:#dce5dc;--green:#176747;--green2:#e5f3ea;--red:#9e332d;--redbg:#fff0ed;--amber:#8d5a10;--amberbg:#fff7e7;--shadow:0 12px 35px rgba(20,39,31,.08)}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.62 system-ui,-apple-system,Segoe UI,sans-serif}a{color:#126244;text-underline-offset:3px}a:hover{color:#093e2a}a:focus-visible{outline:3px solid #d7962d;outline-offset:3px}.wrap{max-width:1120px;margin:0 auto;padding:0 24px}.top{background:#10271e;color:#e8f3eb}.topin{min-height:70px;display:flex;align-items:center;justify-content:space-between;gap:20px}.brand{color:#fff;text-decoration:none;font-weight:800;font-size:19px}.nav{display:flex;gap:15px;flex-wrap:wrap}.nav a{color:#d5e7da;text-decoration:none;font-size:14px}.hero{padding:58px 0 38px;background:linear-gradient(140deg,#edf5ee,#f5f7f2 65%,#e9f0e8);border-bottom:1px solid var(--line)}.eyebrow{font-size:12px;letter-spacing:.13em;text-transform:uppercase;font-weight:800;color:var(--green)}h1,h2,h3{line-height:1.18;letter-spacing:-.03em}h1{font-size:clamp(34px,5vw,54px);margin:12px 0 16px;max-width:850px}h2{font-size:clamp(24px,3vw,32px);margin:0 0 14px}h3{font-size:19px;margin:0 0 9px}.lead{font-size:18px;color:#334b3e;max-width:820px}.section{padding:42px 0}.section+.section{padding-top:10px}.banner{display:flex;gap:14px;padding:19px 21px;margin:22px 0;background:var(--redbg);border:1px solid #efc5bc;border-left:6px solid var(--red);border-radius:14px;box-shadow:var(--shadow)}.banner strong{display:block;color:#79211c;font-size:19px}.banner p{margin:4px 0;color:#633632}.audit{padding:21px;background:var(--amberbg);border:1px solid #ecd9ad;border-radius:14px;margin:22px 0}.audit strong{color:#6e4809}.actions{display:flex;gap:10px;flex-wrap:wrap;margin:18px 0}.button{display:inline-flex;align-items:center;padding:11px 16px;border-radius:9px;background:var(--green);color:#fff;text-decoration:none;font-weight:800}.button.secondary{background:#fff;color:var(--green);border:1px solid var(--green)}.button.warn{background:#8d5a10;color:#fff}.grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px;box-shadow:0 5px 20px rgba(20,39,31,.035)}.card p{color:var(--muted);margin:0}.label{font-size:12px;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);font-weight:800}.value{font-weight:800;font-size:21px;margin-top:6px}.tablewrap{overflow:auto;border:1px solid var(--line);border-radius:12px;background:#fff}.table{border-collapse:collapse;width:100%;min-width:700px}.table th,.table td{text-align:left;padding:11px 13px;border-bottom:1px solid var(--line);vertical-align:top}.table th{background:#edf3ed;font-size:13px}.table tr:last-child td{border-bottom:0}.tag{display:inline-block;padding:3px 9px;border-radius:999px;font-size:12px;font-weight:800;background:var(--green2);color:#28533c}.tag.red{background:#ffe2dc;color:#832d27}.tag.amber{background:#fff0ce;color:#765010}pre,code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace}pre{background:#14221b;color:#e8f3eb;padding:14px;border-radius:9px;overflow:auto;font-size:13px}code{background:#edf2ee;border-radius:4px;padding:2px 5px;font-size:.92em}.small{font-size:13px;color:var(--muted)}.two{display:grid;grid-template-columns:1.2fr .8fr;gap:18px}.list li{margin:8px 0}.footer{background:#10271e;color:#d2e2d7;padding:28px 0;margin-top:30px}.footer a{color:#bde8cf}.md{white-space:pre-wrap;background:#fff;border:1px solid var(--line);border-radius:12px;padding:18px;overflow:auto}@media(max-width:850px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}.two{grid-template-columns:1fr}.topin{align-items:flex-start;flex-direction:column;padding:17px 0}}@media(max-width:520px){.wrap{padding:0 16px}.grid{grid-template-columns:1fr}.hero{padding-top:42px}}
"""

NAV = [
    ("index.html", "Overview"),
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
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)} · 55GEMSDOE</title><style>{CSS}</style></head><body><header class="top"><div class="wrap topin"><a class="brand" href="index.html">55GEMSDOE · tensor lane</a><nav class="nav">{nav}</nav></div></header>{body}<footer class="footer"><div class="wrap"><p>Generated by <code>scripts/build_site.py</code> from committed evidence and the dated public leaderboard snapshot.</p><p>Candidate performance is labelled HOLDOUT-DTI. Organizer-confirmed candidate scores require a submission-page receipt; no such receipt is in this checkout. Public leaderboard observations are separately identified and do not map to a raster.</p></div></footer></body></html>'''


def hero(title: str, subtitle: str, body: str = "") -> str:
    return f'<section class="hero"><div class="wrap"><div class="eyebrow">DOE GEMS · competition 306</div><h1>{title}</h1><p class="lead">{subtitle}</p>{body}</div></section>'


def status_banner() -> str:
    return '''<div class="banner"><div aria-hidden="true">⛔</div><div><strong>NOT CLEARED TO SUBMIT — DUPLICATE-STOP / NEGATIVE HOLDOUT</strong><p>The TIF is downloadable for audit only. The committed prior-run record shows a strict final-dot uniqueness stop and a negative holdout comparison. This checkout lacks the competition inputs/cache and registry rasters, so those gates cannot be rerun. Do not spend a DrivenData slot on this file.</p></div></div>'''


def download_box() -> str:
    return f'''<div class="audit"><strong>Audit artifact generated — download only for review</strong><p><code>{TIF}</code></p><div class="actions"><a class="button warn" href="downloads/{TIF}" download>Download audit .tif</a><a class="button secondary" href="downloads/{ZIP}" download>Download .zip</a><a class="button secondary" href="downloads/{NAN}" download>NaN-outside twin</a></div><p class="small">SHA-256: <code>43743afdb030b739465d4754aabd8605bceef49bcc836bee93e9094807d4695f</code><br>Portal note: <code>{NOTE}</code></p></div>'''


def main() -> None:
    card = json.loads((DOCS / "run-card.json").read_text())
    leaderboard = json.loads((EVID / "leaderboard_snapshot_20261009.json").read_text())
    base = load("holdout_baseline_segment_n40000.json")
    h56 = load("holdout_h56_ms300_900_n40000.json")
    grav = load("holdout_h56_gravity_only_n40000.json")
    uniq = load("uniqueness_h56_strict.json")
    out = load("submission_h56-multiscale-tensor-persistence-40000dots-20261009T162812Z.json")

    bbest = base["ridge_x_agree"]; hfull = h56["tensor_full"]; hrandom = h56["random"]
    body = hero("A transparent fault-discovery experiment — not a cleared upload", "Tensor dimensionality tests whether strike-extended potential-field responses can be separated from compact bodies. The current H56 artifact failed the strict registry gate and is explicitly marked DO NOT SUBMIT.")
    body += '<main class="wrap">' + status_banner() + download_box()
    body += f'''<section class="section"><h2>Executive summary</h2><p>The H56 hypothesis was scale persistence: a fault-related response should remain near-2-D and strike-concordant at 300 m and 900 m Gaussian low-pass scales. RTP magnetic band 2 and isostatic gravity band 13 were differentiated by FFT, decomposed into traceless symmetric tensors, and combined by a geometric mean across scales.</p><p>The scientific result is negative for promotion. <b>HOLDOUT-DTI</b> full H56 tensor = <b>{hfull['pooled']['dti']:.5f}</b> with 95% CI [{hfull['fold_ci95'][0]:.5f}, {hfull['fold_ci95'][1]:.5f}], below the one-scale ridge × strike-agreement comparator <b>{bbest['pooled']['dti']:.5f}</b> with 95% CI [{bbest['fold_ci95'][0]:.5f}, {bbest['fold_ci95'][1]:.5f}]. Withheld positives: <b>{hfull['pooled']['n_truth']:,}</b>. The matched random control was **HOLDOUT-DTI** {hrandom['pooled']['dti']:.5f} (95% CI [{hrandom['fold_ci95'][0]:.5f}, {hrandom['fold_ci95'][1]:.5f}]), same evaluator and {hfull['pooled']['n_truth']:,} withheld positives; H56 beats random but not the current same-evaluator best.</p></section>'''
    snap_rank1 = next(r for r in leaderboard["rows"] if r["rank"] == 1)
    snap_rank7 = next(r for r in leaderboard["rows"] if r["rank"] == 7)
    snap_rank16 = next(r for r in leaderboard["rows"] if r["rank"] == 16)
    body += f'''<section class="section"><h2>Public leaderboard snapshot — not an artifact receipt</h2><p>Observed {html.escape(leaderboard['captured_at_utc'])}: rank 1 <b>{snap_rank1['best_public_score']:.4f}</b>, rank 7 <b>{snap_rank7['best_public_score']:.4f}</b>, rank 16 <b>{snap_rank16['best_public_score']:.4f}</b>. The public table does not identify TIFF filenames or hashes; the H33-to-0.2778 mapping is unverified. See the <a href="leaderboard-analysis.html">full analysis</a> and <a href="../evidence/leaderboard_snapshot_20261009.json">dated snapshot JSON</a>.</p><p class="small">The sibling H33 page labels its 0.2747 figure a projection and the candidate UNSCORED. A public leaderboard row is not a submission-page receipt.</p></section>'''
    body += f'''<section class="section"><h2>Four decisions at a glance</h2><div class="grid"><div class="card"><div class="label">File self-check</div><div class="value"><span class="tag">PASS</span></div><p>Current byte-level checks pass: float32, EPSG:32611, 3730×3292, all finite, [0,1], and 40,000 positive cells. The prior template validator recorded <b>12/12 PASS</b> at generation; this checkout lacks the template and labels to rerun the full checks.</p></div><div class="card"><div class="label">Science</div><div class="value"><span class="tag red">NEGATIVE</span></div><p>Prior H56 holdout did not beat the one-scale comparator.</p></div><div class="card"><div class="label">Uniqueness</div><div class="value"><span class="tag red">STOP</span></div><p>Prior strict check stopped: two registry rows exceeded the literal 70% final-dot overlap rule. Registry rasters are not present to rerun it.</p></div><div class="card"><div class="label">Candidate receipt</div><div class="value">None</div><p>No submission-page receipt is present for this TIF.</p></div></div></section>'''
    body += f'''<section class="section"><div class="two"><div><h2>What the metric rewards</h2><p>The official distance-weighted Tversky metric uses alpha 0.2, beta 0.8, and a 300 m triangular kernel. False negatives cost more than false positives, but a local holdout on mapped faults is only a proxy for the organizer's hidden new-fault labels.</p><pre>DTI = TP_w / (TP_w + 0.2 FP_w + 0.8 FN_w)</pre></div><div class="card"><h3>Grid contract</h3><p>{GRID}</p><p class="small">5,167,373 valid footprint pixels · 60,988 mapped catalogue pixels · 40,000 candidate dots.</p></div></div></section>'''
    body += '</main>'
    executive_page = page("Executive summary", body)
    (DOCS / "index.html").write_text(executive_page)
    (DOCS / "executive-summary.html").write_text(executive_page)

    submit = hero("How to enter a submission", "The workflow is documented here so a future cleared artifact is easy to upload. This H56 file is currently blocked; the steps below are not an instruction to submit it.")
    submit += '<main class="wrap">' + status_banner() + download_box() + f'''<section class="section"><h2>Current gate checklist</h2><div class="tablewrap"><table class="table"><tr><th>Gate</th><th>Measured state</th></tr><tr><td>Format validator</td><td><span class="tag amber">PRIOR REPORT PASS</span> 12/12 at generation. This checkout cannot rerun template/label checks: `data/sample_submission.tif` and `data/labels.tif` are absent.</td></tr><tr><td>Continuous surface uniqueness</td><td><span class="tag amber">PRIOR REPORT PASS</span> max absolute Spearman {uniq.get('max_abs_surface_spearman')} vs 56 rasters; registry files absent here.</td></tr><tr><td>Final-dot uniqueness</td><td><span class="tag red">PRIOR REPORT: FAIL / STOP</span> max overlap {uniq.get('max_final_dot_overlap_within_3px')}; threshold 0.70.</td></tr><tr><td>Holdout promotion</td><td><span class="tag red">PRIOR HOLDOUT-DTI: FAIL</span> H56 {hfull['pooled']['dti']:.5f} (95% CI [{hfull['fold_ci95'][0]:.5f}, {hfull['fold_ci95'][1]:.5f}]) vs one-scale {bbest['pooled']['dti']:.5f} (95% CI [{bbest['fold_ci95'][0]:.5f}, {bbest['fold_ci95'][1]:.5f}]); 60,988 withheld positives, evaluator `src/gems55/dti55.py`.</td></tr><tr><td>Organizer receipt</td><td>None. A local validator is not an organizer receipt.</td></tr></table></div></section><section class="section"><h2>When a future file is cleared</h2><ol class="list"><li>Download the file explicitly marked <b>OK TO SUBMIT</b>; use the all-finite <code>-zeros.tif</code> only if the current portal range validator requires it.</li><li>Optionally verify the published SHA-256 and run <code>scripts/validate_submission.py</code> against the authenticated template.</li><li>Sign in to <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">DrivenData competition 306</a>; this repository never stores credentials.</li><li>Upload one single-band GeoTIFF or a zip containing one GeoTIFF. Confirm CRS EPSG:32611, 100 m resolution, bounds, float32 values [0,1], and null/NaN outside as required by the official page.</li><li>Paste the short note recorded in the run card, check the weekly cap, and submit only after the site says the uniqueness and holdout gates passed.</li></ol></section>'''
    submit += '</main>'
    (DOCS / "submit.html").write_text(page("Submission steps", submit))

    results = hero("Results and evidence", "These are committed prior-run local measurements, not a rerun in the current checkout. Every performance score below is HOLDOUT-DTI, not a public leaderboard result.")
    results += '<main class="wrap">' + status_banner() + f'''<section class="section"><h2>HOLDOUT-DTI results</h2><p>Evaluator <code>src/gems55/dti55.py</code>; alpha=0.2, beta=0.8, 300 m kernel; 5 whole-segment/lattice folds with a 3 px buffer; 60,988 withheld positives; 4,000 resamples of fold DTI for the 95% CI.</p><div class="tablewrap"><table class="table"><tr><th>Arm</th><th>HOLDOUT-DTI</th><th>95% CI</th><th>Interpretation</th></tr>'''
    rows = [("Uniform random control", hrandom, "matched null"), ("One-scale ridge × strike agreement", base["ridge_x_agree"], "current comparator"), ("One-scale full tensor", base["tensor_full"], "baseline lane"), ("H56 multiscale full tensor", hfull, "candidate; negative"), ("H56 multiscale ridge-only ablation", h56["ridge_only"], "ablation only"), ("Gravity-only tensor", grav["tensor_full"], "third experiment; negative")]
    for name, row, interp in rows:
        results += f"<tr><td>{name}</td><td><b>{row['pooled']['dti']:.5f}</b></td><td>[{row['fold_ci95'][0]:.5f}, {row['fold_ci95'][1]:.5f}]</td><td>{interp}</td></tr>"
    results += f'''</table></div></section><section class="section"><h2>Leakage canary</h2><p>H56 maximum single-feature AUC was <b>{card['leakage_canary']['max_auc']:.4f}</b>, below the preregistered 0.90 leakage threshold. This is a diagnostic, not a performance score.</p><h2>Strike diagnostic</h2><p>On the H56 catalogue proxy, 273 withheld segments had a 26.0% within-20° match versus 22.4% for sampled random ridges. The mean angular-difference CI was [−12.50°, −7.21°]. Because the ridge/tensor orientation comparison can be geometrically coupled, this is not a promotion gate.</p><h2>Artifacts</h2><ul><li><a href="../evidence/holdout_baseline_segment_n40000.json">baseline evidence JSON</a></li><li><a href="../evidence/holdout_h56_ms300_900_n40000.json">H56 evidence JSON</a></li><li><a href="../evidence/holdout_h56_gravity_only_n40000.json">gravity-only evidence JSON</a></li><li><a href="../evidence/uniqueness_h56_strict.json">strict uniqueness evidence JSON</a></li><li><a href="run-card.json">run card</a> · <a href="status.json">status JSON</a></li></ul></section>'''
    results += '</main>'
    (DOCS / "results.html").write_text(page("Results", results))
    (DOCS / "executive-summary.html").write_text(page("Executive summary", body))

    hypotheses_md = (DOCS / "hypotheses.md").read_text()
    hyp = hero("Preregistered hypotheses and status", "Five distinct tensor-lane candidates were recorded. H56 was the top candidate, was tested without new external data, and did not clear the promotion gates.")
    hyp += '<main class="wrap"><section class="section"><h2>Preregistered shortlist</h2><div class="md">' + html.escape(hypotheses_md) + '</div></section></main>'
    (DOCS / "hypotheses.html").write_text(page("Hypotheses", hyp))

    method = hero("Method and reproducibility", "A single canonical stack feeds the evaluator, writer, validator, and registry checker. The method is designed to fail closed when evidence is missing.")
    method += f'''<main class="wrap"><section class="section"><h2>H56 pipeline</h2><ol class="list"><li>Read official bands 2 (RTP magnetic) and 13 (isostatic gravity) and the sample footprint.</li><li>Nearest-valid fill only for derivative preparation; robust along-track levelling; mirror-padded FFT derivatives after 300 m and 900 m low-pass filters.</li><li>Build the six-component symmetric traceless potential-field tensor, eigenvalues, dimensionality invariant, intermediate-eigenvector strike, ridge tangent, plunge, and coherence-based line mask.</li><li>Geometric-mean the two scale scores; mask mapped catalogue pixels only during holdout/submission emission, never as a feature of the continuous geophysical surface.</li><li>Hold out whole catalogue segments with a buffer, mask visible faults per fold, pool DTI components, and run the leakage canary.</li><li>Write all-finite and NaN-outside comparison GeoTIFFs, re-read bytes, and check surface and final-dot uniqueness.</li></ol><h2>Official geometry</h2><p>{GRID}</p><h2>Key commands</h2><pre>python scripts/prepare_data.py
python scripts/build_lane.py --tag h56_ms300_900 --scales-m 300,900
python scripts/evaluate_holdout.py --tag h56_ms300_900 --n-dots 40000
python scripts/submission_writer.py --tag h56_ms300_900 --n-dots 40000 --seed 5609
python scripts/validate_submission.py docs/downloads/*h56*-zeros.tif
python scripts/verify_unique.py &lt;tif&gt; --surface data/cache/lane_h56_ms300_900.npz</pre><h2>Important boundary</h2><p>The USGS release documents four acquisition blocks, but verified block polygons are not locally aligned to the competition grid. The current implementation must not claim true per-block FFT processing. Likewise, direct RTP tensor differentiation is not silently described as a fully magnetization-assumption-aware pseudogravity transform.</p></section></main>'''
    (DOCS / "method.html").write_text(page("Method", method))

    sources = hero("Verified sources", "Primary sources, dated public leaderboard observations, local holdout measurements, and user-reported artifact claims are kept distinct.")
    sources += '''<main class="wrap"><section class="section"><div class="tablewrap"><table class="table"><tr><th>Source</th><th>What was verified</th><th>Boundary</th></tr><tr><td><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">DrivenData problem description</a></td><td>Task, provided features, DTI formula, alpha/beta, 300 m kernel, and GeoTIFF contract.</td><td>Does not confirm a score for a named artifact.</td></tr><tr><td><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">DrivenData public leaderboard</a></td><td>Rendered ranked table captured 2026-10-09; dated machine-readable snapshot is linked from the leaderboard analysis.</td><td>Rows show participant best-public values, not submission filenames/hashes or a submission-page receipt; no artifact mapping is asserted.</td></tr><tr><td><a href="https://github.com/drivendataorg/gems-prize-reference-solution">Official reference solution</a></td><td>GitHub repository and baseline notebook exist.</td><td>It is a reference, not our holdout evaluator.</td></tr><tr><td><a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and">USGS GeoDAWN overview</a> · <a href="https://www.sciencebase.gov/catalog/item/657e1d85d34e23d3533209f7">ScienceBase release</a></td><td>Survey purpose, four acquisition blocks, flight paths and processing context; DOI 10.5066/P93LGLVQ.</td><td>Exact block polygons are not yet aligned locally.</td></tr><tr><td><a href="https://doi.org/10.1190/1.1442807">Pedersen &amp; Rasmussen 1990</a> · <a href="https://doi.org/10.1190/1.3484098">Beiki &amp; Pedersen 2010</a> · <a href="https://doi.org/10.1190/1.3555343">Beiki et al. 2011</a></td><td>Peer-reviewed tensor dimensionality/eigenvector/pseudogravity references.</td><td>Method literature does not establish fault presence without geological validation.</td></tr><tr><td><a href="https://pmc.ncbi.nlm.nih.gov/articles/PMC11333590/">Open-access Scientific Reports discussion</a></td><td>Explains dimensionality indicator context and its 0–1 interpretation.</td><td>Secondary explanation, not organizer data.</td></tr></table></div></section></main>'''
    (DOCS / "sources.html").write_text(page("Sources", sources))

    irr = hero("Irregularities and review flags", "Current blockers are stated plainly; historical measurements are not presented as fresh checks.")
    irr_md = (DOCS / "irregularities.md").read_text()
    irr += '<main class="wrap"><section class="section"><div class="md">' + html.escape(irr_md) + '</div><p><a href="irregularities.md">Open the complete Markdown register</a>.</p></section></main>'
    (DOCS / "irregularities.html").write_text(page("Irregularities", irr))

    leader = hero("Public leaderboard snapshot and the H33 question", "Dated observations are distinguished from submission-page receipts and artifact attribution.")
    leader_rows = "".join(f"<tr><td>{int(r['rank'])}</td><td>{html.escape(r['participant'])}</td><td>{float(r['best_public_score']):.4f}</td></tr>" for r in leaderboard['rows'])
    leader += f'''<main class="wrap"><section class="section"><p><b>PUBLIC-LEADERBOARD-SNAPSHOT</b>, captured {html.escape(leaderboard['captured_at_utc'])}. This table is an observation of the official public page, not a submission-page receipt; it does not disclose artifact filenames/hashes.</p><div class="tablewrap"><table class="table"><tr><th>Rank</th><th>Participant</th><th>Best public score shown</th></tr>{leader_rows}</table></div><p>At capture, the displayed leader is 0.3774 (rank 1), 0.3195 is rank 7, and 0.2778 is rank 16. The H33-to-0.2778 attribution remains unverified: the <a href="https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html">GEMSDOE32 page</a> calls its H33 candidate “UNSCORED” and its 0.2747 value a projection, while the leaderboard does not name files. See the <a href="anchor-0.2778.html">full H33 review</a> and <a href="../evidence/leaderboard_snapshot_20261009.json">machine-readable snapshot</a>.</p><p>The official <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">metric definition</a> uses a 300 m triangular kernel, α=0.2 and β=0.8. This makes nearby predictions partly creditable and weighs false negatives more than false positives, but these properties alone cannot identify the cause of a hidden-test score.</p><p><b>Correction:</b> historical anchor proxy-DTI values were retracted because their code assumed TP_w + FP_w = N. This is not generally valid under the official metric. See IR-55-034.</p></section></main>'''
    (DOCS / "leaderboard-analysis.html").write_text(page("Leaderboard analysis", leader))

    evidence = hero("Evidence index", "Current H56 evidence is separated from historical or retracted records so audit files are not mistaken for current results.")
    evidence += '<main class="wrap"><section class="section"><h2>Current H56 review artifacts</h2><ul class="list">'
    current_evidence = {
        "holdout_baseline_segment_n40000.json",
        "holdout_h56_ms300_900_n40000.json",
        "holdout_h56_gravity_only_n40000.json",
        "uniqueness_h56_strict.json",
        "submission_h56-multiscale-tensor-persistence-40000dots-20261009T162812Z.json",
        "leaderboard_snapshot_20261009.json",
    }
    legacy = []
    for p in sorted(EVID.glob("*.json")):
        if p.name not in current_evidence:
            legacy.append(p)
            continue
        evidence += f'<li><a href="../evidence/{html.escape(p.name)}"><code>{html.escape(p.name)}</code></a></li>'
    evidence += '</ul><h2>Historical / retired / retracted artifacts</h2><p class="small">These files are retained for provenance only. They are not current H56 holdout results or submission receipts. The anchor-forensics JSON files are explicitly retracted under IR-55-034; older experimental arms are historical audit material and must not be substituted for the current canonical holdout.</p><ul class="list">'
    for p in legacy:
        evidence += f'<li><span class="tag amber">ARCHIVED</span> <a href="../evidence/{html.escape(p.name)}"><code>{html.escape(p.name)}</code></a></li>'
    evidence += '</ul></section></main>'
    (DOCS / "evidence.html").write_text(page("Evidence", evidence))

    # Keep the data dictionary link useful even without redistributing the payload.
    dictionary = hero("Data dictionary", "The competition provides 19 numerical feature bands; payloads are not committed to this repository.")
    dictionary += '<main class="wrap"><section class="section"><p>Band identities used by this lane are band 2, reduced-to-pole magnetic anomaly, and band 13, isostatic gravity anomaly. The complete tag-derived dictionary is generated locally by <code>scripts/build_docs.py</code> after data placement.</p><p><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">Review the official feature description.</a></p></section></main>'
    (DOCS / "data_dictionary.html").write_text(page("Data dictionary", dictionary))


if __name__ == "__main__":
    main()
