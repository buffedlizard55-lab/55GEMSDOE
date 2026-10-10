# Session review — 2026-10-09 (tensor-dimensionality lane)

**Decision: NOT CLEARED — DO NOT DOWNLOAD OR SUBMIT.** No GeoTIFF was generated, linked, or submitted in this session. Every number below is labelled with its evidence class: `PUBLIC-LEADERBOARD`, `HOLDOUT-DTI`, `SYNTHETIC-CHECK`, `ORGANIZER-CONFIRMED`, or `NOT VERIFIED`. The source-by-source check is in [`official-verification-20261009.md`](official-verification-20261009.md).

---

## 1. The TIF request — why no file is downloadable

The brief asks for a unique, downloadable GeoTIFF now. I did not produce one, because it cannot be done honestly from this sandbox. The blockers are listed in order of severity.

| Gate | Required | Status here | Evidence |
|---|---|---|---|
| Input data | Feature stack, labels, organizer sample template | **Absent.** `data/` holds only READMEs. | `ls data/`; [data tab](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) returns a login page to this sandbox (A9). |
| Footprint and grid | Footprint from the organizer template | **Absent.** The 3292×3730 shape and transform are repo constants (`src/gems55/io55.py`) that have not been checked against an organizer file. The official page gives CRS and 100 m resolution only (A4). | `src/gems55/io55.py`, IR-55-031. |
| Holdout | Same-evaluator HOLDOUT-DTI with evaluator version, count, CI | **Not runnable.** No features, no labels, no shared evaluator. | `docs/run-card.json`; `scripts/evaluate_holdout.py` is retired fail-closed. |
| Leakage canary | Each feature alone, AUC < 0.90 | **Not runnable.** | Same. |
| Uniqueness | Surface ≤ 0.90 rank correlation; final dots ≤ 70% within 3 px of every registry raster | **Not runnable.** Registry rasters absent. The historical records already exceed the literal limit (84.13%, 84.01%, 100%). | `docs/irregularities.md` IR-55-030; `evidence/uniqueness*.json`. |
| Format | Validator against the authentic template | **Not runnable.** The validator needs the template. | `scripts/validate_submission.py` exits non-zero without it. |
| Budget | ≤ 3 experiments or 2 hours | Three recorded experiments already used. | `docs/run-card.json`. |

A raster built with no features would be random placement, not a candidate. Uploading one to the competition would not be a submission of a method, and a file without holdout, leakage, and uniqueness checks cannot be called unique or validated. So the download button stays off, and the site says so at the top.

**What would unlock a file:** a human account holder downloads `training_features.tif`, `labels.tif`, `sample_submission.tif`, and `1m_DEM_links.csv` from the DrivenData data tab (login and rules acceptance required) and places them in `data/` under the canonical names in `src/gems55/io55.py`. Then `scripts/prepare_data.py` checks hashes against the mirror pins. Any mismatch is a stop condition (IR-55-032). Nothing in this sandbox can perform that download.

---

## 2. Why did 0.2778 score, and can we beat it?

**First, the premise needs correction.** The live public leaderboard (fetched this session) does not show 0.2778 as the highest score:

- Rank 1: xiaofanhu, **0.3774**
- Rank 7: DARD, **0.3195**
- Rank 16: op01, 0.2797
- Rank 17: extradr19, **0.2778** (`PUBLIC-LEADERBOARD`, not a receipt)

The repo's earlier snapshot said rank 16 because it omitted rank 8 (giles, 0.3025). That is corrected in `evidence/leaderboard_snapshot_20261009.json` (IR-55-043). The brief also says both "0.3195 is the highest score" and "0.3774 is the high score". The live page supports 0.3774 at rank 1 (IR-55-044).

**Second, the mapping from the H33 site to 0.2778 is unverified.** The owner manifest reports `receipt: null`, labels H33 `UNSCORED`, and calls 0.2747 "projected" — a value that differs from 0.2778 (`NOT VERIFIED`). So no evidence ties this file to the number.

**Third, the mechanism — what the verified metric rewards.** From the official formula (A1–A3), with a synthetic check through the repo's transcription (D3–D4, `SYNTHETIC-CHECK`, not holdout):

1. **Recall dominates.** β=0.8 penalises each unmatched truth pixel far more than α=0.2 penalises a predicted-mass unit. A map must hit truth more than it wastes mass.
2. **Credit decays linearly with distance.** For one truth pixel and one dot at distance d, DTI = k(d) = 1 − d/3 exactly: 1.000, 0.667, 0.333, 0.000 at d = 0, 1, 2, 3 px.
3. **Diffuse mass is punished.** The FP term sums p over the whole footprint. On a 41×41 synthetic line, uniform p=0.5 scores 0.106. Dots every 4 px on the line score 0.722, and the same dots one column off score 0.544.

So a sparse set of high-confidence points placed on or next to the truth beats a smooth probability surface. The public site names suggest this family ("dotted", "dots", "zeros" suffixes, as listed in the user brief). The repo's leaderboard review raises the same sparse/near-miss mechanism only as a hypothesis, not as an established explanation.

**Why this particular entry was high:** I cannot establish that from the evidence. The raster is not in the repo, its feature stack is not available, its hidden-test coverage is unknown, and its mapping is unverified. I withdraw any earlier count-only explanation (IR-55-025). The honest answer is: *the metric favours sparse, on-structure dots; whether 0.2778 is an instance of that is not established.*

**Can we beat it?** Not established. No repo candidate has a valid HOLDOUT-DTI, and the three-experiment budget is spent. Beating a `PUBLIC-LEADERBOARD` value also needs an organizer-scored receipt, and the public score is only a subset of the test data (rules §3.6.1 governs the private and final rounds).

---

## 3. Candidate hypotheses (3–5), ranked

All four in-lane hypotheses in [`hypotheses.md`](hypotheses.md) are still the only in-lane set. The candidates below add one new decision-layer idea and three out-of-lane ideas. The three out-of-lane ideas need a lane change decision from the operator before implementation. Expected DTI improvement is **not estimated**: no holdout exists to measure it.

| Rank | Hypothesis | Layers | Signature | Why it could find an uncatalogued fault | Difference from the repo | Cost | Status |
|---|---|---|---|---|---|---|---|
| **1** | **H-N1 Metric-aware sparse placement.** Convert the existing tensor-lane continuous score into dots by optimising the official DTI on the holdout rather than a coverage surrogate. | Existing tensor-lane surface (bands 2 and 13). | Local maxima of the tensor-lane score, spaced at least 3 px, with a per-dot threshold set by expected DTI. | Placement that accounts for β > α and the 3-px kernel can recover ridge credit without spreading mass. | `greedy_cover` optimises a coverage surrogate and omits FP (IR-55-027). This would optimise full DTI. | Low once the surface exists. | **Not validated.** Needs holdout. Risk: overfitting to the visible-fault geometry. |
| 2 | H-N3 Heat-flow lineament corridor. Heat-flow maps from INGENIOUS (DOI 10.5066/P9BZPVUC). | External heat-flow grid (INGENIOUS listing, C9). | Elevated, linear heat-flow trends perpendicular to a Quaternary-fault trend. | Fault-controlled upflow can be thermally expressed where the trace is not mapped. | Not in the lane; no thermal layer in the repo. | Moderate; licence and interpolation checks. | **Out of lane; licence NOT VERIFIED (C10).** |
| 3 | H-N5 Electrical conductance corridor. Peacock & Bedrosian (DOI 10.5066/P9TWT2LU). | External conductance map. | Conductive linear zones with fluid or clay alteration. | Fluid-bearing fault zones are conductive. | The competition stack already contains surface conductivity and depth to conductive base ([problem description, Provided features](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)). | Low–moderate. | **Largely redundant with the official stack; out of lane.** |
| 4 | H-N4 Slip/dilation tendency (Siler, DOI 10.5066/P9YL58W6). | Derived from the USGS Quaternary fault geometry. | Stress-favourable fault segments. | Could rank unmapped segments by stress. | **Label leakage.** The USGS QFDB is a label source (C7). The product is only usable if rebuilt from visible faults inside each holdout fold. | Moderate. | **Leakage trap; do not use as a feature without per-fold re-derivation.** |

**Ranking logic:** H-N1 ranks first because it is in-lane, cheap, and aimed at the metric's stated structure. Its gain is unmeasured. H-N3 is next on contrarian value; its interpolation artifacts and licence are the main risks. H-N5 ranks below H-N3 because its signal is already in the official stack. H-N4 is included as a warning, not as a candidate.

---

## 4. Sources (verified this session; full list in the verification log)

- [Official problem description and metric](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) — A1–A6.
- [Official rules, NLR PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf) — A7.
- [Data tab (login)](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) — A9.
- [Leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) — B1–B3.
- [GeoDAWN, ScienceBase](https://www.sciencebase.gov/catalog/item/657e1d85d34e23d3533209f7), DOI 10.5066/P93LGLVQ — C1–C5.
- [USGS Quaternary Faults](https://www.usgs.gov/programs/earthquake-hazards/faults), DOI 10.5066/P9BCVRCK — C6–C7.
- [INGENIOUS, GBCGE](https://gbcge.org/current-projects/ingenious/) — C8–C9.

---

## 5. Limitations and access needed

1. **DrivenData login.** The data tab requires an account and rules acceptance. The sandbox cannot authenticate and cannot reach the host. A human account holder must download, or the operator must place the four files in `data/`.
2. **Registry rasters.** Needed for the uniqueness gate. Not in the repo; the historical scans are not current.
3. **Authentic template.** Needed for the format gate and footprint.
4. **Licences.** The C9 products and the GeoDAWN release must be checked for licence and sharing terms before any use in a submission. Not checked here (C10).
5. **Budget and lane.** The three-experiment budget is spent. Out-of-lane candidates need an explicit lane decision.
6. **Score visibility.** Public scores are a subset. Private and final-round scores are not visible, so no leaderboard value predicts final rank.

---

## 6. Irregularities flagged this session

Logged in [`irregularities.md`](irregularities.md) as IR-55-043 to IR-55-047.

- **IR-55-043** — Repo leaderboard snapshot omitted rank 8 and mis-ranked extradr19 (16 → 17).
- **IR-55-044** — The brief's "0.3195 is the highest score" conflicts with the live page (0.3774 at rank 1).
- **IR-55-045** — The brief calls 0.2778 the highest score, while the live page places extradr19 at rank 17. The owner-to-participant mapping is the same open issue as IR-55-034.
- **IR-55-046** — The official page says outside-bounds cells are "null or nan", while the repo's `zeros` variants are not the stated encoding. The portal's treatment of NaN and zeros is not published. The user's reported error "Predicted values must be in range [0, 1]" could not be reproduced here, because no file was generated and the portal was not accessed.
- **IR-55-047** — Sandbox cannot reach DrivenData or NLR. Official verification was done through the fetch tool only.

---

## 7. Three-pass review

- **Pass 1 — implementation.** Verified the metric and the synthetic checks; wrote the verification log; corrected the leaderboard snapshot; wrote this review and the run card.
- **Pass 2 — bug and assumption audit.** Found the snapshot rank error (IR-55-043), the 0.3195 vs 0.3774 conflict (IR-55-044), and the NaN-vs-zeros encoding question (IR-55-046). Confirmed no experiment was run and no receipt was invented.
- **Pass 3 — requirement and source audit.** Quantitative claims are traced to rows in the verification log or to labelled synthetic checks. Required run-card fields are present. Tests are rerun after the edits (see the run card).

---

## 8. Suggested next steps

1. **Operator:** place the four DrivenData files in `data/` under the canonical names (or confirm they are not obtainable). Nothing else unblocks the holdout.
2. **Operator:** decide whether to reopen the experiment budget and whether to allow out-of-lane candidates (H-N3, H-N5).
3. **Engineering:** when data arrives, run H-N1 against the shared holdout with per-feature leakage canaries before any slot is considered.
4. **Engineering:** rebuild the leaderboard snapshot from the live page with all rows, not a truncated capture.
5. **Records:** keep the public and holdout labels separate. Do not promote a `PUBLIC-LEADERBOARD` value into a score.
