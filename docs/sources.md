# Official source register

- [DrivenData problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/): task is prediction of geothermal-indicative faults; new hidden faults are expert-identified and absent from the existing public catalogue; distance-weighted Tversky metric, alpha=0.2, beta=0.8, 300 m triangular kernel, and GeoTIFF contract.
- [DrivenData public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/): rendered ranked table captured 2026-10-09. Snapshot in `evidence/leaderboard_snapshot_20261009.json` shows 0.3774 at rank 1, 0.3195 at rank 7, and 0.2778 at rank 16. The rows do not reveal TIFF filenames/hashes and are not submission-page receipts; no score is mapped to a candidate raster.
- [GEMSDOE32 H33 page](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html): sibling-repository method/report only. The page calls its H33 candidate `UNSCORED` and 0.2747 a projection; it is not an organizer receipt and does not prove a mapping to the leaderboard's 0.2778 row.
- [Organizer metric discussion](https://community.drivendata.org/t/leaderboard-aggregation-pooled-over-public-test-pixels-or-mean-of-per-chunk-scores/11550): pooled aggregation over relevant pixels, not a mean of chunk scores.
- [Official reference solution](https://github.com/drivendataorg/gems-prize-reference-solution): reference notebook and code; it is not this lane's holdout evaluator.
- [USGS GeoDAWN overview](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) and [ScienceBase release](https://www.sciencebase.gov/catalog/item/657e1d85d34e23d3533209f7): survey context, four north–south acquisition blocks, flight paths, DOI `10.5066/P93LGLVQ`, and official public data release.
- [Pedersen & Rasmussen (1990)](https://doi.org/10.1190/1.1442807): potential-field gradient-tensor invariants and dimensionality context.
- [Beiki & Pedersen (2010)](https://doi.org/10.1190/1.3484098): gravity-gradient eigenvector analysis.
- [Beiki, Pedersen & Nazi (2011)](https://doi.org/10.1190/1.3555343): pseudogravity-gradient eigenvector analysis.
- [Open-access dimensionality discussion](https://pmc.ncbi.nlm.nih.gov/articles/PMC11333590/): secondary explanation of dimensionality indicator interpretation; not organizer data.

## Evidence labels

- **HOLDOUT-DTI** means an output from the local canonical hide-and-recover evaluator with evaluator/version, withheld-positive count, and 95% CI recorded. It is not an organizer leaderboard score.
- **ORGANIZER-CONFIRMED** is reserved for a score copied from a submission-page receipt. No such receipt exists in this checkout.
- **PUBLIC-LEADERBOARD-SNAPSHOT** means a dated row displayed on the public organizer leaderboard. It is not a submission-page receipt and cannot be attributed to a GeoTIFF without a matching filename/hash.
- A projection is not a score. A sibling-repository claim is not an organizer receipt. Historical anchor proxy-DTI output has been retracted under IR-55-034.
