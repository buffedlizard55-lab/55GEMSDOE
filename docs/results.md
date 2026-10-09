# Results — tensor-dimensionality lane (2026-10-09)

**Every number on this page is HOLDOUT-DTI.** None is an organiser-confirmed score. No candidate TIFF is published, and no download is allowed (see [status](status.json) and [run card](run-card.json)).

## Holdout (evaluator `gems.metric v1`)

- DTI with α = 0.2, β = 0.8, triangular kernel R = 300 m (3 px). The formula was checked against the worked example on the [problem description page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/).
- Holdout: four quadrant folds (NW, NE, SW, SE) of catalogue fault segments (3,199 segments). Each fold's segments are withheld. Visible faults are masked pixel-exactly.
- Withheld positives: **60,594 px**.
- 95% CI: block bootstrap, 1,000 reps, 10 km blocks.

| Experiment | What it is | HOLDOUT-DTI | 95% CI | TP_w | FP_w | FN_w |
|---|---|---|---|---|---|---|
| E1 | Ridge baseline (RTP gradient ridges, flight-line rows masked) | **0.0578** | 0.0499 – 0.0652 | 3,794.0 | 82,001.6 | 56,800.0 |
| E2 | E1 × (1 − magnetic dimensionality index) | 0.0463 | 0.0398 – 0.0523 | 2,816.3 | 59,038.8 | 57,777.7 |
| E3 | E2 × (1 − mean of magnetic and gravity indices) × strike-agreement gate (lane method) | 0.0444 | 0.0383 – 0.0502 | 2,662.9 | 54,759.9 | 57,931.1 |

Experiment budget: 3 of 3 used.

## Leakage canary (each feature alone, AUC on ridge pixels)

Ridge pixels: n_pos = 23,530, n_neg = 161,645 (from `docs/results/tensor_lane_results.json`). Threshold for leakage: AUC > 0.90.

| Feature | AUC | Flag |
|---|---|---|
| Gradient magnitude | 0.5179 | no |
| − dimensionality (magnetic) | 0.5183 | no |
| − dimensionality (gravity) | 0.4803 | no |
| Strike agreement | 0.5066 | no |
| E1 score | 0.5182 | no |
| E3 score | 0.5184 | no |

No leakage is detected. The features also carry little signal (AUC ≈ 0.5).

## Strike prediction test

- Withheld fault strike matches the field's tensor strike: **43.2%** (N = 910 segments).
- Random ridge orientation matches the field's tensor strike: **87.6%** (N = 133,448 px).
- One-sided Fisher p = 1.0. The test **failed**. Its design is not a fair comparison (irregularity IR-55-017).

## Uniqueness (registry scan)

- Same-grid GEMSDOE rasters compared: 630 of 632 (63 repos).
- Max Spearman (E1, footprint): 0.165, below the 0.90 threshold.
- Overlap rule (≥70% of dots within 3 px of one registry raster): flagged 70 of 630 for E1 and for E3. The rule is saturated by dense registry rasters and is not chance-corrected (IR-55-020).
- Result files: [E1](results/registry_check_tensor_lane_E1.json), [E3](results/registry_check_E3.json).

## Local candidate files (not published)

Both files were checked for format with rasterio against `data/sample_submission.tif`. Each is one float32 band in EPSG:32611, with the template's shape, transform and 100 m resolution. The finite pixels number 5,167,373 (the footprint), values lie in [0, 1], and no infinities are present. These are format checks only; they are not organiser validation. The files are held locally only (gitignored `outputs/`), because the gates did not pass.

- E1 `outputs/tensor-lane-candidate_E1_ridge_baseline.tif`, sha256 `038bfdcd081e3054fd4650a51ee5d37df83d8f3ec003dfc151ad55ae118bf424`
- E3 `outputs/tensor-lane-candidate_E3_full_tensor_lane.tif`, sha256 `25f2ccf40c096efe9b25bed9ab8c28151d48123a7ba4527c85ac490c3dc18d80`

## Reproduce

```bash
python scripts/prepare_data.py                 # checks the sha256 pins in data/
python scripts/run_tensor_lane.py --out outputs/tensor-lane-candidate.tif --tag tensor-lane-v1 --results docs/results/tensor_lane_results.json
python scripts/registry_check.py outputs/tensor-lane-candidate_E1_ridge_baseline.tif <registry_dir> docs/results/registry_check_tensor_lane_E1.json
python scripts/make_run_card.py
```
