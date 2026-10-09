# Source verification log (2026-10-09)

"Fetched" = read in this session with the fetch tool or the GitHub API. "Blocked" = not reachable from this sandbox.

| Source | URL | Status | What it supports |
|---|---|---|---|
| DrivenData problem description | https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/ | Fetched (2 chunks) | Metric (DTI, α=0.2, β=0.8, R=300 m), format (EPSG:32611, 100 m, float32, [0,1], NaN outside bounds), data description |
| Official rules (NLR) | https://docs.nlr.gov/docs/fy26osti/96647.pdf | Fetched (chunks 0–4 of 7; §A.5 read; chunks 5–6 not read) | Submission process, 3/week limit, one final submission, GenAI disclosure, data source citations |
| DrivenData data tab | https://www.drivendata.org/competitions/306/competition-doe-gems/data/ | **Blocked** (login) | — |
| Reference solution | https://github.com/drivendataorg/gems-prize-reference-solution | Cloned (`git clone --depth 1`) | Notebook: submission written with the fault-label CRS/transform; Tversky loss α=0.2, β=0.8 |
| INGENIOUS label source (cited by rules) | https://doi.org/10.15121/1881483 | Cited in rules; not fetched | Label provenance |
| GeoDAWN (cited by rules) | https://doi.org/10.5066/P93LGLVQ | Cited in rules; not fetched | Feature provenance |
| USGS GeoDAWN catalogue page | https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and | **Blocked** | — |
| EPSG:32611 | https://epsg.io/32611 | Cited in brief; not fetched | CRS definition |
| Beiki & Pedersen (2010) abstract (eigenvector analysis; strike from min-eigenvector) | https://www.researchgate.net/publication/228794726_Eigenvector_analysis_of_gravity_gradient_tensor_to_locate_geologic_bodies | Search snippet read | Method basis; not the full paper |
| Beiki TSVD / dimensionality ratio | https://www.sciencedirect.com/science/article/abs/pii/S0926985113000062 | Search snippet read | Index form: smallest/intermediate eigenvalue ratio |
| ASEG 2012 extended abstract | https://www.tandfonline.com/doi/pdf/10.1071/ASEG2012ab057 | Search snippet read | Dimensionality indicator 0 (2-D) to 1 (3-D); 0.5 threshold; PGGT strike |
| Pedersen & Rasmussen (1990) | — | **Not retrieved** | Original indicator definition — flagged |
| Sibling repo GEMSDOE (data bridge, audits, data README) | https://github.com/buffedlizard55-lab/GEMSDOE | Fetched via GitHub API / sparse clone | Data bytes and pins; provenance statements |
| Sibling repo GEMSDOE32 (0.2778 entry) | https://github.com/buffedlizard55-lab/GEMSDOE32 | Fetched via GitHub API | Audit JSON, submission manifest, method notes |
| Public GEMSDOE submission site (user-provided list) | https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html | **Blocked** (github.io not reachable) | Only via the user's list and the sibling repo copy |

## Manual-review links
- Metric and format: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/
- Rules: https://docs.nlr.gov/docs/fy26osti/96647.pdf
- 0.2778 audit file: https://github.com/buffedlizard55-lab/GEMSDOE32/blob/main/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-audit.json
