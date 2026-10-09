# Irregularities and review flags

These are explicit blockers or caveats, not hidden assumptions.

1. **Public leaderboard observed; no submission receipt/artifact mapping.** On
   2026-10-09 the official public leaderboard rendered a ranked table. The dated
   snapshot in `evidence/leaderboard_snapshot_20261009.json` shows 0.3774 at rank 1,
   0.3195 at rank 7, and 0.2778 at rank 16. The public rows do not identify raster
   names or hashes. The H33 sibling page labels its candidate `UNSCORED` and its
   0.2747 figure as a projection; mapping H33 to the 0.2778 row is unverified.
   Per the run protocol, no leaderboard row is treated as an
   `ORGANIZER-CONFIRMED` submission-page receipt, and the current run-card receipt
   list remains empty. The earlier “Loading…” note is stale.
2. **Strict uniqueness is saturated.** The new surface has max absolute Spearman
   0.0223 against 56 registry rasters, but final-dot overlap within 3 px is 1.000
   for the spacing-5 lattice and 0.736 for another prior raster. The literal
   `>70%` stop rule therefore returns `DUPLICATE-STOP`; chance-adjusted overlap is
   diagnostic only.
3. **Holdout correction.** The historical quadrant evaluator was not the required
   whole-segment hide-and-recover design. H56 uses five seeded whole-segment or
   lattice folds, a 3 px buffer, per-fold visible-fault masking, and pooled DTI
   components.
4. **Data provenance.** Local payload hashes match a sibling GitHub bridge
   manifest. The DrivenData data tab is login-gated in this environment;
   organizer-authenticated bytes are not claimed. Do not redistribute payloads.
5. **Acquisition blocks.** USGS documents four blocks and flight paths, but exact
   official block polygons are not aligned in the local competition grid. True
   block-separated FFT processing is a next-session task, not a current result.
6. **Pseudogravity wording.** The direct RTP tensor is a constrained proxy. A
   complete magnetic-to-pseudogravity transform requires an explicit
   magnetization-direction convention; the pseudogravity candidate remains
   unimplemented.
7. **Portal range behavior.** The all-finite `-zeros.tif` removes NaN from the
   local range check and passes the repository validator. The official format page
   still says outside data should be null or NaN. No organizer receipt confirms
   that this encoding is accepted, and the strict uniqueness stop is independent
   of the range result.
8. **Experiment cap reached.** Baseline, H56 multiscale, and gravity-only arms
   were run. No further tuning should be done in this session.

## Final-pass irregularities (tensor-lane session, 2026-10-09; IDs IR-55-025 to IR-55-033)

Earlier fixes in this session, recorded before the merge (pre-merge register IR-55-001…024 is in commit 28919e5): per-fold leakage canary (IR-55-017), segment-fold leak with withheld = full footprint (IR-55-018), and the registry rebuild from `registry.json` (IR-55-016).

- **IR-55-025 (Medium). Validator resolution check was shape-based.** The "resolution is 100 m" check compared the shape, not the pixel size. Fixed once in `scripts/validate_submission.py`: the check now reads |a| and |e| from the transform. Both encodings pass (12/12 zeros, 11/11 NaN twin). Done.
- **IR-55-026 (Low). Feature-raster naming mismatch.** `prepare_data.py` and `run_tensor_lane.py` looked for `training_features.tif`, but the file on disk is `gems-geodawn-numerical-features.tif`. The same sha256 pin applies. Fixed once in both scripts. `prepare_data.py` exits 0 with all three pins OK. Done.
- **IR-55-027 (Medium). Sidecar selection picked the lexicographically last file.** "160000" sorts before "40000". The historical H55 card is `docs/run-card-h55-160k.json`; its DTI metadata was reviewed and its legacy generator `scripts/make_final_card.py` now fails closed because it would overwrite reviewed secondary-score CIs and require absent competition rasters. The stale `evidence/runcard.json` remains superseded.
- **IR-55-028 (High). Striping axis is unreconciled.** ScienceBase (Glen & Earney 2024, doi 10.5066/P93LGLVQ) says flight lines run at azimuth 90° (E–W). The lane masks rows (E–W lines). `evidence/striping_diagnostic.json` reports N–S on real RTP data, but its own coherence numbers are equal (0.185 along x, 0.187 along y). A crude high-pass test here (row-means std 6.3 vs column-means std 8.9; y/x gradient RMS 0.77) leans N–S. If the striping is N–S, the lane's 21% mask is on the wrong axis. Open: the flight-line shapefile (not reachable from the sandbox) would settle it. Do not cite the lane striping mask until then.
- **IR-55-029 (Medium). Two striping counts from two detectors.** 86,947 px (129 rows, z>4, `gems/tensor.py`, `docs/results/tensor_lane_results.json`) and 1,105,919 px (21.4%, coherence-based `gems55` mask, thresh 0.55, lag 60 px, `data/cache/lane_v1.meta.json`). These are not a miscount. Both are reported; the shipped audit file uses the 1,105,919-px mask.
- **IR-55-030 (Medium, blocking for submit). Literal uniqueness stop on the audit file.** `scripts/verify_unique.py` returns REVIEW. The raw 3-px statistic is 0.8401 against the spacing-5 lattice `13GEMSDOE…lattice-s5` (206,895 dots). A random control on that lattice scores 0.8389 (excess +0.0012). Spearman max 0.014, Jaccard max 0.031. Under the shared 70% rule this is DUPLICATE-STOP. It is chance-level overlap, not a copy. Owner decision required; no submit clearance. Evidence: `evidence/uniqueness_160000dots.json`.
- **IR-55-031 (Medium). The secondary protocol disagrees with the primary.** The historical Q4 primary is negative at the selected dot budget; the distance-banded B=15 px secondary comparison is positive, but cannot rescue the preregistered decision. All cited DTI arms are **HOLDOUT-DTI** from `src/gems55/dti55.py`, use 60,988 withheld positives, and now carry 95% fold-level CIs in `docs/run-card-h55-160k.json` and the augmented `evidence/exp9_distance_band_v1_n40000.json` / `evidence/exp10_mass_sweep_v1.json`. CI intervals are Student-t over stored per-fold DTI values; per-fold values were rounded to six decimals and the intervals are approximate. No experiment was rerun for this correction.
- **IR-55-032 (Medium). The holdout arm is not the shipped emitter.** exp10 restricts emission to each fold's withheld domain, excludes striping outright, and uses per-fold seeds. The shipped writer (`scripts/submission_writer.py`) uses the full footprint, down-weights striping by 0.25, and uses seed 55. The holdout therefore does not score the shipped file exactly. Disclosed; a full-footprint holdout needs a different protocol.
- **IR-55-033 (Low–Medium). Zeros versus NaN outside the footprint.** The rules say "null or nan". The earlier site chose zeros on the basis of the portal's [0, 1] range check. That reasoning is not verified against the portal. Confirm on the portal before relying on either encoding; the NaN twin is published for comparison only.
- **Superseded file.** The 40k audit file (`…40000dots-20261009T052235Z`, sha256 b7c7225d…) was removed from `docs/downloads/` on `main` by the parallel session. It is reproducible from `scripts/submission_writer.py --n-dots 40000` and its sidecar is `evidence/submission_h55-tensor2d-strikegate-40000dots-20261009T052235Z.json`.

## IR-55-034 — retracted anchor algebra and stale leaderboard claims (High)

The one-off `exp5_anchor_forensics.py`, `exp6_anchor_mechanism.py`,
`exp7_anchor_verdict.py`, `build_anchor_page.py`, and the associated anchor page
used the shortcut `DTI = TP_w/(0.2N + 0.8|G|)`. The official definitions imply
`TP_w + FN_w = |G|`, but they do **not** imply `TP_w + FP_w = N`: TP is a
max-over-predictions operation performed separately for each truth pixel, while
FP is separately summed over prediction pixels. Thus the historic catalogue-proxy
DTI values, target-score bounds, inferred hidden-truth size, and conclusions that
depend on them are retracted. `evidence/anchor_forensics.json`,
`anchor_mechanism.json`, and `anchor_verdict.json` carry an explicit retraction
marker; scripts 5–7 fail closed; the public-facing analysis page has been replaced.
The same invalid denominator also appeared in the `greedy_cover` helper's docstring
and in the old exp10 sweep rationale; these now state that expected-credit placement
is only a heuristic and that all DTI comparisons use the full exact formula. No
holdout was rerun and no historical score was promoted. Exact DTI must be computed
by `src/gems55/dti55.py` under the canonical whole-segment holdout if it is to be
compared as a score. A regression test exercises a two-pixel truth example where
the shortcut fails.

Separately, the official public leaderboard was accessible on this review and a
dated snapshot is saved. Its score rows cannot be mapped to H33's raster because
neither the public table nor the sibling webpage exposes a matching submission
receipt/hash. H33's sibling page calls its candidate unscored and labels 0.2747 a
projection. Do not claim its score is 0.2778 without the receipt. See
`docs/leaderboard-analysis.md` and the `PUBLIC-LEADERBOARD-SNAPSHOT` evidence file.

**Status:** fixed in analysis/docs/tests; no leaderboard score is recorded as a
submission receipt; no new experiment or slot was used. The competition payloads,
cached feature surface, and prior registry rasters are absent from this checkout,
so the corrected anchor analysis itself has not been rerun.
