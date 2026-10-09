# Results and evidence status

**Current disposition: no valid promotion result; no download or submission is cleared.** This review corrected code/documentation and ran regression tests only. It did not rerun a geological experiment, download competition data, or submit anything. The experiment log records the three-experiment budget as already used.

## Metric algebra correction

The official definitions give `TP_w + FN_w = |G|`, because for each truth pixel the matched-credit maximum and its complement sum to one. Substituting this identity into the distance-weighted Tversky denominator gives

```text
DTI = TP_w / (TP_w + alpha*FP_w + beta*FN_w + eps)
    = TP_w / ((1-beta)*TP_w + alpha*FP_w + beta*|G| + eps)
```

For `alpha=0.2`, `beta=0.8`, the denominator is

```text
0.2*TP_w + 0.2*FP_w + 0.8*|G| + eps
```

It is **not** generally `0.2*N + 0.8*|G|`: `TP_w + FP_w = N` is not an identity. A synthetic regression case in `tests_numeric/test_core.py` has one truth pixel, a unit prediction on it, and a second unit prediction one pixel away. Then `TP_w=1`, `FP_w=1/3`, `FN_w=0`, and the exact DTI is `0.9375`; the invalid count-only formula gives `5/6`. Claims, tables, target-size calculations, and “coverage plateau” conclusions based on the count-only formula are withdrawn.

The old `breakeven_credit` helper also used an incorrect marginal threshold. Its corrected `alpha*DTI` expression is explicitly limited to isolated single-match assumptions; it is not a generic per-dot rule. The greedy coverage routine maximizes a submodular **surrogate** and does not optimize the full DTI ratio because it omits the separate FP term.

## Historical canonical-local HOLDOUT-DTI record — not valid for promotion

- **HOLDOUT-DTI (historical; invalid for promotion)** — evaluator version: unversioned pre-audit `src/gems55/dti55.py` local transcription; withheld-positive count: **60,988**. Tensor-lane pooled value: **0.06670118698244415**; stored fold-bootstrap interval: **[0.05600790445991459, 0.08934589204746593]**.
- **HOLDOUT-DTI random-control record (historical; invalid control)** — same evaluator version, withheld-positive count, and stored interval method. Value: **0.07572925371015232**; stored interval: **[0.05711247628318898, 0.12139421481046019]**. The random branch was filtered by `score > 0` before sampling, so it was not uniform over the eligible domain.
- Both used quadrant folds; a connected mapped fault crossing a quadrant boundary could be split between visible and withheld labels. The stored interval bootstraps four fold DTI values and is not a pooled-DTI confidence interval. These are retained as historical records, not as scientific clearance or an established negative result.

## Separate legacy HOLDOUT-DTI record — not comparable

- **HOLDOUT-DTI (historical; separate private evaluator; not comparable)** — evaluator version `gems.metric v1` (private re-implementation), withheld-positive count **60,594**. E1 ridge baseline **0.0578** (95% CI **[0.0499, 0.0652]**); E2 dimensionality-weighted ridge **0.0463** (95% CI **[0.0398, 0.0523]**); E3 tensor/strike-gated lane **0.0444** (95% CI **[0.0383, 0.0502]**).
- These values came from a different evaluator and fold implementation; they cannot be pooled with or used to “replicate” the canonical-local record. They also do not clear the user-required protocol.

No new **HOLDOUT-DTI** value or confidence interval is reported in this review. Repository-local utility code has synthetic coverage for whole-component assignment, Euclidean buffering, score-independent random placement, and additive metric terms. It is not certified as the authorized shared evaluator; the data-dependent local holdout runner is retired, and there is no budget or authorized feature cache available for another run. Reconcile with the authorized template and explicitly reopen the budget before any future experiment.

## Score attribution and leaderboard

The values **0.2778**, **0.3195**, and **0.3774** are **USER-REPORTED / NOT ORGANIZER-CONFIRMED** in this checkout. No organizer submission-page receipt or official artifact/hash link ties any of them to a TIFF. A read-only check of the owner-maintained GEMSDOE32 artifact manifest reports `receipt: null` for the H33 file and describes that file as `UNSCORED`, with **projected 0.2747**. That secondary manifest does not establish an official score. Accordingly, this repository cannot explain why H33 “scored 0.2778,” nor claim that any current candidate beats a reported leaderboard value.

## Geological and submission conclusions

The tensor-dimensionality lane remains a geologically plausible source-geometry hypothesis, not a validated locator. Existing evidence is insufficient to assert a valid holdout win, an experiment failure under the required protocol, or a submission-slot promotion. The historical raster fails the literal uniqueness rule (see [`docs/status.json`](status.json)); format metadata inspection is partial and not organizer validation. Older E1/E3 registry JSON files report 632 rasters for different candidate files and legacy snapshots, so those counts are not a current scan or a substitute for the 56-raster report. Do not download or submit it.

See the machine-readable [run card](run-card.json), [source register](sources.md), [hypothesis shortlist](hypotheses.md), and [irregularity log](irregularities.md).
