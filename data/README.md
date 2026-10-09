# data/ — competition payloads (NOT committed)

Everything in this folder except this README and `SOURCES.md` is **gitignored on purpose**. The competition
rasters are licensed to registered DrivenData competitors; we have not found a rules clause that permits
redistribution (see `docs/irregularities.md` #4). Do not commit them.

| File | Source | sha256 (as pinned by the sibling repo; see SOURCES.md) |
|---|---|---|
| `training_features.tif` | `gems-geodawn-numerical-features.tif` | `4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5` |
| `labels.tif` | `existing_faults.tif` | `7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093` |
| `sample_submission.tif` | `example_submission.tif` | `2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc` |

Verified in this session: the three files reassemble from the sibling repo's committed parts and match the
pins in that repo's `data/bridge/manifest.json`. **The pins themselves are not independently verified against
DrivenData** (the official data tab was not reachable from this sandbox).

To place them yourself (after logging in to DrivenData and accepting the rules):
download the three files from the data tab into this folder under the names above, then run
`python scripts/prepare_data.py`.
