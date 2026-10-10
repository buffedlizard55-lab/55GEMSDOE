# Irregularities and review flags

These are explicit blockers or caveats, not hidden assumptions. The first list and
IR-55-025–033 below are retained as **historical H55/H56** evidence; current H57
status and fixes are summarized at the end. Current decision: the NaN-outside audit file passes strict format checks, but the expanded uniqueness scan returns DUPLICATE-STOP and the holdout is negative / do not submit.

1. **No leaderboard receipt.** The official leaderboard fetch returned only
   “Loading…”. Values supplied in the owner brief and sibling pages remain
   unverified claims; they are not `ORGANIZER-CONFIRMED`.
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

- **IR-55-025 (Medium). Validator resolution check was shape-based.** The "resolution is 100 m" check compared the shape, not the pixel size. Fixed in `scripts/validate_submission.py`: the check reads |a| and |e| from the transform. The historical 12/12 zero-outside count is superseded: the strict current validator requires NaN exactly outside the footprint (see IR-55-049), so the zeros diagnostic now fails.
- **IR-55-026 (Low). Feature-raster naming mismatch.** `prepare_data.py` and `run_tensor_lane.py` looked for `training_features.tif`, but the file on disk is `gems-geodawn-numerical-features.tif`. The same sha256 pin applies. Fixed once in both scripts. `prepare_data.py` exits 0 with all three pins OK. Done.
- **IR-55-027 (Medium). Sidecar selection picked the lexicographically last file.** "160000" sorts before "40000". `scripts/make_final_card.py` now writes `docs/run-card-h55-160k.json` for the audit file, and the stale `evidence/runcard.json` is superseded. Done.
- **IR-55-028 (High). Striping axis is unreconciled.** ScienceBase (Glen & Earney 2024, doi 10.5066/P93LGLVQ) says flight lines run at azimuth 90° (E–W). The lane masks rows (E–W lines). `evidence/striping_diagnostic.json` reports N–S on real RTP data, but its own coherence numbers are equal (0.185 along x, 0.187 along y). A crude high-pass test here (row-means std 6.3 vs column-means std 8.9; y/x gradient RMS 0.77) leans N–S. If the striping is N–S, the lane's 21% mask is on the wrong axis. Open: the flight-line shapefile (not reachable from the sandbox) would settle it. Do not cite the lane striping mask until then.
- **IR-55-029 (Medium). Two striping counts from two detectors.** 86,947 px (129 rows, z>4, `gems/tensor.py`, `docs/results/tensor_lane_results.json`) and 1,105,919 px (21.4%, coherence-based `gems55` mask, thresh 0.55, lag 60 px, `data/cache/lane_v1.meta.json`). These are not a miscount. Both are reported; the shipped audit file uses the 1,105,919-px mask.
- **IR-55-030 (Medium, blocking for submit). Literal uniqueness stop on the audit file.** `scripts/verify_unique.py` returns REVIEW. The raw 3-px statistic is 0.8401 against the spacing-5 lattice `13GEMSDOE…lattice-s5` (206,895 dots). A random control on that lattice scores 0.8389 (excess +0.0012). Spearman max 0.014, Jaccard max 0.031. Under the shared 70% rule this is DUPLICATE-STOP. It is chance-level overlap, not a copy. Owner decision required; no submit clearance. Evidence: `evidence/uniqueness_160000dots.json`.
- **IR-55-031 (Medium). The secondary protocol disagrees with the primary.** At N = 160k, B = 15 px gives tensor 0.0238 vs random 0.0212 (p = 0.004, positive); Q4 gives 0.1019 vs 0.1627 (negative). At N = 40k, B = 15 px is +0.0015 (p = 0.008); B = 30 px is +0.0009 (p = 0.20). Reported as is; the pre-registered rule (both protocols must pass) gives NEGATIVE. Evidence: `evidence/exp9_distance_band_v1_n40000.json`, `evidence/exp10_mass_sweep_v1.json`.
- **IR-55-032 (Medium). The holdout arm is not the shipped emitter.** exp10 restricts emission to each fold's withheld domain, excludes striping outright, and uses per-fold seeds. The shipped writer (`scripts/submission_writer.py`) uses the full footprint, down-weights striping by 0.25, and uses seed 55. The holdout therefore does not score the shipped file exactly. Disclosed; a full-footprint holdout needs a different protocol.
- **IR-55-033 (Low–Medium; superseded by IR-55-049). Zeros versus NaN outside the footprint.** The earlier site chose zeros on the basis of the portal's [0, 1] range check. The strict current local validator requires NaN exactly outside the template footprint: the NaN-outside TIF passes, and the zeros-outside diagnostic fails the footprint check. A local validator pass is still not organizer portal clearance.
- **Superseded file.** The 40k audit file (`…40000dots-20261009T052235Z`, sha256 b7c7225d…) was removed from `docs/downloads/` on `main` by the parallel session. It is reproducible from `scripts/submission_writer.py --n-dots 40000` and its sidecar is `evidence/submission_h55-tensor2d-strikegate-40000dots-20261009T052235Z.json`.

## H57 session irregularities and fixes (2026-10-09; IR-55-034 to IR-55-042)

- **IR-55-034 (Low; fixed). Feature-file name mismatch.** The downloader writes
  `training_features.tif`, while the SHA checker originally required the descriptive
  alias `gems-geodawn-numerical-features.tif`. `prepare_data.py` now accepts either
  filename against the same pinned SHA. The three local payload files passed the
  pin checks this session. The pins are still not authenticated against the login-
  gated DrivenData download; see `data/SOURCES.md`.
- **IR-55-035 (High; earlier 56-row scan, superseded by IR-55-048). Dense
  lattice registry row.** The prior spacing-5 raster covers 99.87% of the footprint
  within 3 Euclidean pixels; a seeded random-control selection had 0.985 overlap in
  the original 200-dot scan. No row was excluded. The earlier 0.68 maximum was
  incomplete because six additional registry variants were added later. The current
  66-raster scan returns 0.76 and DUPLICATE-STOP; the random-control statistic does
  not waive the literal threshold. The small 200-dot mass does not make the
  geological holdout positive.
- **IR-55-036 (Medium; fixed). Random-control distance metric mismatch.** The old
  uniqueness diagnostic used a 4-connected dilation while the gate used a Euclidean
  distance transform. `scripts/verify_unique.py` now uses the same Euclidean <=3 px
  cover mask for candidate and random-control overlaps. Old 0.839 control values
  are superseded; current evidence is `evidence/uniqueness_h57_final.json`.
- **IR-55-037 (Medium; fixed for current H57 run). Holdout/writer rule mismatch.**
  The canonical H57 evaluation and writer now share hard striping masking, the
  un-eroded tensor-factor sensitivity option, the 15-px flank prior, 3-px minimum
  separation, all-56 registry budgets and total dot mass. Five folds use 40 dots
  each (200 total). Every comparator and candidate returned matched mass. Older
  runs remain historical and are not used for this promotion decision.
- **IR-55-038 (High; invalid exploratory result quarantined).** The first H57
  exploratory holdout excluded the spacing-5 lattice and some arms emitted fewer
  dots than requested. Its scores must not be compared or used for promotion. It is
  archived as `evidence/holdout_h57_exploratory_invalid_excluded-lattice_unmatched-mass.json`.
  The subsequent registered experiment uses no exclusions and matched mass.
- **IR-55-039 (High; fixed in shared registry loader). Misregistered prior raster.**
  `14GEMSDOE__GEMS_r5-geom-horse-ensemble...tif` has the competition shape and EPSG
  but transform origin `(500000, 4500000)` instead of the official `(243350, 4508550)`.
  Earlier pixel-index comparisons treated these as aligned. New `src/gems55/registry55.py`
  reprojects it to the exact EPSG:32611 template with nearest-neighbor resampling;
  all 56 registry entries present at holdout time were included in the emission
  masks and holdout checks. The later expanded uniqueness audit covers 62 registry
  rasters; the same single misregistered entry is reprojected and recorded.
- **IR-55-040 (Medium). H57-A holdout is negative.** Matched-mass **HOLDOUT-DTI**
  candidate `tensor_flank` = 0.00012284, 95% CI [0.00011438, 0.00013397], 60,988
  withheld positives, N=200; tensor_full = 0.00030077, ridge_x_agree = 0.00027391,
  matched random = 0.00015080. Candidate loses to all three. No weekly slot used;
  the NaN-outside audit TIF is not unique under the expanded strict scan and is
  audit-only. Full evidence is `docs/run-card.json` and
  `evidence/holdout_h57_unique_n200.json`.
- **IR-55-041 (Low; fixed). Strike diagnostic count mislabeled.** The previous
  evaluator field `n_withheld_segments` actually counted 273 pixel samples, not
  connected segments. The corrected statistic is 13 PCA-fit connected components
  across five folds and 273 withheld pixel samples; random comparison uses 100,000
  sampled ridge pixels. `scripts/evaluate_holdout.py` now exposes both counts.
- **IR-55-042 (Medium; disclosed). Un-eroded edge sensitivity.** The strict lattice
  budget leaves only edge pixels outside its 3-px coverage. The H57 sensitivity
  score recomputes the same tensor formula from cached factors without the normal
  six-pixel footprint erosion to evaluate 200 unique dots. This increases FFT
  boundary-ringing risk; named mimics include edge artifacts, lithologic contacts,
  dikes and basin-margin edges. The edge variant's holdout is negative.
- **IR-55-043 (Medium; strict local interpretation recorded in IR-55-049).** The
  official problem page says outside-bounds data should be null or NaN. The strict
  local validator compares the NaN mask exactly with the template footprint: the
  `-nan.tif` primary passes 11/11 checks, while `-zeros.tif` passes 10/11 and fails
  only the outside-footprint null/NaN check. A local pass is not organizer portal
  clearance; H57 remains DO NOT SUBMIT for independent uniqueness and holdout
  failures.
- **IR-55-044 (Low). Public block-data listing is readable; binary download blocked.**
  The official USGS ScienceBase page lists Area 1 and Area 2 flight-path ZIPs and
  marks the release CC0. The catalog and file sizes were verified in this session,
  but the sandbox outbound allowlist prevents fetching the ScienceBase payloads;
  block polygons therefore remain unaligned and H57-E is not implemented.
- **IR-55-045 (Medium; future prize-package requirement). Generative-AI disclosure.**
  The September 2026 official rules state generative-AI use is allowed but must be
  described in the submission narrative, including extent and how it was used. This
  repo was developed with an AI agent; any future final prize package must disclose
  that accurately. The current artifact is not being uploaded.
- **IR-55-046 (High; future submission gate). Final selection and eligibility.**
  The official rules permit up to three submissions per week for feedback but require
  one selected final submission before the deadline for both prize phases. Eligibility
  certification and final package/signatures are the registered competitor's
  responsibility. This agent did not log in, submit, select a final slot, or certify
  eligibility.
- **IR-55-047 (Medium; superseded by IR-55-048). Earlier local artifacts.**
  The intermediate H57 uniqueness report covered 56 shared registry rasters and two
  local candidates (58 total), reporting max overlap 0.68. It was incomplete because
  additional registry variants and local history were added later. The current
  comparison set is 62 registry + 4 local historical rasters; do not reuse the
  intermediate PASS-UNIQUE result.
- **IR-55-048 (High; blocking). Expanded strict uniqueness returns DUPLICATE-STOP.**
  The final NaN-outside H57 map was rescanned against all 62 current registry rasters
  plus four local historical candidates (66/66 compatible comparisons). Surface
  max |Spearman| is 0.2443 and passes its 0.90 threshold. The maximum one-sided
  Euclidean 3-pixel final-dot overlap is **0.76**, exceeding the literal **0.70**
  stop. Two PARALLEL16 NaN/zeros encodings of the same continuous raster each produce
  that overlap and are both retained as rows. Their random-control overlap is 0.765;
  chance-adjusted comparison is diagnostic only and does not waive the literal rule.
  Evidence: `evidence/uniqueness_h57_final.json`.
- **IR-55-049 (Medium; fixed in shared writer and validator contract).** The current
  strict validator requires NaN exactly outside the template footprint. The
  NaN-outside primary passes 11/11 checks. The all-finite zeros variant passes
  10/11 and fails only the null/NaN outside-footprint check; it is a diagnostic, not
  an upload candidate. `scripts/submission_writer.py` now names/packages the NaN
  output as primary and labels zeros as a diagnostic. Local format validation is
  not organizer clearance.
- **IR-55-050 (Medium; fixed in shared emitter). Random-control support bug in
  `emit_dots`.** The old `random=True` path applied `score > 0` before branching,
  so unbudgeted random controls in the historical exp8/exp9 analyses sampled only
  candidate-positive pixels instead of the full eligible set. The shared function
  now draws uniformly from eligibility alone, with a regression test. The current
  H57 holdout used `emit_dots_budgeted` because all arms had registry budgets, so
  its recorded result is unaffected. Historical exp8/exp9 controls were not rerun;
  they are not used for the current H57 decision, and no holdout rerun is authorized.

## H57 decision

Current status is **download for audit: YES; submit: NO**. The primary NaN-outside
TIF passes 11/11 strict local format checks; the zeros-outside diagnostic fails
1/11. Pre-placement surface correlation passes (max |Spearman| 0.2443), but final-dot
uniqueness is **DUPLICATE-STOP** against 66/66 rasters (max overlap 0.76 > 0.70),
and matched-mass HOLDOUT-DTI is negative. No organizer-confirmed score or receipt
exists.
