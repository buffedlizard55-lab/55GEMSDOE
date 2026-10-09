# 2026-10-09 leaderboard attribution review

**Disposition: no organizer-confirmed score, no explanation of the reported 0.2778, and no evidence that this repository beats a leaderboard entry. No raster was generated, no experiment or data download was performed, and no submission slot was used in this review.** The full promotion state remains `NOT CLEARED — DO NOT DOWNLOAD OR SUBMIT`.

## Evidence classes

- **PUBLIC-LEADERBOARD** means a value transcribed from the public leaderboard page. It is not a submission-page receipt and does not identify a raster hash.
- **ORGANIZER-CONFIRMED** requires an actual submission-page receipt or an official record that identifies the submitted artifact. No such receipt is present for H33 or the comparison values.
- **HOLDOUT-DTI** is a local validation result only when reported with evaluator version, withheld-positive count, and 95% CI. The historical local results are not promotion-grade; see [`docs/results.md`](results.md).
- A projection, owner-maintained manifest entry, or forensic proxy is not an organizer score.

## What can be established about 0.2778

The saved **PUBLIC-LEADERBOARD (not a submission receipt, not ORGANIZER-CONFIRMED)** snapshot at [`evidence/leaderboard_snapshot_20261009.json`](../evidence/leaderboard_snapshot_20261009.json) lists **0.2778** at rank 17 under participant `extradr19`; it also lists **0.3195** at rank 7 and **0.3774** at rank 1. These are properties of the captured public page, not evidence that H33—or any file in this checkout—received those values. The mapping from the owner site name `GEMSDOE32`/H33 to `extradr19` is unverified.

A read-only GitHub API check of the owner-maintained [GEMSDOE32 submissions manifest](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/main/docs/downloads/submissions_manifest.json) reports `receipt: null` for H33, labels it `UNSCORED`, and calls **0.2747** projected. This is secondary owner-generated evidence, not an organizer receipt. No exact H33-to-leaderboard attribution is established.

Consequently, this review cannot say why a submitted file earned 0.2778, whether the captured public entry belongs to H33, or whether a repository candidate can beat that entry. A sparse or near-miss placement mechanism may be a hypothesis suggested by the official distance-weighted metric, but it has not been tied to the identified submission or tested on the hidden target. It is not an explanation or a score.

## Withdrawn anchor forensics

Earlier anchor-proxy DTI, inferred hidden-truth-size, ratio, and causal conclusions relied on a false count-only denominator and a prediction-side kernel sum that is not the official `TP_w`. The corrected identity is documented in [`docs/results.md`](results.md) and [`docs/irregularities.md`](irregularities.md). Those proxy DTI conclusions are **withdrawn, not recalculated, and not used here**. The raw owner-maintained forensic JSON remains only for traceability; it is not promoted evidence.

## Can this lane beat a leaderboard value?

**Not established.** The historical H56 and H55 results are labeled **HOLDOUT-DTI** in [`docs/results.md`](results.md), with their evaluator status, withheld-positive counts, and stored intervals. Their local evaluator is not reconciled with the authorized shared evaluator; the documented fold/interval defects also make them invalid for promotion. The H56 multiscale candidate did not beat its stored same-evaluator comparator. Holdout values and public-leaderboard values are different evidence and must not be compared as if they were on a common scale.

The repository's five ranked tensor-lane hypotheses, required layers, physical signatures, mimics, costs, and official sources are in [`docs/hypotheses.md`](hypotheses.md). They remain proposals; no new geological experiment was implemented or run. The checked-in record says all three experiment slots have been used. The required authorized feature stack, cached evaluator/writer, and registry inputs are absent, and the local implementation is not certified for promotion.

## Download and submission status

There is **no approved downloadable GeoTIFF**. Historical raster variants are retained under `evidence/historical_artifacts/`, outside the published site, for audit traceability only. No current uniqueness pass, authorized-template validation, promotion-grade holdout, or receipt exists; prior raw final-dot reports breach the literal duplicate-stop threshold. Do not download or submit a historical raster, and do not use a weekly slot.

Only after every scientific, leakage, spatial-holdout, uniqueness, and organizer-format gate passes should an operator sign in to the [DOE GEMS competition](https://www.drivendata.org/competitions/306/competition-doe-gems/), upload the exact cleared GeoTIFF, enter the run-card note (at most 140 characters), submit, and preserve the organizer receipt. The current instruction is **NOT CLEARED — DO NOT DOWNLOAD OR SUBMIT**; see [`docs/submit.html`](submit.html).

## Sources and machine-readable records

- [Public leaderboard page](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) — captured snapshot is stored locally; not a submission receipt.
- [Official problem description and metric](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/).
- [Official DrivenData data tab](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) — authorized competition source; login/terms gate.
- [Owner-maintained H33 manifest](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/main/docs/downloads/submissions_manifest.json) — secondary evidence only.
- [`evidence/leaderboard_snapshot_20261009.json`](../evidence/leaderboard_snapshot_20261009.json) — PUBLIC-LEADERBOARD capture with explicit non-receipt label.
- [`docs/run-card-review-20261009.json`](run-card-review-20261009.json) — this review only; no experiment or submission.
- [`docs/run-card.json`](run-card.json) — canonical project run card; null promotion HOLDOUT-DTI and do-not-submit status.
