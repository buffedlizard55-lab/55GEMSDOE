# Leaderboard evidence and the reported 0.2778

## Finding

No organizer-confirmed leaderboard value or file-to-score attribution is established in this checkout. The reported values **0.2778**, **0.3195**, and **0.3774** are **USER-REPORTED / NOT ORGANIZER-CONFIRMED**; the current official public leaderboard could not be independently read as a machine-readable source in the audit recorded in [`docs/sources.md`](sources.md).

The specific claim that the H33 raster “scored 0.2778” is unsupported. A read-only GitHub API check of the owner-maintained [GEMSDOE32 submissions manifest](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/main/docs/downloads/submissions_manifest.json) reports the H33 artifact as `role: PRIMARY`, `receipt: null`, and its note ends `projected 0.2747; UNSCORED`. The manifest is a secondary owner-generated artifact audit, not an organizer receipt. It cannot establish a competition score.

## What can and cannot be inferred

- A value in a filename, a sibling README, a local audit field, or a projected fold delta is not an organizer-confirmed score.
- A valid attribution requires an actual submission-page receipt or organizer-confirmed record tying the score to the exact raster hash.
- No such receipt for H33 or the comparison values is present here. Therefore no causal explanation of 0.2778 is supported, and this project cannot claim that its lane beats any of the reported leaderboard values.
- The local anchor-forensics artifacts used a per-prediction nearest-catalogue kernel-weight sum and the invalid denominator `0.2*N + 0.8*|G|`. That sum is not official `TP_w`; the denominator is not the official DTI denominator. Their proxy DTI values, implied hidden-truth-size table, and “factor” comparisons are invalidated, not repaired by relabeling them as official scores. See [`evidence/anchor_verdict.json`](../evidence/anchor_verdict.json) and [`evidence/anchor_forensics.json`](../evidence/anchor_forensics.json).

## Evidence classes used by this project

| Evidence class | Meaning |
|---|---|
| `ORGANIZER-CONFIRMED` | Copied from an actual submission-page receipt or official organizer record that identifies the score and artifact. None is present for the values above. |
| `HOLDOUT-DTI` | Local validation result only when paired with the evaluator version, withheld-positive count, and 95% CI; it is not a leaderboard score. The historical records in this repository are invalid for promotion because of the fold/control defects documented in [`docs/results.md`](results.md). |
| `USER-REPORTED / NOT ORGANIZER-CONFIRMED` | Values supplied in the task or owner reports, without a matching organizer receipt. The three values above are in this class. |
| `PROJECTION` | A model-based estimate or extrapolation. Never present it as a score. The sibling manifest labels 0.2747 as projected and the H33 artifact unscored. |

**Decision:** do not chase or benchmark against the alleged H33 0.2778 as if it were established. Establish the score and exact artifact first; then use only the prescribed same-evaluator holdout to decide whether a future candidate merits a submission slot. The current raster is explicitly **not cleared for download or submission**.
