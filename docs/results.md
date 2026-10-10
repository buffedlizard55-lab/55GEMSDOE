# Results — H57 tensor-flank holdout (negative; audit-only TIF)

**Review date:** 2026-10-10 UTC. Every performance value in this report is
**HOLDOUT-DTI**, not an organizer-confirmed leaderboard score. The NaN-outside
primary is format-valid for audit, but the expanded strict scan returns
**DUPLICATE-STOP** and the candidate loses its matched-mass holdout. It is
**DO NOT SUBMIT**. No weekly slot or organizer submission was used.

## H57-A hypothesis and evaluator

H57-A combines the cached tensor-dimensionality lane (bands 2 RTP magnetic and 13
isostatic gravity) with a 15-pixel quadratic flank prior derived from visible
catalogue faults. A sensitivity option recomputes the same cached tensor formula
without the normal six-pixel footprint erosion, to test feasible edge pixels left
by a spacing-5 registry lattice. This can increase FFT boundary-ringing artifacts;
see `docs/irregularities.md` IR-55-042.

- Canonical evaluator: `src/gems55/dti55.py`, regression-tested against brute
  force and the official worked example.
- Formula: alpha 0.2, beta 0.8, triangular support radius 300 m (3 px at 100 m).
- Five seeded whole-segment/lattice folds, 3 px buffer, visible catalogue mask
  recomputed per fold and masked pixel-exactly; DTI components pooled.
- 200 total binary dots (40 per fold), min separation 3 px. Each candidate,
  comparator and random arm was mass-matched.
- Withheld positives: 60,988. CI: bootstrap of 4,000 resamples of the five fold
  DTI values; it is not an organizer uncertainty interval.

| Arm | HOLDOUT-DTI | 95% CI | Dots | Role |
|---|---:|---:|---:|---|
| Uniform random, registry-budgeted | **0.00015080** | 0.00007391–0.00022214 | 200 | matched null |
| Ridge × strike agreement, registry-budgeted | **0.00027391** | 0.00013244–0.00041048 | 200 | one-scale comparator |
| Full tensor lane, registry-budgeted | **0.00030077** | 0.00017780–0.00042363 | 200 | best same-run arm |
| H57-A tensor × visible-catalogue flank, registry-budgeted | **0.00012284** | 0.00011438–0.00013397 | 200 | candidate; negative |
| Flank prior alone, registry-budgeted | **0.00006088** | 0.00004160–0.00007843 | 200 | diagnostic ablation |

The H57-A candidate loses to random and to both tensor comparators. Its verdict
is **NEGATIVE**; it does not meet the promotion rule, and no weekly slot should be
spent on it. These catalogue holdout values are not predictions of organizer
leaderboard performance.

## Leakage canary and strike diagnostic

All single features were tested against fold-specific withheld positives and
eligible negatives. Maximum AUC was **0.89330**, from the visible-catalogue flank
prior, below the 0.90 canary threshold but close to it. This is a diagnostic, not
an accuracy score; the flank channel is catalogue spatial autocorrelation and the
per-fold prior is built from visible faults only.

Corrected strike diagnostic (IR-55-041): 13 connected withheld components passed
the minimum-size rule, represented by 273 pixel samples. The within-20° match was
26.7% for withheld pixel samples versus 22.2% for 100,000 sampled random-ridge
pixels. This is a catalogue proxy, not a promotion result. The historical JSON
field had called the 273 pixel samples “segments”; the count label is corrected
in the current evidence.

## Registry, format and artifact

- **Pre-placement continuous-surface gate:** PASS-SURFACE-UNIQUE; all 62 shared
  registry rasters plus four archived local historical TIFs were scanned (66/66);
  max absolute Spearman **0.2443** (<0.90).
- **Final-dot gate:** **DUPLICATE-STOP**; all 66 comparisons scanned; max one-sided
  overlap within 3 Euclidean pixels is **0.76** (>0.70). Two PARALLEL16 NaN/zeros
  encodings of the same continuous raster each trigger the literal stop and both
  rows count. Their random-control overlap is 0.765, but control-adjusted similarity
  is diagnostic only. No row is excluded. One registry raster is reprojected to the
  official template before comparison (IR-55-039).
- **TIF validator:** the NaN-outside primary passes **11/11** strict local checks;
  the all-finite `-zeros.tif` diagnostic passes 10/11 and fails exactly the
  null/NaN-outside-footprint check. Both use one float32 band, EPSG:32611,
  3730×3292, 100 m template geometry; the primary has finite in-footprint values
  in [0,1] and no positive on mapped catalogue pixels.
- **Primary audit file:**
  [`downloads/h57-tensor-flank-r15-uneroded-registry56-n200-20261009T200831Z-nan.tif`](downloads/h57-tensor-flank-r15-uneroded-registry56-n200-20261009T200831Z-nan.tif)
- **NaN-outside ZIP:**
  [`downloads/h57-tensor-flank-r15-uneroded-registry56-n200-20261009T200831Z-nan.zip`](downloads/h57-tensor-flank-r15-uneroded-registry56-n200-20261009T200831Z-nan.zip)
- **Primary SHA-256:** `57dd4ba81c6fe553166cb193f4ae40e6547f4abe5a8fdabeb9154f648d761326`
- **Portal note (104/140 chars):** `H57 tensor-flank: FFT 2-D/strike gate x visible-catalogue flank, 200 dots; all-registry overlap-budgeted`
- **Submission decision:** audit download = **YES** (NaN primary only); submit to
  DrivenData = **NO**. Both DUPLICATE-STOP and the negative holdout block this
  raster. No weekly slot, organizer submission, receipt, or confirmed score exists.

## Why the claimed 0.2778 H33 result is not established

The 0.2778 value, 0.3195/0.3774 values, and sibling leaderboard values in the
owner brief are unverified claims. GEMSDOE32's audit manifest (as inspected in
`docs/anchor-0.2778.html`) records the H33 entry with `receipt: null` and calls
0.2747 a projection/UNSCORED. The local measured proxy for the H33 raster is
0.00493 against the mapped catalogue, below the matched uniform-random proxy;
that proxy is not the organizer's hidden-label score. The metric algebra explains
why “could exceed 0.2778” cannot be concluded from this holdout: new hidden-label
coverage is unknown and no receipt verifies the anchor. The current H57 candidate
is demonstrably negative on its own matched catalogue holdout, so there is no
scientific basis to claim it beats the organizer leaderboard.

See [`anchor-0.2778.html`](anchor-0.2778.html),
[`run-card.json`](run-card.json), [`status.json`](status.json), and the machine
readable [`holdout_h57_unique_n200.json`](../evidence/holdout_h57_unique_n200.json).

## Historical comparison

The prior H56 multi-scale tensor-persistence run remains archived in
[`run-card-h56.json`](run-card-h56.json) and `evidence/holdout_h56_ms300_900_n40000.json`.
It was negative versus its one-scale comparator and failed the old literal dot
uniqueness gate before the H57 registry loader began aligning every prior raster.
Do not use H56 results as the current H57 score.
