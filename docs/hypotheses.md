# Candidate hypotheses (ranked) — not yet all validated

Gate for every candidate (protocol): validate on the spatially blocked holdout first. Do not spend a
submission slot on an idea that does not beat the current holdout best. **Current holdout bar in this repo:
E1 ridge baseline, HOLDOUT-DTI 0.0578, 95% CI [0.0499, 0.0652], 60,594 withheld positive px** (evaluator
`gems.metric v1`). Band names below are from the GeoTIFF band tags (full list: [data dictionary](data_dictionary.html)).

| Rank | Hypothesis | Layer(s) (band #) | Physical signature targeted | Why it should catch a *missing* fault | Named non-fault mimic | Cost | Status |
|---|---|---|---|---|---|---|---|
| 1 | **Tilt-angle zero-contours** pick out buried, low-contrast faults that amplitude gradients miss | `tc` tilt/total curvature (6); RTP (2) | Zero-crossing of the tilt angle marks the edge of a source regardless of amplitude | Amplitude-normalised: weak but sharp faults show a clean zero-contour, while a strong sediment-hosted anomaly does not swamp it. Uses a layer we have not used | Lithologic contacts and basalt flow edges (2-D, non-fault) | Low (one FFT pass) | **Not tested** — next experiment |
| 2 | **Geodetic strain-rate localisation** | shear rate (7), second invariant (4), dilatation (8) | Ridges of shear-rate magnitude where deformation localises | Active faults localise strain; faults with no surface expression can still show a shear-rate ridge | GPS/InSAR processing artefacts and broad plate-boundary strain | Low (layers present) | **Not tested**. Check the native resolution of the geodetic layers before use |
| 3 | **Seismicity alignment** | earthquake intensity (16), distance to earthquake (10) | Linear alignments of hypocentres and minima of distance-to-event | Microseismicity clusters along unmapped faults | Induced seismicity, mine blasts, and population-density clustering | Low | **Not tested**. The meaning of the n=100 km, a=15° parameters must be confirmed from the official data dictionary |
| 4 | **Topographic scarp detection at 1 m** | detrended elevation slope (19); 1 m DEM (external) | Sharp linear scarps in high-resolution topography | Scarps are direct evidence of young faulting and are absent from the USGS catalogue for many faults | Erosion lines, roads, canals, and field boundaries | High: needs the USGS 1 m DEM tiles | **Blocked here.** The official host (`prd-tnm.s3.amazonaws.com`), the National Map downloader, and ScienceBase all failed to connect from this sandbox (2026-10-09, curl HTTP 000). Free and official, but must be fetched from a machine with open egress |
| — | **Tensor dimensionality + strike gating** (this session) | RTP (2), iso gravity (13) | 2-D ridges with strike agreeing with ridge orientation; down-weighted 3-D bodies | Targets strike-extended structures | E-W flight-line striping (masked); 2-D contacts and dykes | Medium | **Tested, negative.** E1 0.0578 > E2 0.0463 > E3 0.0444. Strike test failed (see caveat, irregularity #8). Canary AUC ≈0.5 (no leakage, but weak signal) |

## Notes on the ranking
- Ranking is judgement: expected DTI gain × (1 / implementation cost). None of ranks 1–4 is yet validated, so no expected gain is claimed as a number.
- The tensor lane (row "—") is kept as a reference result. Its negative holdout result argues that 2-D-ness alone does not separate catalogue faults from other ridges in this area.
- Anything that gets to submission must pass: holdout beats E1's CI lower bound (or a pre-registered margin), canary AUC ≤ 0.90, and the chance-corrected uniqueness check (irregularity #7).
