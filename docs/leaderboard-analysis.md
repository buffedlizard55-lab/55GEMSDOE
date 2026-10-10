# Leaderboard evidence and the reported 0.2778

## Finding

No organizer-confirmed score or file-to-score attribution is established in this checkout. A saved **PUBLIC-LEADERBOARD (not a submission-page receipt, not ORGANIZER-CONFIRMED)** snapshot lists **0.2778** at rank 17 under participant `extradr19`, **0.3195** at rank 7, and **0.3774** at rank 1. The capture is [`evidence/leaderboard_snapshot_20261009.json`](../evidence/leaderboard_snapshot_20261009.json); it establishes what appeared on that captured public page, not which raster was submitted or whether any row belongs to H33.

A read-only GitHub API check of the owner-maintained [GEMSDOE32 submissions manifest](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/main/docs/downloads/submissions_manifest.json) reports the H33 artifact as `role: PRIMARY`, `receipt: null`, and its note ends `projected 0.2747; UNSCORED`. The manifest is a secondary owner-generated artifact audit, not an organizer receipt. The association between the public participant `extradr19` and the owner artifact H33 is unverified.

Therefore the project cannot establish that H33 received the rank-16 public entry, explain why that entry received its value, or claim that the tensor lane beats any public-leaderboard value. A sparse or near-miss placement mechanism is only an untested hypothesis, not a measured explanation.

## Withdrawn analysis

The prior anchor forensics labeled a per-prediction nearest-catalogue kernel-weight sum as official `TP_w` and used the invalid denominator `0.2*N + 0.8*|G|`. The metric requires `TP_w` summed over truth pixels using the maximum match over predictions and retains `FP_w` separately. Consequently, proxy DTI values, inferred hidden-truth-size calculations, ratios, and causal conclusions from that method are withdrawn, not repaired by relabeling them as scores, and not repeated here. The corrected algebra and a synthetic counterexample are in [`docs/results.md`](results.md); the historical JSON is retained only for traceability.

## Evidence classes used by this project

| Evidence class | Meaning |
|---|---|
| `ORGANIZER-CONFIRMED` | Copied from an actual submission-page receipt or official organizer record that identifies the score and artifact. None is present for H33 or the values above. |
| `PUBLIC-LEADERBOARD` | A dated value captured from the public leaderboard. It is not a submission receipt, does not identify a raster hash, and does not qualify as an organizer-confirmed artifact score. |
| `HOLDOUT-DTI` | Local validation result only when paired with evaluator version, withheld-positive count, and 95% CI. The historical records here are invalid for promotion because of evaluator/fold/control defects; see [`docs/results.md`](results.md). |
| `USER-REPORTED / NOT ORGANIZER-CONFIRMED` | Values supplied in the task or owner reports without a matching organizer receipt. |
| `PROJECTION` | A model-based estimate or extrapolation; never present it as a score. The owner manifest calls 0.2747 projected and H33 unscored. |

**Decision:** do not treat the H33 “0.2778” attribution as established or use it as a same-evaluator benchmark. The exact submission and receipt must be established first. Current repository holdouts do not demonstrate that the lane beats a leaderboard value, and no candidate is cleared for download or submission. See the [full 2026-10-09 review](leaderboard-review-20261009.md), [machine-readable review card](run-card-review-20261009.json), and [canonical run card](run-card.json).
