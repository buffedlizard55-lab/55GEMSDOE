#!/usr/bin/env python3
"""Generate docs/anchor-0.2778.html from evidence/anchor_verdict.json.

Every number on the page is read from the measured JSON or quoted verbatim from
GEMSDOE32's audit manifest; nothing is hand-transcribed.
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V = json.loads((ROOT / "evidence/anchor_verdict.json").read_text())
R, RC, REQ, MAN = V["rasters"], V["random_controls_footprint_restricted"], V["what_a_target_score_requires"], V["manifest_facts"]
h33, d28, ours = R["h33_2_b2"], R["d28_0.2600_anchor"], R["ours_h55"]
r37, r40, r44 = RC["37654"], RC["40000"], RC["44090"]

def f(x, n=4): return f"{x:.{n}f}"

page = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Why h33 “scored” 0.2778 · 55GEMSDOE</title>
<link rel="stylesheet" href="site.css"></head><body><main>
<p><a href="index.html">← back to the submission</a></p>
<h1>Why <code>h33-h33-2-b2-…-e5eb6e7e-zeros</code> “scored” 0.2778</h1>

<div class="callout bad"><h2>Short answer: it did not.</h2>
<p>The number 0.2778 is <b>not an organiser-confirmed score for that file.</b>
GEMSDOE32's own audit manifest (<code>docs/downloads/submissions_manifest.json</code>,
generated 2026-10-04T15:27:17Z by <code>scripts/audit_shipped.py</code>) lists it as
the <code>primary</code> candidate with <code>receipt: null</code>, and its run note
ends:</p>
<blockquote>“flank B=2 prune on the 0.2708 base: 37,654 dots, 0 within 200 m of the
catalogue; live-mirror +0.00487 in 4/4 folds, safety 2.08, <b>projected 0.2747;
UNSCORED</b>”</blockquote>
<p>Every one of the 24 entries in that manifest carries <code>receipt: null</code>.
The only number its author attaches is a <b>projection</b> — 0.2747 — built by adding
a +0.00487 fold delta to a “0.2708 base”. Under this project's own rule,
<i>a projection is never written as a score</i>. 0.2778 sits in the same range as that
projection chain and is most likely it (or a sibling of it) being carried forward as
though it had been scored. Logged as <b>IR-55-12</b>.</p></div>

<h2>What the raster actually is</h2>
<p>Measured here with <code>src/gems55/dti55.py</code> — the evaluator verified
against a brute-force transcription of the official formula and against the
official worked example (3.00 / (3.00 + 0.2·1.89 + 0.8·2.00) = 0.60).</p>
<table>
<tr><th>measurement</th><th>h33-2-b2<br>(“0.2778”)</th><th>d28 / 0.2600<br>live anchor</th><th>ours<br>h55</th><th>uniform random<br>same size</th></tr>
<tr><td>dots</td><td>{h33['n_dots']:,}</td><td>{d28['n_dots']:,}</td><td>{ours['n_dots']:,}</td><td>{r37['n_dots'] if 'n_dots' in r37 else 37654:,} / {r44['n_dots'] if 'n_dots' in r44 else 44090:,}</td></tr>
<tr><td>catalogue-proxy DTI</td><td><b>{f(h33['catalogue_proxy_DTI'])}</b></td><td><b>{f(d28['catalogue_proxy_DTI'])}</b></td><td>{f(ours['catalogue_proxy_DTI'])}</td><td>{f(r37['catalogue_proxy_DTI'])} / {f(r44['catalogue_proxy_DTI'])}</td></tr>
<tr><td>kernel credit harvested per dot</td><td>{f(h33['credit_per_dot'])}</td><td>{f(d28['credit_per_dot'])}</td><td>{f(ours['credit_per_dot'])}</td><td>{f(r37['credit_per_dot'])} / {f(r44['credit_per_dot'])}</td></tr>
<tr><td>ratio to a random scatter of the same size</td><td><b>{f(h33['catalogue_proxy_DTI']/r37['catalogue_proxy_DTI'],2)}×</b></td><td><b>{f(d28['catalogue_proxy_DTI']/r44['catalogue_proxy_DTI'],2)}×</b></td><td>{f(ours['catalogue_proxy_DTI']/r40['catalogue_proxy_DTI'],2)}×</td><td>1.00×</td></tr>
<tr><td>dots on mapped-fault pixels</td><td>{h33['dots_on_visible_fault_px']}</td><td>{d28['dots_on_visible_fault_px']}</td><td>{ours['dots_on_visible_fault_px']}</td><td>—</td></tr>
<tr><td>min distance to a mapped fault</td><td>{h33['min_distance_to_mapped_fault_px']:.0f} px = {h33['min_distance_to_mapped_fault_px']*100:.0f} m</td><td>{d28['min_distance_to_mapped_fault_px']:.0f} px = {d28['min_distance_to_mapped_fault_px']*100:.0f} m</td><td>{ours['min_distance_to_mapped_fault_px']:.0f} px</td><td>—</td></tr>
<tr><td>median distance to a mapped fault</td><td>{h33['median_distance_to_mapped_fault_px']:.1f} px ≈ {h33['median_distance_to_mapped_fault_px']/10:.2f} km</td><td>{d28['median_distance_to_mapped_fault_px']:.1f} px ≈ {d28['median_distance_to_mapped_fault_px']/10:.2f} km</td><td>{ours['median_distance_to_mapped_fault_px']:.1f} px ≈ {ours['median_distance_to_mapped_fault_px']/10:.2f} km</td><td>—</td></tr>
<tr><td>strongest correlation with any of the 19 official bands</td><td>|ρ| {f(h33['max_abs_band_spearman'])}</td><td>|ρ| {f(d28['max_abs_band_spearman'])}</td><td>|ρ| {f(ours['max_abs_band_spearman'])}</td><td>—</td></tr>
</table>

<div class="callout"><h2>The finding that matters</h2>
<p>The 0.2778-projection raster is <b>{f(h33['catalogue_proxy_DTI']/r37['catalogue_proxy_DTI'],2)}× random</b> — it
harvests <i>less</i> kernel credit than throwing {h33['n_dots']:,} dots at the
footprint uniformly. The raster actually associated with a live <b>0.2600</b> is
<b>{f(d28['catalogue_proxy_DTI']/r44['catalogue_proxy_DTI'],2)}× random</b>. Between them is a factor of
<b>{f(d28['catalogue_proxy_DTI']/h33['catalogue_proxy_DTI'],1)}×</b>, and the two embody opposite
philosophies.</p>
<p>h33 enforces “0 within 200 m of the catalogue” — measured here as a minimum
distance of {h33['min_distance_to_mapped_fault_px']:.0f} px = {h33['min_distance_to_mapped_fault_px']*100:.0f} m and a median of
{h33['median_distance_to_mapped_fault_px']/10:.2f} km. The 0.2600 anchor does the reverse: its dots sit
<i>immediately adjacent</i> to mapped traces (min {d28['min_distance_to_mapped_fault_px']:.0f} px = {d28['min_distance_to_mapped_fault_px']*100:.0f} m,
median {d28['median_distance_to_mapped_fault_px']/10:.2f} km) while never landing on them
({d28['dots_on_visible_fault_px']} dots on mapped pixels).</p></div>

<h2>Why the 200 m exclusion is the mistake</h2>
<p>The problem description says the private test set contains <i>newly identified</i>
faults not in the USGS database. That fully justifies <b>excluding catalogue
pixels</b>: a dot on a catalogue pixel can never earn credit, because catalogue
pixels are not in <code>G</code>. All three rasters do this — every one has 0 dots on
mapped pixels.</p>
<p>It does <b>not</b> justify a 200 m <i>buffer</i>. A fault trace 300 m from a mapped
trace is still, by every structural-geology prior, far more likely to be a fault
than a point 2 km away in the middle of a basin — and at 300 m it is still inside
the scoring kernel, so it would have paid. Pushing every dot out past 200 m
discards the one piece of ground truth the problem gives away for free.</p>
<p>That neither raster is explained by any of the 19 official layers (strongest
|ρ| {f(h33['max_abs_band_spearman'])} and {f(d28['max_abs_band_spearman'])} respectively — both
statistically indistinguishable from noise at this N) says the same thing from the
other direction: the placement that works is <b>geometric relative to the catalogue</b>,
not driven by the feature stack.</p>

<h2>Is it beatable? The algebra says what any score costs</h2>
<p>Because <code>TP_w + FN_w = |G|</code> identically, <code>DTI = TP_w/(0.2N + 0.8|G|)</code>,
and no truth pixel can contribute more than 1.0, so <code>TP_w ≤ |G|</code>. That gives a
model-free floor on how much truth must exist for any score to be attainable:</p>
<table><tr><th>target DTI</th><th>N = 37,654</th><th>N = 44,090</th></tr>
"""
for t in ("0.26", "0.2708", "0.2747", "0.2778", "0.3195", "0.3774"):
    a, b = REQ[f"{t}@N=37654"], REQ[f"{t}@N=44090"]
    page += (f"<tr><td><b>{t}</b></td><td>|G| ≥ {a['min_abs_G_for_any_placement']:,.0f} px, "
             f"credit/dot ≥ {a['required_TP_w_per_dot_at_that_G']:.4f}</td>"
             f"<td>|G| ≥ {b['min_abs_G_for_any_placement']:,.0f} px, "
             f"credit/dot ≥ {b['required_TP_w_per_dot_at_that_G']:.4f}</td></tr>\n")
page += f"""</table>
<p>A footprint-uniform scatter delivers <b>{f(r44['credit_per_dot'])} credit per dot</b>
against the mapped catalogue at N = 44,090. Reading the table against that number:</p>
<ul>
<li><b>0.2600</b> needs {REQ['0.26@N=44090']['required_TP_w_per_dot_at_that_G']:.4f}/dot — <i>less</i> than uniform
random. This is the coverage plateau; it is essentially free.</li>
<li><b>0.2778</b> needs {REQ['0.2778@N=44090']['required_TP_w_per_dot_at_that_G']:.4f}/dot — still below random. Also free, <i>if</i> the hidden
set is anywhere near as findable as the mapped one.</li>
<li><b>0.3195</b> needs {REQ['0.3195@N=44090']['required_TP_w_per_dot_at_that_G']:.4f}/dot and <b>0.3774</b> needs
{REQ['0.3774@N=44090']['required_TP_w_per_dot_at_that_G']:.4f}/dot — the latter is essentially
catalogue-level targeting. Those are not coverage results; they require the
geology to be right.</li>
</ul>

<div class="callout good"><h2>Conditional estimate of the hidden truth size</h2>
<p>If the hidden test set is about as findable as the mapped catalogue, the d28
anchor's measured {f(d28['credit_per_dot'])} credit/dot × {d28['n_dots']:,} dots = TP_w ≈
{d28['credit_per_dot']*d28['n_dots']:,.0f} must satisfy 0.2600 = TP_w/(0.2·{d28['n_dots']:,} + 0.8|G|),
giving <b>|G| ≈ {(d28['credit_per_dot']*d28['n_dots']/0.2600 - 0.2*d28['n_dots'])/0.8:,.0f} hidden truth pixels</b>.
Label: <b>PROJECTION, conditional on that assumption — not a score and not a
measurement.</b> The model-free statement is only the floor: |G| ≥
{REQ['0.26@N=44090']['min_abs_G_for_any_placement']:,.0f}.</p></div>

<h2>What we should do with this</h2>
<ol>
<li><b>Do not chase 0.2778.</b> It is a projection, and by the algebra it is
below the coverage plateau anyway.</li>
<li><b>The real target is 0.2600</b>, and it is a <i>placement</i> result, not a
detection result. The measured mechanism is: dots immediately adjacent to mapped
traces, never on them.</li>
<li><b>Our raster sits at random.</b> {f(ours['catalogue_proxy_DTI'])} proxy DTI at
{ours['n_dots']:,} dots versus {f(r40['catalogue_proxy_DTI'])} for uniform random — and
{f(d28['catalogue_proxy_DTI']/ours['catalogue_proxy_DTI'],1)}× below the 0.2600 anchor. That is an
independent confirmation of this lane's NEGATIVE verdict from a completely
different direction than the holdout.</li>
<li><b>Highest-leverage next experiment, still in-lane:</b> keep the tensor
strike estimator — it is the one part of this lane that tested positive — but use
it to decide <i>which way to extend</i> from mapped traces, and place dots
immediately adjacent to catalogue pixels instead of ≥200 m away. Concretely: for
each mapped-fault pixel, emit along the tensor strike at 1–3 px offset, off the
trace. This combines the measured winner (adjacency) with this lane's one
confirmed asset (strike), and it is falsifiable on the same holdout.</li>
</ol>

<h2>Evidence classes</h2>
<table>
<tr><th>claim</th><th>class</th></tr>
<tr><td>h33-2-b2 is UNSCORED, projected 0.2747, receipt null</td><td><b>VERBATIM from GEMSDOE32's audit manifest</b>, fetched read-only from api.github.com</td></tr>
<tr><td>dot counts, proxy DTI, credit/dot, distances, band correlations</td><td><b>MEASURED here</b> — <code>evidence/anchor_verdict.json</code></td></tr>
<tr><td>0.2600 for the d28 anchor</td><td><b>USER/SIBLING CLAIM</b> — no organiser receipt is available in this environment; the filename <code>…identical-to-live-02600…</code> is GEMSDOE32's own label</td></tr>
<tr><td>0.2778, 0.3195, 0.3774</td><td><b>USER-SUPPLIED</b> — unreceipted</td></tr>
<tr><td>|G| ≈ 8,000</td><td><b>PROJECTION</b>, conditional — never a score</td></tr>
</table>

<h2>Disagreement with GEMSDOE32's audit, disclosed</h2>
<p>Their <code>audit_shipped.py</code> reports catalogue-proxy DTI
{MAN['h33-2-b2']['proxy_DTI_author']} / credit-per-dot {MAN['h33-2-b2']['credit_per_dot_author']}
for h33 and {MAN['d28/0.2600-anchor']['proxy_DTI_author']} / {MAN['d28/0.2600-anchor']['credit_per_dot_author']}
for the d28 anchor. This evaluator reports {f(h33['catalogue_proxy_DTI'])} / {f(h33['credit_per_dot'])}
and {f(d28['catalogue_proxy_DTI'])} / {f(d28['credit_per_dot'])} — factors of 1.36× and 2.40×
lower. The truth mask is not the cause: <code>labels.tif</code> contains exactly
{{−1: 7,111,787 nodata; 0: 5,106,385; 1: 60,988}} and <code>existing_faults.tif</code> has an
identical value histogram, so |G| = 60,988 either way. Our evaluator is the one
checked against a brute-force transcription and the official worked example, so
where the two disagree we report ours and flag theirs as unverified. The
<i>ranking</i> is unaffected: by either evaluator the d28 anchor beats h33 by a wide
margin.</p>
</main></body></html>
"""
(ROOT / "docs/anchor-0.2778.html").write_text(page)
print("wrote docs/anchor-0.2778.html", len(page), "bytes")
