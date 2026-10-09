# Results — H56 multi-scale tensor persistence

**Review date:** 2026-10-09 UTC. Every score below is **HOLDOUT-DTI**, not an
organizer-confirmed leaderboard score. No weekly submission slot was used.

## Evaluator and holdout

- Canonical evaluator: `src/gems55/dti55.py`.
- Official formula: alpha 0.2, beta 0.8, triangular kernel radius 300 m (3 px at
  100 m). The implementation is regression-tested against a brute-force
  transcription and the official worked arithmetic example.
- Five seeded whole-segment/lattice folds. Each withheld segment receives a 3 px
  buffer; visible catalogue pixels are recomputed and masked per fold; TP/FP/FN
  components are pooled before the ratio.
- Withheld positives: **60,988**. The 95% CI is 4,000 resamples of the five fold
  DTI values; it is not an organizer uncertainty interval.

| Arm | HOLDOUT-DTI | 95% CI | Role |
|---|---:|---:|---|
| Uniform random control, 40,000 dots | **0.01440** | 0.01373–0.01537 | matched null for H56 |
| One-scale ridge × strike agreement | **0.01852** | 0.01782–0.01940 | current same-evaluator comparator |
| One-scale full tensor lane | **0.01774** | 0.01710–0.01837 | baseline lane |
| H56 multiscale full tensor | **0.01728** | 0.01613–0.01847 | preregistered candidate; negative |
| H56 multiscale ridge-only ablation | **0.01927** | 0.01829–0.02026 | ablation, not a valid promoted lane |
| Gravity-only tensor | **0.01671** | 0.01581–0.01762 | third experiment; negative |

H56 beats its matched random control but does not beat the current one-scale
comparator. It is not promoted.

## Leakage canary

The H56 single-feature AUCs were tested against fold-specific withheld positives
and fold-specific eligible negatives. Maximum AUC was **0.5522**, below the
preregistered 0.90 leakage threshold. This is a diagnostic and is not a score.

## Auxiliary strike diagnostic

For H56, 273 withheld catalogue segments were tested. The within-20° agreement
was 26.0% for withheld segments and 22.4% for sampled random ridges; the mean
angular-difference 95% CI was [−12.50°, −7.21°]. This is a catalogue proxy and is
not used as a promotion gate because ridge orientation and tensor strike can be
geometrically coupled.

## Registry gate and artifact

The continuous H56 surface was checked before placement and had maximum absolute
Spearman correlation **0.0223** across 56 same-grid registry rasters, below the
0.90 threshold. Final-dot checking then found 1.000 overlap within 3 px against
the spacing-5 lattice and 0.736 against another prior raster. Because the protocol
says `>70% => duplicate and stop`, the strict verdict is **DUPLICATE-STOP**.
A control-adjusted overlap is retained only as a diagnostic; it cannot change the
verdict.

The generated artifact is available for audit, not upload:

- `docs/downloads/h56-multiscale-tensor-persistence-40000dots-20261009T162812Z-zeros.tif`
- SHA-256 `43743afdb030b739465d4754aabd8605bceef49bcc836bee93e9094807d4695f`
- `docs/run-card.json` and `docs/status.json`

## Reproduce

```bash
python scripts/prepare_data.py
python scripts/build_lane.py --tag h56_ms300_900 --scales-m 300,900
python scripts/evaluate_holdout.py --tag h56_ms300_900 --n-dots 40000
python scripts/submission_writer.py --tag h56_ms300_900 --n-dots 40000 --seed 5609
python scripts/validate_submission.py docs/downloads/*h56*-zeros.tif
python scripts/verify_unique.py <candidate.tif> --surface data/cache/lane_h56_ms300_900.npz
```
