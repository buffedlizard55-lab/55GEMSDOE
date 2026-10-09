# 55GEMSDOE — tensor-dimensionality review

> **Current status: NOT CLEARED — DO NOT DOWNLOAD OR SUBMIT.** Historical GeoTIFF files remain under `evidence/historical_artifacts/` for audit traceability, outside the published site; they are not valid deliverables. The stored final-dot registry comparison breaches the literal uniqueness limit; the scientific holdout and format gates are not validly cleared. No competition data were downloaded or geological experiment rerun in this review.

**Core values:** “Maximize P(Win” and “Own the Outcome.” Owning the outcome means withholding a file when evidence does not clear it, rather than manufacturing a download button or upgrading a projection into a score.

## Current answer on the reported leaderboard values

The values **0.2778**, **0.3195**, and **0.3774** are **USER-REPORTED / NOT ORGANIZER-CONFIRMED** in this checkout. No organizer submission-page receipt ties any of them to a raster/hash. A read-only GitHub API check of the owner-maintained GEMSDOE32 manifest reports `receipt: null` for the H33 artifact, labels it `UNSCORED`, and describes **0.2747** as projected. That is secondary owner-generated evidence, not an organizer receipt. Therefore this project cannot establish why H33 “scored 0.2778,” explain a causal mechanism for that value, or claim to beat a reported leaderboard score.

## Critical metric correction — prior conclusions withdrawn

For the official distance-weighted Tversky definitions, `TP_w + FN_w = |G|` is valid. It yields

```text
DTI = TP_w / (TP_w + alpha*FP_w + beta*(|G|-TP_w) + eps)
    = TP_w / ((1-beta)*TP_w + alpha*FP_w + beta*|G| + eps)
```

At `alpha=0.2`, `beta=0.8` this is

```text
DTI = TP_w / (0.2*TP_w + 0.2*FP_w + 0.8*|G| + eps)
```

It is **not** generally `TP_w/(0.2*N + 0.8*|G|)`: `TP_w+FP_w=N` is not a general identity. The old target-size tables, “coverage plateau” claims, anchor-proxy DTI calculations, and any conclusions that rely on the count-only denominator are withdrawn. A synthetic regression case in `tests_numeric/test_core.py` demonstrates the error: with one truth pixel, a correct unit dot, and another unit dot one pixel away, `TP_w=1`, `FP_w=1/3`, `FN_w=0`; exact DTI is **0.9375**, while the invalid simplification gives **5/6**. This is a synthetic metric test, not a HOLDOUT-DTI result.

`breakeven_credit` now documents the conditional single-match threshold `w > alpha*DTI_now` under its assumptions. It is not a generic per-dot rule. `greedy_cover` maximizes a coverage surrogate and does not optimize full DTI because it omits the separate FP term.

## Evidence and gate status

- **Valid promotion HOLDOUT-DTI:** none. No valid evaluator version, withheld-positive count, value, and 95% CI are available for promotion.
- **Historical HOLDOUT-DTI (not valid for promotion):** the canonical-local record used an unversioned pre-audit `src/gems55/dti55.py` transcription with **60,988** withheld positives. Tensor record **0.0667012**, stored interval **[0.0560079, 0.0893459]**. The quadrant split can split a connected fault; its purported random control was filtered by `score > 0`; the interval bootstraps four fold values rather than pooled-DTI contributions. This cannot clear or condemn a candidate under the required protocol.
- **Separate historical HOLDOUT-DTI (private evaluator; not comparable):** `gems.metric v1`, **60,594** withheld positives. E1 ridge **0.0578 [0.0499, 0.0652]**, E2 dimensionality **0.0463 [0.0398, 0.0523]**, E3 tensor/strike **0.0444 [0.0383, 0.0502]**. This fork and different holdout cannot be compared to the canonical-local record.
- **Uniqueness:** the historical report for this 40,000-dot artifact says 56 rasters were scanned and a raw maximum **84.13%** of candidate dots were within 3 pixels of one prior raster. The literal rule stops above **70%**. Older E1/E3 files report 632 rasters for different candidates and legacy snapshots; they are explicitly superseded and cannot be combined with this report. The former control-adjusted pass is withdrawn. Registry rasters and the continuous score cache are absent, so neither a fresh surface scan nor a fresh final-dot scan is available.
- **Format:** a previous byte inspection recorded one-band float32, EPSG:32611, 3730×3292, and the expected affine transform. That is partial metadata inspection, not an official format pass: the authentic organizer template is not present here and the validator was not rerun. The historical `zeros`-outside encoding is not cleared against the official footprint.
- **Score receipt:** none found in this checkout. No weekly slot was used.

The detailed machine-readable verdict is [`docs/run-card.json`](docs/run-card.json); live project status is [`docs/status.json`](docs/status.json). Historical artifact is unlinked and marked uncleared.

## Ranked geological hypotheses (stay in the tensor lane)

Before any experiment, read [`docs/hypotheses.md`](docs/hypotheses.md). It ranks four distinct tensor-dimensionality hypotheses and specifies required layers, physical signatures, uncatalogued-fault rationale, differences from the existing method, compute/validation cost, non-fault mimics, and official data sources. The top candidate uses competition band 2 (reduced-to-pole magnetic anomaly) and band 13 (isostatic gravity anomaly). The current prototype exists, but its holdout is not promotion-grade. No new hypothesis was implemented or tested in this review; the experiment budget is recorded as exhausted (three experiments).

## Standing project brief

This repository is the recurring starting point for the DOE GEMS project. The assigned scientific lane is **potential-field tensor dimensionality**; do not switch to another method family to force a file.

1. **Keep the scientific protocol intact.** Reuse the authorized shared cached feature stack, evaluator, writer, and uniqueness checker. Do not make a private evaluator/writer fork. Whole-segment hide-and-recover must use a buffer, exact visible-fault masking, pooled DTI with α=0.2, β=0.8, and the 300 m triangular kernel. Run each leakage-canary feature alone. Compare the continuous surface before placement and final dots afterward.
2. **Holdout before promotion.** Test the top ranked candidate on a spatial holdout before any submission-slot promotion. A same-evaluator holdout win is required. Stop at three experiments or two hours; the stored run record says three experiments were already used. Do not use a weekly slot without a same-evaluator holdout win.
3. **Label every score-like result.** Use `HOLDOUT-DTI` with evaluator version, withheld-positive count, and 95% CI, or `ORGANIZER-CONFIRMED` copied from an actual organizer submission receipt. Mark projections as projections. Never invent a receipt, leaderboard attribution, registry comparison, or validator pass.
4. **Uniqueness stop rule is literal.** If absolute rank-correlation exceeds 0.90 or more than 70% of candidate dots lie within 3 pixels of any prior raster, log the duplicate and stop. A chance-adjusted statistic does not override the literal threshold.
5. **Publish a GeoTIFF only when honestly cleared.** The file must be unique, valid against the authentic organizer template, scientifically cleared, and have passed leakage, surface and final-dot uniqueness checks. The site must state plainly whether download/submission is allowed. The executive summary must explain the portal workflow; keep the TIFF unlinked unless every gate passes.
6. **Keep sources and irregularities explicit.** Use official or verified links, state data/validation limitations, and distinguish organizer files from owner-maintained mirrors. Do not download sibling-repository data mirrors without provenance/legal approval.
7. **End any run with the JSON run card.** Required fields: hypothesis, mechanism, named non-fault mimic, holdout plus CI, registry comparisons, raster hash, validator findings, submission name and note (≤140 characters), and verdict. The current card records `NOT_CLEARED` and null valid-holdout fields.
8. **Review every change three times:** implementation, bug/assumption audit, and final requirement/source audit. Verify changed lines and do not rerun experiments to resolve missing inputs or gate failures.

## Data, provenance, and preparation

The authorized competition source is the [DrivenData data tab](https://www.drivendata.org/competitions/306/competition-doe-gems/data/), which requires login and acceptance of the rules. The feature stack, labels, organizer sample template, cached surface, and registry rasters are absent from this checkout.

The owner-maintained [GEMSDOE sibling repository](https://github.com/buffedlizard55-lab/GEMSDOE) contains mirror references, not authenticated organizer downloads. Its recorded SHA-256 pins are explicitly identified in [`data/README.md`](data/README.md) and [`data/SOURCES.md`](data/SOURCES.md) as mirror-derived. The downloader is disabled by default and requires `GEMS_ALLOW_UNOFFICIAL_MIRROR=1`; that opt-in does not establish provenance or permission. It was not run.

After downloading authorized files from DrivenData under the canonical names defined in `src/gems55/io55.py`, run:

```bash
python scripts/prepare_data.py
```

The check validates canonical filenames, the recorded hashes, and grid geometry. If an authorized organizer file differs from a mirror pin, stop and reconcile it against the official source; do not silently overwrite pins. See [`docs/sources.md`](docs/sources.md) for sources and retrieval status.

## Repository map

- `src/gems55/dti55.py` — single local DTI transcription, synthetic exactness tests, additive contribution maps, and spatial block bootstrap helper. It is **not yet reconciled to an authorized shared evaluator**.
- `src/gems55/holdout55.py` — repository-local synthetic/support utilities for whole 8-connected components, Euclidean buffers, and score-independent random draws; not certified as the authorized shared holdout/evaluator.
- `src/gems55/io55.py` — canonical raster paths, grid constants, and local writer. The writer does not certify a submission.
- `scripts/evaluate_holdout.py` — retired fail-closed entry point; no local holdout run is allowed until the authorized shared evaluator/cache are reconciled and the exhausted budget is explicitly reopened.
- `scripts/verify_unique.py` — repository-local fail-closed full-manifest uniqueness checker; requires the authentic template and every registry raster, and is not the authorized shared checker.
- `scripts/validate_submission.py` — local structural validator; requires authentic template/labels and is not an organizer receipt.
- Legacy data-dependent experiment, local writer, mirror-registry downloader, page generator, and status-mutator entry points are retired fail-closed because the experiment budget is exhausted or their evidence path is invalid.
- `scripts/prepare_data.py` — canonical filename/hash/grid preparation checks.
- `evidence/` — historical run records. Invalid evidence is annotated, not treated as current promotion support.
- `docs/` — GitHub Pages source; current landing page has no TIFF link and prominently says not to download/submit.

The former duplicate `gems/` evaluator/writer package was removed. The old `scripts/run_tensor_lane.py` is retired and refuses to run because it depended on that private fork and quadrant folds; the older private-evaluator results remain only as labeled historical records.

## Final portal workflow (only after clearance)

When a future file has passed every scientific, leakage, uniqueness, and format gate: sign in to the [DOE GEMS competition](https://www.drivendata.org/competitions/306/competition-doe-gems/), open the submission page, upload the exact cleared single-band GeoTIFF, enter its published run-card name/note (no more than 140 characters), submit, and preserve the organizer receipt. This repository has no portal credentials and has not submitted any file. See [`docs/submit.html`](docs/submit.html) for the current explicit answer: **not cleared; do not download or submit**.

## Sources, results, and status pages

- [Official problem description and metric](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [Official GEMS rules (NLR PDF)](https://docs.nlr.gov/docs/fy26osti/96647.pdf)
- [USGS GeoDAWN release, DOI 10.5066/P93LGLVQ](https://doi.org/10.5066/P93LGLVQ)
- [Results and metric correction](docs/results.md) · [Leaderboard attribution](docs/leaderboard-analysis.md) · [Irregularities](docs/irregularities.md) · [Source register](docs/sources.md) · [Three-pass review log](docs/review-log.md)
