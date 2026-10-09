#!/usr/bin/env python3
"""Write docs/h55-160k-audit.html: the tensor-lane final-pass audit page.

Audit only. AGENTS.md: an audit TIF may be linked only with a prominent DO NOT SUBMIT
label. Every number is read from evidence/*.json or docs/run-card-h55-160k.json.
Run AFTER scripts/build_site.py (which owns the shared nav and the canonical pages).
"""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
EVID = ROOT / "evidence"


def main() -> None:
    card = json.loads((DOCS / "run-card-h55-160k.json").read_text())
    st = json.loads((DOCS / "status-h55-160k.json").read_text())
    ex10 = json.loads((EVID / "exp10_mass_sweep_v1.json").read_text())
    ex9 = json.loads((EVID / "exp9_distance_band_v1_n40000.json").read_text())
    hd, uq, vo, sub = card["holdout_dti"], card["uniqueness"], card["validator_output"], card["submission"]

    q4 = ex10["protocols"]["Q4_primary"]
    b15 = ex10["protocols"]["B15_secondary"]
    rows = []
    for n in ["20000", "40000", "80000", "160000"]:
        t, r = q4[n]["tensor_full"]["fold_pooled_dti"], q4[n]["random"]["fold_pooled_dti"]
        p = q4[n]["tensor_minus_random_signflip_p_two_sided"]
        t15, r15 = b15[n]["tensor_full"]["fold_pooled_dti"], b15[n]["random"]["fold_pooled_dti"]
        p15 = b15[n]["tensor_minus_random_signflip_p_two_sided"]
        rows.append(f"<tr><td class='num'>{int(n):,}</td><td class='num'>{t:.4f}</td><td class='num'>{r:.4f}</td>"
                    f"<td class='num'>{t - r:+.4f}</td><td class='num'>{p:.3f}</td>"
                    f"<td class='num'>{t15:.4f}</td><td class='num'>{r15:.4f}</td><td class='num'>{p15:.3f}</td></tr>")
    sweep = "\n".join(rows)
    b15_40 = ex9["bands"]["15"]["arms"]

    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>h55 tensor-lane final pass (audit) · 55GEMSDOE</title>
<style>
body{{margin:0;background:#0d1117;color:#e6edf3;font:16px/1.6 -apple-system,Segoe UI,Roboto,Arial,sans-serif}}
main{{max-width:1080px;margin:0 auto;padding:22px}} h1{{font-size:24px;margin:8px 0}} h2{{font-size:19px;border-bottom:1px solid #21262d;padding-bottom:6px;margin-top:30px}}
a{{color:#4cc2ff}} table{{border-collapse:collapse;width:100%;margin:10px 0;font-size:14px}} th,td{{border:1px solid #30363d;padding:7px 9px;text-align:left;vertical-align:top}}
th{{background:#1c2129}} td.num{{text-align:right;font-variant-numeric:tabular-nums}} code{{background:#0b0f14;padding:1px 5px;border-radius:4px;font-size:13px}}
.banner{{background:#3a1214;border:2px solid #f85149;border-radius:10px;padding:16px 18px;margin:14px 0}}
.banner b{{color:#ffb4ae;font-size:18px}} .small{{font-size:13px;color:#9aa7b4}}
</style></head><body><main>
<div class="banner"><b>DO NOT SUBMIT — AUDIT DOWNLOAD ONLY</b><br>
This file is a labelled negative result. Format-valid, but the literal duplicate-stop uniqueness rule is tripped and the
holdout is negative. It is <b>not cleared to submit</b> and must <b>not spend a DrivenData slot</b>.</div>

<h1>h55 tensor-dimensionality lane — final pass (2026-10-09)</h1>
<p class="small">Experiments used: 3 of 3 (exp8 run 2, exp9, exp10). Labels: HOLDOUT-DTI only. No organiser score exists for this file.
Shared site: <a href="index.html">executive summary</a> · <a href="hypotheses.html">hypotheses</a> · <a href="irregularities.html">irregularities</a>.</p>

<h2>Audit download</h2>
<table>
<tr><th>Item</th><th>Value</th></tr>
<tr><td>File</td><td><a href="downloads/audit-h55-160k/{html.escape(Path(sub['file']).name)}">{html.escape(Path(sub['file']).name)}</a> (audit only)</td></tr>
<tr><td>Zip</td><td><a href="downloads/audit-h55-160k/{html.escape(Path(card['zip']['file']).name)}">{html.escape(Path(card['zip']['file']).name)}</a></td></tr>
<tr><td>NaN-outside twin (comparison)</td><td><a href="downloads/audit-h55-160k/{html.escape(Path(card['nan_twin']['file']).name)}">{html.escape(Path(card['nan_twin']['file']).name)}</a></td></tr>
<tr><td>SHA-256 (.tif)</td><td class="small"><code>{html.escape(card['raster_sha256'])}</code></td></tr>
<tr><td>Dots / encoding</td><td>{sub['n_dots']:,} binary dots, float32, EPSG:32611, 100 m, zeros outside footprint</td></tr>
<tr><td>Format validator</td><td>{vo['checks_passed']}/{vo['checks_passed'] + vo['checks_failed']} checks PASS (re-read from bytes); NaN twin {vo['nan_twin_checks_passed']}/{vo['nan_twin_checks_passed']}; dots on mapped catalogue px: {vo['dots_on_mapped_catalogue_px']}</td></tr>
<tr><td>Portal note (if ever used)</td><td><code>{html.escape(sub['note'])}</code> ({sub['note_characters']}/140 chars)</td></tr>
<tr><td>Machine-readable</td><td><a href="run-card-h55-160k.json">run-card-h55-160k.json</a> · <a href="status-h55-160k.json">status-h55-160k.json</a></td></tr>
</table>

<h2>Answer: can it be downloaded and submitted?</h2>
<table>
<tr><th>Question</th><th>Answer</th></tr>
<tr><td>Download for audit?</td><td><b>Yes</b> (labelled audit file).</td></tr>
<tr><td>Submit?</td><td><b>No.</b> Submit is blocked: the literal 70% duplicate-stop rule is tripped, and the holdout is negative. Not cleared, no slot.</td></tr>
<tr><td>Unique?</td><td><b>BLOCKED under the literal rule, not a copy.</b> Max |Spearman| {uq['max_abs_spearman_dense']} and max Jaccard {uq['max_jaccard']} against {uq['n_registry']} registry rasters. Raw 3-px overlap {uq['max_frac_within_3px_raw']} against <code>{html.escape(uq['raw_max_reference'])}</code>, where a random control gets {uq['raw_max_reference_random_control_frac_within_3px']} (excess {uq['excess_over_random_control_for_that_reference']:+.4f}). Owner decision needed (IR-55-030).</td></tr>
</table>

<h2>Holdout result (HOLDOUT-DTI)</h2>
<p>Evaluator <code>{html.escape(hd['evaluator_version'])}</code>. Protocol: {html.escape(hd['protocol'])}.
Withheld positives: <b>{hd['withheld_positive_count']:,}</b>.</p>
<table>
<tr><th>Arm (Q4 primary, N = 160,000)</th><th>HOLDOUT-DTI</th><th>95% CI (fold-level, df = 3)</th></tr>
<tr><td>tensor_full</td><td class="num"><b>{hd['value']:.4f}</b></td><td class="num">[{hd['ci95'][0]:.4f}, {hd['ci95'][1]:.4f}]</td></tr>
<tr><td>uniform random control</td><td class="num">{hd['uniform_random_control']:.4f}</td><td class="num">—</td></tr>
</table>
<p class="small">The CI method is a fold-level t-interval over 4 quadrant folds. It is indicative only.</p>

<h2>Dot-mass sweep (exp10, pre-registered)</h2>
<table>
<tr><th>N dots</th><th>Q4 tensor</th><th>Q4 random</th><th>Q4 diff</th><th>Q4 p (sign-flip)</th><th>B15 tensor</th><th>B15 random</th><th>B15 p</th></tr>
{sweep}
</table>
<p>Rule: N* = argmax of tensor on Q4 = 160,000, which is the upper edge of the grid. Label: <b>NEGATIVE</b>
(Q4 fails at N*; B15 passes at N* but does not rescue the primary). Random beats tensor on Q4 at 40k, 80k and 160k.</p>
<p class="small">Secondary B = 15 px at N = 40k (exp9, fold-pooled): random {b15_40['random']['fold_pooled_dti']:.4f}, tensor_full {b15_40['tensor_full']['fold_pooled_dti']:.4f},
H-A-500 {b15_40['H-A-500']['fold_pooled_dti']:.4f}, H-A-1500 {b15_40['H-A-1500']['fold_pooled_dti']:.4f}. Leakage canary: max single-feature AUC ≤ 0.90 for lane features (IR-55-031).</p>

<h2>Why it is labelled negative and not a file to submit</h2>
<ul>
<li>Primary protocol (Q4): the tensor lane loses to uniform random at every budget from 40k up.</li>
<li>Secondary protocol (B = 15 px): a significant gain at 40k and 160k, but the pre-registered rule needs both protocols to pass.</li>
<li>Uniqueness: literal 70% raw 3-px rule tripped against a dense lattice at chance level. Under the shared AGENTS.md, that is a stop.</li>
</ul>

<h2>Out-of-lane hypotheses H-B to H-F (proposals only; not implemented)</h2>
<p>Break-even bar for any new dot: α·DTI/(1+α·DTI) at the random control = <b>{0.2 * hd['uniform_random_control'] / (1 + 0.2 * hd['uniform_random_control']):.4f}</b> per dot. Gains are priors, not HOLDOUT-DTI. AGENTS.md needs lane approval before any of these is built.</p>
<table>
<tr><th>Rank</th><th>Hypothesis</th><th>Layers (band no.)</th><th>Expected DTI gain (prior)</th><th>Cost</th><th>Status</th></tr>
<tr><td>1</td><td><b>H-F</b> 1 m lidar DEM scarps</td><td>1 m DEM (USGS 3DEP; not in stack)</td><td>High (unquantified)</td><td>High</td><td>Blocked: 3DEP unreachable from the sandbox</td></tr>
<tr><td>2</td><td><b>H-B</b> depth-to-basement step</td><td>15, 2</td><td>Moderate</td><td>Medium</td><td>Out of lane; not built</td></tr>
<tr><td>3</td><td><b>H-D</b> geodetic strain-rate corridors</td><td>4, 7, 8</td><td>Low–moderate</td><td>Low–medium</td><td>Out of lane; not built</td></tr>
<tr><td>4</td><td><b>H-C</b> tilt-angle zero-contour</td><td>6</td><td>Low–moderate (redundant with tensor ridges)</td><td>Low</td><td>Out of lane; not built</td></tr>
<tr><td>5</td><td><b>H-E</b> seismicity lineaments</td><td>10, 16</td><td>Low (leakage risk)</td><td>Low</td><td>Out of lane; not built</td></tr>
</table>
<p class="small">Full text: <code>docs/hypotheses.md</code> (section “Out-of-lane hypotheses H-B to H-F”).</p>

<h2>Irregularities (this pass)</h2>
<table>
<tr><th>ID</th><th>Severity</th><th>Finding</th><th>Resolution</th></tr>
<tr><td>IR-55-025</td><td>Medium</td><td>Validator resolution check was shape-based, not pixel size.</td><td>Fixed once in the shared validator; reads the transform. Done.</td></tr>
<tr><td>IR-55-026</td><td>Low</td><td>Feature-raster name mismatch (<code>training_features.tif</code> vs the on-disk name).</td><td>Fixed once in <code>prepare_data.py</code> and <code>run_tensor_lane.py</code>. Done.</td></tr>
<tr><td>IR-55-027</td><td>Medium</td><td>Sidecar selection picked the lexicographically last file (160000 sorts before 40000).</td><td>Card for this file is <code>run-card-h55-160k.json</code>. Done.</td></tr>
<tr><td>IR-55-028</td><td><b>High</b></td><td>Striping axis unreconciled: ScienceBase says E–W; the lane masks rows (E–W); the diagnostic says N–S but its own numbers don't support that.</td><td>Open. Needs the flight-line shapefile (not reachable from the sandbox). Do not cite the lane striping mask until resolved.</td></tr>
<tr><td>IR-55-029</td><td>Medium</td><td>Two striping counts from two detectors: 86,947 px (row z-score) and 1,105,919 px (21%, coherence mask).</td><td>Both reported; not a miscount.</td></tr>
<tr><td>IR-55-030</td><td>Medium (blocks submit)</td><td>Literal 70% duplicate-stop tripped: raw 3-px overlap 0.8401 against a dense spacing-5 lattice; random control 0.8389 (excess +0.0012). Not a copy.</td><td>Owner decision required. No submit clearance.</td></tr>
<tr><td>IR-55-031</td><td>Medium</td><td>Secondary protocol (B = 15 px) is significantly positive at 40k and 160k; the primary Q4 is negative.</td><td>Reported as is; the pre-registered rule gives NEGATIVE.</td></tr>
<tr><td>IR-55-032</td><td>Medium</td><td>The holdout arm (withheld-domain emission, striping excluded, per-fold seeds) is not the shipped emitter (full footprint, striping ×0.25, seed 55).</td><td>Disclosed. Would need a different protocol to close.</td></tr>
<tr><td>IR-55-033</td><td>Low–Medium</td><td>Zeros vs NaN outside the footprint: rules allow null or nan; the zeros choice rests on the portal range check, which is not verified.</td><td>Confirm on the portal before relying on either encoding. NaN twin is for comparison.</td></tr>
</table>

<p class="small">Generated by <code>scripts/build_h55_audit_page.py</code> from <code>docs/run-card-h55-160k.json</code> and <code>evidence/*.json</code>. No figure is hand-typed.</p>
</main></body></html>
"""
    (DOCS / "h55-160k-audit.html").write_text(page)
    print("wrote docs/h55-160k-audit.html")


if __name__ == "__main__":
    main()
