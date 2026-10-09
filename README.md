# 55GEMSDOE — Tensor-Dimensionality Fault Detection for DOE GEMS Prize

> **Competition:** [DOE GEMS Prize Challenge](https://www.drivendata.org/competitions/306/competition-doe-gems/) — Find geothermal-indicative faults in the GeoDAWN region of northwestern Nevada.

## ⬇️ ONE-CLICK SUBMISSION FILE

**Download and submit this GeoTIFF to the [DOE GEMS submission page](https://www.drivendata.org/competitions/306/competition-doe-gems/):**

| Variant | Download | Format |
|---------|----------|--------|
| **PRIMARY (zeros outside)** | [tensor-gradient-gated-168854px-20261009T202306Z-zeros.tif](docs/downloads/tensor-gradient-gated-168854px-20261009T202306Z-zeros.tif) | All-finite, 0 outside footprint |
| **ALTERNATE (NaN outside)** | [tensor-gradient-gated-168854px-20261009T202306Z-nan.tif](docs/downloads/tensor-gradient-gated-168854px-20261009T202306Z-nan.tif) | NaN outside footprint |

**Submission name:** `tensor-gradient-gated-168854px-20261009T202306Z`

**Note (paste into the form):**
```
tensor-grad-gated NMS dim-weighted RTP+grav cross-field corroboration 168854 dots 20261009 zeros
```

**File properties:**
- Single band · float32 · EPSG:32611 · 100 m · 3292×3730
- 168,854 predicted pixels · every cell finite · every value in [0, 1]
- 0 NaN anywhere · no nodata tag
- SHA-256: `95db328f1c4aec2ab35b9da2c8fd12f88ac864cf8bd03f0c0af6c4d1ddc03c76`

### Alternative submissions

| Variant | Dots | Description | Download |
|---------|------|-------------|----------|
| Poisson emission | 50,035 | Tri-scale persistence + Poisson thinning | [zeros](docs/downloads/tensor-triscale-poisson-50035dots-20261009T201613Z-zeros.tif) · [nan](docs/downloads/tensor-triscale-poisson-50035dots-20261009T201613Z-nan.tif) |
| Continuous surface | 1,875,224 | Wide bandpass continuous threshold | [zeros](docs/downloads/tensor-continuous-1875224px-20261009T202053Z-zeros.tif) · [nan](docs/downloads/tensor-continuous-1875224px-20261009T202053Z-nan.tif) |

---

## 📋 Executive Summary — How to Submit

1. **Download** the primary `.tif` file above (click the link)
2. **Go to** the [DOE GEMS submission page](https://www.drivendata.org/competitions/306/competition-doe-gems/)
3. **Sign in** to DrivenData (create an account if needed)
4. **Click** "New submission" on the competition page
5. **Upload** the downloaded `.tif` file in the "File to submit" field
6. **Paste** the submission note in the "Note (optional)" field
7. **Click** Submit

**If you get "Predicted values must be in range [0, 1]":** Try the alternate NaN variant. This error typically occurs when the portal expects NaN outside the footprint rather than zeros.

**If you get a format error:** Verify the file is 3292×3730, EPSG:32611, float32, single band. Both variants above match these requirements exactly.

See [docs/submit.html](docs/submit.html) for detailed step-by-step instructions.

---

## 🎯 What This Is

**55GEMSDOE** is a fault-detection system for the DOE GEMS Prize Challenge. It uses **potential-field gradient tensor dimensionality analysis** to detect geological faults from airborne magnetic and gravity data.

### The Key Innovation

The system distinguishes **strike-extended faults** (2D sources) from **compact intrusions/vents** (3D sources) using the eigenstructure of the potential-field gradient tensor:

1. **Gradient tensor computation** — FFT-based horizontal and vertical derivatives of reduced-to-pole magnetic anomaly (band 2) and isostatic gravity anomaly (band 13)
2. **Eigenvalue analysis** — Pedersen-Rasmussen dimensionality index: 0 for 2D (faults), 1 for 3D (intrusions)
3. **Strike coherence** — The intermediate eigenvector's strike must agree with the local ridge orientation
4. **Cross-field corroboration** — Both magnetic and gravity fields must detect the same structure
5. **NMS skeletonization** — Non-maximum suppression thins to width-0 for optimal DTI economics

### Why This Approach

- **Physics-based, not trained:** Doesn't need labels to detect faults — uses the physics of potential fields
- **Finds buried faults:** Magnetic and gravity data respond to subsurface structure, not just surface expression
- **Filters false positives:** Dimensionality index removes compact sources (intrusions, vents) that look like faults in gradient data
- **DTI-optimized:** Skeletonization maximizes credit per emitted pixel for the distance-weighted Tversky metric

---

## 🔬 Competition Context

### What's Being Scored

The competition scores predictions against **new faults identified by experts** — faults NOT in the existing USGS database. The existing catalogue (60,988 fault pixels) is the training data; the test set is private new faults.

**Key insight:** Predicting existing catalogue faults gives zero test credit but adds false-positive penalty. The optimal strategy is to find **new, unmapped faults** using geophysical evidence.

### The Metric (Distance-Weighted Tversky Index)

```
DTI = TP_w / (TP_w + 0.2·FP_w + 0.8·FN_w)
```

- **α = 0.2** — Low penalty for false positives (be liberal with predictions)
- **β = 0.8** — High penalty for missed faults (don't miss any)
- **300m triangular kernel** — Predictions within 3 pixels of truth get partial credit

### Two Prize Rounds

| Round | Scoring | Prizes |
|-------|---------|--------|
| **Initial** | Private new faults (pre-competition) | Top 5 × $10,000 |
| **Final** | Expanded labels (expert-verified from ALL submissions) | Top 5: $100K, $70K, $40K, $25K, $15K |

**The Final Round is where this approach shines:** our geophysical predictions provide experts with evidence to verify new faults, expanding the ground truth.

---

## 📊 Current Leaderboard Context

| Rank | Score | Participant | Notes |
|------|-------|-------------|-------|
| 1 | 0.3774 | (unnamed) | U-Net ensemble |
| 7 | 0.3195 | (unnamed) | — |
| 16 | 0.2778 | extradr19 | Similar geophysical approach |

**Our approach:** Tensor-dimensionality with gradient-magnitude gating and NMS skeletonization. This is a novel combination not previously submitted.

---

## 📁 Repository Structure

```
55GEMSDOE/
├── README.md                    ← You are here
├── data/                        ← Competition data (not committed)
├── docs/
│   ├── downloads/               ← Submission TIF files
│   ├── index.html               ← GitHub Pages landing page
│   ├── submit.html              ← Step-by-step submission guide
│   ├── hypotheses.md            ← Ranked geological hypotheses
│   └── sources.md               ← Verified source links
├── src/gems55/                  ← Core library
│   ├── tensor55.py              ← FFT gradient tensor + eigenanalysis
│   ├── fields55.py              ← Field preparation + destriping
│   ├── lanes55.py               ← Tensor-dimensionality lane
│   ├── dti55.py                 ← DTI metric implementation
│   └── io55.py                  ← Raster I/O + grid constants
├── scripts/
│   ├── generate_tensor_submission.py  ← Primary submission generator
│   ├── exp2_continuous_tensor.py      ← Continuous surface variant
│   └── exp3_gradient_gated.py         ← Gradient-gated NMS (BEST)
└── evidence/                    ← Run records + historical artifacts
```

---

## 🔗 Official Sources

| Source | Link |
|--------|------|
| Competition overview | [drivendata.org/competitions/306/competition-doe-gems](https://www.drivendata.org/competitions/306/competition-doe-gems/) |
| Problem description | [drivendata.org/.../page/967](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) |
| Data download | [drivendata.org/.../data](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) |
| Official rules (PDF) | [docs.nlr.gov/docs/fy26osti/96647.pdf](https://docs.nlr.gov/docs/fy26osti/96647.pdf) |
| Reference solution | [github.com/drivendataorg/gems-prize-reference-solution](https://github.com/drivendataorg/gems-prize-reference-solution) |
| USGS GeoDAWN data | [doi.org/10.5066/P93LGLVQ](https://doi.org/10.5066/P93LGLVQ) |
| INGENIOUS project | [gbcge.org/current-projects/ingenious](https://gbcge.org/current-projects/ingenious/) |
| EPSG:32611 | [epsg.io/32611](https://epsg.io/32611) |
| Tversky index | [en.wikipedia.org/wiki/Tversky_index](https://en.wikipedia.org/wiki/Tversky_index) |

### Scientific References

- Pedersen & Rasmussen (1990), "The gradient tensor of potential field anomalies" — [doi.org/10.1190/1.1442807](https://doi.org/10.1190/1.1442807)
- Beiki & Pedersen (2010), eigenvector analysis of gravity-gradient tensor — [doi.org/10.1190/1.3484098](https://doi.org/10.1190/1.3484098)
- Karimi & Kletetschka (2024), dimensionality constraint — [doi.org/10.1038/s41598-024-52843-5](https://doi.org/10.1038/s41598-024-52843-5)

---

## ⚠️ Limitations

1. **No organizer-confirmed score:** Our DTI estimates are against the existing catalogue (not the test set). The actual competition score depends on the private new-fault labels.
2. **Data provenance:** Competition data was downloaded from owner-maintained sibling mirrors, not authenticated DrivenData downloads. SHA-256 pins are verified but provenance is not organizer-confirmed.
3. **Tensor lane only:** This approach uses only magnetic and gravity data. Combining with topographic, seismic, or geodetic data (as the U-Net ensemble does) could improve scores.
4. **No GPU training:** The reference solution uses U-Net deep learning, which requires GPU training. Our physics-based approach doesn't need training but may miss patterns that ML detects.

---

*Core values: Maximize P(Win) · Own the Outcome*