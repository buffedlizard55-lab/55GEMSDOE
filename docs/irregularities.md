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
