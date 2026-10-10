# `data/` — competition payloads (not committed)

The raster payloads are ignored by Git. The authorized source is the [official DrivenData data tab](https://www.drivendata.org/competitions/306/competition-doe-gems/data/), which requires an eligible account and acceptance of the competition terms. This repository does not contain those files at present.

| Canonical filename (from `src/gems55/io55.py`) | SHA-256 reference pin | Provenance status |
|---|---|---|
| `gems-geodawn-numerical-features.tif` | `4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5` | Owner-maintained sibling-mirror pin; not independently matched to organizer bytes |
| `labels.tif` | `7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093` | Owner-maintained sibling-mirror pin; not independently matched to organizer bytes |
| `sample_submission.tif` | `2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc` | Owner-maintained sibling-mirror pin; not independently matched to organizer bytes |

The hash pins came from an owner-maintained sibling-repository manifest. They are SHA-256 integrity references, not an organizer signature, legal authorization, or proof of source. See [`SOURCES.md`](SOURCES.md). No mirror download was performed for this review.

After obtaining the files through the official data tab and placing them under the canonical names above, run:

```bash
python scripts/prepare_data.py
```

That check verifies file hashes against the listed mirror pins and checks the canonical grid contract. If an authorized organizer download differs from a mirror pin, stop and verify the discrepancy against the official source before changing a pin; do not silently overwrite it.
