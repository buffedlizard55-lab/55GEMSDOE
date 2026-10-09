# Why the 0.2778 "zeros" entry scored high — and what it means for us

**Entry:** `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` (GEMSDOE32), score **0.2778** as listed by the user.
**Score status:** the 0.2778 value comes from the user's list. **We have no organiser receipt for it.** Treat it as user-reported.

## What the entry actually is (verified from the sibling audit JSON)
Source: [audit file](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/main/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-audit.json).
- Base: "0.2708 base with every dot at d(catalogue) ≤ 2 px deleted", giving **37,654 positive pixels** (value 1.0, all others 0.0).
- Grid: EPSG:32611, 100 m, 3,730 × 3,292, transform (100, 0, 243350, 0, −100, 4508550) — matches our template.
- Dots on the catalogue: 0. Dots within 100 m and 200 m of the catalogue: 0.
- File: `float32`, `zeros` variant, SHA-256 `c55bafc4…6fa9`, 219,065 bytes.
- The audit's own holdout figures (`sgmc_prevalence_calibrated_dti` 0.0641, `drift_corrected_holdout_mean` 0.0450, `ei_drift_corrected` 0.00487) use the sibling's protocol. They are **not** comparable to ours.
- `predicted_leaderboard_dti: 0.2747` is a **projection**, not a score. Its own record says `UNSCORED`.

## Why this kind of entry scores well (reasoning from the official metric)
Metric (verified, [problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)):
DTI = TP_w / (TP_w + 0.2·FP_w + 0.8·FN_w), kernel k(d) = max(1 − d/300 m, 0).

1. **FN is 4× as costly as FP.** Missing a fault costs 0.8, a false dot costs at most 0.2. A sparse set of confident dots can therefore score better than a dense probability map, provided the dots sit within 300 m of real faults.
2. **Binary 1-valued dots maximise credit per dot.** A dot at distance d from a true fault earns k(d) of TP, and costs 0.2·(1 − k(d)) of FP if no fault is near. Probabilities below 1 shrink both terms. *Derived from the formula; not yet tested on our holdout.*
3. **Removing dots next to the catalogue is rational when the test set is new faults.** The public test is described as *newly identified* faults (problem description). A dot on a known fault is a likely false positive for the new-fault test, unless a new fault lies within 300 m. The sibling's own holdout reported +0.00487 in 4/4 folds for this prune. That is the sibling's evaluator, so label it HOLDOUT-DTI (sibling), not ours.
4. **Zero-filled outside the footprint is accepted by the platform** (per the user's list, which includes the zeros-variant entries). The rules say out-of-bounds values must be null or NaN, and zeros are inside the grid bounds. This is the platform's behaviour, not a verified rule reading.

## What we can and cannot conclude
- We **cannot** confirm that 0.2778 is the top score (the brief lists 0.3774 and 0.3195 elsewhere; see [irregularities](irregularities.md) #6).
- We **can** say the winning-type recipe is: binary, sparse, catalogue-pruned dots, placed by a base model, with the 0.2/0.8 asymmetry exploited deliberately.
- To beat 0.2778 we need a dot placement that is more likely to lie within 300 m of **new** faults. Our holdout (catalogue quadrants) only partly tests that.

## Implication for our lane (tensor-dimensionality, this session)
Our lane's ridge baseline E1 gave HOLDOUT-DTI 0.0578 [0.0499, 0.0652] (60,594 withheld positive px). This is far below the sibling's figures, but the protocols differ, so the numbers are **not comparable**. The lane's added structure (E2, E3) lowered holdout DTI (see [run card](results/run_card_tensor_lane.json)).
