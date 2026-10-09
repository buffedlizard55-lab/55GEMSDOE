# Sources, evidence classes, and retrieval status

**Review date: 2026-10-09 UTC.** This register distinguishes authoritative sources from owner-maintained mirrors and reports only what was checked. A URL listed here is not proof that a file was downloaded or that a score was confirmed.

## Competition and official sources

| Source | Class | What is established | Limits |
|---|---|---|---|
| [DrivenData DOE GEMS problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) | Competition primary source | Primary reference for task, feature descriptions, distance-weighted Tversky metric, and output contract. The project records the formula as α=0.2, β=0.8, triangular radius 300 m, one-band float32 GeoTIFF, EPSG:32611, 100 m, [0,1], and null/NaN outside bounds. | The official page does not identify which raster earned a score. Its content was not freshly fetched during this read-only correction pass; consult the live page before any submission. |
| [DrivenData data tab](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) | Authorized competition data source | The only authorized source named here for competition-provided rasters, subject to login and terms. | No authentication or data download occurred in this review. The feature stack, labels, organizer template, and cache are absent. |
| [DrivenData public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) | Competition primary source | A `fetch_page` capture on 2026-10-09 recorded ranks 1–22 in `evidence/leaderboard_snapshot_20261009.json`; values in that snapshot are labeled PUBLIC-LEADERBOARD, not receipt-confirmed. | The capture is a dated snapshot, not a current refresh or submission-page receipt; rows do not identify a raster/hash or establish the mapping from `extradr19` to H33. |
| [GEMS Prize Official Rules PDF (NLR)](https://docs.nlr.gov/docs/fy26osti/96647.pdf) | Official rules | Official source for eligibility, submissions, and use/redistribution terms. | Read the complete current rules before any submission or redistribution. This review did not re-fetch the PDF or make a legal determination. |
| [Official GEMS reference solution](https://github.com/drivendataorg/gems-prize-reference-solution) | Competition reference code | Read-only GitHub API inspection found conventional `segmentation_models_pytorch` Tversky loss in the notebook. | That training loss is not the competition's distance-weighted evaluator and is not evidence of a score. |
| [USGS GeoDAWN data release, DOI 10.5066/P93LGLVQ](https://doi.org/10.5066/P93LGLVQ) and [USGS overview](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) | Official government data | Reference source for survey context and possible flight/block metadata relevant to tensor processing. | No block polygons or flight-line files were downloaded, aligned, checksum-pinned, or verified in this review. Public USGS data do not replace authorized competition inputs. |
| [EPSG:32611](https://epsg.io/32611) | CRS reference | WGS 84 / UTM zone 11N in metres. | The organizer template remains controlling for exact grid geometry. |

## Scientific references (background, not performance evidence)

- [Pedersen & Rasmussen (1990), “The gradient tensor of potential field anomalies: Some implications on data collection and data processing of maps”](https://doi.org/10.1190/1.1442807).
- [Beiki & Pedersen (2010), eigenvector analysis of gravity-gradient tensors](https://doi.org/10.1190/1.3484098).
- [Beiki, Pedersen & Nazi (2011), eigenvector analysis of pseudogravity-gradient tensors](https://doi.org/10.1190/1.3555343).

These references motivate source-geometry hypotheses; they do not prove that a tensor signature identifies a fault or improves this competition's HOLDOUT-DTI.

## Owner-maintained artifacts and mirrors (secondary evidence)

| Source | What was checked | Limits |
|---|---|---|
| [GEMSDOE32 submissions manifest](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/main/docs/downloads/submissions_manifest.json) | Read-only GitHub API inspection on 2026-10-09 returned an H33 artifact record with `receipt: null`; the project note calls 0.2747 projected and the file unscored. | It is an owner-generated audit, not an organizer receipt. It does not establish a score or official artifact attribution. |
| [GEMSDOE owner-maintained data mirror](https://github.com/buffedlizard55-lab/GEMSDOE) | Repository documentation/manifests name feature, label, and template copies and provide SHA-256 pins. | The mirror is not an authenticated organizer download. This review did not download its raster files. The pins are integrity references only, not provenance, permission, or legal approval. |
| [GEMSDOE26](https://github.com/buffedlizard55-lab/GEMSDOE26) and [GEMSDOE54](https://github.com/buffedlizard55-lab/GEMSDOE54) | Listed in prior-art notes for DILCOND, magnetic-ridge, and cross-gradient methods. | Owner-maintained reports; exact code, pixel overlap, and reported scores are not independently validated here. |
| [Registry manifest](../registry/registry.json) | Local manifest lists 56 prior raster entries. | `registry/rasters/` is absent, so no full current uniqueness scan can be performed. The historical report is not a fresh pass. |

## Data files, pins, and legal boundary

- Canonical paths are defined in [`src/gems55/io55.py`](../src/gems55/io55.py). The recorded SHA-256 pins are in [`data/README.md`](../data/README.md), and their limitations in [`data/SOURCES.md`](../data/SOURCES.md).
- Pins came from an owner-maintained sibling mirror. They are not independently authenticated against the organizer's files. Git blob SHA-1 and file SHA-256 are different hash algorithms.
- `scripts/download_competition_data.sh` accesses owner-maintained GitHub mirrors only; it is disabled unless explicitly opted into with `GEMS_ALLOW_UNOFFICIAL_MIRROR=1`. It was not run. Do not describe it as an official or authenticated download.
- No external dataset, competition raster, registry raster, or new candidate artifact was fetched during this review.

## Score evidence classes

- `ORGANIZER-CONFIRMED`: copied from an actual organizer submission receipt/record tied to the artifact. None is present for the H33 or comparison entries in this checkout.
- `PUBLIC-LEADERBOARD`: transcribed from the dated public-page snapshot. It establishes a row/value on that capture but is not a submission receipt, does not identify a raster hash, and is not used as promotion evidence.
- `HOLDOUT-DTI`: local validation only when evaluator version, withheld-positive count, and 95% CI accompany the result. The stored local values are historical and invalid for promotion; see [`docs/results.md`](results.md).
- `USER-REPORTED / NOT ORGANIZER-CONFIRMED`: claims supplied by the owner without a corresponding public-page capture or receipt. A public-page value still does not establish that a named local artifact earned it.
- `PROJECTION`: estimate only; never a score. The secondary GEMSDOE32 record labels 0.2747 projected.
