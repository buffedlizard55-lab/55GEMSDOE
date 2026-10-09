# Agent working agreement

Before every work session, read the root `README.md`, `docs/run-card.json`, `docs/hypotheses.md`, and `docs/irregularities.md`. The README records the current user brief and verified status.

- Work only on the Arena-assigned branch; do not change branches or edit sibling repositories.
- The only assigned scientific lane is potential-field tensor dimensionality. Do not implement a different family to force a deliverable.
- Reuse the canonical cached stack, evaluator, writer, and uniqueness checker. Do not create a private evaluator/writer fork. The former duplicate `gems/` implementation has been removed. `src/gems55/` is the sole local implementation, but is not certified as the organizer/shared evaluator; reconcile it with the authorized shared template before any promotion use. Local synthetic-test fixes are not an official evaluator validation.
- Do not make up a TIFF, score, receipt, registry scan, or validation result. A format-valid raster is not automatically scientifically cleared or slot-approved.
- Do not publish a download CTA unless holdout, leakage-canary, pre-placement and final-dot uniqueness, and format gates all pass. Historical TIFFs are preserved under `evidence/historical_artifacts/`, outside the published site, but none is a cleared deliverable. Current status: no approved download / do not submit.
- Treat user- and sibling-repository-reported leaderboard numbers as claims unless linked to an organizer submission-page receipt. Label all candidate evaluation results `HOLDOUT-DTI` with evaluator version, withheld-positive count, and 95% CI.
- Respect the three-experiment / two-hour budget and keep promotion separate from experimentation.
- Review all changes at least three times: first implementation, bug/assumption audit, and final requirement/source audit. Keep a negative result if the evidence is negative or unavailable.
