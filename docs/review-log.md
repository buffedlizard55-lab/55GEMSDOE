# Review log — 2026-10-09 UTC

## Pass 1 — implementation and scope

- Re-derived the DTI denominator from `TP_w + FN_w = |G|`; replaced the false count-only identity throughout the current results narrative and added a synthetic regression case.
- Reclassified the leaderboard values as user-reported, withdrew the H33 score attribution and any causal/beating claim, and kept the owner-maintained manifest as secondary evidence only.
- Preserved four ranked tensor-dimensionality hypotheses with required layers, physical signatures, rationales, method differences, costs, non-fault mimics, and official references.
- Removed the duplicate `gems/` evaluator/writer package and retired data-dependent local runners, private/unsafe page and run-card generators, status mutator, mirror-registry downloader, and submission writer. Moved uncleared raster/archive variants out of the published `docs/` tree into an explicitly labeled evidence archive.
- Made site and run-card status fail closed: no valid promotion HOLDOUT-DTI, no organizer receipt, no uniqueness pass, and no download or submission clearance.

## Pass 2 — bug and assumption audit

- Checked the exact metric terms in code and docs; retained `FP_w` separately and confirmed the count-only `0.2*N + 0.8*|G|` expression is explicitly invalidated.
- Audited fold/random/uniqueness/format language against actual local code. `src/gems55/` is the sole repository-local implementation, **not certified as the authorized shared or organizer evaluator**; no local results may clear promotion.
- Checked data preparation uses the canonical filenames in `src/gems55/io55.py` and mirror-derived hash pins are not labeled as official provenance.
- Reconciled `status.json`, `run-card.json`, artifact SHA-256, and download-link policy. Flagged the distinct 56-raster vs older 632-raster registry snapshots as non-comparable. Fixed a stale site-status test that still required a downloadable, positive file.
- Kept the user-reported 0.2778, 0.3195, and 0.3774 distinct from `ORGANIZER-CONFIRMED`; no receipt or score attribution was invented.

## Pass 3 — final requirement and line audit

- Reviewed the final changed paths for formula/source/status consistency and ran `git diff --check`.
- Audited the merged lane-code claims line by line: corrected fixed 64-pixel normalization tiles versus actual acquisition-block polygons and clarified direct-RTP tensor processing as a proxy, not a known-direction pseudogravity transform. Updated the published evidence/irregularities pages to match the reconciled historical records.
- Reconciled PR #10 with the updated `main` history without rerunning any data-dependent work. Preserved the previously committed H56 and H55 evidence records, moved every historical raster/archive outside the published `docs/` tree, and corrected current and historical status cards to forbid download and submission.
- Retired the merged `exp8`–`exp10` entry points and the unsafe H55 audit-page/run-card generators. The committed result JSON is retained as historical evidence; no experiment was executed.
- `./.venv/bin/python -m pytest -q`: **39 passed, 2 skipped** (data-dependent raster tests skipped because the authorized feature/label/template rasters are absent). Three non-failing Rasterio affine warnings occurred in synthetic writer tests.
- `./.venv/bin/python -m unittest discover -s tests -v`: **9 passed**.
- `scripts/make_runcard.py`: all run-card field, note-length, no-receipt, null-holdout, and uncleared-artifact checks passed.
- `scripts/build_site.py`: status gates passed and all 13 HTML pages had no GeoTIFF/ZIP download links; no raster/archive file is physically under `docs/`.
- `compileall`, shell syntax check, `git diff --check`, and JSON parsing (31 files under `docs/` and `evidence/`) passed.
- No competition data were downloaded, no geological experiment was run, no candidate TIFF was generated, and no weekly slot was used.

## Remaining blockers

The authorized shared feature cache/evaluator/writer/uniqueness checker, competition rasters, authentic organizer template, full registry rasters/surface cache, and organizer receipt are not present. The recorded experiment budget is exhausted. No new HOLDOUT-DTI value/CI exists. The historical raw final-dot overlap exceeds the literal stop limit. The outcome remains **NOT CLEARED — DO NOT DOWNLOAD OR SUBMIT**.
