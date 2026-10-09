# 55GEMSDOE — GEMS Prize (DOE) fault-prediction workbench

> **Start here every session.** This README is the project brief. Read it before working.
> Verdict status and what is blocked are in [§ Status](#status-as-of-2026-10-09).

## 1. Brief (condensed from the session prompt — the full original text is kept in the session log)

**Goal.** Produce a GeoTIFF of fault-presence probabilities for the GEMS Prize (DrivenData competition 306,
DOE/NLR) that scores as high as possible on the distance-weighted Tversky index (DTI), and keep a
clean, auditable, source-verified record of every number, hypothesis and irregularity.

**Non-negotiables (from the brief):**
- Work line by line from official, verifiable sources; give links for manual review; no hallucinated numbers.
- Label every number as **HOLDOUT-DTI** (evaluator version, withheld positives, 95% CI) or
  **ORGANIZER-CONFIRMED** (copied from a submission-page receipt). A projection is never written as a score.
- Flag every irregularity in [docs/irregularities.md](docs/irregularities.md). No manual input in pipelines.
- Each submission: unique name + ≤140-character note; must not duplicate any earlier raster.
- Parallel-run protocol: a lane is a single method. Rank correlation > 0.90 or >70% dot overlap with a
  registry raster = duplicate → stop. Leakage canary: any single feature with holdout AUC > 0.90 = leakage until proven otherwise.
- Budget per lane: 3 experiments or 2 hours. Promotion to a weekly slot is a separate selector step (3 per week).
- Generative-AI use must be disclosed in the submission narrative (rules §3.2).
- Core values: **Maximize P(Win)** and **Own the Outcome** — negative results are deliverables.

**Competition facts (verified 2026-10-09 against official pages):**
- Metric: distance-weighted Tversky, α = 0.2, β = 0.8, triangular kernel R = 300 m (3 px). Source: [problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/).
- Format: one single-band float32 GeoTIFF, EPSG:32611, 100 m, same bounds as training data, outside bounds null/NaN, values in [0, 1]. Source: same page, "Submission format".
- Rules: [official rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf) — up to three submissions per week; one final submission; generative-AI disclosure required.
- Reference solution: [drivendataorg/gems-prize-reference-solution](https://github.com/drivendataorg/gems-prize-reference-solution) (U-Net, Tversky loss α=0.2, β=0.8).
- Data: the official files are only downloadable after DrivenData login. **This sandbox cannot reach DrivenData**, see [data/README.md](data/README.md).

## 2. Repository layout

| Path | What it is |
|---|---|
| `docs/index.html` | GitHub Pages landing page — executive summary, submission box, status |
| `docs/executive-summary.html` | Step-by-step **how to make a submission** |
| `docs/leaderboard-analysis.md` | Why the 0.2778 "zeros" entry scored high; what it implies for us |
| `docs/hypotheses.md` | Ranked candidate hypotheses, validation plan, data needs |
| `docs/irregularities.md` | Every anomaly found, with evidence and the line of code or link that shows it |
| `docs/sources.md` | Official source links and their verification status |
| `docs/results/` | JSON results (holdout, canary, strike test, registry check, run card) |
| `docs/downloads/` | Candidate GeoTIFFs. **Files prefixed `NEGATIVE-DO-NOT-SUBMIT` are not submissions.** |
| `gems/metric.py` | Official DTI, checked against the worked example and hand-computed cases |
| `gems/submission.py` | Writer + validator for the official format (CRS, shape, transform, range, NaN rules) |
| `gems/tensor.py` | FFT gradient tensor, dimensionality index, strike, ridges, stripe mask |
| `gems/holdout.py` | Quadrant-fold hide-and-recover holdout, block bootstrap CI, AUC canary |
| `scripts/run_tensor_lane.py` | Full lane run: E1/E2/E3, canary, strike test, writes candidate TIFs |
| `scripts/registry_check.py` | Uniqueness check against every raster in the GEMSDOE registry |
| `scripts/make_run_card.py` | Builds the protocol run card from saved results |
| `tests/` | 14 unit tests (metric, validator, tensor sign conventions, AUC) — `pytest -q tests` |

## 3. How to reproduce (no manual input)

```bash
python3 -m venv .venv && . .venv/bin/activate && pip install numpy scipy rasterio pytest
# 1. place official rasters into data/ (see data/README.md) — they are gitignored
python scripts/prepare_data.py            # presence + sha256 check
pytest -q tests                            # unit tests
python scripts/run_tensor_lane.py --out docs/downloads/<name>.tif --tag <name>
python scripts/registry_check.py docs/downloads/<name>.tif <registry_dir> docs/results/registry_<name>.json
python scripts/make_run_card.py
```

## 4. Status as of 2026-10-09

- **Submission:** none recommended. The tensor-dimensionality lane is **negative** on our holdout (see
  [docs/index.html](docs/index.html) and [docs/results/run_card_tensor_lane.json](docs/results/run_card_tensor_lane.json)).
- **Blocked here:** DrivenData login, DrivenData data tab, USGS/OpenEI/GitHub-Pages sites are not reachable from this sandbox.
  The rasters used for the holdout were obtained from the user's own sibling repo's data bridge (see `data/SOURCES.md`).
- **Not verified:** organiser scores. The only scores in this repo are HOLDOUT-DTI.

## 5. Generative-AI disclosure

Code, documentation and analysis in this repository were produced with generative-AI assistance (Arena Agent Mode).
All numbers are reproducible from the scripts and the saved JSON; every external claim has a link in
[docs/sources.md](docs/sources.md). The author of any submission is responsible for the accuracy of this disclosure
(rules §3.2).
