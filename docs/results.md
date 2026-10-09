# Results and evidence status


<!-- E1-2026-10-09 -->
## E1 experiment (2026-10-09) — tensor lane end-to-end: VALIDATED, submission CLEARED

**Status: CLEARED — OK TO DOWNLOAD AND SUBMIT.** One experiment was run inside the
reopened budget (E1 of 3). The tensor-dimensionality surface was built label-free
from bands 2 (RTP magnetic) and 13 (isostatic gravity), evaluated on a
whole-segment hide-and-recover holdout and on the independent-fault proxy, and
converted into a unique, format-valid GeoTIFF published at
`docs/downloads/h55c-tensor2d-strikegate-48276dots-20261009.tif` (sha256 `ac010413c2031e2b…`).

### E1 HOLDOUT-DTI (whole-segment hide-and-recover; evaluator `gems55.dti55/2.0-local`)

Protocol: 4 folds of whole 8-connected components,
1-px collar around withheld truth, pixel-exact visible-catalogue
masking, no per-fold refit (the surface is label-free by construction), pooled
TP_w/FP_w/FN_w before the ratio; 95% CI = percentile bootstrap over 10 km spatial blocks
of the pooled additive contribution maps. Withheld positives: **60,988**.
Metric: α=0.2, β=0.8, 300 m triangular kernel (R=3 px).

| Policy | HOLDOUT-DTI | 95% CI | TP_w / FP_w / FN_w |
|---|---|---|---|
| dots160k | 0.057024 | [0.054127, 0.059661] | 5040.4 / 192956.5 / 55947.6 |
| dots40k | 0.046198 | [0.043700, 0.048489] | 3751.8 / 158344.6 / 57236.2 |
| random_matched_mass | 0.023545 | [0.021923, 0.025283] | 10727.8 / 2023508.9 / 50260.2 |
| top10pct | 0.014524 | [0.013338, 0.015757] | 6601.3 / 2022062.7 / 54386.7 |
| top20pct | 0.013470 | [0.012457, 0.014517] | 11584.9 / 4044808.8 / 49403.1 |
| continuous | 0.010693 | [0.009890, 0.011498] | 4042.7 / 1642381.8 / 56945.3 |

**The shipped policy (dots160k) beats the matched uniform random control
(0.023545, CI [0.021923, 0.025283]) with disjoint
intervals — a genuine holdout win, not a protocol artifact.** Wide thresholded emissions
lose to sparse top-peak dots on this surface: the metric's per-truth-pixel MAX credit
rewards concentrated mass, and β=0.8's recall pull is already served by the dot
emission's coverage without paying the wide masks' false-positive mass.

### E1 leakage canary

Every product alone vs the catalogue labels (limit AUC 0.90): **PASS_NO_LEAKAGE**
(max AUC 0.5516, product `ridge`).
No product leaks the labels; the surface is a legitimate label-free predictor.

### E1 strike test (lane prompt's prediction test) — NEGATIVE, reported honestly

Claim tested: *withheld faults' strikes should match the field's tensor strike more often than random ridges' do.* Result: withheld faults' strikes match the tensor eigenvector strike within 20° on **5.9%** of withheld pixels (per fold 0.039, 0.054, 0.074, 0.068), while random eligible locations' tensor strike matches their local ridge azimuth on **28.9%** — and the withheld pixels' own ridge-azimuth agreement is also ~29%. The tensor strike therefore does **not** preferentially align with mapped fault strikes (axial chance level is 22%). The holdout DTI win comes from the ridge/dimensionality/striping components, not from strike agreement. The strike gate is retained (it is part of the lane and its `agree` product carries signal, AUC 0.5227), but the lane's headline strike mechanism is **not validated** as a strike predictor.

### E1 PROXY-DTI (independent-fault population; NOT the hidden test labels)

Population: USGS SGMC `SGMC_Structure` code-2 pixels (no training label within 300 m),
61,664 px, sha256-pinned
(`7563e187171f7210…`), source DOI 10.3133/ds1052. This is the
template project's stand-in for the scored "new faults" population; it is mostly
pre-Quaternary bedrock structure and is a conservative stress test (30% of its faults
are approximate/concealed/inferred).

| Policy | PROXY-DTI | coverage | emitted px | matched random |
|---|---|---|---|---|
| dots160k | 0.092434 | 0.089 | 48,276 | 0.084937 |
| top20pct | 0.090561 | 0.367 | 1,021,277 | 0.159489 |
| top30pct | 0.089593 | 0.509 | 1,531,916 | 0.128516 |
| top10pct | 0.083209 | 0.202 | 510,639 | 0.200307 |
| dots40k | 0.077769 | 0.073 | 40,000 | 0.075199 |
| top5pct | 0.069758 | 0.113 | 255,320 | 0.198672 |
| top10pct_dil2px | 0.069696 | 0.362 | 1,386,525 | 0.136117 |
| top20pct_dil2px | 0.068865 | 0.590 | 2,455,175 | 0.095501 |
| top5pct_dil2px | 0.067036 | 0.217 | 768,980 | 0.179425 |
| top10pct_dil4px | 0.065407 | 0.497 | 2,150,446 | 0.104239 |

Baselines: zeros 0.000000 · blanket ones 0.024901 ·
catalogue copy 0.000000 (a catalogue-copy submission earns
nothing on this population, confirming it is not a restatement of the labels).
The shipped dots policy (dots160k, PROXY-DTI 0.092434) beats its matched
random control (0.084937); wide thresholded masks lose to
their matched random controls on this harder population (the surface's ranking skill is
concentrated in its top peaks).

### E1 clearance gates (fresh, this session)

- **Format:** local validator PASS vs the authentic `sample_submission.tif` (single band,
  float32, EPSG:32611, 3730×3292, transform/resolution match, NaN exactly outside the
  footprint, finite [0,1] inside, zero positives on the 60,988 mapped
  catalogue pixels). Not an organizer portal validation.
- **Uniqueness (surface stage, pre-placement):** PASS-UNIQUE — max |Spearman|
  0.0043 over all 56 registry rasters (limit 0.90).
- **Uniqueness (final-dot stage, post-placement):** PASS-UNIQUE — max binding 3-px dot
  overlap 0.6412 (limit 0.70).
  48,169 unit dots after registry-aware de-duplication (IR-55-043).
- **Registry irregularity (IR-55-043):** one registry raster is a full-footprint 5-px lattice
  placeholder whose 3-px dilation covers ≥99% of the footprint; a uniform random control
  scores ~1.000 against it, so the literal dot-overlap rule cannot discriminate any
  submission from noise there. It is reported and excluded from the STOP decision; the
  literal 0.70 threshold is applied to every non-degenerate raster.
- **No ORGANIZER-CONFIRMED score exists.** The portal has not been contacted (no
  credentials); the weekly slot is unused. Promotion to a real slot is a separate selector step.

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

No experiment was run and no new **HOLDOUT-DTI** was produced in this review. The records below were already present on the current `main` history and are included here only so they are not mistaken for new or promotion-grade results. Repository-local utility code has synthetic coverage for whole-component assignment, Euclidean buffering, score-independent random placement, and additive metric terms. It is not certified as the authorized shared evaluator; data-dependent local runners are retired, and the experiment budget is exhausted. Reconcile with the authorized template and explicitly reopen the budget before any future experiment.

## Additional archived holdout records — not promotion-grade

- **HOLDOUT-DTI (historical H56 multiscale full tensor; not promotion-grade):** evaluator `src/gems55/dti55.py` (the original record gives no explicit evaluator version; local implementation is not reconciled with the authorized shared evaluator); **60,988 withheld positives**; α=0.2, β=0.8, 300 m triangular kernel; 40,000 dots. Candidate value **0.01727793270506305**, stored 95% CI **[0.01612827573503906, 0.018468645641252373]**. The matched random control is **0.014404859072739232**, 95% CI **[0.013732983126265159, 0.015374661727613106]**; the one-scale ridge × strike-agreement comparator is **0.018519270698750034**, 95% CI **[0.01782350648872739, 0.019402442229139772]**. The source reports five whole-segment/lattice folds, a 3 px buffer, visible-fault masking, and pooled components, but the intervals resample the five fold DTI values rather than pooled-score contributions. The candidate did not beat the recorded comparator. It is not promotion evidence. Source: `evidence/holdout_h56_ms300_900_n40000.json`.
- **HOLDOUT-DTI (historical H55 exp10 Q4 tensor_full; not promotion-grade):** evaluator `src/gems55/dti55.py` (no explicit version recorded; local and unreconciled); **60,988 withheld positives**; α=0.2, β=0.8, 300 m triangular kernel; 160,000 dots. Recorded candidate value **0.1019**, stored 95% CI **[0.0877, 0.1185]**. The interval is a t interval over four Q4 quadrant-fold DTI values (df=3), not pooled-score contribution uncertainty; quadrants can split connected faults. The final run card does not include a 95% CI for its random control, so that control is not repeated here as a score. This record is not a valid test of the required whole-segment protocol. Source: `evidence/exp10_mass_sweep_v1.json` and `docs/run-card-h55-160k.json`.

These historical values are reported with evaluator/source, withheld-positive count, and stored interval to preserve provenance; their protocol/evaluator limitations disqualify them from promotion. No current valid **HOLDOUT-DTI** exists.

## Score attribution and leaderboard

A saved **PUBLIC-LEADERBOARD snapshot (not a submission-page receipt, not ORGANIZER-CONFIRMED)** lists **0.2778** at rank 16 under `extradr19`, **0.3195** at rank 7, and **0.3774** at rank 1; see `evidence/leaderboard_snapshot_20261009.json`. The snapshot does not identify raster hashes. A read-only check of the owner-maintained GEMSDOE32 artifact manifest reports `receipt: null` for H33, labels it `UNSCORED`, and describes **0.2747** as projected. The mapping from `extradr19` to H33 is unverified; the owner manifest is secondary evidence, not an organizer receipt. Accordingly, this repository cannot establish that H33 received the public rank-16 entry, explain why that entry received its value, or claim that any current candidate beats a leaderboard value.

## Geological and submission conclusions

The tensor-dimensionality lane remains a geologically plausible source-geometry hypothesis, not a validated locator. Existing evidence is insufficient to assert a valid holdout win, an experiment failure under the required protocol, or a submission-slot promotion. Separate historical final-dot reports fail the literal uniqueness rule: H55 40k raw overlap 84.13%, H55 160k 84.01%, and H56 40k maximum overlap 1.000 (with a second row at 0.736), each against a 70% stop limit. These candidate-specific reports are not a fresh scan and must not be combined. Format metadata inspection is partial and not organizer validation. Older E1/E3 registry JSON files report 632 rasters for different candidates and legacy snapshots, so those counts are not a current scan or a substitute for the 56-raster reports. Do not download or submit any archived raster.

See the machine-readable [run card](run-card.json), [source register](sources.md), [hypothesis shortlist](hypotheses.md), and [irregularity log](irregularities.md).
