# 55GEMSDOE — tensor-dimensionality lane, DOE GEMS Prize Challenge

DrivenData competition **306** · *The Geologic Enhanced Mapping System (GEMS) Prize
Challenge* · GeoDAWN, northwestern Great Basin, Nevada.

**Read this file first, every session.** It carries the standing brief, the current
state, and the download.

---

## 1. Download the submission

| | |
|---|---|
| **File to upload** | `docs/downloads/h55-tensor2d-strikegate-40000dots-20261009T052235Z-zeros.tif` |
| **Zip** | `docs/downloads/h55-tensor2d-strikegate-40000dots-20261009T052235Z-zeros.zip` |
| **NaN-outside twin** (reference only, do **not** upload) | `…-nan.tif` |
| **Portal “Note”** (86 / 140 chars) | `tensor-dim lane: FFT grad-tensor RTP-mag+iso-grav, 2-D/strike-gated ridges, 40000 dots` |
| **SHA-256 (.tif)** | `b7c7225d1b35559d27a7800e40ac75a48d9a15ef79f169de0b5b64fc1bd9d368` |

### Is it OK to download and submit this file?

| Question | Answer |
|---|---|
| Meets the official format contract? | **YES** — 12/12 checks, re-read from the written bytes |
| Will it trip `Predicted values must be in range [0, 1]`? | **NO** — min 0.0, max 1.0, **0 NaN** across all 12,279,160 cells |
| Unique against every earlier scored raster? | **YES** — max abs Spearman **0.0043** vs 56 rasters (threshold 0.90); max Jaccard 0.0080; density-matched 3-px overlap 0.6694 (threshold 0.70) |
| Expected to beat the current best score? | **NO — negative result.** Holdout DTI **0.0667** vs **0.0757** for a uniform-random control at the same mass, and below it in 4/4 folds |

**The file is format-safe and legal to upload. It is scientifically a negative
result.** Upload it only if you want the negative result on the board. Do not
spend a weekly slot expecting it to beat 0.3195.

Site: `docs/` (GitHub Pages) — the executive summary and the download button are
the first thing on `docs/index.html`.

---

## 2. Current state (measured, not asserted)

* **Grid contract, measured from the organiser template:** 3292 × 3730 (w × h),
  EPSG:32611, 100 m, transform `(100, 0, 243350, 0, −100, 4508550)`,
  5,167,373 valid px, 7,111,787 NaN, 60,988 mapped catalogue px.
* **Tests:** `16 passed`. They cover exactness of the DTI evaluator against a
  brute-force transcription, the official worked example ratio, the FFT gradient
  tensor against an analytic harmonic solution, the closed-form eigen-decomposition
  against `numpy.linalg.eigh`, both dimensionality endpoints, the survey-line
  degeneracy, and the grid contract.
* **Confirmed:** the tensor **strike** prediction. Withheld faults' strikes agree
  with the tensor strike more often than random ridges' do — 0.302 vs 0.222 within
  20° (+8.0 pp); mean |Δθ| 38.03° vs 45.05°, 95 % CI of the difference
  [−9.19, −4.68]° (excludes 0). 45.0° is the exact null mean for independent
  undirected azimuths, so the null is calibrated.
* **Refuted:** the tensor surface as a **locator**. It loses to uniform placement
  at every dot budget and every NMS separation tested.
* **Metric algebra, verified numerically:** `TP_w + FN_w = |G|` identically, so
  **`DTI = TP_w / (0.2·N + 0.8·|G|)`**. Coverage dominates precision: a false
  positive costs 0.2, an uncovered truth pixel costs 0.8. This is the single most
  transferable finding in the repo.

---

## 3. Reproduce

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
bash scripts/download_competition_data.sh   # needs `gh` auth; or log in at DrivenData
.venv/bin/python scripts/prepare_and_cache.py  # verifies data/, builds data/cache/lane_v1.npz
.venv/bin/python scripts/prepare_data.py        # concurrent session's sha256 pin check
.venv/bin/python -m pytest -q
.venv/bin/python scripts/diagnose_striping.py
.venv/bin/python scripts/evaluate_holdout.py --tag v1 --n-dots 40000
.venv/bin/python scripts/exp2_placement.py 40000 v1
.venv/bin/python scripts/exp3_segment_holdout.py v1 24000,40000   # leakage-flagged
.venv/bin/python scripts/exp4_arrangement.py v1 40000
.venv/bin/python scripts/build_registry.py
.venv/bin/python scripts/submission_writer.py --tag v1 --n-dots 40000 --min-sep 3.0
.venv/bin/python scripts/validate_submission.py docs/downloads/*.tif
.venv/bin/python scripts/verify_unique.py docs/downloads/<the -zeros file>.tif
.venv/bin/python scripts/make_runcard.py
.venv/bin/python scripts/build_site.py
```

`data/` is gitignored (the feature grid alone is 419 MB). The registry rasters
under `registry/rasters/` are prior submissions used **only** as a uniqueness
control — no pixel of any of them enters our deliverable.

---

## 4. Standing brief (the prompt this project exists to serve)

> THE FOLLOWING IS THE HIGHEST URGENCY AND MUST BE FOLLOWED!
>
> MUST GENERATE A UNIQUE TIF SUBMISSION FOR THE COMPETITION. DO NOT COPY A
> PREVIOUS SUBMISSION UNLESS IT'S FOR LEARNING AND EDUCATION. BUT WE MUST
> GENERATE A UNIQUE TIF SUBMISSION. IT MUST BE OBVIOUS WHETHER IT IS OK TO
> DOWNLOAD AND SUBMIT THE GENERATED TIF SUBMISSION.
>
> There should be an easy to download submission tif file as described by the
> prompt. Read the entire prompt.
>
> Tensor-dimensionality lane: separate strike-extended structures from compact
> bodies. Gradient-ridge detectors cannot tell a long fault or contact from an
> intrusion or vent, and both produce ridges. Pedersen and Rasmussen (Geophysics,
> 1990) showed the potential-field gradient tensor carries this information. A
> dimensionality index built from its eigenvalues is zero for strictly
> two-dimensional (strike-extended) sources, and the eigenvectors carry strike for
> 2-D sources. Beiki and Pedersen (Geophysics, 2010) built source-location methods
> on it, and the analysis has been extended to aeromagnetic data through the
> pseudogravity transform. Compute horizontal and vertical derivatives of the RTP
> magnetic and isostatic gravity grids by FFT. Derivative noise is amplified, so
> low-pass first and work within each acquisition block separately. Form the
> tensor and map local dimensionality and strike. Keep gradient ridges that are
> near-2-D and whose eigenvector strike agrees with the ridge's own orientation,
> and down-weight compact 3-D signatures. Test it as a prediction: withheld
> faults' strikes should match the field's strike more often than random ridges'
> do. East–west flight-line striping is one-dimensional by construction, so mask
> it. Output the standard validated GeoTIFF, uniqueness-checked against every
> earlier raster.
>
> **PARALLEL-RUN PROTOCOL — read first.** This session is one of several running
> from this same prompt.
>
> 1. **LANE.** Your lane is the single method paragraph below. Stay inside it. If
>    your raster's rank-correlation with any registry raster exceeds [0.90], or
>    more than [70%] of your dots fall within 3 px of one registry raster's dots,
>    you have drifted into another lane: log it as a duplicate and stop. Check
>    this on the surface before placement AND on the final dots.
> 2. **REUSE, DON'T REBUILD.** Use the template's cached feature stack,
>    `evaluate_holdout.py` and `submission_writer.py`. Holdout = hide-and-recover:
>    withhold whole fault segments with a buffer, derive every catalogue-based
>    feature only from the visible faults, mask visible faults pixel-exactly, score
>    pooled DTI (alpha 0.2, beta 0.8, 300 m triangular kernel). If a shared tool is
>    wrong, fix it once in the template and report it; never keep a private fork.
> 3. **LABEL EVERY NUMBER** as HOLDOUT-DTI (evaluator version, number of withheld
>    positives, 95% CI) or ORGANIZER-CONFIRMED (copied from a submission-page
>    receipt). A projection is never written as a score.
> 4. **LEAKAGE CANARY.** Test each feature alone on the holdout before trusting any
>    result. AUC above [0.90] means leakage until proven otherwise.
> 5. **RUN CARD.** End with one JSON card: hypothesis; mechanism; the named
>    non-fault process that could mimic it; holdout DTI + CI; correlation/overlap
>    vs registry; raster sha256; validator output (no NaN inside the footprint,
>    values in [0,1], CRS/shape/transform match); submission name + note of at most
>    140 characters; verdict promote / negative. Negative results are deliverables.
> 6. **BUDGET.** Stop after [3] experiments or [2] hours. Do not pick submissions:
>    promotion to a real slot is a separate selector step, within the weekly cap
>    shown on the submission page.

Operational addenda from the owner, in force for every session:

* Work line by line, verifying from official verified trusted sources, and provide
  links for manual review. No manual input; no hallucinations. Flag irregularities.
* Generate 3–5 candidate geological hypotheses before implementing, each naming
  the layers, the physical signature, why it should catch a fault *missing* from
  the catalogue, and how it differs from what already exists. Rank by expected DTI
  improvement against implementation cost. **No holdout win, no submission slot.**
* If a candidate needs new external data, name the specific free official source
  and confirm it is obtainable before proposing it as viable.
* Put this brief in the README and re-read it every session.
* The site must make the download obvious on arrival, and must carry an executive
  summary subpage explaining exactly how to enter a submission.
* Core values: **Maximize P(Win)** and **Own the Outcome** — own results end to
  end, treat failure and success as signals, stay accountable for the final
  outcome.

---

## 5. Core values applied here

**Own the Outcome.** The lane's locator hypothesis failed. That was reported
instead of buried, the metric algebra that explains *why* was derived and verified,
and a format-valid, unique, downloadable file was still delivered with its verdict
printed next to the download button. The brief's own words are followed: *negative
results are deliverables.*

**Maximize P(Win).** The highest-leverage thing this session produced is not a
raster, it is the identity `DTI = TP_w/(0.2N + 0.8|G|)`. Every future lane should
be evaluated *inside* a coverage-optimal emitter, not as a standalone ridge map,
because on this evidence a standalone ridge map is beaten by uniform placement.

---

## 6. Verified sources

| Source | Used for | Link |
|---|---|---|
| Official problem description | Task, 19 layers, DTI definition (α=0.2, β=0.8, 300 m triangular kernel), submission contract | <https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/> |
| Competition landing page | Structure, rules entry point | <https://www.drivendata.org/competitions/306/competition-doe-gems/> |
| Organiser reference solution | Band conventions, `X < −1e38 → NaN` sentinel, Tversky loss parameters. It does **not** implement the scoring evaluator | <https://github.com/drivendataorg/gems-prize-reference-solution> |
| Pedersen & Rasmussen (1990), *Geophysics* 55(12) 1558–1566 | Gradient tensor; dimensionality concept | <https://doi.org/10.1190/1.1442807> |
| Beiki & Pedersen (2010), *Geophysics* 75(6) I37–I49 | Eigenvector analysis; strike of quasi-2-D bodies | <https://doi.org/10.1190/1.3484098> |
| Karimi & Kletetschka (2024), *Sci. Rep.* 14:2440 (open access) | Invariant form of the dimensionality indicator and its endpoints | <https://doi.org/10.1038/s41598-024-52843-5> · <https://pmc.ncbi.nlm.nih.gov/articles/PMC11333590/> |
| Beiki et al. (2011), ASEG Extended Abstracts | Pseudo-gravity gradient tensor from gridded magnetic anomalies | <https://doi.org/10.1071/ASEG2012ab057> |
| USGS GeoDAWN | Provenance of the magnetic and radiometric surveys | <https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and> · <https://www.sciencebase.gov/catalog/item/657e1d85d34e23d3533209f7> |
| INGENIOUS / GBCGE | Provenance of labels and subsurface layers | <https://gbcge.org/current-projects/ingenious/> |
| EPSG:32611 | Required CRS | <https://epsg.io/32611> |
| Tversky index | The α/β asymmetry the metric uses | <https://en.wikipedia.org/wiki/Tversky_index> |

Data provenance (the DrivenData data page needs a login this environment lacks):
the official rasters were recovered from sibling repositories under the same
account and verified by content address — `sample_submission.tif` blob
`7d865a9921a40ed2ea4c742a6a25b1fa2f357c5a` (1,599,597 B, identical in five
independently built repos), `labels.tif` blob
`4ad3c1f3f19823e40924589bee7e51e44ae3a2e7` (425,830 B), and the 19-band feature
grid reassembled from five parts to 418,912,844 B, opening as float32 EPSG:32611
at 100 m with band descriptions matching the official layer list word for word.

---

## 6b. Concurrent session on the same lane — an independent replication

A second session working the *same* tensor-dimensionality lane on this repository
merged to `main` while this one was running (PR #3, `gems/` package,
`docs/executive-summary.html`). Its run card reached the **same verdict by a
completely separate implementation**:

| | this session (`src/gems55`) | concurrent session (`gems/`) |
|---|---|---|
| Ridge baseline | 0.0499 pooled | 0.0578 [0.0499, 0.0652] |
| + dimensionality | 0.0697 pooled | 0.0463 [0.0398, 0.0523] |
| Full tensor lane | 0.0667 pooled | 0.0444 [0.0383, 0.0502] |
| Leakage canary max AUC | 0.542 | 0.518 |
| Verdict | NEGATIVE | negative |

Neither implementation's tensor gating beats its own ridge baseline, and neither
finds leakage. Two independent code paths agreeing that the lane does not locate
faults is much stronger evidence than either alone, and it is the reason the
verdict here is stated without hedging.

The two sessions also **independently confirmed the input data**. Their
`scripts/prepare_data.py` pins SHA-256 hashes obtained from a sibling-repo
manifest; this session reassembled the same files from five GitHub blobs in a
different repository. The hashes agree exactly:

```
labels.tif                              7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093
sample_submission.tif                   2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc
gems-geodawn-numerical-features.tif     4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5
                                        (= their training_features.tif pin)
```

Their guardrail tests asserted that no TIF may be published, which was correct for
a session that produced no raster but contradicts the owner's standing requirement
for an obvious, downloadable, validated submission. `tests/test_site_status.py` was
therefore fixed **once, in place**: it now requires that any published TIF exists,
that its SHA-256 matches the run card, that it passes the validator, and that the
site states plainly whether it is OK to download and submit. See IR-55-10.

Both sessions' pages are kept. Theirs: `docs/executive-summary.html`,
`docs/results.html`, `docs/data_dictionary.html`, `docs/leaderboard-analysis.html`,
`docs/run-card.json`, `docs/status.json`.

---

## 7. Limitations and what is needed next

1. **No DrivenData credentials and no general network in the build sandbox.** Only
   github.com, api.github.com, codeload.github.com, pypi.org and
   registry.npmjs.org are reachable. Needed: an authenticated download of
   `training_features.tif`, `labels.tif`, `sample_submission.tif`,
   `1m_DEM_links.csv`, and permission to read the submission-page receipts so
   scores can be labelled ORGANIZER-CONFIRMED.
2. **No organiser score for any number in this repo.** Every figure is HOLDOUT-DTI
   or a local measurement. A local holdout does not forecast the hidden score.
3. **The catalogue is only a proxy for the hidden truth.** The private test set is
   *newly identified* faults. Nothing available here can validate discovery of a
   fault that is, by construction, absent from the only truth we hold.
4. **No survey-block vector.** Acquisition-block levelling uses a regular block
   partition as a surrogate. The official alternative is the USGS GeoDAWN survey
   area polygons (ScienceBase item `657e1d85d34e23d3533209f7`), unreachable from
   this sandbox.
5. **3 GB RAM ceiling.** Forces float32 and chunked eigen-decomposition; a larger
   box would allow the 1 m DEM layers, which are the most promising unused input.
6. **Next lanes, in order.** (a) Re-run candidates 3–5 from
   `docs/hypotheses.html` *inside* a coverage-optimal emitter. (b) Build the
   coverage-optimal emitter properly (greedy maximum-expected-credit placement
   keyed on the kernel-convolved remaining-credit field — the version shipped here
   keys on raw credit and is therefore raster-scan degenerate on a flat prior;
   that is a known defect, logged, not hidden). (c) Obtain the 1 m DEM tiles and
   test LiDAR scarp geometry gated by tensor dimensionality.
7. **Irregularities.** Nine are logged in `docs/irregularities.html`, including
   the empty starting repository, the wrong flight-line direction in the lane
   brief, the leakage in the segment-level holdout, the template that is not the
   all-zero raster its caption claims, and the vacuous 3-px uniqueness rule.
