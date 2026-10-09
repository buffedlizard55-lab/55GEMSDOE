# 55GEMSDOE — GEMS fault-mapping research

> **CURRENT DECISION — NOT CLEARED. There is no candidate GeoTIFF in this checkout. Do not download or submit anything from this repository.** A download link will be shown here only after the tensor-lane candidate passes holdout, registry-uniqueness, and on-disk format gates. A fabricated blank or synthetic raster would be misleading and is intentionally not provided.

**Start every session by reading this README and [the run card](docs/run-card.json).** The persistent task brief and the required gates are below. The site landing page and exact upload guide are [here](docs/index.html) and [here](docs/executive-summary.html).

## What this repository actually contains

The checked-out branch began with a single tracked file, `README.md`. It contains no competition rasters, cached feature stack, training code, holdout evaluator, submission writer, registry rasters, or tests. The previously mentioned `scripts/download_competition_data.sh`, `scripts/prepare_data.py`, `evaluate_holdout.py`, and `submission_writer.py` are **not present in this checkout**. This is a repository-state finding, not a claim that those tools do not exist elsewhere.

The official competition data page redirected to DrivenData login in this review. A public, owner-maintained data bridge exists in the separate [GEMSDOE template repository](https://github.com/buffedlizard55-lab/GEMSDOE/tree/main/data/bridge); that repository's own manifest says the bridge bytes match its recorded hashes. This is useful for research, but a hash match to an owner-maintained mirror is not organizer authentication. Neither the bridge nor the sibling-repository tools have been copied into this checkout or treated as authoritative without approval.

## Executive answer: the reported H33 score

The user-supplied prompt attributes **0.2778 — USER-REPORTED / NOT ORGANIZER-CONFIRMED** to `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros`. That attribution is not established by the evidence currently accessible:

- The [GEMSDOE32 artifact page](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html) labels the H33 file **UNSCORED** and describes a projected value as a model projection, not a score. Its linked [owner-generated audit JSON](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-audit.json) also labels the file `UNSCORED`. Those are owner-page claims; this checkout has not re-read the TIFF bytes.
- The [GEMSDOE54 dated review](https://buffedlizard55-lab.github.io/GEMSDOE54/docs/index.html) reports that the public leaderboard showed **0.3774 — PUBLIC-LEADERBOARD SNAPSHOT, NOT A SUBMISSION-PAGE RECEIPT** at rank one, **0.3195 — PUBLIC-LEADERBOARD SNAPSHOT, NOT A SUBMISSION-PAGE RECEIPT** at rank seven, and **0.2778 — PUBLIC-LEADERBOARD SNAPSHOT, NOT A SUBMISSION-PAGE RECEIPT** at rank thirteen for a different participant; it says the row is not linked to the H33 TIFF. This is a sibling project's dated report, not independent organizer-confirmed file-to-score evidence.
- When fetched directly for this review, the official [DrivenData leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) returned only “Loading…”. Therefore the live rank and the H33 filename-to-row relationship remain **unverified here**. See [irregularities](docs/irregularities.md).

So we cannot honestly explain why that specific TIFF earned the reported value: the file-to-score link is missing. Mechanistically, the official distance-weighted Tversky score rewards prediction mass that covers nearby truth and penalizes mass away from truth. Its published parameters are α=0.2 and β=0.8, with a 300 m triangular distance kernel. Sparse pruning can improve a score if it removes low-credit mass while retaining useful coverage; a new filename, a `zeros` suffix, a site projection, or a local proxy result does not prove that this happened on the organizer's test set. The official target is **geological fault mapping**, not direct geothermal-vent detection; a fault prediction is not a verified geothermal resource.

## Assigned research lane: potential-field tensor dimensionality

The only permitted method lane for this session is the tensor-dimensionality paragraph in the user brief: use the reduced-to-pole magnetic and isostatic-gravity grids; smooth before differentiation; process acquisition blocks separately; construct potential-field gradient tensors; estimate local source dimensionality and strike; retain near-2-D ridges only when tensor strike agrees with ridge orientation; suppress compact 3-D signatures; and mask flight-line striping. Do not substitute another lane or combine unrelated submission families.

The mechanism is scientifically plausible, not sufficient proof of a fault. Tensor eigenvalue invariants can distinguish idealized strike-extended from compact source geometries, and eigenvectors can indicate strike for quasi-2-D sources. They do **not** uniquely identify faults: lithologic contacts, dikes, intrusive bodies, vents, survey artifacts, and some 3-D configurations can mimic parts of the signal. The dimensionality index alone is not a geological classifier. See the literature links in [Sources](docs/sources.md).

### Candidate hypotheses before implementation

Four test candidates—all sub-hypotheses of the assigned tensor lane, not permission to test unrelated methods—are ranked in [the hypothesis register](docs/hypotheses.md). Rank is a qualitative research priority, **not a score or DTI projection**. The highest-priority candidate is joint magnetic/gravity tensor-dimensionality and strike-concordant ridges; it has **not** been run or validated. A related `DILCOND` name appears in the external GEMSDOE26 archive, and sibling repositories report magnetic-ridge and cross-gradient experiments, so novelty against the broader archive is **not established** until the full registry is available and scanned.

## Non-negotiable protocol for every future experiment

1. **Stay in lane and check uniqueness before placement and after dots.** Compare the continuous surface and final prediction against every available registry raster. If absolute rank-correlation exceeds 0.90, or more than 70% of dots fall within 3 pixels of one registry raster, record a duplicate and stop. Do not waive or silently narrow the corpus.
2. **Reuse, do not privately rebuild.** Use the canonical cached feature stack, whole-segment `evaluate_holdout.py`, and `submission_writer.py` when their authoritative locations are identified. The current checkout has none. The separate template has similarly purposed but differently named tools; its current holdout implementation has not been shown here to satisfy this exact protocol. Do not make a private fork or claim a shared-tool repair that was not made in the template.
3. **Hide and recover whole fault segments with a buffer.** Recompute any catalogue-derived feature from visible faults only; mask visible-fault pixels exactly; pool DTI at α=0.2, β=0.8 and the 300 m triangular kernel. Evaluate strike agreement on held-out fault segments against random ridges. Test each feature alone first; AUC >0.90 is a leakage canary until explained.
4. **No score inflation by language.** Every actual candidate result must be labelled `HOLDOUT-DTI` with evaluator/version, withheld-positive count, and 95% CI, or `ORGANIZER-CONFIRMED` copied from an organizer submission-page receipt. A projection, external site's claim, or public leaderboard row is not an organizer receipt and never becomes a score in the run card.
5. **Budget and promotion.** Stop at three experiments or two hours. Negative results are valid deliverables. Do not select or promote a weekly submission from the experiment step; a separate selector owns promotion and must honor the live weekly cap.
6. **End with a machine-readable run card.** Include hypothesis, mechanism, a named non-fault mimic, holdout result/CI, uniqueness, raster SHA-256, validator output, submission name/note (at most 140 characters), and `promote` or `negative`. The current card is negative because the required inputs and shared tools are absent.

## Submission status and the previous range error

There is no candidate file, so no file is safe to download or submit. The official [submission specification](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) requires a single-band `float32` GeoTIFF on the training grid (EPSG:32611, 100 m, same bounds), probabilities in [0,1], and null/NaN outside the footprint. Before any future release, validate the written bytes against the authentic sample/template and verify **no NaN/Inf or nodata sentinel inside the scored footprint**. The exact cause of the user's earlier “Predicted values must be in range [0, 1]” rejection cannot be diagnosed without the rejected file and its template. An out-of-range value, infinity, or NaN inside the scored footprint is a plausible cause; do not claim one was confirmed for that upload.

When a candidate passes all research and format gates, the site should show the `.tif` download, unique submission name, and short comment prominently. Until then the site's status is explicit: **NOT CLEARED — no download, no upload**. The exact portal procedure is documented in the [executive summary](docs/executive-summary.html). This repository does not upload files to DrivenData.

## Sources and audit status

The authoritative source register, what was fetched, and what remains unchecked are in [docs/sources.md](docs/sources.md). Key links:

- [DrivenData problem, metric, inputs and submission format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [DrivenData about page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/)
- [DrivenData data page](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) (login wall observed)
- [Official reference solution](https://github.com/drivendataorg/gems-prize-reference-solution)
- [USGS GeoDAWN data release](https://doi.org/10.5066/P93LGLVQ) and [USGS overview](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)
- [Pedersen & Rasmussen (1990)](https://doi.org/10.1190/1.1442807), [Beiki & Pedersen (2010)](https://doi.org/10.1190/1.3484098), and [Beiki, Pedersen & Nazi (2011)](https://doi.org/10.1190/1.3555343)

**Feed limitation:** the site is a status dashboard, not yet an automatically refreshed official leaderboard feed. The official leaderboard did not render data to the page-fetcher in this review. Until an official, stable endpoint is identified and tested, it must say “not checked” rather than present stale or guessed values as current.

## Next work, in order

1. Identify and pin the authoritative shared template/tool location and verify that its evaluator implements whole-segment buffered hide-and-recover, exact visible-pixel masking, pooled DTI, and paired segment-level uncertainty. Raise a template-level fix there if a genuine shared defect is found; do not duplicate the tool here.
2. Place/reassemble the cached competition rasters only through an approved, checksum-verifiable route; record that owner-mirror hashes do not authenticate organizer origin. Confirm layer names, valid footprint, CRS/shape/transform, and acquisition-block/flight-line metadata.
3. Freeze the 3–5 tensor-lane hypotheses, non-fault mimics, band-limited derivative choices, and leakage-canary tests before looking at holdout outcomes. Run no more than the stated budget.
4. Test the top candidate on the shared spatially blocked set, including the strike-vs-random-ridge prediction. Compare against a same-evaluator current holdout best; this checkout has no such baseline.
5. Only if both holdout and uniqueness gates pass, write with the canonical submission writer, validate/re-read the TIFF, publish the card and download, and leave slot promotion to the separate selector.
6. Build a scheduled source feed only after the organizer's public interface is understood and its parser is tested; keep login-only data private and never commit credentials.

## Persistent project brief (consolidated from the user request)

This brief consolidates the repeated instructions in the original request so future sessions have one durable starting point. The appendix groups the score claims supplied in that prompt; it is not a complete prior-art registry, and every value remains a claim unless a cited receipt proves otherwise.

- **Mission:** create an auditable, useful research system for the DOE GEMS / DrivenData challenge; improve the probability of winning without promising a score; identify geological faults indicative of geothermal systems, not “vents” directly; use official, free/public sources and organize sources, hypotheses, experiments, and irregularities.
- **Scientific lane:** tensor dimensionality in RTP magnetics and isostatic gravity, low-pass before FFT derivatives, process four acquisition blocks independently, map dimensionality/strike, compare tensor strike with ridge direction, down-weight compact signatures, and mask east–west flight-line striping. Do not leave the lane.
- **Research first:** rank 3–5 untried hypotheses with layer, physics, reason for catalogue-missing faults, prior-art distinction, expected relative DTI opportunity and implementation cost. If new external data are required, identify the exact free official source and verify it is obtainable before calling the idea viable.
- **Evaluation:** reuse the shared cached stack, evaluator and writer; withhold whole fault segments with a buffer; build catalogue-derived features from visible faults only; mask visible labels exactly; score pooled distance-weighted Tversky and report a 95% CI; test each feature alone for leakage; compare held-out fault strikes with random ridge strikes; do not use a submission slot unless a comparable current holdout best is beaten.
- **Integrity:** uniqueness checks before placement and on final dots against the registry; no cloning a previous raster; no fabricated score; every result has the specified run card; stop after three experiments or two hours; negative results count; submission selection is separate.
- **Product:** clean GitHub Pages site; executive summary at the beginning; clear “OK / NOT OK to submit” status; an easy GeoTIFF download only when cleared; unique submission name and short note; exact click-by-click DrivenData instructions; support an up-to-date source feed without asking the user to manually check every item.
- **Quality bar:** perform multiple review passes; verify line-by-line against official sources; report limitations and irregularities; do not hallucinate; keep Arena’s values—“Maximize P(Win)” and “Own the Outcome”—central.
- **User-supplied score context:** the prompt listed many prior sibling-repository artifacts, including H33-2-B2 and dozens of unrelated experiments. These are not independent scientific validation. The conflicting H33 attribution and leaderboard snapshot are recorded in [irregularities](docs/irregularities.md) and must be resolved before using any prior number as evidence.
- **Submission/data context:** competition materials are linked above; the data tab required login in this review; a sample/example TIFF and owner-maintained mirrors are not substitutes for an authenticated organizer receipt. The competition's own page defines the expected CRS, resolution, extent, single-band float32 and range checks.
- **Workflow request:** the user asked for this prompt to be read at every session, the next steps from prior sessions to be addressed first, an executive-summary submission guide, and a PR merged to `main`. See `AGENTS.md` for the session-start rule. Work on the Arena-assigned branch only; the PR is from this branch.

<details>
<summary>Historical score claims supplied by the user (not independently verified)</summary>

The following is a compact index of the prior values in the user prompt. Every value below is **USER-PROVIDED / ARCHIVE-REPORTED**, not a `HOLDOUT-DTI` result from this session and not `ORGANIZER-CONFIRMED` by a submission-page receipt. Filenames and values alone do not prove file-to-score attribution.

| Site / archive | Results stated by the user |
|---|---|
| [GEMSDOE32](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html) | H33-H33-2-B2 `0.2778` (attribution disputed; source page says unscored) |
| [GEMSDOE](https://buffedlizard55-lab.github.io/GEMSDOE/docs/index.html), [6GEMSDOE](https://buffedlizard55-lab.github.io/6GEMSDOE/) | `0.1563`; `0.0286` |
| [GEMSDOE3](https://buffedlizard55-lab.github.io/GEMSDOE3/docs/index.html), [GEMSDOE2](https://buffedlizard55-lab.github.io/GEMSDOE2/docs/index.html) | Pindrop nodes `0.1193`, discovery `0.0830`, ridge `0.1152`; dual-family union `0.1560` |
| [GEMSDOE4](https://buffedlizard55-lab.github.io/GEMSDOE4/), [5GEMSDOE](https://buffedlizard55-lab.github.io/5GEMSDOE/docs/index.html), [7GEMSDOE](https://buffedlizard55-lab.github.io/7GEMSDOE/), [8GEMSDOE](https://buffedlizard55-lab.github.io/8GEMSDOE/) | `0.0343`; `0.1563`; `0.1461`; `0.1563` |
| [GEMSDOE9](https://buffedlizard55-lab.github.io/GEMSDOE9/docs/index.html), [11GEMSDOE](https://buffedlizard55-lab.github.io/11GEMSDOE/docs/index.html), [12GEMSDOE](https://buffedlizard55-lab.github.io/12GEMSDOE/docs/index.html), [15GEMSDOE](https://buffedlizard55-lab.github.io/15GEMSDOE/docs/index.html), [14GEMSDOE](https://buffedlizard55-lab.github.io/14GEMSDOE/docs/index.html) | `0.0107`; `0.0202`; `0.1294`; `0.0782`; `0.0020` |
| [17GEMSDOE](https://buffedlizard55-lab.github.io/17GEMSDOE/), [18GEMSDOE](https://buffedlizard55-lab.github.io/18GEMSDOE/), [19GEMSDOE](https://buffedlizard55-lab.github.io/19GEMSDOE/docs/index.html), [GEMSDOE10](https://buffedlizard55-lab.github.io/GEMSDOE10/) | `0.0187`; `0.0297`; `0.1894`, `0.1922`; `0.0461`, `0.0921`, `0.1280`, `0.1839` |
| [13GEMSDOE](https://buffedlizard55-lab.github.io/13GEMSDOE/), [16GEMSDOE](https://buffedlizard55-lab.github.io/16GEMSDOE/docs/index.html), [GEMSDOE21](https://buffedlizard55-lab.github.io/GEMSDOE21/), [20GEMSDOE](https://buffedlizard55-lab.github.io/20GEMSDOE/docs/index.html) | `0.0904`; `0.1855`, `0.0976`, `0.0360`; `0.1894`; `0.1890`, `0.1859` |
| [GEMSDOE22](https://buffedlizard55-lab.github.io/GEMSDOE22/docs/index.html), [GEMSDOE23](https://buffedlizard55-lab.github.io/GEMSDOE23/), [GEMSDOE24](https://buffedlizard55-lab.github.io/GEMSDOE24/), [GEMSDOE25](https://buffedlizard55-lab.github.io/GEMSDOE25/), [GEMSDOE26](https://buffedlizard55-lab.github.io/GEMSDOE26/) | `0.1002`, `0.0748`; `0.1352`; `0.2477`; `0.2600`; DILCOND `0.1223` |
| [GEMSDOE27](https://buffedlizard55-lab.github.io/GEMSDOE27/), [GEMSDOE30](https://buffedlizard55-lab.github.io/GEMSDOE30/), [GEMSDOE31](https://buffedlizard55-lab.github.io/GEMSDOE31/docs/), [GEMSDOE33](https://buffedlizard55-lab.github.io/GEMSDOE33/) | `0.2449`; `0.2600`; `0.2708`; `0.2632` |
| [GEMSDOE34](https://buffedlizard55-lab.github.io/GEMSDOE34/docs/index.html), [GEMSDOE35](https://buffedlizard55-lab.github.io/GEMSDOE35/docs/index.html), [GEMSDOE36](https://buffedlizard55-lab.github.io/GEMSDOE36/docs/), [GEMSDOE37](https://buffedlizard55-lab.github.io/GEMSDOE37/) | `0.0778`; `0.0418`; `0.2750`; `0.1193` |
| [GEMSDOE38](https://buffedlizard55-lab.github.io/GEMSDOE38/docs/index.html), [GEMSDOE42](https://buffedlizard55-lab.github.io/GEMSDOE42/docs/index.html), [GEMSDOE43](https://buffedlizard55-lab.github.io/GEMSDOE43/docs/index.html), [GEMSDOE45](https://buffedlizard55-lab.github.io/GEMSDOE45/) | `0.0763`; `0.0581`; `0.0424`; `0.0106` |
| [GEMSDOE49](https://buffedlizard55-lab.github.io/GEMSDOE49/), [GEMSDOE32](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html), [GEMSDOE28](https://buffedlizard55-lab.github.io/GEMSDOE28/), [GEMSDOE29](https://buffedlizard55-lab.github.io/GEMSDOE29/docs/index.html) | `0.2376`; `0.2778`; `0.2708`, `0.2649`, `0.2710`, `0.2707`; `0.2600`, `0.2560`, `0.0532` |
| [GEMSDOE46](https://buffedlizard55-lab.github.io/GEMSDOE46/), [GEMSDOE39](https://buffedlizard55-lab.github.io/GEMSDOE39/), [GEMSDOE40](https://buffedlizard55-lab.github.io/GEMSDOE40/docs/index.html), [GEMSDOE41](https://buffedlizard55-lab.github.io/GEMSDOE41/docs/index.html), [GEMSDOE44](https://buffedlizard55-lab.github.io/GEMSDOE44/docs/) | `0.1589`, `0.0843`; `0.0339`; `0.0355`; `0.0245`; `0.0715` |
| [GEMSDOE47](https://buffedlizard55-lab.github.io/GEMSDOE47/), [GEMSDOE48](https://buffedlizard55-lab.github.io/GEMSDOE48/docs/index.html), [GEMSDOE50](https://buffedlizard55-lab.github.io/GEMSDOE50/), [GEMSDOE51](https://buffedlizard55-lab.github.io/GEMSDOE51/), [GEMSDOE53](https://buffedlizard55-lab.github.io/GEMSDOE53/docs/index.html), [GEMSDOE54](https://buffedlizard55-lab.github.io/GEMSDOE54/docs/) | `0.0430`; `0.2296`; no score supplied; no score supplied; no score supplied; no score supplied |
| [Official leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) | The prompt calls `0.3195` the current high value. This was not verified by the live page-fetch in this review; sibling dated reports disagree and must be checked directly. |

These rows are retained for history only. They are not a promotion criterion; only the current same-evaluator holdout and an organizer receipt can support the respective claims.

</details>
