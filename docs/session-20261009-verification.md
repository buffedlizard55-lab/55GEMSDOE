# Session 2026-10-09: line-by-line verification log

**Disposition: NOT CLEARED — DO NOT DOWNLOAD OR SUBMIT (unchanged).** This session did not produce a GeoTIFF, did not run an experiment, did not use a submission slot, and did not download any competition file. The organizer inputs are absent from this checkout and the sandbox cannot reach the data host, so no candidate could be built or evaluated. Negative and blocked outcomes are recorded as deliverables.

Evidence labels used below: **OFFICIAL-VERIFIED** (read from an official page or document this session), **REPO-VERIFIED** (checked by running or reading the repository), **SECONDARY** (bibliographic index, not the publisher page), **NOT VERIFIED** (stated but not checked). No score here is a HOLDOUT-DTI or ORGANIZER-CONFIRMED value.

## 1. Access and data availability

| # | Claim | Check performed | Result | Evidence |
|---|---|---|---|---|
| A1 | The official data tab requires login. | `fetch_page` on the DrivenData data tab. | **Confirmed.** It redirects to `accounts/login/?next=/competitions/306/competition-doe-gems/data/`. | [DrivenData data tab](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) — OFFICIAL-VERIFIED |
| A2 | The sandbox cannot reach the data hosts. | `curl` to DrivenData, Dropbox, NLR, OpenEI, and epsg.io. | DrivenData, Dropbox, NLR, OpenEI, and epsg.io returned no response (`000`). GitHub, PyPI, and npm returned 200. | REPO-VERIFIED (shell check, 2026-10-09) |
| A3 | `fetch_page` reads some official pages that `curl` cannot reach. | `fetch_page` on the problem page, rules PDF, leaderboard, and NOAA page. | It returned text. This tool reads pages only and does not save files, so no competition file was obtained. | OFFICIAL-VERIFIED (read-only) |
| A4 | The `data/` directory holds only READMEs. | `ls -la data/`. | Only `README.md` and `SOURCES.md` are present. The three canonical rasters are absent. | REPO-VERIFIED |
| A5 | `scripts/prepare_data.py` fails closed. | Ran `python scripts/prepare_data.py`. | Reports MISSING for `gems-geodawn-numerical-features.tif`, `labels.tif`, and `sample_submission.tif`; exit code 1. | REPO-VERIFIED |
| A6 | The local validator fails closed on the archived raster. | Ran `scripts/validate_submission.py` on the archived H55 40k `zeros` file (read-only). | Result: NOT CLEARED. Failed on the missing organizer template. No output was written. | REPO-VERIFIED |
| A7 | The registry holds enough to check uniqueness. | Read `registry/registry.json`. | 56 entries. Each has repo, path, scored key, size, `n_pos`, and dtype. It has **no dot coordinates, no raster hashes, and no rasters**. A literal uniqueness check cannot be run from it. | REPO-VERIFIED |

## 2. Official competition rules, metric, and format

| # | Claim | Source text (verbatim where quoted) | Result | Evidence |
|---|---|---|---|---|
| M1 | Metric is distance-weighted Tversky, α=0.2, β=0.8, triangular kernel with R=300 m. | "DTI(α,β) = TP_w / (TP_w + α FP_w + β FN_w + ε)" and "k(d)=(1−d/R)+", with "R is 300 meters (i.e., 3 pixels at 100m resolution)". | **Confirmed.** Matches the repo's stated metric. | [Problem description, Mathematical representation](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) — OFFICIAL-VERIFIED |
| M2 | FP_w uses the weight p(x)[1−max_g k(d(x,g))], summed over p(x)>0. | Same page. | Confirmed as text. A prediction within 3 px of a mapped fault pays only a fraction of the FP penalty. | OFFICIAL-VERIFIED |
| M3 | Worked example: TP_w=3.00, FP_w=1.89, FN_w=2.00 gives TI_w=0.60. | Same page. | Arithmetic check: 3/(3+0.2·1.89+0.8·2) = **0.6027**, which rounds to 0.60. | OFFICIAL-VERIFIED + REPO-VERIFIED (arithmetic) |
| M4 | Submission format. | "same projected coordinate reference system ... EPSG 32611", "100m", "data outside the bounds is null or nan", "single layer with datatype of 32-bit float (`float32`) with values between 0 and 1". | **Confirmed.** Outside-bounds cells must be null or NaN. The repo's `zeros`-outside primary encoding is **not** the spec's encoding (see IR-55-043). | [Problem description, Submission format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) — OFFICIAL-VERIFIED |
| M5 | Submission count and entry format. | Rules §3.2: "a single GeoTIFF with a single raster layer at 100-meter resolution", "three submissions per week". | **Confirmed.** | [Official rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf) — OFFICIAL-VERIFIED |
| M6 | Generative-AI use must be disclosed in the narrative. | Rules §3.2: "you must indicate in the narrative ... the extent to which ... you used generative AI technology". | **Confirmed.** No narrative exists in this repository. See IR-55-047. | Same rules PDF — OFFICIAL-VERIFIED |
| M7 | Public and private scores differ. | Rules §3.2: "Scores displayed on the public leaderboard ... may not be the same as the final scores on the private leaderboard". | **Confirmed.** Public leaderboard values cannot establish final ranking. | Same rules PDF — OFFICIAL-VERIFIED |
| M8 | Two prize phases. Phase 1 ranks on the private set; Phase 2 ranks on an expanded label set. | Rules §1.1 and the problem page. | **Confirmed.** Phase 1 is $50,000 across the top five, and Phase 2 is $250,000 across five places. | OFFICIAL-VERIFIED |
| M9 | Feature list. | Problem page "Provided features": conductivity, detrended elevation and slope, strain-rate invariants, isostatic gravity and slope, magnetics (RTP, TMI, slopes, top-of-crust depth), earthquake density. | **Radiometric grids are not in the listed official features.** The page shows a radiometric map only as a visual. | OFFICIAL-VERIFIED |
| M10 | Reference solution. | GitHub page: "Download the data from the GEMS Prize Challenge website and place it in the `data/` directory." | Confirmed. It is an unofficial starting point and has a single commit. | [Reference solution repo](https://github.com/drivendataorg/gems-prize-reference-solution) — OFFICIAL-VERIFIED (sponsor-linked) |
| M11 | External data may be used only if the participant holds a licence that permits use and sharing with the sponsor. | Problem page "External datasets". | Confirmed. Any new layer requires a licence check before use. | OFFICIAL-VERIFIED |

## 3. Leaderboard (live capture, 2026-10-09)

| # | Claim | Result | Evidence |
|---|---|---|---|
| L1 | Current top public score is 0.3774 by xiaofanhu. | **Confirmed.** The owner brief's "0.3195 is the highest" is **incorrect**; 0.3195 is rank 7 (DARD). | [Leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) — OFFICIAL-VERIFIED |
| L2 | extradr19 has 0.2778 at rank 17 in this capture. | Confirmed in this capture. The repo's saved snapshot has rank 16. The order has changed. See IR-55-045. | OFFICIAL-VERIFIED; saved as `evidence/leaderboard_capture_20261009_live.json` |
| L3 | H33 (GEMSDOE32) is the same entry as extradr19. | **Not established.** No receipt, raster hash, or organizer link ties them. The owner manifest reports `receipt: null` and H33 as `UNSCORED`. | Owner manifest (secondary only), cited in `docs/leaderboard-review-20261009.md` |

## 4. Scientific and literature citations

| # | Citation | Check | Result | Evidence |
|---|---|---|---|---|
| S1 | Pedersen & Rasmussen (1990), Geophysics 55(12):1558–1566, doi 10.1190/1.1442807. | Two bibliographic indexes. | **Confirmed.** The full title is "The gradient tensor of potential field anomalies: Some implications on data collection and data processing of maps". The repo's hypothesis document omits the subtitle (IR-55-046). | [HAL reference list](https://theses.hal.science/tel-00341117v1/html_references); [birocoles/gravmag references](https://github.com/birocoles/gravmag/blob/main/references.md) — SECONDARY; DOI https://doi.org/10.1190/1.1442807 |
| S2 | Beiki & Pedersen (2010), Geophysics 75(6):I37–I49, doi 10.1190/1.3484098. | Crossref record. | **Confirmed.** Title: "Eigenvector analysis of gravity gradient tensor to locate geologic bodies." | [Crossref record](https://chooser.crossref.org/?doi=10.1190%2F1.3484098) — SECONDARY; https://doi.org/10.1190/1.3484098 |
| S3 | Beiki, Pedersen & Nazi (2011), Geophysics 76(3):L1–L10, doi 10.1190/1.3555343. | Two bibliographic indexes. | **Confirmed** as a reference. Title: "Interpretation of aeromagnetic data using eigenvector analysis of pseudo gravity gradient tensor." | [Wiley reference list](https://agupubs.onlinelibrary.wiley.com/doi/abs/10.1002/cjg2.1733) — SECONDARY; https://doi.org/10.1190/1.3555343 |
| S4 | Normalised source strength (NSS) from tensor eigenvalues, peaks over 2-D and 3-D compact sources, thin sheets, and contacts. | EarthDoc corrigendum abstract. The original article was not fetched in full. | **Partly verified.** Authorship of the original paper is not confirmed here. | [EarthDoc corrigendum, EG12020](https://www.earthdoc.org/content/journals/10.1071/EG12020_CO) — SECONDARY |
| S5 | Pseudogravity transform for aeromagnetic tensors. | Beiki et al. (2011), S3. | Confirmed as a method reference. The repo does not implement it (see R2). | SECONDARY |

## 5. USGS GeoDAWN source (free, official; for future candidates)

| # | Claim | Result | Evidence |
|---|---|---|---|
| G1 | GeoDAWN data release, Glen & Earney (2024), DOI 10.5066/P93LGLVQ, publication date 2024-03-01. | **Confirmed.** | [ScienceBase item](https://www.sciencebase.gov/catalog/item/657e1d85d34e23d3533209f7); [DOI](https://doi.org/10.5066/P93LGLVQ) — OFFICIAL-VERIFIED |
| G2 | The release includes radiometric and magnetic data, and it includes geoTIFF grids. | "Radiometric data ... processed by the contractor"; "geoTIFF images of geophysical grids". | **Confirmed.** Obtainable as a public release. The file-level download was not performed here. Licence terms are **NOT VERIFIED** in this session. | Same ScienceBase item — OFFICIAL-VERIFIED |
| G3 | Four acquisition blocks: Winnemucca, Fallon, Hawthorne, Tonopah. | Summary text. | **Confirmed.** The repo's 64-px tiles are not these blocks (see IR-55-036). | Same ScienceBase item — OFFICIAL-VERIFIED |
| G4 | Magnetic processing used the IGRF for the survey time. | "an International Geomagnetic Reference of the Earth for the time of the survey". | **Confirmed.** This is relevant to a pseudogravity transform (inclination and declination). | Same ScienceBase item — OFFICIAL-VERIFIED |
| G5 | NOAA NCEI provides magnetic-field calculators for declination and IGRF. | Page fetched. | **Confirmed.** Free official source for inclination and declination. | [NOAA NCEI calculators](https://www.ngdc.noaa.gov/geomag/calculators/magcalc.shtml) — OFFICIAL-VERIFIED |

## 6. Repository claims (code and records)

| # | Claim | Check | Result |
|---|---|---|---|
| R1 | Dimensionality indicator and eigenratio exist. | `grep` and reading `src/gems55/tensor55.py`: `dimensionality_invariant`, `dimensionality_eigratio`, `strike_eigenvector`. | **Confirmed.** |
| R2 | No pseudogravity transform is implemented. | `grep -i pseudo src scripts`. Only the lane docstring says "No pseudogravity". | **Confirmed.** This is a real, documented gap (IR-55-036). |
| R3 | No normalised source strength is implemented. | `grep -i "NSS\|source strength"` returned no code hit. | **Confirmed** as a gap. |
| R4 | No radiometric layer is used. | `grep -i radiometr\|potassium\|thorium`. Only the data dictionary and HTML mention radiometrics. | **Confirmed** as a gap. |
| R5 | Destriping exists. | `tensor55.destripe` and `fields55.prepare_field`. | **Confirmed** (already implemented; not a new candidate). |
| R6 | Grid constants match the official grid. | `io55.py`: EPSG 32611, 100 m, width 3292, height 3730. The archived raster's transform is origin (243350, 4508550) at 100 m. | **Confirmed**. The grid matches the official spec, but it has not been checked against the authoritative template. |
| R7 | Archived rasters: each is float32, EPSG:32611, 3730×3292, with values inside [0,1]. | Read-only inspection of all six archived TIFFs. | **Confirmed**: min 0, max 1, and no value outside [0,1]. The `nan` twins have 7,111,787 NaN cells outside the footprint. The `zeros` primaries have 0 NaN and 12,119,160 or 12,239,160 zeros outside. Each has exactly as many 1.0 cells as dots (40,000 or 160,000). |
| R8 | The user's upload error "Predicted values must be in range [0, 1]" is explained by the archived rasters. | Checked R7. | **Not explained.** None of the archived rasters has a value outside [0,1]. The file the user uploaded is not identified. Possible causes (unverified): NaN handling in the portal, a different file, or a value outside [0,1] inside the footprint. See IR-55-044. |

## 7. Experiments and budget

- No experiment was run. The recorded three-experiment budget is exhausted (`docs/run-card.json`).
- No candidate raster was generated. No holdout, leakage canary, or uniqueness check was run.
- No submission slot was used.

## 8. Re-checks (run after the edits in this session)

- `python3 -m unittest discover -s tests -v` (stdlib guardrails, 15 tests): **OK**. This includes the new session checks for the run card, leaderboard capture, submission contract, and README brief.
- `python -m pytest tests_numeric -q` (numpy 2.4.6, scipy 1.17.1, rasterio 1.4.4, in a virtualenv): **30 passed, 2 skipped**. No numeric code was changed in this session.
- `python scripts/prepare_data.py`: **exit 1**, three canonical files missing (section 1, A5).
- Read-only archive inspection (section 6, R7): no value outside [0,1] in the six archived TIFFs.
