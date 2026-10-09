# Leaderboard review and submission-status audit — 2026-10-09

Status: **no new submission raster was generated in this session.** The competition
feature rasters are not on this machine, and the sandbox cannot reach the
DrivenData data tab (login-gated), ScienceBase, or Dropbox. The only copies of
the features that earlier sessions used came from a sibling GitHub repo (see
Irregularity IR-55-034). Nothing below is a new score.

Evidence labels used here:

- **PUBLIC-LEADERBOARD**: value shown on the organizer's public leaderboard page, fetched this session. Not a submission-page receipt.
- **ORGANIZER-CONFIRMED**: copied from a submission-page receipt. None exists in this repo.
- **USER-SUPPLIED**: value written in the owner brief or a sibling site. Unverified.
- **HOLDOUT-DTI**: evaluator `src/gems55/dti55.py`, alpha 0.2, beta 0.8, 300 m kernel, with the withheld-positive count and 95% CI.

## 1. Answer: why did 0.2778 score, and can we beat it?

**What is verified.** On the public leaderboard page, the 0.2778 value is
**PUBLIC-LEADERBOARD rank 16**, listed under participant `extradr19`
([leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/),
captured in [`evidence/leaderboard_snapshot_20261009.json`](../evidence/leaderboard_snapshot_20261009.json)).
Rank 1 is 0.3774 (xiaofanhu). **0.3195 is rank 7, not the highest score**, as the
owner brief states. The mapping of the GEMSDOE32 site name to the `extradr19`
account is not verified.

**What the repo's own forensics show** about the anchor raster
(`h33-2-b2`, 37,654 unit dots; [`evidence/anchor_forensics.json`](../evidence/anchor_forensics.json),
[`evidence/anchor_verdict.json`](../evidence/anchor_verdict.json)):

| Property | Value | Read |
|---|---|---|
| Dot count | 37,654 = 0.73% of the 5,167,373-px scored footprint | Sparse. Score is set by where the few dots are, not by coverage. |
| Dots on mapped/visible faults | 0 | Not a copy of the training catalogue. |
| Fraction of dots within 3 px of a visible fault | 10.2% vs 11.0% expected for uniform random | Roughly neutral, slightly below random. |
| Dot-to-dot nearest-neighbour spacing, 10th percentile | 2.83 px (verdict) or 4.12 px (forensics) | **The two files disagree** (IR-55-036). Either way the dots are clustered, not Poisson. |
| Catalogue-proxy DTI (whole visible catalogue as truth) | 0.0049 vs 0.0321 for uniform random (44,090 dots) | On the catalogue proxy the anchor is **worse than random**. |

**Mechanism (reasoned from the official metric, not measured on labels).** The
official metric is `DTI = TPw / (TPw + 0.2 FPw + 0.8 FNw)`, with a triangular
300 m (3 px) kernel. The page states that FP weight is `p(x)[1 - max_g k(d)]`,
so a dot 1–2 px from a true trace has a small FP cost and earns TP credit.
A dot 3 px or more away pays the full FP cost. The best use of a sparse budget
is therefore dots packed tight along the most probable new trace, not dots
spread over the footprint. The anchor's clustering is consistent with this. The
reasoning is not a measured result.

**Why the repo's holdout ranks candidates the wrong way (key finding).** The
official problem statement says the test faults are **new faults that are not in
the public USGS database**
([problem page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)).
The repo's holdout asks a different question: can a method recover catalogue
faults that were hidden? The anchor was not run through that holdout. Under the
whole-catalogue proxy it scores worse than random (0.0049 vs 0.0321). On the
leaderboard it scores 0.2778. A holdout that rewards catalogue recovery
can therefore rank candidates in the wrong order for the real target. This is a
validity risk for every HOLDOUT-DTI number in this repo. It is a hypothesis
about the evaluator, not yet a proven fact. It is tested in T-D of
[`docs/hypotheses.md`](hypotheses.md).

**Second structural difference.** The repo's shipped emitter enforces a minimum
dot separation of 3 px (`scripts/submission_writer.py --min-sep 3.0`,
`src/gems55/holdout55.py` `emit_dots`). The anchor's own evidence reports
dot-to-dot spacing below 3 px at the 10th percentile in one computation. So the
repo's constraint may cap the tight-packing strategy above. This is untested.

**Can we beat 0.2778?** Unknown in this session. Reasons:

1. No feature stack is on disk, so no candidate can be generated or scored.
2. The repo's best one-scale holdout arm (ridge × strike agreement, HOLDOUT-DTI
   0.01852, CI [0.01782, 0.01940], 60,988 withheld positives, evaluator
   `dti55.py`) beats its one-scale ridge-only arm (0.01779). Its preregistered H56
   multi-scale candidate (0.01728, CI [0.01613, 0.01847]) does **not** beat that
   comparator. The H56 multi-scale ridge-only ablation (0.01927) does score
   higher, but it is an ablation, not the shipped candidate.
3. The holdout's ranking may not match the leaderboard target (see above), so a
   holdout win would not be enough evidence to spend a slot.
4. The public top is 0.3774, so there is room, but no route to it is verified.

Holdout numbers and leaderboard numbers are on different scales and are not
comparable.

## 2. Is the existing TIF OK to download and submit?

| Question | Decision | Basis |
|---|---|---|
| Format valid? | Yes | Re-read this session with rasterio 1.4.4: one float32 band, EPSG:32611, 3730 × 3292, transform `(100, 0, 243350, 0, -100, 4508550)`, values in [0,1]. The zeros file has no NaN. The NaN twin has 7,111,787 NaN, which equals 12,279,160 − 5,167,373 footprint pixels. The run card's sha256 matches (`43743afd…`). |
| Download for audit? | Yes | Format valid. Provenance is weak: the inputs came from a sibling repo mirror, not the official DrivenData download (IR-55-034). |
| **Submit?** | **NO — DO NOT SUBMIT** | Strict uniqueness gate = DUPLICATE-STOP (final dots overlap a prior raster 1.000 and 0.736 within 3 px, above 0.70). The registry covers 56 rasters, not every site in the owner's list. No organizer receipt exists. |

The official format says values must be in [0,1] and that outside-bounds data
should be "null or nan". The repo writes zeros outside the footprint. The
official reference notebook
([repo](https://github.com/drivendataorg/gems-prize-reference-solution)) also
writes a zero-initialised array with sigmoid probabilities. That supports the
zeros choice, but it is not an organizer confirmation. It also writes float64
by default, which is not the spec's float32 (IR-55-037).

## 3. What is needed to make a real, unique submission

1. **Official data placement (user action, the only real blocker).** Log in to
   DrivenData, accept the rules, download `training_features.tif`,
   `labels.tif`, `sample_submission.tif` and the DEM links from the
   [data tab](https://www.drivendata.org/competitions/306/competition-doe-gems/data/),
   and place them in `data/`. Then run `python scripts/prepare_data.py`. Hash
   pins are in `data/README.md`, but they came from the sibling mirror and are
   not verified against DrivenData.
2. **Eligibility and disclosure (user action).** The rules limit individual
   competitors to U.S. citizens or permanent residents
   ([rules §1.3](https://docs.nlr.gov/docs/fy26osti/96647.pdf)). The rules also
   require a narrative statement of any generative-AI use (§3.2). The owner
   must confirm both.
3. **Submission cap.** The rules allow three submissions per week (§3.2, §3.4).
   The repo's policy keeps promotion separate from experimentation.
4. **Data-provenance decision.** Whether to keep using the sibling-repo copy is a
   decision for the owner. See the question at the end of this review.

## 4. Sources (checked this session)

| Item | Link | Checked |
|---|---|---|
| Problem description and metric | https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/ | fetched; metric, format, new-fault test set, layer list |
| Public leaderboard | https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/ | fetched; ranks 1–22 captured |
| Official rules | https://docs.nlr.gov/docs/fy26osti/96647.pdf | fetched; §1.3, §3.2, §3.4, §3.5, §3.6, App. A |
| Data tab | https://www.drivendata.org/competitions/306/competition-doe-gems/data/ | fetched; redirects to login, not downloadable here |
| Official reference solution | https://github.com/drivendataorg/gems-prize-reference-solution | downloaded archive; README says data must come from the GEMS data page; notebook output zero-initialised |
| GeoDAWN release | https://doi.org/10.5066/P93LGLVQ | cited by the rules; not downloadable from the sandbox |
| INGENIOUS label compilation | https://doi.org/10.15121/1881483 | cited by the rules §3.3 |
| USGS Quaternary Fault and Fold Database (ScienceBase) | https://www.sciencebase.gov/catalog/item/589097b1e4b072a7ac0cae23 ; DOI https://doi.org/10.5066/P9BCVRCK | search result: last update 2020-09-02, change log and GIS zip listed; **not downloaded** (sandbox blocks sciencebase.gov) |
| USGS faults page | https://www.usgs.gov/programs/earthquake-hazards/faults | search result: database search retired 26 Feb 2026; download still listed |

## 5. Verification log (this session)

- `fetch_page` on the problem page, the rules PDF (chunks 0–5), the data tab
  (login redirect), and the leaderboard (chunk 0 of 3). Quotes above are from
  these pages.
- Reference repo archive: file tree via the GitHub API; notebook cells 0, 1, 5,
  6, 12, 16, 17, 19 parsed with `json`. Output init and final write confirmed.
- Audit TIFs (`docs/downloads/`): sha256 recomputed; rasterio re-read of every
  file (counts, dtype, CRS, shape, transform, NaN, min/max, positive count).
- `pytest tests_numeric tests`: **34 passed, 2 skipped**.
- Not run: `validate_submission.py` and `verify_unique.py`. Both need the
  template feature raster, which is not on disk. Their results are therefore
  **not re-measured** this session. The earlier results are the run-card values.

## 6. Run card (review session; no experiment run)

```json
{
  "schema": "55gemsdoe.run-card.v3",
  "run_id": "55GEMSDOE-REVIEW-2026-10-09",
  "hypothesis": "none tested this session; review of why the 0.2778 public entry scored and whether the repo can beat it",
  "mechanism": "not tested; reasoned from the official DTI kernel: near-miss dots cost little FP and earn TP",
  "named_non_fault_mimic": "linear artefacts (flight-line striping, levelling seams, FFT ringing) and lithologic contacts or dikes, which are also long and 2-D",
  "holdout_dti": {"status": "NOT RUN", "evidence_class": "none"},
  "leakage_canary": {"status": "NOT RUN"},
  "correlation_overlap_vs_registry": {"status": "NOT RUN", "reason": "no feature stack or candidate surface on disk"},
  "raster_sha256": "43743afdb030b739465d4754aabd8605bceef49bcc836bee93e9094807d4695f (existing audit file, unchanged; re-read this session)",
  "validator_output": {"status": "NOT RE-RUN (template raster missing)", "independent_reread": "PASS for format fields (see section 2)"},
  "submission": {"name": null, "note": null, "submit_allowed": false},
  "public_leaderboard": {"evidence_class": "PUBLIC-LEADERBOARD", "rank_0_2778": 16, "top": 0.3774, "rank_0_3195": 7},
  "verdict": "negative (no new candidate); data blocker"
}
```

## 7. Question for the owner (decision required)

The official data must come from DrivenData. The sibling repo copy has
unverified provenance and may fall outside the rules (IR-55-034). Choose one:

- **A (recommended):** you download the three files from the DrivenData data tab into `data/` (you have the login, not the sandbox). I then run the pipeline and the uniqueness gate end to end.
- **B:** I pull the sibling `data/bridge` copy into the sandbox's gitignored `data/`, with an explicit licence-risk note on the run card.
- **C:** stop data work and keep the repo as an audit and research record.
