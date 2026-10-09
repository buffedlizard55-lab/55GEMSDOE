# Official-source verification log — 2026-10-09

Line-by-line check of every factual claim used in the 2026-10-09 review. Each row names the source, the quoted text or observed value, and the verification method. **Nothing here is a score, a submission receipt, or a clearance.** Status key:

- **VERIFIED** — read from the source in this session (fetch tool or local command output).
- **NOT VERIFIED** — claimed by a user message or sibling repository; not confirmed from an official source.
- **BLOCKED** — could not be reached from this sandbox.

## A. Competition rules, metric, and format

| # | Claim | Source (link) | Evidence in this session | Status |
|---|---|---|---|---|
| A1 | Metric is a distance-weighted Tversky index, α=0.2, β=0.8, triangular kernel with 300 m support (3 px at 100 m). | [Problem description, Performance metric](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) | Quoted: "For this competition, we set 𝛼=0.2 and 𝛽=0.8" and "range R is 300 meters (i.e., 3 pixels at 100m resolution)". | VERIFIED |
| A2 | Kernel is k(d)=max(1−d/R, 0); TP_w, FP_w, FN_w definitions as in `src/gems55/dti55.py` docstring. | Same page, "Mathematical representation" | Formulas read from the page (rendered text with some glyph loss; structure confirmed). | VERIFIED (structure) |
| A3 | Worked example: TP_w=3.00, FP_w=1.89, FN_w=2.00 gives TI_w=0.60. | Same page, "Scoring example" | Recomputed: 3.00/(3.00+0.2·1.89+0.8·2.00) = 0.6027, which rounds to the printed 0.60. | VERIFIED (arithmetic) |
| A4 | Submission must be a GeoTIFF, EPSG 32611, 100 m, same bounds as training data, outside bounds "null or nan", single float32 layer, values between 0 and 1. | Same page, "Submission format" | Quoted: "data outside the bounds is null or nan" and "single layer with datatype of 32-bit float (`float32`) with values between 0 and 1". | VERIFIED |
| A5 | Labels come from USGS quaternary fault maps and INGENIOUS. | Same page, "Labels" | Quoted: "The labels for this challenge come from the USGS quaternary fault maps and from INGENIOUS." | VERIFIED |
| A6 | Test faults are newly identified, not in the USGS database; the test set is split into public and private chunks. | Same page, "Competition structure" | Quoted: "...not included in the existing USGS fault database" and "split into a public test set and a private test set." | VERIFIED |
| A7 | Participants submit a single entry; Phase 1 uses a private set, Phase 2 uses an expanded label set. | [Official rules (NLR PDF, Sept 2026), §1.1](https://docs.nlr.gov/docs/fy26osti/96647.pdf) | Quoted: "Participants will submit a single entry, which will be evaluated in two prize phases". | VERIFIED |
| A8 | External data is allowed when the participant holds a license permitting use and sharing for evaluation. | Problem description, "External datasets" | Quoted: "provided that the participants possess a license that permits the data to be used in this challenge and shared with the sponsor for evaluation purposes." | VERIFIED |
| A9 | The data tab requires login. | [Data tab](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) | Fetch tool returned the login page ("Log in … Don't have an account? Sign up") and redirected to `accounts/login/?next=…/data/`. | VERIFIED |
| A10 | Sandbox cannot reach DrivenData or NLR directly. | Local `curl` in this session | TLS error (SSL_ERROR_SYSCALL) for both hosts; the sandbox allow-list does not include them. Data must come from a human account holder, or the operator must supply the file. | BLOCKED |

## B. Public leaderboard (PUBLIC-LEADERBOARD — not a submission receipt)

| # | Claim | Source | Evidence | Status |
|---|---|---|---|---|
| B1 | Top public DW-Tversky is 0.3774 (xiaofanhu). | [Leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) | Rank #1 row, fetched in this session. | VERIFIED (public, not receipt) |
| B2 | 0.3195 is at rank 7 (DARD), **not** the top score. | Same | Rank #7 row. | VERIFIED — conflicts with the user's brief ("0.3195 is the highest score right now"). See IR-55-044. |
| B3 | extradr19 is at **rank 17** with 0.2778. The repo snapshot said rank 16. | Same | Rows #16 op01 (0.2797) and #17 extradr19 (0.2778). The snapshot omitted rank 8 (giles, 0.3025), shifting ranks 8–22 by one. See IR-55-043. | VERIFIED |
| B4 | The mapping from the owner's "H33 / GEMSDOE32" site to participant `extradr19` is established. | — | No receipt; owner manifest reports `receipt: null`. | NOT VERIFIED — unresolved |

## C. Data sources (free, official)

| # | Claim | Source | Evidence | Status |
|---|---|---|---|---|
| C1 | GeoDAWN airborne magnetic and radiometric surveys, DOI 10.5066/P93LGLVQ; USGS data release published 2024-03-01; surveys flown 2021-11-01 to 2022-11-20. | [ScienceBase item 657e1d85d34e23d3533209f7](https://www.sciencebase.gov/catalog/item/657e1d85d34e23d3533209f7) | Fetched: publication date, flight dates, DOI. | VERIFIED |
| C2 | GeoDAWN has 149,030 line-km over 51,857 km², in four acquisition blocks (Winnemucca, Fallon, Hawthorne, Tonopah). | Same | Quoted summary text. | VERIFIED |
| C3 | Area 1 flight lines 200 m apart; Area 2 flight lines 400 m apart; tie lines 2000 m / 4000 m. | Same | Quoted summary text. | VERIFIED |
| C4 | The release includes geoTIFF images of geophysical grids, and `.csv` flight-line data. | Same | Quoted: "...geoTIFF images of geophysical grids" and "...`.csv` files of flight line data for magnetic and radiometric surveys". | VERIFIED |
| C5 | Magnetic processing included diurnal, aircraft, tie-line leveling, and micro-leveling corrections. | Same | Quoted summary text. | VERIFIED |
| C6 | USGS Quaternary Fault and Fold Database: KML (13 MB) and GIS ZIP (16 MB) downloads; database search retired 2026-02-26; DOI 10.5066/P9BCVRCK. | [USGS faults page](https://www.usgs.gov/programs/earthquake-hazards/faults) | Fetched links and text. | VERIFIED |
| C7 | This QFDB is a **label source** for the competition (the official labels come from USGS quaternary fault maps). Any feature derived from it must use visible faults only. | A5 above + C6 | Logical consequence of A5. | VERIFIED (inference is explicit) |
| C8 | INGENIOUS project ran 1 Feb 2021 – 30 Jun 2025; $10M; DOE GTO award DE-EE0009254. | [INGENIOUS page, GBCGE](https://gbcge.org/current-projects/ingenious/) | Fetched. | VERIFIED |
| C9 | INGENIOUS-listed regional products: Glen et al., regional geophysical maps (DOI 10.5066/P9Z6SA1Z); Siler, slip and dilation tendency for Quaternary faults (DOI 10.5066/P9YL58W6); DeAngelo et al., heat-flow maps (DOI 10.5066/P9BZPVUC); Peacock & Bedrosian, electrical conductance (DOI 10.5066/P9TWT2LU); INGENIOUS regional compilation (DOI 10.15121/1881483). | Same page, "Publications to date" | Listed on the page with the DOIs. The DOI landing pages and their licences were **not** fetched. | VERIFIED (listing); licence NOT VERIFIED |
| C10 | Licences and downloadability of the C9 products. | — | Not checked in this session. | NOT VERIFIED — required before any use |

## D. Local repository checks (this session)

| # | Check | Command / result |
|---|---|---|
| D1 | Site guardrails (stdlib) | `python3 -m unittest discover -s tests` → Ran 11 tests, OK. |
| D2 | Numeric suite in a clean venv with `requirements.txt` | `python -m pytest tests_numeric -q` → 30 passed, 2 skipped. |
| D3 | Metric transcription on synthetic cases (repo `src/gems55/dti55.py`, not a fork) | Single truth pixel, one dot at distance d: DTI = 1.000, 0.667, 0.333, 0.000 for d = 0, 1, 2, 3 px. This equals k(d), as the formula implies. |
| D4 | Global prediction-mass effects (synthetic line, 41×41) | Uniform p=0.5: DTI 0.106. Dots every 4 px on the line: 0.722. Dots every 4 px one column off the line: 0.544. |
| D5 | Zero-filled vs NaN-outside encoding under the metric | Zero-filled cells add nothing to FP_w (FP sums only p>0). The organizer's handling of NaN is not stated on the page, so zeros and NaN may score the same here but are not verified to be equal at the portal. See IR-55-046. |
| D6 | Registry rasters, template, labels, feature stack present locally | No. `data/` contains only READMEs. |

## Verdict on this verification pass

Every quantitative claim used in the 2026-10-09 review is either VERIFIED above, labelled as a synthetic check (D3–D5), or labelled NOT VERIFIED / BLOCKED. No score, receipt, uniqueness value, or holdout value was created.
