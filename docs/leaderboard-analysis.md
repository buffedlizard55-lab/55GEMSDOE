# Public leaderboard snapshot and H33 claim review

**Snapshot captured:** 2026-10-09 18:48:54 UTC. **Source:** [official DrivenData public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/). The page displayed a ranked participant table during this review. The table reports each participant's best public score; it does **not** identify the corresponding file name, raster hash, or submission receipt. Therefore this snapshot is not an `ORGANIZER-CONFIRMED` submission-page receipt and does not populate the run card's score ledger. Machine-readable capture: [`evidence/leaderboard_snapshot_20261009.json`](../evidence/leaderboard_snapshot_20261009.json).

## What is verified now

| Public rank | Participant | Best public score shown | Evidence boundary |
|---:|---|---:|---|
| 1 | xiaofanhu | 0.3774 | Public leaderboard observation; file mapping unknown |
| 2 | alexoktaba | 0.3361 | Public leaderboard observation; file mapping unknown |
| 3 | nchuzhoy | 0.3262 | Public leaderboard observation; file mapping unknown |
| 4 | joeyfezster | 0.3260 | Public leaderboard observation; file mapping unknown |
| 5 | kinghorton42 | 0.3222 | Public leaderboard observation; file mapping unknown |
| 6 | Batik Shirt Brothers | 0.3221 | Public leaderboard observation; file mapping unknown |
| 7 | DARD | 0.3195 | Public leaderboard observation; file mapping unknown |
| 16 | extradr19 | 0.2778 | Public leaderboard observation; file mapping unknown |
| 23 | raboush2 | 0.2747 | Public leaderboard observation; file mapping unknown |

This corrects two stale statements in earlier project pages: **0.3195 is not the current public leader in this snapshot**, and an earlier claim that the leaderboard fetch returned only “Loading…” is no longer true for this review. Leaderboard values are time-varying; the file is a dated snapshot, not a live feed.

## Does the public 0.2778 belong to the H33 raster?

**Not established.** The official page shows a 0.2778 best-public row for participant `extradr19` at rank 16, but gives no submission file name or raster hash. The [GEMSDOE32 H33 page](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html) describes `h33-h33-2-b2-20261004T220000Z-e5eb6e7e` as a candidate and quotes a note ending “projected 0.2747; UNSCORED.” Its page also says its local manifest has `receipt: null`. The user-provided association between that raster and 0.2778 may be right, but these sources do not prove it. Do not rewrite the projection as an observed score or attribute the leaderboard row to a file without a matching submission-page receipt or artifact hash.

## What could plausibly produce a high score—and what cannot be inferred

The official [problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) says the hidden initial-round target consists of expert-identified faults absent from the existing public fault catalogue. It scores a distance-weighted Tversky index with a triangular 300 m kernel, `alpha = 0.2`, and `beta = 0.8`. Thus false-positive mass is penalized less than missed positive mass, and a prediction near (not necessarily exactly on) an expert trace can receive partial credit. Sparse, well-placed predictions can therefore be competitive **if** they cover enough of the hidden expert labels without adding too much unsupported mass.

That is a metric-based mechanism, not a diagnosis of H33. The public labels are incomplete and are not the hidden test truth. A local score against known catalogue faults can rank candidate placement rules but cannot show which one discovered the expert-held-out faults. The H33 page's B=2 pruning, 37,654 dots, and 200 m catalogue exclusion are claims about that artifact's construction; they do not establish why the public score was high. The official leaderboard exposes neither the hidden labels nor per-file score history. The responsible answer to “why did it score 0.2778?” is therefore: **the public table contains a 0.2778 row, but the exact raster-to-row mapping and causal mechanism remain unverified.**

The public problem page also describes an expert review and a later round in which submitted predictions may be used to update labels. Public leaderboard optimization and scientific discovery are related but not identical objectives; a high public score alone does not certify that the proposed structures are faults or that they will generalize to the expanded labels.

## Important correction: prior H33 forensics used an invalid shortcut

The official metric is computed from three separately defined quantities:

```text
TP_w = sum over truth pixels of the maximum nearby prediction × triangular weight
FP_w = sum over predicted pixels of prediction × (1 − nearest-truth weight)
FN_w = sum over truth pixels of (1 − maximum nearby prediction × weight)
DTI  = TP_w / (TP_w + 0.2 FP_w + 0.8 FN_w)
```

`TP_w + FN_w = |G|` is an identity. But it does **not** imply `TP_w + FP_w = N`, where `N` is the number/sum of prediction pixels. A single predicted pixel can contribute to multiple nearby truth pixels in `TP_w`; conversely, the per-prediction FP sum is defined independently. Therefore replacing the official denominator with `0.2 N + 0.8 |G|` is not generally valid.

The old `evidence/anchor_forensics.json`, `anchor_mechanism.json`, and `anchor_verdict.json` and the old `anchor-0.2778.html` used that shortcut for catalogue-proxy DTI values and target-score algebra. **Those proxy DTI values, inferred hidden-label sizes, random comparisons, and conclusions that depended on them are retracted.** They are retained only as audit history, not as HOLDOUT-DTI and not as evidence for promotion. The exact metric remains implemented in `src/gems55/dti55.py`; a regression test now demonstrates the mass identity failure on a two-pixel truth example. The same invalid simplification was removed from the old `greedy_cover` rationale; that placement emitter is a heuristic, not an exact DTI optimizer. See `docs/irregularities.md`, IR-55-034.

## What the tensor-lane evidence says

The candidate H56 multiscale tensor surface did not beat its same-evaluator one-scale comparator and failed the literal final-dot uniqueness stop. Its committed result is **HOLDOUT-DTI** `0.01728`, 95% CI `[0.01613, 0.01847]`, evaluator `src/gems55/dti55.py`, 60,988 withheld catalogue positives, five whole-segment/lattice folds; the comparator is **HOLDOUT-DTI** `0.01852`, 95% CI `[0.01782, 0.01940]`, same evaluator and withheld-positive count. Those are local hide-and-recover results, not predictions of the public leaderboard score.

**Can this repo claim a candidate above 0.2778 or 0.3774? No.** The current checkout has no competition feature stack, labels, sample template, cached tensor surface, or registry raster set, so it cannot rerun holdout, final-dot uniqueness, or template-based validation. The stored H56 TIF is available for audit only and is marked **DO NOT SUBMIT**. A new scientifically supported TIF requires restoration of the authorized competition payloads and registry assets, a winning pre-registered holdout result, and a passing strict uniqueness check; no weekly slot should be used before those gates pass.

## Sources for manual review

- [DrivenData problem description and metric](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [DrivenData public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)
- [GEMSDOE32 H33 page](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html) — sibling project, not an organizer receipt
- [Current H56 run card](run-card.json) and [holdout results](results.md)
- [IR-55-034 correction record](irregularities.md#ir-55-034--retracted-anchor-algebra-and-stale-leaderboard-claims)
