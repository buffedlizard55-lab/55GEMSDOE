#!/usr/bin/env python3
"""Build the H33 / public-leaderboard evidence page without score inference.

Inputs are the dated public leaderboard snapshot and committed H56 run card.
The page deliberately does not load the retracted anchor-forensics metrics.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
SNAPSHOT = ROOT / "evidence" / "leaderboard_snapshot_20261009.json"
CARD = DOCS / "run-card.json"

CSS = """
body{max-width:1100px;margin:2rem auto;padding:0 1rem;font:16px/1.6 system-ui,sans-serif;color:#17251d;background:#f7f8f5}
a{color:#176747}.box{padding:1rem 1.25rem;margin:1rem 0;border-radius:10px;background:#fff;border:1px solid #d8e1d8}.warn{border-left:6px solid #a3342e;background:#fff1ef}.note{border-left:6px solid #936317;background:#fff8e8}table{width:100%;border-collapse:collapse;background:#fff}th,td{text-align:left;padding:.55rem;border-bottom:1px solid #d8e1d8}th{background:#eaf0e9}code,pre{font-family:ui-monospace,monospace}pre{overflow:auto;background:#eef2ed;padding:1rem;border-radius:8px}.tag{font-weight:700}
"""


def main() -> None:
    snapshot = json.loads(SNAPSHOT.read_text())
    card = json.loads(CARD.read_text())
    rows = "\n".join(
        f"<tr><td>{int(r['rank'])}</td><td>{html.escape(r['participant'])}</td>"
        f"<td>{float(r['best_public_score']):.4f}</td><td>{int(r['submission_count'])}</td></tr>"
        for r in snapshot["rows"]
    )
    h = card["holdout_dti"]
    current = h["value"]
    ci_lo, ci_hi = h["ci95"]
    holdout_text = (
        f"<b>HOLDOUT-DTI</b> {current:.5f}, 95% CI [{ci_lo:.5f}, {ci_hi:.5f}], "
        f"evaluator {html.escape(h['evaluator_version'])}, "
        f"{int(h['withheld_positive_count']):,} withheld positives."
    )
    page = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>H33 and the public leaderboard · 55GEMSDOE</title><style>{CSS}</style></head><body>
<p><a href="index.html">← Project overview</a> · <a href="leaderboard-analysis.html">Leaderboard analysis</a></p>
<h1>H33, the 0.2778 row, and what the evidence does—and does not—show</h1>
<div class="box warn"><p class="tag">NO CLEARED NEW SUBMISSION — DO NOT SUBMIT THE AUDIT TIFF</p>
<p>The current H56 raster remains download-for-audit only. The stored evidence says its holdout result is negative and the strict final-dot uniqueness rule stops it. The current checkout is also missing the official template, feature stack, labels, cached tensor surface, and registry rasters, so the full gates cannot be rerun here.</p></div>

<h2>Dated official public leaderboard snapshot</h2>
<p>Captured {html.escape(snapshot['captured_at_utc'])}. This is a public leaderboard observation, <b>not</b> a per-submission receipt. It identifies participants' best public scores but not the submitted raster name or hash. Its evidence class is <code>{html.escape(snapshot['evidence_class'])}</code>.</p>
<div class="box"><table><thead><tr><th>Rank</th><th>Participant</th><th>Best public score shown</th><th>Submission count shown</th></tr></thead><tbody>{rows}</tbody></table></div>
<p>At capture, 0.3774 is rank 1, 0.3195 is rank 7, and 0.2778 is rank 16. This corrects the older 0.3195 “current high” statement. Leaderboard values can change; see the <a href="../evidence/leaderboard_snapshot_20261009.json">machine-readable dated snapshot</a> and the <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">live official page</a>.</p>

<h2>Can the 0.2778 leaderboard row be attributed to the H33 TIF?</h2>
<div class="box note"><p><b>No artifact-to-row mapping is verified.</b> The public leaderboard row names participant <code>extradr19</code> and shows 0.2778, but does not expose the file name or hash. The <a href="https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html">GEMSDOE32 page</a> describes an H33-2-B2 candidate and labels its note “projected 0.2747; UNSCORED”; it also states that no organizer score exists for artifacts in that repository. The two observations cannot be connected without a submission-page receipt or matching artifact hash.</p></div>

<h2>Why a sparse predictor can score well in principle</h2>
<p>The official <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">problem description</a> defines a distance-weighted Tversky metric with a triangular 300 m kernel, α=0.2 and β=0.8. Nearby predictions can receive partial credit; false positives are weighted less than false negatives; hidden labels are expert-identified faults absent from the existing public catalogue. That makes a low-mass, accurately placed candidate plausible. These metric properties explain a possible mechanism, not the cause of any particular leaderboard row.</p>
<pre>DTI = TP_w / (TP_w + 0.2 FP_w + 0.8 FN_w)
TP_w, FP_w, and FN_w are separately defined by the official distance-weighted metric.</pre>
<p>The missing causal evidence matters: public scores use private expert labels; local catalogue holdouts use known faults as a proxy. A high leaderboard score cannot be explained from the public raster alone, and local catalogue overlap cannot verify hidden-fault discovery.</p>

<h2>Correction to prior in-repository anchor forensics</h2>
<p>Historical anchor scripts incorrectly substituted <code>TP_w + FP_w = N</code> after observing the valid identity <code>TP_w + FN_w = |G|</code>. The first identity is not generally true: TP is a maximum taken separately for each truth pixel, while FP is summed separately over predictions. The resulting old catalogue-proxy DTI values, hidden-label-size calculations, and conclusions derived from them are <b>retracted</b>, retained only for audit, and must not guide promotion. See <a href="irregularities.html">IR-55-034</a> and the updated <a href="leaderboard-analysis.md">analysis notes</a>.</p>

<h2>What is recorded in the prior-run H56 card</h2>
<p>The committed card records {holdout_text} It is below the same-evaluator one-scale comparator and does not predict the hidden public leaderboard score. This holdout was not rerun in the present review; no new experiment or submission slot was used. The old H56 TIF is an audit artifact, not a cleared submission.</p>
<p><a href="results.html">Full holdout results</a> · <a href="submit.html">Download/submit status</a> · <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">Official metric and submission format</a></p>
</body></html>'''
    (DOCS / "anchor-0.2778.html").write_text(page)
    print("wrote docs/anchor-0.2778.html", len(page), "bytes")


if __name__ == "__main__":
    main()
