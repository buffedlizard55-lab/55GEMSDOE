# 55GEMSDOE — tensor-dimensionality lane

**Read this README first at the start of every work session.** The current source of
truth is [`docs/run-card.json`](docs/run-card.json), [`docs/status.json`](docs/status.json),
and the evidence files linked below. Every model-performance number must be labelled
**HOLDOUT-DTI** (evaluator, withheld-positive count, and 95% CI) or
**ORGANIZER-CONFIRMED** (copied from a submission-page receipt). This checkout has no
organizer-confirmed score or receipt.

## Executive status — audit-only; duplicate-stop and negative

**Download for audit/review: YES. Submit to DrivenData: NO.** H57 is a newly emitted
tensor-lane raster, not a copy of an earlier submission. The NaN-outside primary
passes the current strict local format validator, but the expanded one-sided
uniqueness scan finds a duplicate-stop and the matched-mass scientific holdout is
negative. Do not submit it or spend a weekly slot.

- **Audit-only primary TIF (NaN outside):** [Download `h57-tensor-flank-r15-uneroded-registry56-n200-20261009T200831Z-nan.tif`](docs/downloads/h57-tensor-flank-r15-uneroded-registry56-n200-20261009T200831Z-nan.tif)
- **NaN-outside ZIP:** [Download the single-TIF ZIP](docs/downloads/h57-tensor-flank-r15-uneroded-registry56-n200-20261009T200831Z-nan.zip)
- **Zeros-outside diagnostic only:** [Download `...-zeros.tif` (fails the strict outside-footprint check)](docs/downloads/h57-tensor-flank-r15-uneroded-registry56-n200-20261009T200831Z-zeros.tif)
- **SHA-256 of the primary NaN-outside TIF:** `57dd4ba81c6fe553166cb193f4ae40e6547f4abe5a8fdabeb9154f648d761326`
- **Portal note (104/140 characters):** `H57 tensor-flank: FFT 2-D/strike gate x visible-catalogue flank, 200 dots; all-registry overlap-budgeted`

### Is it OK to download and submit?

| Action | Decision | Evidence |
|---|---|---|
| Download for audit/review | **YES — AUDIT ONLY** | The NaN-outside primary passes 11/11 strict local checks. The zeros-outside diagnostic passes 10/11 and fails exactly the null/NaN outside-footprint rule. The primary is single-band float32, EPSG:32611, 3730×3292, 100 m template geometry; 200 positive dots; no dot on mapped catalogue pixels. |
| Treat as unique against prior rasters | **NO — DUPLICATE-STOP** | Strict scan: all 62 registry rasters plus four local historical candidates (66/66). Surface max |Spearman| is 0.2443 (<0.90), but max one-sided final-dot overlap within 3 Euclidean px is **0.76**, above the literal **0.70** limit. Two PARALLEL16 NaN/zeros variants each trigger the stop and both rows count. Random-control similarity is diagnostic only and does not waive the threshold. |
| Upload to DrivenData / spend a weekly slot | **NO — DO NOT SUBMIT** | **HOLDOUT-DTI** candidate = 0.00012284, 95% CI [0.00011438, 0.00013397], 60,988 withheld positives; below matched random (0.00015080), ridge × strike (0.00027391), and full tensor (0.00030077). Verdict: **NEGATIVE**. The independent uniqueness stop is an additional blocker. |
| Claim an organizer score | **NO** | No submission-page receipt exists in this checkout. User/sibling leaderboard values remain unverified claims, not ORGANIZER-CONFIRMED scores. |

The same decision is displayed at the top of the [executive summary site](docs/index.html).
The [submission steps page](docs/submit.html) is conditional on a future banner saying
`OK TO DOWNLOAD AND SUBMIT`; the current artifact is audit-only. The official problem
page says outside-bounds pixels should be null or NaN, and the strict local validator
requires NaN exactly outside the footprint. A local format pass is not organizer
clearance and does not override either the uniqueness or holdout failure.

## Matched-mass H57-A result (HOLDOUT-DTI)

H57-A combines the cached potential-field tensor score with a 15-pixel
visible-catalogue flank prior. This sensitivity run recomputes the same tensor formula
from cached factors without the normal six-pixel footprint erosion; that makes edge
pixels available but increases FFT boundary-artifact risk.

- Canonical evaluator: `src/gems55/dti55.py`, regression-tested against brute force
  and the official worked example.
- DTI: alpha 0.2, beta 0.8, triangular support radius 300 m (3 px at 100 m).
- Five seeded whole-segment/lattice folds; 3 px buffer; visible catalogue masks
  recomputed and masked pixel-exactly per fold; pooled TP/FP/FN.
- 200 dots total (40 per fold), minimum separation 3 px. Every tested arm returned
  exactly the requested mass.
- Withheld positives: 60,988. The 95% CI is a bootstrap of 4,000 resamples of the
  five fold DTI values; it is not an organizer uncertainty interval.

| Arm | HOLDOUT-DTI | 95% CI | Dots | Interpretation |
|---|---:|---:|---:|---|
| Uniform random, registry-budgeted | 0.00015080 | [0.00007391, 0.00022214] | 200 | matched null |
| Ridge × strike agreement, registry-budgeted | 0.00027391 | [0.00013244, 0.00041048] | 200 | comparator |
| Full tensor lane, registry-budgeted | 0.00030077 | [0.00017780, 0.00042363] | 200 | best same-run arm |
| Tensor × visible-catalogue flank (H57-A) | **0.00012284** | **[0.00011438, 0.00013397]** | 200 | candidate; negative |
| Flank prior alone | 0.00006088 | [0.00004160, 0.00007843] | 200 | diagnostic ablation |

H57-A loses to random and to both tensor comparators. It does not meet the promotion
rule, and no weekly slot should be spent on it. These mapped-catalogue holdout values
are not predictions of organizer leaderboard performance.

The leakage canary tested each feature alone. Maximum AUC was 0.89330 for the
visible-catalogue flank prior, below the 0.90 threshold but close to it. This is a
diagnostic, not a score; it indicates catalogue spatial autocorrelation, not
hidden-label leakage. The auxiliary strike diagnostic tested 13 connected withheld
segments (273 pixel samples) and is not a promotion result. See
[`docs/results.md`](docs/results.md), [`evidence/holdout_h57_unique_n200.json`](evidence/holdout_h57_unique_n200.json),
and [`docs/run-card.json`](docs/run-card.json).

## The claimed 0.2778 H33 score: what can and cannot be concluded

The user-supplied 0.2778 value is **not verified as an organizer score** here. The
GEMSDOE32 audit manifest was fetched read-only from the sibling repository's GitHub
API and records the H33 entry with `receipt: null`; its run note says “projected
0.2747; UNSCORED”. All 24 entries in that manifest have `receipt: null`. This proves
the local sibling manifest does not confirm 0.2778; it does not prove what might be
on a private DrivenData receipt. The values 0.3195, 0.3774, and other sibling scores
in the user brief are likewise unverified without receipts.

The local anchor forensics compare rasters against the mapped catalogue, not the
organizer's hidden new-fault labels. The raster labelled as the 0.2778 candidate
places dots at least 224 m from mapped traces and earns less catalogue-proxy kernel
credit than a same-size uniform random control. A separate sibling raster labelled
as a 0.2600 result places dots next to (but not on) mapped traces and earns more
catalogue-proxy credit. Both leaderboards labels remain unreceipted. Metric algebra
can state what kernel credit a target DTI would require under assumptions; it cannot
establish hidden-fault extent, a private score, or a guarantee that a method beats a
leaderboard entry.

**Answer to “can this score higher than 0.2778?”** This checkout cannot honestly
claim that. The 0.2778 anchor is unreceipted, and the current H57 audit artifact has
a negative, low-mass holdout and fails the strict uniqueness gate. No score projection is written as a result. The
available evidence supports an audit TIF and a negative decision, not a high-scoring
competition upload. Full local forensic details and the manifest citation are in
[`docs/anchor-0.2778.html`](docs/anchor-0.2778.html).

## What was tested; why this TIF is not cleared

H57-A was preregistered within the assigned tensor lane: combine a near-2-D,
strike-concordant tensor score with a flank prior derived from visible mapped faults,
then test whole fault segments withheld from the catalogue. The current strict scan
covers every available reference: 62 registry rasters plus four local historical
candidates (66/66, no incompatible rows). The surface passes (max |Spearman| 0.2443
<0.90), but the final map returns **DUPLICATE-STOP**: 0.76 of the final dots are
within 3 Euclidean pixels of two PARALLEL16 NaN/zeros variants, above the literal
0.70 limit. Both rows count; their random-control overlap is diagnostic only and
cannot waive the rule. No raster is excluded. This H57 map is **not unique** under
the specified gate, and its holdout is also negative.

An earlier exploratory H57 output excluded the lattice and had unmatched arm masses;
it is quarantined at
[`evidence/holdout_h57_exploratory_invalid_excluded-lattice_unmatched-mass.json`](evidence/holdout_h57_exploratory_invalid_excluded-lattice_unmatched-mass.json)
and **must not be used** for promotion. The three-experiment budget is exhausted;
do not run another experiment or rerun the holdout. The strict audit changes only
registry comparison/evidence, not the existing holdout result. See
`docs/irregularities.md` IR-55-048–049.

## Recheck the retained artifact (no experiment or holdout rerun)

The H57 holdout and three-experiment budget are complete. Do not rerun
`evaluate_holdout.py` or generate a new candidate in this session. The commands below
only recheck the existing TIF format and expanded registry comparison. Competition
payloads are not committed; local SHA-pinned mirror files are not claimed as
organizer-authenticated. See `data/SOURCES.md`.

```bash
# Primary NaN-outside file: expected to pass 11/11 strict local checks.
.venv/bin/python scripts/validate_submission.py \
  docs/downloads/h57-tensor-flank-r15-uneroded-registry56-n200-20261009T200831Z-nan.tif

# Diagnostic only: expected to fail exactly the outside-footprint null/NaN check.
.venv/bin/python scripts/validate_submission.py \
  docs/downloads/h57-tensor-flank-r15-uneroded-registry56-n200-20261009T200831Z-zeros.tif

# The uniqueness command returns exit 2 by design: DUPLICATE-STOP (0.76 > 0.70).
.venv/bin/python scripts/verify_unique.py \
  docs/downloads/h57-tensor-flank-r15-uneroded-registry56-n200-20261009T200831Z-nan.tif \
  --surface data/cache/h57_tensor_flank_surface.tif \
  --additional evidence/historical_artifacts/audit-h55-160k/h55-tensor2d-strikegate-160000dots-20261009T164334Z-zeros.tif \
  --additional evidence/historical_artifacts/h55-tensor2d-strikegate-40000dots-20261009T052235Z-zeros.tif \
  --additional evidence/historical_artifacts/h56-multiscale-tensor-persistence-40000dots-20261009T162812Z-zeros.tif \
  --additional evidence/historical_artifacts/gems55-tensor_full-n16000-sep3-20261009T211747Z-nan.tif \
  --out /tmp/uniqueness_h57_review.json
```

`registry/rasters/` is ignored and must contain the complete 62-raster registry for
a fresh local scan. One registry raster has a wrong geotransform and is reprojected
to the official template with nearest-neighbor resampling. The four archived local
rasters above are passed explicitly. The final run card and evidence under `docs/`
and `evidence/` are the current source of truth; rechecking them does not rerun the
holdout or authorize submission.

## Verified sources and research leads

- [DrivenData problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) — describes fault prediction for geothermal-resource mapping; known fault labels are incomplete and the initial test includes expert-identified faults absent from the existing USGS database. It specifies DTI and GeoTIFF format.
- [DrivenData competition rules](https://www.drivendata.org/competitions/306/competition-doe-gems/rules/) and [GEMS rules PDF (September 2026)](https://docs.nlr.gov/docs/fy26osti/96647.pdf) — up to three submissions per week for feedback; one final selection by the deadline for both phases; and a narrative explaining the extent and manner of generative-AI use. Eligibility and final declarations belong to the registered competitor.
- [DrivenData data tab](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) — login required; no organizer-authenticated local download is claimed.
- [Official reference solution](https://github.com/drivendataorg/gems-prize-reference-solution) — U-Net/MC-CV reference baseline, not this lane's evaluator.
- [USGS GeoDAWN overview](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) — four acquisition blocks, E–W flight lines, N–S tie lines, leveling/micro-leveling.
- [USGS ScienceBase GeoDAWN release, DOI 10.5066/P93LGLVQ](https://www.sciencebase.gov/catalog/item/657e1d85d34e23d3533209f7) — public catalog lists flight-path files, outlines and grids; release rights are CC0 1.0. Binary downloads are blocked by this sandbox's host allowlist; see IR-55-044.
- Tensor literature: [Pedersen & Rasmussen (1990)](https://doi.org/10.1190/1.1442807), [Beiki & Pedersen (2010)](https://doi.org/10.1190/1.3484098), [Beiki, Pedersen & Nazi (2011)](https://doi.org/10.1190/1.3555343), and [Karimi & Kletetschka (2024)](https://pmc.ncbi.nlm.nih.gov/articles/PMC11333590/).
- [INGENIOUS project](https://gbcge.org/current-projects/ingenious/) — official project context and links to Great Basin data/publications.
- Full source descriptions are in [`docs/sources.md`](docs/sources.md) and the [sources page](docs/sources.html).

## Limitations and next session

1. **No organizer receipt.** The official leaderboard fetch returned a client-side
   loading state. Do not label user/sibling values ORGANIZER-CONFIRMED without a
   submission-page receipt.
2. **No DrivenData account session.** We cannot inspect current receipts/weekly slot
   counts or authenticate the local sibling-bridge payload hashes against the login-
   gated data download.
3. **H57 is audit-only and fails two gates.** Do not submit this TIF: the matched
   holdout is negative and the expanded strict uniqueness audit returns
   DUPLICATE-STOP (0.76 > 0.70). The three-experiment budget is spent; no fourth
   experiment or holdout rerun is authorized by this session.
4. **Acquisition-block processing is open.** The official public ScienceBase catalog
   lists flight-path files, but their binary downloads are blocked by the sandbox's
   outbound host allowlist. Download/checksum the official data in an allowed
   environment, then align block IDs before claiming per-block FFT.
5. **Pseudogravity is not fully implemented.** Band-2 RTP tensor differentiation is
   a proxy; a complete magnetic-to-pseudogravity transform needs an explicit
   magnetization-direction convention and synthetic tests.
6. **Edge and striping risk.** The H57 un-eroded edge sensitivity is vulnerable to
   FFT boundary artifacts. USGS states E–W flight lines; previous local striping-axis
   diagnostics did not reconcile all axes. Verify against the actual flight paths.
7. **Outside-footprint encoding.** The official problem page says null/NaN outside;
   the strict local validator requires NaN exactly outside the template footprint.
   The current NaN TIF passes 11/11 checks; the zeros diagnostic fails the outside
   check (10/11). Local format validation is not organizer clearance.
8. **Uniqueness remains blocking.** The 200-dot H57 map returns DUPLICATE-STOP at
   0.76 one-sided overlap within 3 px of two PARALLEL16 variants, above the literal
   0.70 rule. Random-control similarity cannot waive that stop. It also has a
   negative HOLDOUT-DTI; it is not a cleared unique submission.
9. **Official final-package obligations.** The September 2026 rules allow up to
   three weekly submissions for feedback but require one final selection by the
   deadline for both prize phases. They also require a narrative explaining the extent and manner of generative-AI use
   if applicable. This project used an AI agent; a future final package must
   disclose that accurately. The registered competitor must handle eligibility and
   final certifications; this agent has not signed or submitted anything.

## Standing owner brief — read every session

> **Urgency:** Generate a unique TIF for the competition without copying a prior
> submission. Make it obvious at the top of the site whether download is permitted
> and whether upload is permitted. Keep a one-click TIF/ZIP and an executive
> summary/submission-steps page. A format-valid file is not automatically cleared.
>
> **Assigned lane:** potential-field tensor dimensionality — separate strike-extended
> structures from compact bodies. Low-pass and FFT-differentiate RTP magnetic and
> isostatic-gravity grids; form the gradient tensor; map dimensionality and
> eigenvector strike; retain near-2-D, strike-concordant ridges; down-weight compact
> signatures; mask flight-line striping; test withheld-fault strikes against random
> ridges; output a standard validated GeoTIFF and check its surface and final dots
> against every earlier raster.
>
> **Parallel-run protocol:** stay in the assigned lane; continuous |Spearman| >0.90
> or >70% of final dots within 3 px of any registry raster means duplicate/stop.
> Reuse the shared cache, canonical evaluator and writer. Hold out whole fault
> segments with a buffer; derive catalogue features only from visible faults; mask
> visible faults pixel-exactly; pool official DTI (alpha 0.2, beta 0.8, 300 m
> triangular kernel). Test every feature alone as a leakage canary; AUC >0.90 is
> leakage until proven otherwise. Label performance values HOLDOUT-DTI with
> evaluator/version, withheld positives and 95% CI, or ORGANIZER-CONFIRMED only from
> a receipt. Each run card contains hypothesis, mechanism, named non-fault mimic,
> holdout value/CI, registry correlation/overlap, TIF SHA, validator output, unique
> name/note ≤140 chars, and promote/negative verdict. Stop at 3 experiments or 2
> hours; weekly-slot promotion is a separate selector step.
>
> **Research/operations:** rank 3–5 hypotheses before coding and name layers,
> physical signature, omitted-fault rationale, difference from the repo and cost.
> Verify free official data sources before relying on them; keep an auditable
> knowledge base with official links; work autonomously; flag irregularities; review
> at least three passes. Focus on geothermal fault/structure discovery, but do not
> claim direct vent detection without evidence.
>
> **Core values:** **Maximize P(Win)** and **Own the Outcome**. Do not trade scientific
> honesty for a submission slot. Publish negative results and fix shared tools once.

**Maximize P(Win):** H57 is not submitted: its matched holdout is negative and its
expanded strict uniqueness audit is DUPLICATE-STOP. The NaN-outside format pass does
not override either failure.

**Own the Outcome:** publish the exact TIF/SHA, the negative holdout, the registry
alignment and evaluator-count fixes, official source links, and the remaining data
and portal limitations rather than turning an unreceipted claim or projection into
an organizer score.
