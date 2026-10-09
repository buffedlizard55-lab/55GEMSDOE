# Tensor-dimensionality hypotheses — preregistration shortlist

**Status (updated 2026-10-09): rank 1 (the tensor lane) was implemented and tested on the spatial holdout and is NEGATIVE (see the results section below). H-B to H-F are new, out-of-lane proposals: they were not implemented or evaluated, and each needs lane approval under AGENTS.md first.** The shortlist stays inside the assigned tensor-dimensionality lane. Relative opportunity and cost are qualitative research priorities—not `HOLDOUT-DTI`, not projections, and not scores. The checkout contains no code/data/registry, so novelty against the wider archive and performance against the current holdout best are not established.

## Candidate ranking

| Rank | Hypothesis and required layers | Physical signature | Why it could find a fault omitted from USGS / INGENIOUS | Difference from current repo and known prior work | Expected relative DTI opportunity / cost |
|---|---|---|---|---|---|
| **1** | **Joint RTP-magnetic + isostatic-gravity tensor dimensionality and strike concordance.** Competition-provided reduced-to-pole magnetic anomaly and isostatic gravity anomaly, plus official acquisition-block/flight-line footprints for processing controls. | Low-pass each acquisition block before FFT derivatives; form the symmetric potential-field gradient tensor; compute eigenvalue dimensionality and the quasi-2-D eigenvector strike; identify the local gradient-ridge axis; retain/weight only near-2-D ridges whose strike agrees with their own orientation; down-weight compact 3-D responses; remove flight-line striping. | A fault can produce a laterally persistent magnetic and/or density boundary even where no public fault trace is mapped. The signal is label-independent, so it can be tested on whole held-out catalogue segments; it is not derived by extending a visible line. It remains only a fault *candidate* until geological review. | No implementation exists in this checkout. The official template repository has no exact `evaluate_holdout.py` / `submission_writer.py` filenames and no demonstrated implementation of this exact tensor-index + strike-concordance filter. Sibling archives include `DILCOND`, magnetic-ridge, and magnetic/gravity cross-gradient concepts; their code and decoded rasters must be compared before claiming uniqueness. | **Highest priority; moderate-to-high scientific upside, unquantified. High cost** because block boundaries, spectral edge treatment, tensor stability, and strike/ridge agreement all need independent checks. |
| **2** | **Scale-persistent near-2-D strike filter.** Same RTP-magnetic and isostatic-gravity layers and the same four block geometries. | Recompute dimensionality/strike after a small, preregistered set of low-pass scales; preserve ridge candidates only when dimensionality class and axial strike remain stable across scales. This is a stability test of the same tensor lane, not a separate detector family. | A real structural edge may retain its orientation over scale while derivative noise, shallow compact bodies, and flight-line artifacts change more rapidly. Stable responses may reveal a buried continuation that is absent from the catalogue. | No implementation in this checkout. It differs from one-scale edge and cross-gradient methods reported by siblings, but the scale rule must be checked against all earlier rasters; no novelty claim yet. | **Second priority; moderate upside, unquantified. Medium/high cost** (repeat tensor calculations and freeze scales without holdout tuning). |
| **3** | **Gravity-only near-2-D tensor ridges.** Isostatic gravity anomaly only, with block mask. | Gravity Hessian eigenvalue index, near-2-D mask, strike from the smallest-absolute-eigenvalue eigenvector, and ridge/strike concordance. | A density boundary at a basin margin or basement offset may continue beyond mapped traces and may be weak in magnetics. This is an independent modality ablation and avoids magnetic remanence as a direct source of strike disagreement. | No such tensor implementation in this checkout. Sibling reports mention simple horizontal-gravity-gradient ridges; those are not the same statistic as the full eigenvalue dimensionality index plus strike test, but the raster-level overlap still has to be measured. | **Third priority; low-to-moderate upside, unquantified. Medium cost.** |
| **4** | **RTP-derived pseudogravity tensor.** Reduced-to-pole magnetic anomaly, transformed to pseudogravity with declared field/magnetization assumptions, then the same tensor dimensionality and strike analysis. | Quasi-2-D eigenvalue signature and strike from the pseudogravity gradient tensor. | A source geometry expressed through pseudogravity may yield a more interpretable structural strike than raw RTP for a long contact or fault, including an unmapped continuation. | The method is distinct from raw magnetic ridge or magnetic/gravity cross-gradient scoring, but the 2011 method's assumptions and the archive's `DILCOND` work must be checked. No pseudogravity tensor is implemented in this checkout. | **Fourth priority; low-to-moderate upside, unquantified. Medium/high cost** because the magnetization-direction assumption and transform conditioning are additional risks. |

## Prior-art boundary and external data

- **Within this project checkout:** the original branch had no scientific code; the current work adds project documentation and site checks only. No candidate implementation exists here to differentiate from.
- **Sibling archive:** GEMSDOE26 publishes a `DILCOND` result and GEMSDOE54 publishes magnetic-ridge/cross-gradient work. These owner-maintained reports are relevant warnings, not proof that the exact tensor method is new or already tested. A complete decoded-pixel and source-code registry scan is required before placement.
- **Competition bands:** the official problem description lists reduced-to-pole magnetic anomaly and isostatic gravity anomaly in `training_features.tif`. The data page redirected to login in this review; the rasters are not in this checkout.
- **Block and line metadata:** the official USGS GeoDAWN release states that the survey has four acquisition blocks and lists flight paths/survey outlines among its released files. It is public and marked CC0 on the USGS page. The exact polygons/flight paths have not been downloaded, intersected with the competition grid, or checksum-pinned here. Source: [USGS GeoDAWN data release](https://doi.org/10.5066/P93LGLVQ) and [overview](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and).

No candidate in this list requires a new geothermal observation dataset to formulate the test. If the block masks/flight-line data cannot be recovered from the shared cache, the named official fallback is the USGS GeoDAWN ScienceBase release linked above. It is publicly listed, but it is **not locally available in this checkout**, so the candidate is not yet runnable.

## Frozen validation plan (not run)

1. Identify the authoritative shared feature stack, whole-segment evaluator, writer, and registry. Do not substitute a private fork. Verify tool code and version before any fit.
2. Freeze block polygons, FFT window/taper, low-pass bandwidth(s), dimensionality definition, ridge-orientation estimator, strike tolerance, stripe mask, and compact-body down-weight before querying holdout outcomes. Process each of the four official acquisition blocks independently.
3. For each feature/rule alone, run the leak canary. AUC above 0.90 is leakage until proven otherwise. Recompute every label-derived channel from visible catalogue segments only.
4. Withhold whole fault segments with a buffer; mask visible catalogue pixels exactly; use the shared evaluator to pool `HOLDOUT-DTI` at the organizer's α=0.2, β=0.8, 300 m triangular kernel. Report evaluator version, withheld-positive count, and paired whole-segment 95% CI.
5. Test the prespecified strike prediction: compare axial strike agreement on held-out fault segments against matched random ridges. No result is reported until the shared evaluator returns it.
6. Compare the continuous candidate surface with every registry raster before placement. Stop and log duplicate if |Spearman ρ| exceeds 0.90 or more than 70% of placed dots fall within 3 px of a registry raster. Repeat on final dots. The current registry is absent, so this gate cannot pass.
7. Compare only with a same-evaluator current holdout best. No comparable baseline exists in this checkout. Do not spend a competition slot or publish a candidate TIFF before every gate passes.

## Named non-fault mimics to preregister

- Long lithologic contacts, dikes, and intrusive sheets can be two-dimensional or strike-extended without being faults.
- Compact intrusions, volcanic/vent bodies, and topographic or magnetic source edges can make 3-D signatures.
- East–west flight lines, tie lines, block seams, leveling/micro-leveling residuals, and FFT wraparound can create artificial ridges or preferred orientations.
- Isostatic/gravity correction artifacts, remanent magnetization, and imperfect RTP/pseudogravity assumptions can shift or rotate a geophysical signature.

A tensor dimensionality index is a source-geometry discriminator under potential-field assumptions, not a fault detector by itself. Geological interpretation and the held-out prediction test remain necessary.


## Reconciliation with the earlier ranked table (2026-10-09)

- Rank 1 in the table above is the tensor lane. It has since been run. Its final HOLDOUT-DTI result is negative on the primary Q4 protocol: 0.1019 vs 0.1627 random at N = 160,000 (see the 2026-10-09 final-pass section below and docs/run-card.json).
- The "registry absent, gate cannot pass" note in the frozen validation plan (step 6) is out of date. The registry is present (56 rasters, scripts/build_registry.py). verify_unique.py gives REVIEW for the final file (IR-55-030).
- The earlier results section below comes from a concurrent session. Its numbers use 60,594 withheld positives and labels E1–E3. This session uses 60,988 withheld positives and labels exp8, exp9 and exp10. The two sets are not interchangeable and neither has been overwritten.
- The "Strike test: failed" line below is contested. IR-55-017 and the strike-test entry in the run card both record this. The holdout_v1 strike test confirmed a strike prediction at 0.302 vs 0.222 (500 segments). The two protocols differ.

## New hypotheses H-B to H-F (2026-10-09) — ranked by expected DTI gain, then cost

Break-even bar for any new dot (computed, not assumed): a dot raises DTI only if its expected kernel credit exceeds alpha·DTI/(1+alpha·DTI). At the random control DTI 0.0757 this is 0.2×0.0757/1.0151 ≈ **0.0149 per dot**. Gain labels below are priors, not measurements, and are not HOLDOUT-DTI. H-A (visible-prior gate, exp8/exp9) was tested before this list and failed; it is not repeated here.

| Rank | Hypothesis | Layers (band numbers from docs/data_dictionary.md) | Physical reasoning | Expected DTI gain (prior) | Implementation cost | Out of lane? |
|---|---|---|---|---|---|---|
| 1 | **H-F — 1 m lidar DEM scarp detection.** Fault scarps in young alluvium show as topographic steps. | 1 m DEM from USGS 3DEP (not in the competition stack) | Quaternary faults in the label set are usually expressed as scarps; a scarp map is the most direct independent evidence for an unmapped trace. | **High** (potentially the largest, unquantified) | **High**: 3DEP tiles not reachable from this sandbox (curl returned 000 for prd-tnm S3); large download; scarp detector needs its own canary. | Yes. Blocked on data access. |
| 2 | **H-B — depth-to-basement step.** A fault offsets the magnetic basement, so the depth surface shows a step across the trace. | 15 (depth to basement), 2 (RTP mag) | A fault can offset basement without any surface trace, so the step is independent of mapping. | Moderate (partly redundant with ridge detectors on band 2) | Medium: derivative of an existing band, co-location with ridges, sensitivity to the basement-model interpolation. | Yes (not a tensor method). |
| 3 | **H-D — geodetic strain-rate corridors.** Unmapped faults sit in deforming crust. | 4 (second invariant), 7 (shear rate), 8 (dilatation rate) | Strain accumulates on structures whether or not they are mapped. | Low–moderate (coarse grid; interpolation artefacts likely) | Low–medium: bands are provided; needs a leakage canary on the strain-derived features. | Yes. |
| 4 | **H-C — tilt-angle zero-contour.** Zero-contours of the tilt angle locate horizontal edges. | 6 (tilt / total curvature) | Standard edge-location method (citation not verified in this session; do not cite until it is). | Low–moderate. Highly redundant with the tensor lane's ridges, which use the same field derivatives. | Low: band provided, contouring is simple. | Yes. |
| 5 | **H-E — seismicity lineaments.** Earthquake density and distance trace active structures. | 10 (distance to earthquake), 16 (earthquake intensity) | Seismicity clusters along active faults. | Low. Leakage risk: the seismic layers are derived from an external catalogue, so the canary must run first. | Low: bands provided. | Yes. |

Ordering rationale: rank 1 has the largest physical upside but is blocked, so its cost is high and its gain is untested. Ranks 2–4 use bands already in the stack, so their costs are lower, but their redundancy with the tensor lane limits their gain. Rank 5 is cheap but has a leakage risk.

**Nothing in H-B to H-F has been implemented or evaluated.** AGENTS.md keeps this checkout to the tensor-dimensionality lane, so each candidate needs lane approval, a preregistered plan, a leakage canary (AUC > 0.90 = leakage), a held-out evaluation, and the uniqueness gate before any slot is considered.

## Result of the tensor-lane run (2026-10-09) — HOLDOUT-DTI

Evaluator `gems.metric v1` (DTI α=0.2, β=0.8, R=300 m). Holdout = four quadrant folds of catalogue fault segments, visible faults masked pixel-exactly. 60,594 withheld positive pixels. 95% CI from a 1,000-rep block bootstrap (10 km blocks).

| Experiment | Hypothesis tested | HOLDOUT-DTI | 95% CI |
|---|---|---|---|
| E1 | Gradient ridges of RTP (stripe rows masked). Reference, not a tensor test | **0.0578** | 0.0499 – 0.0652 |
| E2 | E1 weighted by (1 − dimensionality index), magnetic pseudogravity tensor | 0.0463 | 0.0398 – 0.0523 |
| E3 | E2 combined with the gravity index and a strike-agreement gate (candidate lane method) | 0.0444 | 0.0383 – 0.0502 |

Leakage canary: every single feature has AUC 0.48–0.52 on ridge pixels (threshold 0.90): no leakage detected, but also little discriminative signal. Strike test: **failed** (43.2% vs 87.6%; design caveat IR-55-017). Budget used: 3 experiments.

**Verdict for the tensor lane: negative.** From E1 to E2 the weighted true positives fell from 3,794 to 2,816 and false positives from 82,002 to 59,039, while missed positives rose from 56,800 to 57,778. The weight removed signal and noise at similar rates, so the Tversky score fell. This is the opposite of the lane's premise and is recorded as a result. Possible next experiments (within the lane only): pixel-matched strike test, and a chance-corrected uniqueness check.

Out-of-lane ideas (tilt-angle zero-contours, geodetic strain, seismicity alignments, 1 m DEM scarps) were drafted in this session and are **parked**. `AGENTS.md` keeps this checkout to the tensor lane, so they are not implemented here. They need a separate lane approval and their own preregistration.

## Final pass of the tensor lane (2026-10-09, this session) — HOLDOUT-DTI

Evaluator: src/gems55/dti55.py (exact official DTI; verified against a brute-force transcription and the official worked example). Protocols: Q4 quadrant hide-and-recover (PRIMARY) and B = 15 px distance-banded whole-segment folds (SECONDARY). Withheld positives: 60,988. Labels: HOLDOUT-DTI in every case. No organiser score exists.

| Experiment | What it tested | Result |
|---|---|---|
| exp8 run 2 | H-A visible-prior gate | Q4 fails (H-A-500 0.0521 vs random 0.0742); promote = false |
| exp9 | H-A at distance bands 3, 15, 30 px | H-A fails at every band ≥ 1.5 km (B15: H-A-500 0.0001, worse than random in all 10 folds) |
| exp10 | Dot-mass sweep, N ∈ {20k, 40k, 80k, 160k} | Q4: tensor_full 0.0459 / 0.0666 / 0.0889 / 0.1019 vs random 0.0422 / 0.0742 / 0.1202 / 0.1627 |

- **Pre-registered file: N* = 160,000** (argmax of tensor_full on Q4). Label: **NEGATIVE**. Audit note: tensor_full's Q4 score rises monotonically with N, so the argmax sits on the upper edge of the tested grid. The rule therefore selects the largest N tested; a larger N was not tested and the budget is spent. Q4 loses to random at N = 40k, 80k and 160k. At N = 20k it is +0.0030 (p = 0.25, not significant).
- Secondary, B = 15 px: tensor beats random at N = 40k (+0.0015, p = 0.008) and N = 160k (+0.0026, p = 0.004), but not at 80k (p = 0.20). The sign depends on the protocol (IR-55-031). The primary governs under the rule.
- Shipped file: docs/downloads/h55-tensor2d-strikegate-160000dots-20261009T164334Z-zeros.tif (sha256 ffd2a892…). Validator 12/12. Uniqueness REVIEW (IR-55-030). Note that the holdout arm differs from the shipped emitter (IR-55-032).
- Budget: 3 of 3 experiments used.
