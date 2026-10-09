# 55GEMSDOE — tensor-dimensionality lane

DrivenData competition **306**, *The Geologic Enhanced Mapping System (GEMS)
Prize Challenge*, GeoDAWN region, northwestern Great Basin. Read this file first
at the start of every session, then read `docs/run-card.json`, `docs/status.json`,
`docs/hypotheses.md`, and `docs/irregularities.md`. The dated public leaderboard observation is in
`evidence/leaderboard_snapshot_20261009.json`; numbers in this README are labelled
by evidence class.

## Current decision: audit artifact generated, submission blocked

A new raster was generated from this checkout and is **not a copy of the earlier
H55 raster**:

- **Audit TIF:** [`docs/downloads/h56-multiscale-tensor-persistence-40000dots-20261009T162812Z-zeros.tif`](docs/downloads/h56-multiscale-tensor-persistence-40000dots-20261009T162812Z-zeros.tif)
- **Audit ZIP:** [`docs/downloads/h56-multiscale-tensor-persistence-40000dots-20261009T162812Z-zeros.zip`](docs/downloads/h56-multiscale-tensor-persistence-40000dots-20261009T162812Z-zeros.zip)
- **NaN-outside comparison only:** `docs/downloads/h56-multiscale-tensor-persistence-40000dots-20261009T162812Z-nan.tif`
- **TIF SHA-256:** `43743afdb030b739465d4754aabd8605bceef49bcc836bee93e9094807d4695f`
- **Portal note, 86/140 characters:** `tensor-dim lane: FFT grad-tensor RTP-mag+iso-grav, 2-D/strike-gated ridges, 40000 dots`

### Is it OK to download and submit?

| Question | Decision | Measured reason |
|---|---|---|
| Can the all-finite TIF be downloaded for audit? | **YES — AUDIT ONLY** | This checkout's byte-level read confirms one float32 band, EPSG:32611, shape 3730×3292, transform `(100, 0, 243350, 0, -100, 4508550)`, all finite values in [0,1], and 40,000 positive cells. The committed run card records the prior full 12/12 template-based validator result; it cannot be reproduced in this checkout because `data/sample_submission.tif` and `data/labels.tif` are absent. |
| Is the H56 candidate scientifically cleared? | **NO** | Prior HOLDOUT-DTI evidence was negative versus the one-scale comparator; prior strict dot uniqueness was `DUPLICATE-STOP`. Competition features/cache and registry rasters are absent here, so none of those checks was rerun. |
| Is it cleared to upload to DrivenData? | **NO — DO NOT SUBMIT** | The strict parallel-run uniqueness gate is `DUPLICATE-STOP`: final dots overlap one prior raster by 1.000 and another by 0.736 within 3 px, above the 0.70 stop threshold. No weekly slot was used. |
| Did the organizer confirm a score for this raster? | **NO** | There is no submission-page receipt. The official public leaderboard snapshot is recorded separately, but its rows do not map to a raster filename or hash. |
| Did the candidate beat the current same-evaluator holdout best? | **NO** | **HOLDOUT-DTI** full multiscale tensor lane = 0.01728, 95% CI [0.01613, 0.01847], versus one-scale `ridge_x_agree` comparator = 0.01852, 95% CI [0.01782, 0.01940]. Both use 60,988 withheld positives and the corrected segment evaluator. |

The file is therefore a **hash-identified audit artifact**, not a cleared
competition submission. The web site repeats this distinction at the top
of [`docs/index.html`](docs/index.html). A chance-adjusted overlap is reported for
research, but it never overrides the literal >70% stop rule.

## Official public leaderboard snapshot — not a file receipt

The official public leaderboard rendered during this review (captured 2026-10-09
18:48:54 UTC). Its displayed best-public rows show **0.3774 at rank 1**,
**0.3195 at rank 7**, and **0.2778 at rank 16**. The leaderboard identifies
participants, not GeoTIFF filenames or hashes, so it cannot verify that the H33
raster named in the user brief produced the 0.2778 row. The GEMSDOE32 H33 page
itself labels that candidate `UNSCORED` and calls 0.2747 a projection. Do not
attribute a public row to that raster without a matching submission-page receipt.
See [dated snapshot](evidence/leaderboard_snapshot_20261009.json) and
[H33 analysis](docs/leaderboard-analysis.md). This public-page observation is not
an `ORGANIZER-CONFIRMED` submission receipt; the run-card receipt list remains
empty.

## Retraction: anchor proxy-DTI analysis

A line-by-line audit found that the old anchor-forensics scripts assumed
`TP_w + FP_w = N`. The official metric only implies `TP_w + FN_w = |G|`; TP and
FP are separately defined, so the old proxy-DTI values, hidden-label-size algebra,
and conclusions based on them are **retracted**. Those historical JSON files
remain with a retraction marker; scripts 5–7 now fail closed. The same invalid
denominator also appeared in a `greedy_cover` docstring and the old exp10 sweep
rationale; both now state that greedy expected-credit placement is only a heuristic,
not an exact DTI optimizer. Exact DTI must be measured by the canonical evaluator
inside a proper segment holdout. See `docs/irregularities.md` IR-55-034. No holdout
experiment or submission slot was used to make this correction.

## Historical tensor-lane final pass (h55) — DO NOT SUBMIT

The h55 audit used its three-experiment budget and reached a **negative**
pre-registered decision; its secondary protocol disagreed with its primary. No
submission slot was used. The exact measured results must be read from
[`docs/run-card-h55-160k.json`](docs/run-card-h55-160k.json), where each score is
paired with the evaluator, withheld-positive count, CI, and protocol. That audit
is historical, not a fresh result from this review. Its TIFF is for audit only and
is blocked by the strict registry rule.

- **Artifact:** `docs/downloads/audit-h55-160k/h55-tensor2d-strikegate-160000dots-20261009T164334Z-zeros.tif` (SHA-256 begins `ffd2a892`).
- **Page:** `docs/h55-160k-audit.html`.
- **Historical caveats:** striping axis, two striping detectors, holdout-emitter mismatch, and zeros-versus-NaN remain logged in `docs/irregularities.md`.
- **Budget:** prior run used its three-experiment cap; this review ran no new holdout experiment.


---

## Reproducible commands

Competition payloads are intentionally not committed. On a machine where the
participant has accepted the competition terms, place the official files in
`data/` and verify their hashes:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
python scripts/prepare_data.py

# One-scale comparator and the preregistered H56 multi-scale candidate
.venv/bin/python scripts/build_lane.py --tag baseline --along-axis 0
.venv/bin/python scripts/build_lane.py --tag h56_ms300_900 --scales-m 300,900 --along-axis 0
.venv/bin/python scripts/evaluate_holdout.py --tag baseline --n-dots 40000 --min-sep 3 \
  --arms random,ridge_only,ridge_x_dim,ridge_x_agree,tensor_full \
  --out evidence/holdout_baseline_segment_n40000.json
.venv/bin/python scripts/evaluate_holdout.py --tag h56_ms300_900 --n-dots 40000 --min-sep 3 \
  --arms random,ridge_only,ridge_x_dim,ridge_x_agree,tensor_full \
  --out evidence/holdout_h56_ms300_900_n40000.json

.venv/bin/python scripts/submission_writer.py --tag h56_ms300_900 --n-dots 40000 \
  --min-sep 3 --seed 5609 \
  --name h56-multiscale-tensor-persistence-40000dots-20261009T162812Z
.venv/bin/python scripts/validate_submission.py docs/downloads/*h56*-zeros.tif
# Exit code 2 from verify_unique.py is intentional for the current DUPLICATE-STOP.
.venv/bin/python scripts/verify_unique.py \
  docs/downloads/h56-multiscale-tensor-persistence-40000dots-20261009T162812Z-zeros.tif \
  --surface data/cache/lane_h56_ms300_900.npz \
  --out evidence/uniqueness_h56_strict.json
```

Use `scripts/evaluate_holdout.py` and `scripts/submission_writer.py` as the
canonical evaluator/writer. Do not create a private scoring fork. `data/cache/`
is ignored because the feature stack is large; the committed JSON evidence records
its configuration and measured outputs.

## Current evidence ledger

All score values below are **HOLDOUT-DTI** from `src/gems55/dti55.py`
(alpha=0.2, beta=0.8, 300 m triangular kernel), using 5 buffered whole-segment
folds and 60,988 withheld positives; each score has its fold-resample 95% CI
shown. They are not leaderboard scores.

- Official grid measured from the placed payload: 3292 columns × 3730 rows,
  EPSG:32611, 100 m, transform `(100, 0, 243350, 0, -100, 4508550)`, 5,167,373
  valid footprint pixels and 60,988 mapped catalogue pixels.
- One-scale baseline arms, 40,000 dots, 5 whole-segment folds:
  - random control: **0.01547**, CI [0.01449, 0.01665];
  - ridge-only: **0.01779**, CI [0.01672, 0.01895];
  - ridge × dimensionality: **0.01763**, CI [0.01740, 0.01786];
  - ridge × strike agreement: **0.01852**, CI [0.01782, 0.01940];
  - full one-scale tensor surface: **0.01774**, CI [0.01710, 0.01837].
- H56 multi-scale candidate (300 m and 900 m Gaussian sigma, geometric
  persistence): **0.01728**, CI [0.01613, 0.01847]. It beats its matched random
  control (**0.01440**, CI [0.01373, 0.01537]) but does not beat the preregistered
  one-scale best.
- Leakage canary: maximum single-feature AUC **0.5522**, below the 0.90 canary
  threshold; this is a holdout diagnostic, not a score.
- Auxiliary strike diagnostic: 273 withheld catalogue segments, 26.0% within 20°
  versus 22.4% for sampled random ridges; mean angular difference CI
  [−12.50°, −7.21°]. It is a catalogue-proxy diagnostic and is not used to promote
  the raster because ridge orientation and tensor strike can be geometrically
  coupled.
- Registry: 56 same-grid rasters scanned. Maximum absolute continuous-surface
  Spearman correlation **0.0223** (below 0.90), but the literal final-dot rule
  fails: maximum overlap 1.000 and two rows over 0.70. Verdict:
  **DUPLICATE-STOP**.

The full run card, evidence JSON, validator output, and irregularity ledger are
linked from the [executive summary](docs/index.html).

## Standing owner brief — keep this in force

> **Highest urgency:** generate a unique TIF submission for the competition. Do
> not copy a previous submission except for learning and education. Make it obvious
> whether the generated TIF is OK to download and submit.
>
> **Assigned lane:** separate strike-extended structures from compact bodies using
> potential-field tensor dimensionality. Gradient ridges cannot distinguish a long
> fault/contact from an intrusion/vent because both produce ridges. Pedersen and
> Rasmussen (1990) introduced the potential-field gradient-tensor dimensionality
> information; eigenvalues describe source geometry and eigenvectors carry strike
> for quasi-2-D sources. Beiki and Pedersen (2010) developed eigenvector methods,
> and Beiki, Pedersen and Nazi (2011) described the aeromagnetic pseudogravity
> extension. Compute horizontal and vertical derivatives of RTP magnetic and
> isostatic-gravity grids by FFT. Low-pass before differentiation and process each
> acquisition block separately when verified block metadata are available. Form
> the tensor and map dimensionality and strike. Keep ridges that are near-2-D and
> whose eigenvector strike agrees with their own orientation; down-weight compact
> 3-D signatures. Test withheld fault strikes against random ridges. Mask
> acquisition-line striping. Output a standard validated GeoTIFF and uniqueness
> check it against every earlier raster.
>
> **Parallel-run protocol:**
>
> 1. Stay inside this single tensor-dimensionality lane. If continuous-surface
>   rank correlation with a registry raster exceeds 0.90, or more than 70% of
>   final dots fall within 3 px of one registry raster, log a duplicate and stop.
>   Run the surface check before placement and the dot check after placement.
> 2. Reuse the canonical cached stack, `evaluate_holdout.py`, and
>   `submission_writer.py`. Hold out whole fault segments with a buffer; derive
>   catalogue-based controls only from visible faults; mask visible faults
>   pixel-exactly; pool DTI with alpha 0.2, beta 0.8, and 300 m triangular kernel.
> 3. Label every number HOLDOUT-DTI with evaluator version, withheld-positive count,
>   and 95% CI, or ORGANIZER-CONFIRMED only when copied from a submission-page
>   receipt. Never write a projection as a score.
> 4. Run each feature alone as a leakage canary. AUC > 0.90 is leakage until
>   proven otherwise.
> 5. End with one JSON run card containing hypothesis, mechanism, named non-fault
>   mimic, holdout DTI/CI, registry correlation/overlap, raster SHA-256, validator
>   output, submission name/note, and verdict promote/negative.
> 6. Stop after three experiments or two hours. Do not pick submissions; promotion
>   to a real slot is separate and subject to the weekly cap.
>
> **Owner operating requirements:** generate 3–5 new hypotheses before coding;
> name layers, physical signature, omitted-fault rationale, difference from this
> repo, and implementation cost; use a free official source and verify it before
> relying on new external data; research line by line with trusted sources; flag
> irregularities; provide an obvious executive submission page; and apply the
> values **Maximize P(Win)** and **Own the Outcome**.

## Verified source register

- [DrivenData problem description, metric, data, and submission format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [DrivenData data tab](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) — login required; no organizer-authenticated download is claimed here.
- [DrivenData official rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf)
- [Official reference solution](https://github.com/drivendataorg/gems-prize-reference-solution)
- [USGS GeoDAWN overview](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)
- [USGS ScienceBase GeoDAWN data release, DOI 10.5066/P93LGLVQ](https://www.sciencebase.gov/catalog/item/657e1d85d34e23d3533209f7)
- [Pedersen & Rasmussen (1990), DOI 10.1190/1.1442807](https://doi.org/10.1190/1.1442807)
- [Beiki & Pedersen (2010), DOI 10.1190/1.3484098](https://doi.org/10.1190/1.3484098)
- [Beiki, Pedersen & Nazi (2011), DOI 10.1190/1.3555343](https://doi.org/10.1190/1.3555343)
- [Karimi & Kletetschka (2024), open-access dimensionality discussion](https://pmc.ncbi.nlm.nih.gov/articles/PMC11333590/)

## Limitations and next session

1. The dated official leaderboard snapshot is a public-page observation, not a
   submission-page receipt and not a file mapping. It shows 0.3774 at rank 1,
   0.3195 at rank 7, and 0.2778 at rank 16; H33-to-row attribution is unresolved.
2. The official competition feature stack, labels, sample template, cached tensor
   surface, and registry rasters are **absent from this checkout**. The TIF can be
   inspected by bytes, but exact template/label checks, holdout reruns, and strict
   registry rescans are blocked. Do not claim this review regenerated a new
   scientifically supported candidate.
3. Historical payload hashes were pinned to a sibling GitHub bridge manifest, not
   independently authenticated against the DrivenData download because that data
   tab is login-gated here. Do not redistribute those payloads.
4. The official USGS release documents four acquisition blocks and flight paths,
   but exact block polygons are not aligned to the competition grid in this
   checkout. Current FFT results do not demonstrate true per-block processing.
5. The direct RTP tensor is a documented proxy for the requested pseudogravity
   extension, not proof that a magnetization-direction transform has been applied.
6. The strict overlap gate is dominated by dense prior rasters (the spacing-5
   lattice is within 3 px of every candidate dot). This is a protocol irregularity,
   not permission to silently relax its literal stop rule.
7. The historical anchor proxy-DTI analysis was mathematically invalid and is
   retracted under IR-55-034. Corrected analysis requires authorized data and a
   valid holdout; no extra experiment was run in this review.

## Project values

**Maximize P(Win):** do not spend a slot on H56. The corrected evaluator shows that
scale persistence is not yet better than the one-scale comparator, and the strict
registry gate stops the artifact.

**Own the Outcome:** publish the negative evidence, the exact SHA, the validation
failure mode, the official links, and the next blockers instead of converting a
projection or a format check into a leaderboard claim.
