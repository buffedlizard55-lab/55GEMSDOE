# 55GEMSDOE — tensor-dimensionality review



## Session status — 2026-10-09 (read with the brief above)

**NOT CLEARED — DO NOT DOWNLOAD OR SUBMIT.** No GeoTIFF was generated in this session, and no competition file was downloaded, submitted, or linked.

- Why, gate by gate: [session review §1](docs/session-20261009-review.md).
- Why 0.2778 is not explained, and where its leaderboard rank stands: [session review §2](docs/session-20261009-review.md). The live public leaderboard puts 0.2778 at **rank 17**, not highest, and the H33 mapping is unverified.
- Ranked hypotheses (3–5, with layers, signatures, mimics, and leakage traps): [session review §3](docs/session-20261009-review.md) and [`docs/hypotheses.md`](docs/hypotheses.md).
- Line-by-line source verification with links: [`docs/official-verification-20261009.md`](docs/official-verification-20261009.md).
- Irregularities flagged for review: IR-55-043 to IR-55-047 in [`docs/irregularities.md`](docs/irregularities.md).
- Run card: [`docs/run-card-20261009-session.json`](docs/run-card-20261009-session.json) (verdict: negative).

**To unblock a candidate file, a human account holder must:** download `training_features.tif`, `labels.tif`, `sample_submission.tif`, and `1m_DEM_links.csv` from the [DrivenData data tab](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) (login and rules acceptance required) into `data/` under the canonical names in `src/gems55/io55.py`, then run `python scripts/prepare_data.py`. The sandbox cannot reach that host.

**Core values:** Maximize P(Win) and Own the Outcome. Owning the outcome means withholding a file when the evidence does not clear it.

> **Current status: NOT CLEARED — DO NOT DOWNLOAD OR SUBMIT.** Historical GeoTIFFs and ZIPs remain under `evidence/historical_artifacts/` for audit traceability, outside the published site; none is a valid deliverable or linked for download. Separate historical final-dot reports breach the literal uniqueness limit; no promotion-grade holdout or organizer format clearance exists. No competition data were downloaded, no geological experiment rerun, and no submission slot used in this review.

**Core values:** “Maximize P(Win” and “Own the Outcome.” Owning the outcome means withholding a file when evidence does not clear it, rather than manufacturing a download button or upgrading a projection into a score.

## Read first — standing brief (read every session)

This is the user brief for the project, pasted verbatim from the 2026-10-09 session. Read it at the start of every session before working, and check the work against it. The short version: **produce a unique, validated GeoTIFF that is easy to download and submit, but only when every scientific, leakage, uniqueness, and format gate is honestly cleared; otherwise say plainly that it is NOT CLEARED.** Current status is in the next section.

<details>
<summary>Full standing prompt (verbatim, 2026-10-09)</summary>

Review the repo.

THE FOLLOWING IS THE HIGHEST URGENCY AND MUST BE FOLLOWED!

MUST GENERATE A UNIQUE TIF SUBMISSION FOR THE COMPETITION.  DO NOT COPY A PREVIOUS SUBMISSION UNLESS IT'S FOR LEARNING AND EDUCATION.  BUT WE MUST GENERATE A UNIQUE TIF SUBMISSION.  IT MUST BE OBVIOUS WHETHER IT IS OK TO DOWNLOAD AND SUBMIT THE GENERATED TIF SUBMISSION.

There should be an easy to download submission tif file as described by the prompt.  Read the entire prompt.

Tensor-dimensionality lane: separate strike-extended structures from compact bodies. Gradient-ridge detectors cannot tell a long fault or contact from an intrusion or vent, and both produce ridges. Pedersen and Rasmussen (Geophysics, 1990) showed the potential-field gradient tensor carries this information. A dimensionality index built from its eigenvalues is zero for strictly two-dimensional (strike-extended) sources, and the eigenvectors carry strike for 2-D sources. Beiki and Pedersen (Geophysics, 2010) built source-location methods on it, and the analysis has been extended to aeromagnetic data through the pseudogravity transform. Compute horizontal and vertical derivatives of the RTP magnetic and isostatic gravity grids by FFT. Derivative noise is amplified, so low-pass first and work within each acquisition block separately. Form the tensor and map local dimensionality and strike. Keep gradient ridges that are near-2-D and whose eigenvector strike agrees with the ridge's own orientation, and down-weight compact 3-D signatures. Test it as a prediction: withheld faults' strikes should match the field's strike more often than random ridges' do. East–west flight-line striping is one-dimensional by construction, so mask it. Output the standard validated GeoTIFF, uniqueness-checked against every earlier raster.

PARALLEL-RUN PROTOCOL — read first. This session is one of several running from this same prompt.

1. LANE. Your lane is the single method paragraph below. Stay inside it. If your raster's rank-correlation with any registry raster exceeds [0.90], or more than [70%] of your dots fall within 3 px of one registry raster's dots, you have drifted into another lane: log it as a duplicate and stop. Check this on the surface before placement AND on the final dots.

2. REUSE, DON'T REBUILD. Use the template's cached feature stack, evaluate_[holdout.py](http://holdout.py) and submission_[writer.py](http://writer.py). Holdout = hide-and-recover: withhold whole fault segments with a buffer, derive every catalogue-based feature only from the visible faults, mask visible faults pixel-exactly, score pooled DTI (alpha 0.2, beta 0.8, 300 m triangular kernel). If a shared tool is wrong, fix it once in the template and report it; never keep a private fork.

3. LABEL EVERY NUMBER as HOLDOUT-DTI (evaluator version, number of withheld positives, 95% CI) or ORGANIZER-CONFIRMED (copied from a submission-page receipt). A projection is never written as a score.

4. LEAKAGE CANARY. Test each feature alone on the holdout before trusting any result. AUC above [0.90] means leakage until proven otherwise.

5. RUN CARD. End with one JSON card: hypothesis; mechanism; the named non-fault process that could mimic it; holdout DTI + CI; correlation/overlap vs registry; raster sha256; validator output (no NaN inside the footprint, values in [0,1], CRS/shape/transform match); submission name + note of at most 140 characters; verdict promote / negative. Negative results are deliverables.

6. BUDGET. Stop after [3] experiments or [2] hours. Do not pick submissions: promotion to a real slot is a separate selector step, within the weekly cap shown on the submission page.

The following sites should serve as a starting point for understanding how to generate TIF submissions.  These websites are researched, and tested and have generated TIF submissions.  But we need to generate high scoring submissions.

Here are the results from submissions into the competition, separated by ....:

WE NEED TO STUDY, ANALYZE, AND UNDERSTAND THE HIGHEST SCORE FROM THE GEMDOE SITE WHERE THE SUBMISSION TIF IS DOWNLOADED FROM WHICH IS THE FOLLOWING:

[https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html)

h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros: 0.2778

Why and how did this get the highest score and are we able to generate a submission that scores higher than 0.2778?

Answer the question using Phd level experience, knowledge, and judgement. Then use the answer to generate a unique TIF submission into the competition.  Must be unique submission unlike any within the GEMSDOE sites above.  Verify working line by line no hallucinations.

Current competition leaderboard GEMSDOE high score:

0.3774	

[https://buffedlizard55-lab.github.io/GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE/docs/index.html)

gems-submission-20260925T001403Z-7f00890a: 0.1563

....

[https://buffedlizard55-lab.github.io/6GEMSDOE/](https://buffedlizard55-lab.github.io/6GEMSDOE/)

gems6_hgb88-topk03_33cec71ff0: 0.0286

....

[https://buffedlizard55-lab.github.io/GEMSDOE3/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE3/docs/index.html)

pindrop-v4-nodes-20260925T152420Z-f347b70daa: 0.1193

pindrop-v4-discovery-20260925T152423Z-37f9d5b855: 0.0830

pindrop-v4-ridge-20260925T152422Z-4e03fc9705: 0.1152

....

[https://buffedlizard55-lab.github.io/GEMSDOE2/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE2/docs/index.html)

gemsdoe2-dual-family-union-20260925T160406Z-f68e590f: 0.1560

....

[https://buffedlizard55-lab.github.io/GEMSDOE4/](https://buffedlizard55-lab.github.io/GEMSDOE4/)

gems-submission-20260926T163915Z-237f0063: 0.0343

....

[https://buffedlizard55-lab.github.io/5GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/5GEMSDOE/docs/index.html)

gems-submission-20260926T175114Z-7f00890a: 0.1563

....

[https://buffedlizard55-lab.github.io/7GEMSDOE/](https://buffedlizard55-lab.github.io/7GEMSDOE/)

lidarscarp-ridge-top2pct-36c3a3f341c8: 0.1461

....

[https://buffedlizard55-lab.github.io/8GEMSDOE/](https://buffedlizard55-lab.github.io/8GEMSDOE/)

Hedge-v2_submission: 0.1563

....

[https://buffedlizard55-lab.github.io/GEMSDOE9/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE9/docs/index.html)

2314b599: 0.0107

....

[https://buffedlizard55-lab.github.io/11GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/11GEMSDOE/docs/index.html)

gems-structural-area06-v1: 0.0202

....

[https://buffedlizard55-lab.github.io/12GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/12GEMSDOE/docs/index.html)

r7-nms3-dem10-scarp_0c9199f14e62:0.1294

r7-nms3-dem10-scarp_0c9199f14e62_allfinite:0.1294

....

[https://buffedlizard55-lab.github.io/15GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/15GEMSDOE/docs/index.html)

gems-tso1-20260929T005627Z-conj_alteration_mag: 0.0782

....

[https://buffedlizard55-lab.github.io/14GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/14GEMSDOE/docs/index.html)

GEMS_r5-geom-horse-ensemble_20260929T154852Z_ccbe1de0_site_e96e942f: 0.0020

....

[https://buffedlizard55-lab.github.io/17GEMSDOE/](https://buffedlizard55-lab.github.io/17GEMSDOE/)

17GEMSDOE_F-ensemble-2pct_20260930T050626Z:0.0187

....

[https://buffedlizard55-lab.github.io/18GEMSDOE/](https://buffedlizard55-lab.github.io/18GEMSDOE/)

H19-C_20260930T212401Z_c11e495e: 0.0297

....

[https://buffedlizard55-lab.github.io/19GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/19GEMSDOE/docs/index.html)

h19-4-multiline-corroborated-openness-thermal-pop-20260930-691e4dfa-nan: 0.1894

h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan: 0.1922

....

[https://buffedlizard55-lab.github.io/GEMSDOE10/](https://buffedlizard55-lab.github.io/GEMSDOE10/)

h16-continuation-20260927T065521077735Z-3431b83c7c: 0.0461

h20-dem10-scarp-thin-20260927T155223039488Z-ffc91a1686: 0.0921

H25-ctx-ridge-20260927T232947704150Z-6452ae1d00: 0.1280

h28-dotted-ridge-20260928T020256236880Z-6452ae1d00: 0.1839

....

[https://buffedlizard55-lab.github.io/13GEMSDOE/](https://buffedlizard55-lab.github.io/13GEMSDOE/)

20261001_r13-lattice-s5_v2_nan-outside:0.0904

....

[https://buffedlizard55-lab.github.io/16GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/16GEMSDOE/docs/index.html)

h16-1-topo-geophys-baseline-ridges-20260930-df20f65e-nan: 0.1855

h18-3a-topo-geophys-x-complexity-prior-20260930-c502dfab-nan: 0.0976

h18-4-usgs-geologic-map-faults-gap-20260930-aef8f42c-nan: 0.0360

....

[https://buffedlizard55-lab.github.io/GEMSDOE21/](https://buffedlizard55-lab.github.io/GEMSDOE21/)

h19-4-reference-20260930-691e4dfa: 0.1894

....

[https://buffedlizard55-lab.github.io/20GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/20GEMSDOE/docs/index.html)

h20-1-sarnnpu-powerlaw-pi0363-tilt-wingcrack-20260930-be0e8f6b-nan: 0.1890

h20-5-continuous-pu-proxy-unverified-20260930-824ce73a-nan: 0.1859

....

[https://buffedlizard55-lab.github.io/GEMSDOE22/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE22/docs/index.html)

h23-a-dti-optimal-emission-6pct-20261002-e2ec4b49-nan: 0.1002

h23-b-dti-optimal-emission-10pct-20261002-86176698-nan: 0.0748

....

[https://buffedlizard55-lab.github.io/GEMSDOE23/](https://buffedlizard55-lab.github.io/GEMSDOE23/)

h30-arrangement-matched-habitat-20261002-0d4e02e8-nan: 0.1352

....

[https://buffedlizard55-lab.github.io/GEMSDOE24/](https://buffedlizard55-lab.github.io/GEMSDOE24/)

h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan: 0.2477

....

[https://buffedlizard55-lab.github.io/GEMSDOE25/](https://buffedlizard55-lab.github.io/GEMSDOE25/)

dotted-h19-5-d2-8-20261002-e56ea318af89-nan: 0.2600

....

[https://buffedlizard55-lab.github.io/GEMSDOE26/](https://buffedlizard55-lab.github.io/GEMSDOE26/)

dilcond-oof-v1-20261003-47629f496133-nan: 0.1223

....

[https://buffedlizard55-lab.github.io/GEMSDOE27/](https://buffedlizard55-lab.github.io/GEMSDOE27/)

topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan: 0.2449

....

[https://buffedlizard55-lab.github.io/GEMSDOE30/](https://buffedlizard55-lab.github.io/GEMSDOE30/)

d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca: 0.2600

....

[https://buffedlizard55-lab.github.io/GEMSDOE31/docs/](https://buffedlizard55-lab.github.io/GEMSDOE31/docs/)

h27-4-solo-d28-20261004-8acb75e1-nan:0.2708

....

[https://buffedlizard55-lab.github.io/GEMSDOE33/](https://buffedlizard55-lab.github.io/GEMSDOE33/)

h33d-analog-tip-stepover-r30-20261004-cb490425926e: 0.2632

....

[https://buffedlizard55-lab.github.io/GEMSDOE34/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE34/docs/index.html)

h34-scatter-q50-arr-matched-20261004T223317Z: 0.0778

....

[https://buffedlizard55-lab.github.io/GEMSDOE35/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE35/docs/index.html)

h35-06-aaa86efb25-20261004T225420098147Z-candidate: 0.0418

....

[https://buffedlizard55-lab.github.io/GEMSDOE36/docs/](https://buffedlizard55-lab.github.io/GEMSDOE36/docs/)

anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros: 0.2750

....

[https://buffedlizard55-lab.github.io/GEMSDOE37/](https://buffedlizard55-lab.github.io/GEMSDOE37/)

h6-physics-dotted-80k-20261005T055000Z-0bef9211631c: 0.1193

....

[https://buffedlizard55-lab.github.io/GEMSDOE38/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE38/docs/index.html)

D-step-3p0-07pct-tipProt-20261005-ecfbf59e2b48-zero: 0.0763

....

[https://buffedlizard55-lab.github.io/GEMSDOE42/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE42/docs/index.html)

xscale-worm-persistence-20261006T000541Z-nan: 0.0581

....

[https://buffedlizard55-lab.github.io/GEMSDOE43/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE43/docs/index.html)

sup01-hgb21-sep40-n40000-20261006-bc2e4e9a8d6f-nan: 0.0424

....

[https://buffedlizard55-lab.github.io/GEMSDOE45/](https://buffedlizard55-lab.github.io/GEMSDOE45/)

h51-km-faultzone-20261006-zeros: 0.0106

....

[https://buffedlizard55-lab.github.io/GEMSDOE49/](https://buffedlizard55-lab.github.io/GEMSDOE49/)

gate_ortho_w0.25-40k-20261006T213721Z-nan: 0.2376

....

[https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html)

h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros: 0.2778

....

[https://buffedlizard55-lab.github.io/GEMSDOE28/](https://buffedlizard55-lab.github.io/GEMSDOE28/)

h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan: 0.2708

h32-1-prethin-tip-euler-d2-8-20261003-31e35eee884e-nan: 0.2649

h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan: 0.2710

h38-1-hf-euler-r30-r1-20261003-56a9f473edc7-nan: 0.2707

....

[https://buffedlizard55-lab.github.io/GEMSDOE29/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE29/docs/index.html)

efd28-repro-20261003-1cc7dc534d51-nan: 0.2600

repo-c0-habitat-emission-20261003-a4d439b07426-nan: 0.0041

sgmc-off-catalogue-44k-20261003-c8dcd780e3fd-nan: 0.0512

wormrank-d28-20261003-59dcaf6dd11d-zeros:0.2560

wormsurv-filter-20261003-921f10960d6e-zeros: 0.0532

xfit-c0-habitat-20261003-ca879db0089a-zeros:

xfit-h41-union-qfaults-20261003-9edb34b99e3a-zeros:

....

[https://buffedlizard55-lab.github.io/GEMSDOE46/](https://buffedlizard55-lab.github.io/GEMSDOE46/)

r11f-scarp-radiometric-fusion-00e049b51218-zeros:0.1589

r12-scarp-rad-concordance-23e807e2de9f-zeros: 0.0843

....

[https://buffedlizard55-lab.github.io/GEMSDOE39/](https://buffedlizard55-lab.github.io/GEMSDOE39/)

h40-e-disc-h40e-30k-zeros: 0.0339

....

[https://buffedlizard55-lab.github.io/GEMSDOE40/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE40/docs/index.html)

h8-euler-lineament-depthcluster-20261006-785c4f5d5ce1: 0.0355

h8-euler-lineament-depthcluster-20261006-785c4f5d5ce1-hard:

h45-eulerdepthreadcluster-20261006-f28e5cff6826-zeros:

....

[https://buffedlizard55-lab.github.io/GEMSDOE41/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE41/docs/index.html)

h42-submission-primary: 0.0245

....

[https://buffedlizard55-lab.github.io/GEMSDOE44/docs/](https://buffedlizard55-lab.github.io/GEMSDOE44/docs/)

h46-twostageAB_20261006T160000Z_b0cfe956-zeros: 0.0715

....

[https://buffedlizard55-lab.github.io/GEMSDOE47/](https://buffedlizard55-lab.github.io/GEMSDOE47/)

h60-lidarscarp-s2p0-20261007-nanoutside: 0.0430

....

[https://buffedlizard55-lab.github.io/GEMSDOE48/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE48/docs/index.html)

h59-cover-ds-belief-b2xh33d-20261008T184547Z-b79c4c61d8d8: 0.2296

....

[https://buffedlizard55-lab.github.io/GEMSDOE50/](https://buffedlizard55-lab.github.io/GEMSDOE50/)

h59-sharpened-scarp-scatter-90k-20261007T171954Z-allfinite: 

....

[https://buffedlizard55-lab.github.io/GEMSDOE51/](https://buffedlizard55-lab.github.io/GEMSDOE51/)

h53-twostage-20261008T040951Z-9a0b32c871:

....

[https://buffedlizard55-lab.github.io/GEMSDOE52/](https://buffedlizard55-lab.github.io/GEMSDOE52/)

:

....

[https://buffedlizard55-lab.github.io/GEMSDOE53/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE53/docs/index.html)

h8-tiprelay-ridgeconcord-pr2-n80000-20261009-49bec522-zeros:

....

[https://buffedlizard55-lab.github.io/GEMSDOE54/docs/](https://buffedlizard55-lab.github.io/GEMSDOE54/docs/)

h54c-manifest-edge-20261009T025732Z-73454bc5:

....

[https://buffedlizard55-lab.github.io/55GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/55GEMSDOE/docs/index.html)

:

....

[https://buffedlizard55-lab.github.io/56GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/56GEMSDOE/docs/index.html)

h56-final-dotted-ridge-d2p8-20261009T190421Z:

....

[https://buffedlizard55-lab.github.io/57GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/57GEMSDOE/docs/index.html)

:

....

The following is the leaderboard for the competition:

[https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)

See below for more links and information related to the competition:

[https://github.com/drivendataorg/gems-prize-reference-solution](https://github.com/drivendataorg/gems-prize-reference-solution)

[https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)

[https://gbcge.org/current-projects/ingenious/](https://gbcge.org/current-projects/ingenious/)

[https://epsg.io/32611](https://epsg.io/32611)

[https://en.wikipedia.org/wiki/Tversky_index](https://en.wikipedia.org/wiki/Tversky_index)

We need to quickly look at the results and results from the GEMSDOE websites above.

Before implementing, generate 3–5 candidate geological hypotheses we haven't tried yet, each naming: the specific layer(s) involved, the physical signature being targeted (e.g., an edge-detection or curvature transform), why it should catch a fault missing from the USGS/INGENIOUS catalogue rather than one already in it, and how it differs from anything already implemented in this repo. Rank them by expected DTI improvement and implementation cost. Validate the top candidate on our spatially-blocked holdout set before touching a weekly submission slot — do not spend a submission slot on an idea that hasn't beaten the current holdout best. If a candidate can't be validated without new external data, name the specific free, official source needed and check it's obtainable before proposing the idea as viable.

Work line by line verifying from official verified trusted sources, provide links for manual review.  There should be no manual input, work on your own to complete tasks.  Flag any irregularities for review.  No hallucinations.

Verify no hallucinations.

The goal of this project is to get a full list that follow our requirements.  No hallucinations.  Verify line by line.

We have a good understanding of how our hypothesis, methodology, calculations, analysis are done so we should be able to figure out a way to score higher on the leaderboard using previous results and scoring that we have across the sites listed above.  We need to come up with distinct and unique strategies to score higher in this competition leaderboard.  We need to start doing heavy and deep research into the part of the project that matters the most, which is the scientific discovery of geothermal vents.  We should store all of our information and knowledge that we can gather from official verified sources.  This will serve as a starting point for other projects as well.  We need to think outside the box but still be grounded in proper scientific research, we are ultimately aiming for a top prize that many others are competing for.  So it's important to be contrarian but be smart about it.  We need to find sources of data that others are over looking or areas of the project when it comes to geothermal vents.  We need to do deep research and critical thinking and come up with new hypothesis to test.

0.3195	is the highest score right now so we need to design a new strategy, research, testing, analyzing, and generating submission system than the current website.  It should be unique, take unique approaches to generating a submission that can score higher than 0.3195.  

Put this prompt into the repo readme and read it everytime we work on the project as a starting point to make sure we are building what we are aiming for and have a strong base to continue building and improving on making something useful for everyday use.  It should solve the problem of having to manually check everything ourselves and having an up to date current feed.

Review the repo.

The following is taken from the Arena AI team and I think it makes a good point on building a successful project, so let's keep the Core Values and Own the Outcome as a focal point when building, developing, researching, suggesting upgrades, and implementing the work.

Our Core Values

Maximize P(Win)

"Maximize the Probability of Winning": our decision making framework. In every decision, we weigh tradeoffs, assess risk, and choose the path that maximizes the probability that Arena succeeds. We set aside our emotions and make tough decisions in order to maximize P(Win). "Maximize P(Win)" frees us from constraints and clarifies that we must put Arena first.

Own the Outcome

We own results end to end — not just our individual slice of the work. When problems arise and we have the means to act, we do so without waiting for permission or assignment. We treat failure and success as signals and use them to improve. At Arena, we stay accountable to the final outcome.

Work line by line verifying from official verified trusted sources, provide links for manual review.  There should be no manual input, work on your own to complete tasks.  Flag any irregularities for review.  No hallucinations.

Verify no hallucinations.

The goal of this project is to get a full list that follow our requirements.  No hallucinations.  Verify line by line.

We need to focus on being able to generate a submission into the competition.

The site should be able to generate a TIF file that is required for submission.  It should be as easy as download to click a File to submit into the competition.  This needs to be in the executive summary or the very beginning of the site.  it should be obvious when you visit the site.

I tried to submit the document that i downloaded from the site but it returned this error on the submission form:

"Predicted values must be in range [0, 1]"

Also we need to give it a unique name and A short comment to help you or your team tell submissions apart later e.g. clustering with k=25

Here is the submission page when i click submit file

New submission

File to submitNo file chosen

You can submit a single-band GeoTIFF (.tif) file, or a .zip file containing a single GeoTIFF, with your predictions. It must match the submission format's CRS, shape, and geotransform. You may wish to review the competition rules first.

Note (optional)

A short comment to help you or your team tell submissions apart later e.g. clustering with k=25

Create a executive summary subpage that explains exactly how to make a submission into the contest.

Work on the next steps from the previous sessions first.

The goal of this project is to place top of the leaderboard in this competition.  The following is the competition:

[https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)

We need to create a project that can compete and place top of the leaderboard.  We need to understand the problem, collect all the data and organize it into a clean easily auditable table with official verified links for manual verification.  

This is the guidelines we need to follow.[https://www.drivendata.org/competitions/306/competition-doe-gems/](https://www.drivendata.org/competitions/306/competition-doe-gems/)

Get familiar with the problem through the overview and problem description,[https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/). You might also want to reference additional resources available on the about page,[https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/).

Download the data from the data,[https://www.drivendata.org/competitions/306/competition-doe-gems/data/](https://www.drivendata.org/competitions/306/competition-doe-gems/data/), tab.

Create and train your own model. This reference solution,[https://github.com/drivendataorg/gems-prize-reference-solution](https://github.com/drivendataorg/gems-prize-reference-solution) implements a simple approach.

Use your model to generate predictions that match the submission format.

Tell me what are you limitations and what you need access to during this project.  We will need to find free publicly available sources and data from official and verified sources if we are to use 3rd party or external data.

this pdf outlines how submissions must be entered into the competition.

[https://docs.nlr.gov/docs/fy26osti/96647.pdf](https://docs.nlr.gov/docs/fy26osti/96647.pdf)

You must be able to do your own research, deep research, scientific literature research and organize the knowledge so that we can critically think through the problem and generate a solution through scientific and free publicly available information.  this must be done autonomously and must be constantly reviewed and improved upon.  Provide suggestions and improvements and implement them.

No DrivenData auth → cannot auto-download training_features.tif, labels.tif, sample_submission.tif, 1m_DEM_links.csv from the data tab (verified redirect to login)

See below for links from the above site.  See attached files for links from the above site.

[https://gdr.openei.org/submissions/1391](https://gdr.openei.org/submissions/1391)

Download competition data from the data tab (requires login) to data/

See links below for competition data:

[https://www.dropbox.com/scl/fi/aemhtutjgcp6tr3tint94/GEMS_96647.pdf?rlkey=rek210cj2smnmzb8n0sla1vmd&st=wz4kofki&dl=0](https://www.dropbox.com/scl/fi/aemhtutjgcp6tr3tint94/GEMS_96647.pdf?rlkey=rek210cj2smnmzb8n0sla1vmd&st=wz4kofki&dl=0)

[https://www.dropbox.com/scl/fi/6rgvnuady818ol8yqgis4/example_submission.tif?rlkey=kbykilvau066xuogoosbf4cq8&st=8junzdyw&dl=0](https://www.dropbox.com/scl/fi/6rgvnuady818ol8yqgis4/example_submission.tif?rlkey=kbykilvau066xuogoosbf4cq8&st=8junzdyw&dl=0)

[https://www.dropbox.com/scl/fi/t7fyt03qdh9egyme0itwo/existing_faults.tif?rlkey=yiao96uluqdkipf0h5vju71jf&st=rnino7ya&dl=0](https://www.dropbox.com/scl/fi/t7fyt03qdh9egyme0itwo/existing_faults.tif?rlkey=yiao96uluqdkipf0h5vju71jf&st=rnino7ya&dl=0)

[https://www.dropbox.com/scl/fi/3vz9o0wwavi26xaeoxlwr/gems-geodawn-numerical-features.tif?rlkey=je8d8fepqfbst9lnwsq9rkplu&st=zj1lag1r&dl=0](https://www.dropbox.com/scl/fi/3vz9o0wwavi26xaeoxlwr/gems-geodawn-numerical-features.tif?rlkey=je8d8fepqfbst9lnwsq9rkplu&st=zj1lag1r&dl=0)

[https://www.dropbox.com/scl/fi/ig0mban712ns1atphgphe/Digital-elevation-model-links-JSON.pdf?rlkey=zm77f1vbtt2if8hlruymptnu3&st=srhhir10&dl=0](https://www.dropbox.com/scl/fi/ig0mban712ns1atphgphe/Digital-elevation-model-links-JSON.pdf?rlkey=zm77f1vbtt2if8hlruymptnu3&st=srhhir10&dl=0)

Work line by line verifying from official verified trusted sources, provide links for manual review.  There should be no manual input, work on your own to complete tasks.  Flag any irregularities for review.  No hallucinations.

Verify no hallucinations.

The goal of this project is to get a full list that follow our requirements.  No hallucinations.  Verify line by line.

Site creation

Create a github page for this repo that has clean ui, user friendly, simple and easy to use.  It should be organized and clean.

It should include all relevant information in an easy to read format with official verified links as sources for review.  Work line by line verify everything no hallucinations.

**The single remaining blocker to training is data placement**: run `bash scripts/download_competition_data.sh` on any unrestricted machine into `data/`, then `python scripts/prepare_data.py` — after that the full train→inference→validate pipeline is ready to run (GPU needed for training; metric/losses/validation all verified working here on CPU).

you need to complete the above task by yourself.  Work line by line verifying from official verified trusted sources, provide links for manual review.  There should be no manual input, work on your own to complete tasks.  Flag any irregularities for review.  No hallucinations.

Verify no hallucinations.

The goal of this project is to get a full list that follow our requirements.  No hallucinations.  Verify line by line.

Run this task through multiple passes.

Pass 1: Implement the task completely and verify the result.

Pass 2: Review your work for bugs, missing requirements, incorrect assumptions, and edge cases. Fix everything you find.

Pass 3: Re-check the entire implementation against the original request. Improve accuracy, reliability, completeness, and code quality. Fix any remaining issues.

Do not stop after the first pass. Each pass must build on the previous one. Before finishing, verify that the final result fully satisfies the original request.  Work line by line verify everything no hallucinations.

Go ahead and create a pull request and then merge the pull request onto the main. Make suggestions for what work still needs to be done and any limitations that is in the way of a successful project.  It should be worked on in this next session or the next session.  Work line by line verify everything no hallucinations.

</details>

## Current answer on the reported leaderboard values

A saved **PUBLIC-LEADERBOARD snapshot (not a submission-page receipt and not ORGANIZER-CONFIRMED)** lists **0.2778** at rank 17 under `extradr19`, **0.3195** at rank 7, and **0.3774** at rank 1; see [`evidence/leaderboard_snapshot_20261009.json`](evidence/leaderboard_snapshot_20261009.json). The mapping from `extradr19` to the owner-maintained H33 artifact is unverified. A read-only GitHub API check of the owner's GEMSDOE32 manifest reports `receipt: null` for H33, labels it `UNSCORED`, and describes **0.2747** as projected. That is secondary owner-generated evidence, not an organizer receipt. Therefore this project cannot establish that H33 produced the public rank-17 entry, why that entry received its value, or that any repository candidate beats it. The previous anchor-proxy DTI and causal conclusions that depended on the invalid count-only formula are withdrawn and were not recomputed. Any near-miss/clustered-dot explanation is only a hypothesis, not an established mechanism. See the [2026-10-09 leaderboard review](docs/leaderboard-review-20261009.md).

## Critical metric correction — prior conclusions withdrawn

For the official distance-weighted Tversky definitions, `TP_w + FN_w = |G|` is valid. It yields

```text
DTI = TP_w / (TP_w + alpha*FP_w + beta*(|G|-TP_w) + eps)
    = TP_w / ((1-beta)*TP_w + alpha*FP_w + beta*|G| + eps)
```

At `alpha=0.2`, `beta=0.8` this is

```text
DTI = TP_w / (0.2*TP_w + 0.2*FP_w + 0.8*|G| + eps)
```

It is **not** generally `TP_w/(0.2*N + 0.8*|G|)`: `TP_w+FP_w=N` is not a general identity. The old target-size tables, “coverage plateau” claims, anchor-proxy DTI calculations, and any conclusions that rely on the count-only denominator are withdrawn. A synthetic regression case in `tests_numeric/test_core.py` demonstrates the error: with one truth pixel, a correct unit dot, and another unit dot one pixel away, `TP_w=1`, `FP_w=1/3`, `FN_w=0`; exact DTI is **0.9375**, while the invalid simplification gives **5/6**. This is a synthetic metric test, not a HOLDOUT-DTI result.

`breakeven_credit` now documents the conditional single-match threshold `w > alpha*DTI_now` under its assumptions. It is not a generic per-dot rule. `greedy_cover` maximizes a coverage surrogate and does not optimize full DTI because it omits the separate FP term.

## Evidence and gate status

- **Valid promotion HOLDOUT-DTI:** none. No valid evaluator version, withheld-positive count, value, and 95% CI are available for promotion.
- **Historical HOLDOUT-DTI (not valid for promotion):** the canonical-local record used an unversioned pre-audit `src/gems55/dti55.py` transcription with **60,988** withheld positives. Tensor record **0.0667012**, stored interval **[0.0560079, 0.0893459]**. The quadrant split can split a connected fault; its purported random control was filtered by `score > 0`; the interval bootstraps four fold values rather than pooled-DTI contributions. This cannot clear or condemn a candidate under the required protocol.
- **Separate historical HOLDOUT-DTI (private evaluator; not comparable):** `gems.metric v1`, **60,594** withheld positives. E1 ridge **0.0578 [0.0499, 0.0652]**, E2 dimensionality **0.0463 [0.0398, 0.0523]**, E3 tensor/strike **0.0444 [0.0383, 0.0502]**. This fork and different holdout cannot be compared to the canonical-local record.
- **Merged historical H56 result (not promotion-grade):** **HOLDOUT-DTI**, evaluator `src/gems55/dti55.py` (explicit version absent; not reconciled with the authorized shared evaluator), **60,988** withheld positives; multiscale tensor **0.0172779**, stored 95% CI **[0.0161283, 0.0184686]**. The CI resamples five fold DTI values rather than pooled-score contributions; the stored candidate did not beat its same-evaluator comparator. This is not a clearance result.
- **Merged historical H55 160k result (not promotion-grade):** **HOLDOUT-DTI**, evaluator `src/gems55/dti55.py` (explicit version absent; local/unreconciled), **60,988** withheld positives; Q4 tensor_full **0.1019**, stored 95% CI **[0.0877, 0.1185]**. The CI is a four-quadrant fold-level t interval; quadrant folds can split connected faults. The control CI is absent from the final card, so its raw value is not repeated. This is not a valid test of the required holdout.
- **Uniqueness:** the historical H55 40,000-dot report says 56 rasters were scanned and raw maximum overlap was **84.13%**; the separate H55 160,000-dot report records **84.01%**; H56 40,000-dot reported maximum final-dot overlap **100%** (with another row at **73.6%**). Each exceeds the literal **70%** stop rule. The older 632-raster reports concern different candidates and legacy snapshots; do not combine them with the 56-raster reports. No current complete registry scan or surface-cache check is available.
- **Format:** a previous byte inspection recorded one-band float32, EPSG:32611, 3730×3292, and the expected affine transform. That is partial metadata inspection, not an official format pass: the authentic organizer template is not present here and the validator was not rerun. The historical `zeros`-outside encoding is not cleared against the official footprint.
- **Score receipt:** none found in this checkout. No weekly slot was used.

The detailed machine-readable verdict is [`docs/run-card.json`](docs/run-card.json); live project status is [`docs/status.json`](docs/status.json). The separate H55 160k historical record is [`docs/run-card-h55-160k.json`](docs/run-card-h55-160k.json); all raster variants are archived outside the published site and marked uncleared.

## Ranked geological hypotheses (stay in the tensor lane)

Before any experiment, read [`docs/hypotheses.md`](docs/hypotheses.md). It ranks four distinct tensor-dimensionality hypotheses and specifies required layers, physical signatures, uncatalogued-fault rationale, differences from the existing method, compute/validation cost, non-fault mimics, and official data sources. The top candidate uses competition band 2 (reduced-to-pole magnetic anomaly) and band 13 (isostatic gravity anomaly). The current prototype exists, but its holdout is not promotion-grade. No new hypothesis was implemented or tested in this review; the experiment budget is recorded as exhausted (three experiments).

## Standing project brief

This repository is the recurring starting point for the DOE GEMS project. The assigned scientific lane is **potential-field tensor dimensionality**; do not switch to another method family to force a file.

1. **Keep the scientific protocol intact.** Reuse the authorized shared cached feature stack, evaluator, writer, and uniqueness checker. Do not make a private evaluator/writer fork. Whole-segment hide-and-recover must use a buffer, exact visible-fault masking, pooled DTI with α=0.2, β=0.8, and the 300 m triangular kernel. Run each leakage-canary feature alone. Compare the continuous surface before placement and final dots afterward.
2. **Holdout before promotion.** Test the top ranked candidate on a spatial holdout before any submission-slot promotion. A same-evaluator holdout win is required. Stop at three experiments or two hours; the stored run record says three experiments were already used. Do not use a weekly slot without a same-evaluator holdout win.
3. **Label every score-like result.** Use `HOLDOUT-DTI` with evaluator version, withheld-positive count, and 95% CI, or `ORGANIZER-CONFIRMED` copied from an actual organizer submission receipt. Mark projections as projections. Never invent a receipt, leaderboard attribution, registry comparison, or validator pass.
4. **Uniqueness stop rule is literal.** If absolute rank-correlation exceeds 0.90 or more than 70% of candidate dots lie within 3 pixels of any prior raster, log the duplicate and stop. A chance-adjusted statistic does not override the literal threshold.
5. **Publish a GeoTIFF only when honestly cleared.** The file must be unique, valid against the authentic organizer template, scientifically cleared, and have passed leakage, surface and final-dot uniqueness checks. The site must state plainly whether download/submission is allowed. The executive summary must explain the portal workflow; keep the TIFF unlinked unless every gate passes.
6. **Keep sources and irregularities explicit.** Use official or verified links, state data/validation limitations, and distinguish organizer files from owner-maintained mirrors. Do not download sibling-repository data mirrors without provenance/legal approval.
7. **End any run with the JSON run card.** Required fields: hypothesis, mechanism, named non-fault mimic, holdout plus CI, registry comparisons, raster hash, validator findings, submission name and note (≤140 characters), and verdict. The current card records `NOT_CLEARED` and null valid-holdout fields.
8. **Review every change three times:** implementation, bug/assumption audit, and final requirement/source audit. Verify changed lines and do not rerun experiments to resolve missing inputs or gate failures.

## Data, provenance, and preparation

The authorized competition source is the [DrivenData data tab](https://www.drivendata.org/competitions/306/competition-doe-gems/data/), which requires login and acceptance of the rules. The feature stack, labels, organizer sample template, cached surface, and registry rasters are absent from this checkout.

The owner-maintained [GEMSDOE sibling repository](https://github.com/buffedlizard55-lab/GEMSDOE) contains mirror references, not authenticated organizer downloads. Its recorded SHA-256 pins are explicitly identified in [`data/README.md`](data/README.md) and [`data/SOURCES.md`](data/SOURCES.md) as mirror-derived. The downloader is disabled by default and requires `GEMS_ALLOW_UNOFFICIAL_MIRROR=1`; that opt-in does not establish provenance or permission. It was not run.

After downloading authorized files from DrivenData under the canonical names defined in `src/gems55/io55.py`, run:

```bash
python scripts/prepare_data.py
```

The check validates canonical filenames, the recorded hashes, and grid geometry. If an authorized organizer file differs from a mirror pin, stop and reconcile it against the official source; do not silently overwrite pins. See [`docs/sources.md`](docs/sources.md) for sources and retrieval status.

## Repository map

- `src/gems55/dti55.py` — single local DTI transcription, synthetic exactness tests, additive contribution maps, and spatial block bootstrap helper. It is **not yet reconciled to an authorized shared evaluator**.
- `src/gems55/holdout55.py` — repository-local synthetic/support utilities for whole 8-connected components, Euclidean buffers, and score-independent random draws; not certified as the authorized shared holdout/evaluator.
- `src/gems55/io55.py` — canonical raster paths, grid constants, and local writer. The writer does not certify a submission.
- `scripts/evaluate_holdout.py` — retired fail-closed entry point; no local holdout run is allowed until the authorized shared evaluator/cache are reconciled and the exhausted budget is explicitly reopened.
- `scripts/verify_unique.py` — repository-local fail-closed full-manifest uniqueness checker; requires the authentic template and every registry raster, and is not the authorized shared checker.
- `scripts/validate_submission.py` — local structural validator; requires authentic template/labels and is not an organizer receipt.
- Legacy data-dependent experiment, local writer, mirror-registry downloader, page generator, and status-mutator entry points are retired fail-closed because the experiment budget is exhausted or their evidence path is invalid. The previously completed `exp8`–`exp10` entry points are also disabled; their committed JSON records remain historical evidence only.
- `scripts/prepare_data.py` — canonical filename/hash/grid preparation checks.
- `evidence/` — historical run records. Invalid evidence is annotated, not treated as current promotion support.
- `docs/` — GitHub Pages source; current landing page has no TIFF link and prominently says not to download/submit.

The former duplicate `gems/` evaluator/writer package was removed. The old `scripts/run_tensor_lane.py` is retired and refuses to run because it depended on that private fork and quadrant folds; the older private-evaluator results remain only as labeled historical records.

## Final portal workflow (only after clearance)

When a future file has passed every scientific, leakage, uniqueness, and format gate: sign in to the [DOE GEMS competition](https://www.drivendata.org/competitions/306/competition-doe-gems/), open the submission page, upload the exact cleared single-band GeoTIFF, enter its published run-card name/note (no more than 140 characters), submit, and preserve the organizer receipt. This repository has no portal credentials and has not submitted any file. See [`docs/submit.html`](docs/submit.html) for the current explicit answer: **not cleared; do not download or submit**.

## Sources, results, and status pages

- [Official problem description and metric](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [Official GEMS rules (NLR PDF)](https://docs.nlr.gov/docs/fy26osti/96647.pdf)
- [USGS GeoDAWN release, DOI 10.5066/P93LGLVQ](https://doi.org/10.5066/P93LGLVQ)
- [Results and metric correction](docs/results.md) · [Leaderboard attribution](docs/leaderboard-analysis.md) · [2026-10-09 public-leaderboard audit](docs/leaderboard-review-20261009.md) · [Irregularities](docs/irregularities.md) · [Source register](docs/sources.md) · [Three-pass review log](docs/review-log.md)
