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
