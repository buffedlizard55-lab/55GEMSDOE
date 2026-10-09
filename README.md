# 55GEMSDOE — tensor-dimensionality review

> **Current status: NOT CLEARED — DO NOT DOWNLOAD OR SUBMIT.** Historical GeoTIFFs and ZIPs remain under `evidence/historical_artifacts/` for audit traceability, outside the published site; none is a valid deliverable or linked for download. Separate historical final-dot reports breach the literal uniqueness limit; no promotion-grade holdout or organizer format clearance exists. No competition data were downloaded, no geological experiment rerun, and no submission slot used in this review.

**Core values:** “Maximize P(Win” and “Own the Outcome.” Owning the outcome means withholding a file when evidence does not clear it, rather than manufacturing a download button or upgrading a projection into a score.

## User brief (condensed; read at the start of every session)

This is the owner's standing request as of 2026-10-09, condensed. The full verification record is in [`docs/session-20261009-verification.md`](docs/session-20261009-verification.md).

**Goal:** place at the top of the DOE GEMS leaderboard with a unique, valid GeoTIFF that the portal accepts, and make the download obvious only when it is cleared. The leaderboard shows 0.3774 at rank 1 (captured 2026-10-09; see [`evidence/leaderboard_capture_20261009_live.json`](evidence/leaderboard_capture_20261009_live.json)).

**Operating rules:**

- **Core values:** Maximize P(Win), and Own the Outcome.
- **No hallucinations:** verify each claim against an official or verified source, provide the link, flag irregularities, and record negative results.
- **Lane and protocol:** stay in the potential-field tensor lane. Reuse the shared evaluator, cache, writer, and uniqueness checker. Label every number `HOLDOUT-DTI` (with evaluator version, withheld-positive count, and 95% CI) or `ORGANIZER-CONFIRMED`. Run a leakage canary on each feature. Stop on duplicates (rank correlation above 0.90, or over 70% of dots within 3 px of a registry raster).
- **Budget:** three experiments or two hours. Promotion to a submission slot is a separate, later selector step.
- **Review:** three passes (implement, bug and assumption audit, final requirement audit). End each run with a JSON run card.
- **Submission:** a name and a note of 140 characters or fewer. Format: single-band float32 GeoTIFF, EPSG 32611, 100 m, values in [0, 1], null or NaN outside the bounds.

**Requirement status (2026-10-09):**

| Requirement | Status | Where |
|---|---|---|
| Unique GeoTIFF that the portal accepts | **BLOCKED.** No organizer inputs, no registry rasters, and no evaluator in this checkout. None was created. | [`docs/run-card-session-20261009.json`](docs/run-card-session-20261009.json), IR-55-050 |
| Explain the 0.2778 result | **NOT ESTABLISHED.** No organizer receipt links it to H33. The metric mechanism is a derivation, not a finding. | [`docs/hypotheses.md`](docs/hypotheses.md) §A; [`docs/leaderboard-review-20261009.md`](docs/leaderboard-review-20261009.md) |
| 3–5 new hypotheses, ranked, with validation plan | **DONE as proposals.** Two in lane (H-N1, H-N2). Two out of lane (H-N3, H-N4), pending owner decision. None validated. | [`docs/hypotheses.md`](docs/hypotheses.md) §B–D |
| Executive summary and how to submit | **DONE.** Verified format contract, a troubleshooting checklist for the [0, 1] error, and a naming convention. Download remains withheld. | [`docs/submit.html`](docs/submit.html) |
| Line-by-line verification with links | **DONE.** Each row is marked confirmed, not verified, or blocked. | [`docs/session-20261009-verification.md`](docs/session-20261009-verification.md) |
| Irregularities flagged | **DONE.** Nine new items, IR-55-043 to IR-55-051. | [`docs/irregularities.md`](docs/irregularities.md) |
| Pull request and merge to main | See the pull request record in this session. | GitHub |

**Limitations and access needed:**

1. **Organizer data.** The data tab requires a DrivenData login (verified). An account holder must place `gems-geodawn-numerical-features.tif`, `labels.tif`, and `sample_submission.tif` under `data/`, then run `python scripts/prepare_data.py`. The sandbox cannot download them. This is a real access limit, not a judgment call.
2. **Registry rasters or dot coordinates.** Needed for the literal uniqueness check. The current registry holds metadata only.
3. **The rejected upload.** The file name and SHA-256 of the file behind "Predicted values must be in range [0, 1]" are needed to diagnose the error.
4. **Budget decision.** The three-experiment budget is exhausted. Reopening it needs an explicit owner decision.
5. **Lane decision.** H-N3 (radiometric alteration corridor) is outside the tensor lane. It needs an owner decision and a confirmed licence. Its data are on the public USGS release (verified), not in the official feature list.
6. **Generative-AI disclosure.** Rules §3.2 require a narrative disclosure. The team must write it.
7. **Team eligibility.** Rules §1.3 set eligibility. Confirming it is the team's responsibility, not this repository's.

**Suggested next steps (next session):**

1. Place the authorized organizer files under `data/` and run `scripts/prepare_data.py`. Resolve any mismatch with the official files before changing a pin.
2. Reconcile the local evaluator with the shared template. Run the leakage canary on each feature alone; an AUC above 0.90 counts as leakage until shown otherwise.
3. With the budget reopened and the evaluator reconciled, test H-N1 (pseudogravity tensor) against the H1 baseline on the same holdout, with a pooled 95% CI.
4. Obtain the registry rasters or dot coordinates for the uniqueness check.
5. Review the H-N3 licence on the USGS release, and decide on the lane change.

## Current answer on the reported leaderboard values

A saved **PUBLIC-LEADERBOARD snapshot (not a submission-page receipt and not ORGANIZER-CONFIRMED)** lists **0.2778** at rank 16 under `extradr19`, **0.3195** at rank 7, and **0.3774** at rank 1; see [`evidence/leaderboard_snapshot_20261009.json`](evidence/leaderboard_snapshot_20261009.json). The mapping from `extradr19` to the owner-maintained H33 artifact is unverified. A read-only GitHub API check of the owner's GEMSDOE32 manifest reports `receipt: null` for H33, labels it `UNSCORED`, and describes **0.2747** as projected. That is secondary owner-generated evidence, not an organizer receipt. Therefore this project cannot establish that H33 produced the public rank-16 entry, why that entry received its value, or that any repository candidate beats it. The previous anchor-proxy DTI and causal conclusions that depended on the invalid count-only formula are withdrawn and were not recomputed. Any near-miss/clustered-dot explanation is only a hypothesis, not an established mechanism. See the [2026-10-09 leaderboard review](docs/leaderboard-review-20261009.md).

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
- **Merged historical H56 result (not promotion-grade):** **HOLDOUT-DTI**, evaluator `src/gems55/dti55.py` (explicit version absent; not reconciled with the authorized shared evaluator), **60,988** withheld positives; multiscale tensor **0.0172779**, stored 95% CI **[0.0161283, 0.0184686]**. The CI resamples five fold DTI values rather than pooled-score contributions; the stored candidate did not beat its same-evaluator comparator. This is not a clearance result.
- **Merged historical H55 160k result (not promotion-grade):** **HOLDOUT-DTI**, evaluator `src/gems55/dti55.py` (explicit version absent; local/unreconciled), **60,988** withheld positives; Q4 tensor_full **0.1019**, stored 95% CI **[0.0877, 0.1185]**. The CI is a four-quadrant fold-level t interval; quadrant folds can split connected faults. The control CI is absent from the final card, so its raw value is not repeated. This is not a valid test of the required holdout.
- **Uniqueness:** the historical H55 40,000-dot report says 56 rasters were scanned and raw maximum overlap was **84.13%**; the separate H55 160,000-dot report records **84.01%**; H56 40,000-dot reported maximum final-dot overlap **100%** (with another row at **73.6%**). Each exceeds the literal **70%** stop rule. The older 632-raster reports concern different candidates and legacy snapshots; do not combine them with the 56-raster reports. No current complete registry scan or surface-cache check is available.
- **Format:** a previous byte inspection recorded one-band float32, EPSG:32611, 3730×3292, and the expected affine transform. That is partial metadata inspection, not an official format pass: the authentic organizer template is not present here and the validator was not rerun. The historical `zeros`-outside encoding is not cleared against the official footprint.
- **Score receipt:** none found in this checkout. No weekly slot was used.

The detailed machine-readable verdict is [`docs/run-card.json`](docs/run-card.json); live project status is [`docs/status.json`](docs/status.json). The separate H55 160k historical record is [`docs/run-card-h55-160k.json`](docs/run-card-h55-160k.json); all raster variants are archived outside the published site and marked uncleared.

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
- Legacy data-dependent experiment, local writer, mirror-registry downloader, page generator, and status-mutator entry points are retired fail-closed because the experiment budget is exhausted or their evidence path is invalid. The previously completed `exp8`–`exp10` entry points are also disabled; their committed JSON records remain historical evidence only.
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
- [Results and metric correction](docs/results.md) · [Leaderboard attribution](docs/leaderboard-analysis.md) · [2026-10-09 public-leaderboard audit](docs/leaderboard-review-20261009.md) · [Irregularities](docs/irregularities.md) · [Source register](docs/sources.md) · [Three-pass review log](docs/review-log.md)
