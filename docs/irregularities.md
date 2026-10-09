# Irregularities and review flags

These are explicit blockers or caveats, not hidden assumptions.

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

- **IR-55-025 (Medium). Validator resolution check was shape-based.** The "resolution is 100 m" check compared the shape, not the pixel size. Fixed once in `scripts/validate_submission.py`: the check now reads |a| and |e| from the transform. Both encodings pass (12/12 zeros, 11/11 NaN twin). Done.
- **IR-55-026 (Low). Feature-raster naming mismatch.** `prepare_data.py` and `run_tensor_lane.py` looked for `training_features.tif`, but the file on disk is `gems-geodawn-numerical-features.tif`. The same sha256 pin applies. Fixed once in both scripts. `prepare_data.py` exits 0 with all three pins OK. Done.
- **IR-55-027 (Medium). Sidecar selection picked the lexicographically last file.** "160000" sorts before "40000". `scripts/make_final_card.py` now writes `docs/run-card-h55-160k.json` for the audit file, and the stale `evidence/runcard.json` is superseded. Done.
- **IR-55-028 (High). Striping axis is unreconciled.** ScienceBase (Glen & Earney 2024, doi 10.5066/P93LGLVQ) says flight lines run at azimuth 90° (E–W). The lane masks rows (E–W lines). `evidence/striping_diagnostic.json` reports N–S on real RTP data, but its own coherence numbers are equal (0.185 along x, 0.187 along y). A crude high-pass test here (row-means std 6.3 vs column-means std 8.9; y/x gradient RMS 0.77) leans N–S. If the striping is N–S, the lane's 21% mask is on the wrong axis. Open: the flight-line shapefile (not reachable from the sandbox) would settle it. Do not cite the lane striping mask until then.
- **IR-55-029 (Medium). Two striping counts from two detectors.** 86,947 px (129 rows, z>4, `gems/tensor.py`, `docs/results/tensor_lane_results.json`) and 1,105,919 px (21.4%, coherence-based `gems55` mask, thresh 0.55, lag 60 px, `data/cache/lane_v1.meta.json`). These are not a miscount. Both are reported; the shipped audit file uses the 1,105,919-px mask.
- **IR-55-030 (Medium, blocking for submit). Literal uniqueness stop on the audit file.** `scripts/verify_unique.py` returns REVIEW. The raw 3-px statistic is 0.8401 against the spacing-5 lattice `13GEMSDOE…lattice-s5` (206,895 dots). A random control on that lattice scores 0.8389 (excess +0.0012). Spearman max 0.014, Jaccard max 0.031. Under the shared 70% rule this is DUPLICATE-STOP. It is chance-level overlap, not a copy. Owner decision required; no submit clearance. Evidence: `evidence/uniqueness_160000dots.json`.
- **IR-55-031 (Medium). The secondary protocol disagrees with the primary.** At N = 160k, B = 15 px gives tensor 0.0238 vs random 0.0212 (p = 0.004, positive); Q4 gives 0.1019 vs 0.1627 (negative). At N = 40k, B = 15 px is +0.0015 (p = 0.008); B = 30 px is +0.0009 (p = 0.20). Reported as is; the pre-registered rule (both protocols must pass) gives NEGATIVE. Evidence: `evidence/exp9_distance_band_v1_n40000.json`, `evidence/exp10_mass_sweep_v1.json`.
- **IR-55-032 (Medium). The holdout arm is not the shipped emitter.** exp10 restricts emission to each fold's withheld domain, excludes striping outright, and uses per-fold seeds. The shipped writer (`scripts/submission_writer.py`) uses the full footprint, down-weights striping by 0.25, and uses seed 55. The holdout therefore does not score the shipped file exactly. Disclosed; a full-footprint holdout needs a different protocol.
- **IR-55-033 (Low–Medium). Zeros versus NaN outside the footprint.** The rules say "null or nan". The earlier site chose zeros on the basis of the portal's [0, 1] range check. That reasoning is not verified against the portal. Confirm on the portal before relying on either encoding; the NaN twin is published for comparison only.
- **Superseded file.** The 40k audit file (`…40000dots-20261009T052235Z`, sha256 b7c7225d…) was removed from `docs/downloads/` on `main` by the parallel session. It is reproducible from `scripts/submission_writer.py --n-dots 40000` and its sidecar is `evidence/submission_h55-tensor2d-strikegate-40000dots-20261009T052235Z.json`.

## Leaderboard-review session (2026-10-09; IDs IR-55-034 to IR-55-040)

- **IR-55-034 (High, blocks submission). Competition data provenance.** The feature rasters in earlier sessions came from the sibling GitHub repository `buffedlizard55-lab/GEMSDOE` (`data/bridge/`), not from the DrivenData data tab. The data tab is login-gated (https://www.drivendata.org/competitions/306/competition-doe-gems/data/), and the problem page limits external data to sources the participant holds a licence for, "that permits the data to be used in this challenge and shared with the sponsor" (https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/, section "External datasets"). Hash pins came from that mirror and are not verified against DrivenData. `data/` is empty in this checkout. **Owner decision required** (see `docs/leaderboard-review-20261009.md` §7).
- **IR-55-035 (High, correction to the owner brief). Leaderboard figures.** The owner brief says 0.3195 is the highest score. The DrivenData public leaderboard shows **0.3774** at rank 1 (xiaofanhu) and **0.3195 at rank 7** (DARD) (`evidence/leaderboard_snapshot_20261009.json`). The 0.2778 entry is rank 16 under participant `extradr19`. The mapping from the GEMSDOE32 site name to that account is not verified. Public-leaderboard values are not ORGANIZER-CONFIRMED.
- **IR-55-036 (Medium). Three nearest-neighbour calculations disagree for one raster.** For the anchor `h33-2-b2`, `scripts/exp7_anchor_verdict.py` gives a mean dot-to-dot distance of 3.74 px (p10 2.83 px); `scripts/exp5_anchor_forensics.py` gives a mean of 15.02 px (p10 4.12 px); `scripts/exp6_anchor_mechanism.py` stores a **median** (12.08 px) under the key `nn_px_mean`. `evidence/anchor_forensics.json` also stores the user-supplied 0.2778 under a field named `organizer_confirmed_DTI`, which is a mislabel: the value is USER-SUPPLIED. Not yet reconciled; no conclusion depends on the exact value beyond "clustered".
- **IR-55-037 (Medium). Reference-solution output dtype and encoding.** The official notebook (`unet-mc-cv-reference-solution.ipynb`, cell 16 and 19) initialises the output with `np.zeros` (float64 by default) and writes that array with `dtype=y_final.dtype`. The spec requires float32 (https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/, "Submission format"). The repo's writer uses float32 (correct). The zeros-outside-footprint choice matches the reference, but neither is an organizer confirmation (see IR-55-033).
- **IR-55-038 (Medium). Uniqueness registry is incomplete.** `registry/registry.json` has 56 entries keyed by sibling-repo filenames. It does not cover the competitor sites the owner listed (for example the `h33-h33-2` family is not present by name). The literal 70% duplicate gate is therefore only as complete as this list. Owner must provide the full list of prior rasters before any uniqueness result is final.
- **IR-55-039 (High, validity). Holdout target mismatch.** The official problem statement says the test faults are **new** faults not in the public USGS database (https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/). The repo's holdout measures recovery of **catalogue** faults. On the whole-catalogue proxy (a different measure; the anchor was not run through the holdout) the 0.2778 anchor scores 0.0049 against 0.0321 for uniform random, yet it scores 0.2778 on the leaderboard. Every HOLDOUT-DTI ranking in this repo may therefore be on the wrong target. Tested by proposal T-D only.
- **IR-55-040 (Medium). Minimum dot separation.** The shipped writer enforces `min_sep_px = 3.0` (`scripts/submission_writer.py`, `src/gems55/holdout55.py`). Whether tighter packing helps is untested (candidate T-C). The 3 px rule was chosen for the lane, not from the metric.
