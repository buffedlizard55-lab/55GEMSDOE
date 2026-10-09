# Candidate hypotheses before experiment H56

**Preregistration time:** 2026-10-09 UTC. **Lane:** tensor dimensionality only.
These are proposals, not scores and not leaderboard projections. The ordering is a
research priority, not a measured ranking. The current implementation already has
one-scale FFT tensors, magnetic/gravity ridge corroboration, dimensionality
weighting, a strike-agreement weight, and a survey-line mask; the candidates below
must therefore add a falsifiable tensor-lane property rather than rename the same
surface.

## Ranking

| Rank | Candidate; layers | Physical signature targeted | Why it can find an omitted fault | Difference from this repo | Expected DTI opportunity / implementation cost |
|---|---|---|---|---|---|
| **1** | **Multi-scale tensor persistence.** Band 2 reduced-to-pole magnetic anomaly and band 13 isostatic gravity anomaly. | Recompute the low-pass FFT gradient tensor at two preregistered structural scales (300 m and 900 m Gaussian spatial sigma); retain the geometric mean of the two scale scores, with a separate persistence fraction for near-2-D and strike concordance. | A mapped fault continuation should preserve a strike-extended tensor geometry over a range of wavelengths, while derivative noise, block-edge ringing, shallow cultural/flight-line artefacts, and compact sources are less persistent. The test uses no catalogue geometry to create the signal, so it can target faults absent from USGS/INGENIOUS. | The repo has one 400 m low-pass surface. It does not require the same pixel to remain a near-2-D, strike-concordant ridge at more than one scale. | **Highest expected opportunity; moderate/high cost.** Only existing competition rasters are needed. The exact scales are frozen before holdout; no holdout tuning is allowed. |
| **2** | **Cross-field tensor strike-consensus.** Band 2 RTP magnetics + band 13 isostatic gravity. | Use the axial circular resultant of the magnetic and gravity tensor strikes, rather than the current arithmetic mean of two angular differences; require a high resultant length and low dimensionality in both fields. | A fault-related boundary can be weak in one potential field but its structural strike should be coherent where both fields resolve it. A compact body or lithologic contact may produce modality-specific strikes and be down-weighted. | The current lane averages two field-specific agreement angles and ridge ranks; it has no explicit axial circular-consensus confidence or discordance channel. | **Moderate opportunity; moderate cost.** No external data. It is a distinct multi-field geometry test, but it may reduce recall when gravity is weak. |
| **3** | **Eigenvalue-sign/shape stability.** Same bands 2 and 13. | In addition to the scalar dimensionality invariant, require the ordered eigenvalue pattern and the intermediate-eigenvector horizontal plunge to be stable under a 180°-invariant tensor sign convention at both modalities. | Long faults should produce a coherent saddle/line-of-poles signature along a trace; compact 3-D bodies and tensor degeneracies should have less stable eigenvalue ordering. This is label-independent and can find an unmapped continuation. | The current lane uses the invariant and a plunge multiplier but does not test local eigenvalue-shape stability or degeneracy margin. | **Moderate/low opportunity; moderate cost.** No external data. Risk: sign is physical-field dependent, so the test must be documented and not treated as a fault classifier by itself. |
| **4** | **Blockwise tensor normalization with official flight-line/block masks.** Bands 2 and 13 plus GeoDAWN acquisition-block and flight-path metadata. | Compute the FFT tensor independently per official acquisition block, remove each block's robust long-wavelength level, and mask line/tie-line coherence only within that block. | The USGS data release documents four acquisition blocks and different flight specifications. A real fault can cross a block seam; an edge caused by leveling or a seam should not. Processing by the true block geometry may recover structure currently suppressed or prevent false ridges. | The repo currently uses one grid-wide FFT and a configurable along-axis profile; it does not have verified block polygons/IDs in the competition stack. | **Potentially high opportunity; high cost and currently blocked.** Official fallback is the USGS GeoDAWN ScienceBase release, DOI `10.5066/P93LGLVQ`; it is publicly listed, but the exact block polygons must be downloaded, intersected with EPSG:32611, and checksum-pinned before this candidate is viable. No implementation or score is claimed now. |
| **5** | **RTP-to-pseudogravity tensor sensitivity ensemble.** Band 2 RTP magnetic anomaly; band 13 remains the independent gravity comparator. | Apply an explicitly declared pseudogravity Fourier transform for a small, preregistered set of magnetization-direction assumptions, then keep only strike/dimensionality responses stable across assumptions. | A fault/contact may be structurally real but its magnetic response depends on magnetization. Stability across plausible directions can suppress remanence-specific compact anomalies and retain a buried, strike-extended boundary not in the catalogue. | The current code differentiates the RTP field directly and documents that as a proxy; it does not implement the magnetic-to-pseudogravity transform or a direction-sensitivity test. | **Potentially moderate opportunity; high cost/high risk.** No new dataset is required, but a magnetization direction is an assumption. The method is not viable for a submission until the transform convention and its effect on synthetic fields are independently tested. |

## Source checks and external-data gate

The official competition problem page was fetched on 2026-10-09 and supports the
following statements:

* The task is fault prediction for geothermal-resource mapping, not direct vent
  detection. It lists RTP magnetic anomaly and isostatic gravity among the provided
  features and defines the distance-weighted Tversky metric with alpha 0.2, beta
  0.8, and 300 m support: [DrivenData problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/).
* The official source for the survey context is the USGS GeoDAWN data release,
  DOI [10.5066/P93LGLVQ](https://doi.org/10.5066/P93LGLVQ), with the USGS overview
  at [usgs.gov/data/geodawn...](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and).
  The overview states that the release contains flight-path information and four
  acquisition blocks, and describes magnetic tie-line leveling and micro-leveling.
* The tensor rationale is grounded in the cited peer-reviewed literature: [Pedersen
  & Rasmussen (1990), DOI 10.1190/1.1442807](https://doi.org/10.1190/1.1442807),
  [Beiki & Pedersen (2010), DOI 10.1190/1.3484098](https://doi.org/10.1190/1.3484098),
  and [Beiki, Pedersen & Nazi (2011), DOI 10.1190/1.3555343](https://doi.org/10.1190/1.3555343).
  The 2011 abstract explicitly makes the pseudogravity transform conditional on a
  known magnetization direction; this is why candidate 5 is not silently assumed.
  An open explanation of the dimensionality invariant is [Karimi & Kletetschka
  (2024), Scientific Reports](https://pmc.ncbi.nlm.nih.gov/articles/PMC11333590/).

Candidates 1, 2, and 3 use only the already placed competition rasters, so they do
not need a new external-data license. Candidate 4 is **not runnable yet** until the
USGS block/flight metadata are downloaded and aligned. Candidate 5 needs no new
file but does need a synthetic transform validation; neither candidate 4 nor 5 is
allowed to enter a submission slot on a projection.

## Frozen validation plan

1. Establish the current holdout best with the canonical `src/gems55/dti55.py`,
   `scripts/evaluate_holdout.py`, and `scripts/submission_writer.py`. Hold out
   whole catalogue segments with a 3-pixel buffer, recompute catalogue-derived
   masks per fold, mask visible faults pixel-exactly, and pool TP/FP/FN before the
   DTI ratio.
2. Test each feature/rule alone as a leakage canary. Any AUC above 0.90 is leakage
   until explained. Numbers must carry the evaluator version, withheld-positive
   count, and 95% CI.
3. Run no more than three experiments. H56 is selected because it is the only
   candidate that adds a scale-persistence invariant without new data. It must
   beat the preregistered ridge/strike-consensus holdout best; otherwise its result
   is a negative deliverable.
4. Run the continuous-surface uniqueness check before placement and the final-dot
   check after placement. A rank correlation above 0.90 or more than 70% of dots
   within 3 pixels of one registry raster is a duplicate and stops the run.
5. Write a TIF only after the format validator, uniqueness checks, and holdout
   evidence are recorded. A format-valid TIF is not an organizer-confirmed score.

## Prior-run status

The previous one-scale tensor run used a quadrant-style evaluator and is **not the
current baseline** for this experiment. It is retained as historical evidence, not
combined with the segment holdout below. The evaluator design correction is logged
in `docs/irregularities.md` and the new results will replace stale status claims.

## Out-of-lane hypotheses H-B to H-F (2026-10-09, tensor-lane final pass)

These are **proposals only**. None has been implemented or evaluated. AGENTS.md keeps this checkout to the tensor-dimensionality lane, so each one needs lane approval before any work. Gain labels are priors, not measurements, and are not HOLDOUT-DTI.

Break-even bar for any new dot: expected kernel credit above α·DTI/(1+α·DTI). At the random control DTI 0.0757 (HOLDOUT-DTI, 60,988 withheld positives) that is **≈ 0.0149 per dot**. H-A (visible-prior gate) was tested earlier in this session and failed, so it is not repeated here.

| Rank | Hypothesis | Layers (band no., `docs/data_dictionary.md`) | Physical reasoning | Expected DTI gain (prior) | Implementation cost | Status |
|---|---|---|---|---|---|---|
| 1 | **H-F: 1 m lidar DEM scarp detection.** Fault scarps in young alluvium show as topographic steps. | 1 m DEM from USGS 3DEP (not in the competition stack) | Quaternary faults in the label set usually show as scarps. A scarp map is the most direct independent evidence for an unmapped trace. | High (potentially largest, unquantified) | High: 3DEP tiles unreachable from this sandbox (curl returned 000 for the prd-tnm S3 host); large download; scarp detector needs its own canary | Blocked on data access; out of lane |
| 2 | **H-B: depth-to-basement step.** A fault offsets the magnetic basement, so the depth surface shows a step across the trace. | 15 (depth to basement), 2 (RTP mag) | A fault can offset basement without a surface trace, so the step is independent of mapping. | Moderate (partly redundant with ridge detectors on band 2) | Medium: derivative of an existing band, co-location with ridges, sensitivity to basement-model interpolation | Out of lane; not built |
| 3 | **H-D: geodetic strain-rate corridors.** Unmapped faults sit in deforming crust. | 4 (second invariant), 7 (shear rate), 8 (dilatation rate) | Strain accumulates on structures whether or not they are mapped. | Low–moderate (coarse grid; interpolation artefacts likely) | Low–medium: bands provided; leakage canary first | Out of lane; not built |
| 4 | **H-C: tilt-angle zero-contour.** Zero-contours of the tilt angle locate horizontal edges. | 6 (tilt / total curvature) | Standard edge-location method (citation not verified in this session; do not cite until it is). | Low–moderate. Highly redundant with the tensor lane's ridges, which use the same field derivatives. | Low: band provided; contouring is simple | Out of lane; not built |
| 5 | **H-E: seismicity lineaments.** Earthquake density and distance trace active structures. | 10 (distance to earthquake), 16 (earthquake intensity) | Seismicity clusters along active faults. | Low. Leakage risk: derived from an external catalogue, so the canary must run first. | Low: bands provided | Out of lane; not built |

Ordering: rank 1 has the largest physical upside but is blocked, so its cost is high and its gain is untested. Ranks 2–4 use bands already in the stack, so their costs are lower, but their redundancy with the tensor lane limits their gain. Rank 5 is cheap but carries leakage risk.

## Tensor-lane final pass — HOLDOUT-DTI (2026-10-09, h55 audit file)

Evaluator `src/gems55/dti55.py` (exact official DTI). Protocols: Q4 quadrant hide-and-recover (PRIMARY) and B = 15 px distance-banded whole-segment folds (SECONDARY). Withheld positives 60,988. Audit page: `docs/h55-160k-audit.html`.

| Experiment | What it tested | Result |
|---|---|---|
| exp8 run 2 | H-A visible-prior gate | Q4 fails (H-A-500 0.0521 vs random 0.0742); promote = false |
| exp9 | H-A at distance bands 3, 15, 30 px | H-A fails at every band ≥ 1.5 km (B15: H-A-500 0.0001, worse than random in all 10 folds) |
| exp10 | Dot-mass sweep, N ∈ {20k, 40k, 80k, 160k} | Q4 tensor_full 0.0459 / 0.0666 / 0.0889 / 0.1019 vs random 0.0422 / 0.0742 / 0.1202 / 0.1627 |

- **Pre-registered N\* = 160,000** (argmax of tensor_full on Q4; upper edge of the grid, so the largest N tested). Label **NEGATIVE**. Q4 loses to random at 40k, 80k and 160k. At 20k it is +0.0030 (p = 0.25, not significant).
- Secondary B = 15 px: tensor beats random at 40k (+0.0015, p = 0.008) and 160k (+0.0026, p = 0.004), not at 80k (p = 0.20). The sign depends on the protocol (IR-55-031). The primary governs under the rule.
- Audit file: `docs/downloads/audit-h55-160k/h55-tensor2d-strikegate-160000dots-20261009T164334Z-zeros.tif` (sha256 ffd2a892…). Validator 12/12. Uniqueness BLOCKED under the literal 70% rule (IR-55-030). **DO NOT SUBMIT.** Download for audit only.
- Budget: 3 of 3 experiments used.

## Session 2026-10-09 (leaderboard review) — new candidates T-A to T-D

**Status: proposals only. Nothing below is implemented, scored, or submitted.** The
feature stack is not on disk, so none of these can be validated in this session. Layer
names are taken from the official problem page
(https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/, section
"Provided features"). Band numbers are **not** verified here, because the band-order
metadata lives in the data file that is missing. Each candidate names its band by
description only.

Ranking is by expected DTI improvement, then implementation cost. T-D is an enabler (a
validation fix), not a candidate, so it is ranked separately.

| Rank | Candidate; layers | Physical signature | Why it can find an omitted fault | Difference from this repo | Expected opportunity / cost |
|---|---|---|---|---|---|
| **T-A** | **Source-depth step across tensor ridges.** Layer: "Magnetics … top-of-crustal magnetic source depth estimate" (band number to be read from tags). Gated by the existing tensor ridge and strike. | A fault offsets the magnetic source depth, so a lateral **step** in source depth should lie along the ridge and parallel its strike. A compact intrusion gives a closed depth **minimum**, not a line-parallel step. | The depth step comes from the field itself, not from the catalogue, so it can flag an uncatalogued trace. | The repo uses bands 2, 12, 13, 14, 9 and 18 (`src/gems55/io55.py`). It does not use the depth layer, and it has no step-vs-minimum test. | Moderate opportunity, moderate cost. **Mimic to test:** basin-margin or lithologic depth contacts, and depth-estimate artefacts at flight-line edges. |
| **T-B** | **Seismicity-density consensus on tensor ridges.** Layer: "Density of earthquakes". Keep a tensor-gated ridge only when the seismicity-density ridge agrees in position and strike. | Active faults concentrate epicentres along strike. This signal is independent of the fault catalogue. | Seismicity is a separate, active-structure signal. It can support a new trace that is not yet mapped. | No current use of the seismicity layer in `src/` or `scripts/`. | Moderate opportunity, low cost. **Mimic:** injection or quarry seismicity, and network-coverage bias in the density layer. Overlaps H2 only partly (H2 uses magnetics and gravity). |
| **T-C** | **Tight-packed chain placement along the top tensor ridges.** No new layer; changes the emitter. | Under the official kernel a dot 1–2 px from a true trace costs little FP and earns TP. A sparse, tightly packed chain along the most probable trace should beat the repo's 3 px-spaced placement. Derived from the anchor forensics, not yet measured. | Chains can sit on an uncatalogued continuation of a strong ridge, which the catalogue holdout cannot test. | `scripts/submission_writer.py` and `src/gems55/holdout55.py` `emit_dots` enforce `min_sep_px = 3.0`. The anchor's own evidence reports dot spacing below 3 px in one computation (IR-55-036). | High opportunity if the reasoning holds, low cost. **Mimic:** any linear artefact (striping, levelling seams, FFT ringing) that is also strongly ridged. **Must not be scored with the catalogue holdout alone** (see T-D). |
| **T-D** | **Enabler: a dated, official "new faults" holdout.** Use the USGS Quaternary Fault and Fold Database (DOI 10.5066/P9BCVRCK; ScienceBase item 589097b1e4b072a7ac0cae23, last update 2020-09-02, change log and GIS zip listed) to define faults that appear in a later release but are absent from the competition's label snapshot. | Not a physical signature. This makes the holdout target match the leaderboard's target (new faults). | The current holdout asks whether a method recovers catalogue faults. The official target is new faults. T-D tests whether the ranking holds on the right target. | The repo's holdout (`scripts/evaluate_holdout.py`) uses hide-and-recover on the competition catalogue only. | Enabler, not a DTI gain. Low/moderate cost. **Needs:** the competition label snapshot date (not verified), and a download of the ScienceBase GIS zip, which the sandbox cannot reach. |

**Validation plan (applies to every candidate; no holdout tuning allowed).** 1) Leakage
canary: test each new feature alone; AUC above 0.90 means leakage until proven otherwise.
2) Score on the existing hide-and-recover holdout with the existing evaluator and
the pinned seeds, with HOLDOUT-DTI and a 95% CI. 3) Score on the T-D new-fault holdout
once it exists, and report any disagreement between the two. 4) Registry check
(correlation and overlap) before placement and on final dots. 5) Only then consider a
weekly slot (three per week, rules §3.2).

**Do not promote any candidate on the current holdout alone.** The anchor scores 0.2778
on the leaderboard while scoring worse than random on the whole-catalogue proxy (see
`docs/leaderboard-review-20261009.md`).
