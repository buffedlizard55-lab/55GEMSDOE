# Data provenance and retrieval boundary

## Authorized source

- [DOE GEMS Prize Challenge data tab](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) is the authorized competition source. It requires a DrivenData login and acceptance of the competition terms. This review did not authenticate to or download from that page.

## Secondary mirror evidence (not official provenance)

- An owner-maintained sibling repository, [`buffedlizard55-lab/GEMSDOE`](https://github.com/buffedlizard55-lab/GEMSDOE), contains copies/parts and a manifest. The manifest reports SHA-256 pins for the canonical feature, label, and sample-submission files.
- Its own documentation says its chain leads to Dropbox mirrors linked on the competition data tab. That assertion is not independent organizer verification. Public GitHub copies may be useful for development, but this project does not call them official or authenticated competition downloads.
- `scripts/download_competition_data.sh` is therefore disabled by default. It only accesses those sibling mirrors if `GEMS_ALLOW_UNOFFICIAL_MIRROR=1` is set explicitly. It must not be used as evidence of organizer provenance or licensing approval.

## Local state and validation

- The feature stack, labels, organizer sample template, cache, and registry raster corpus are not present in this checkout.
- `scripts/prepare_data.py` uses canonical paths from `src/gems55/io55.py`, verifies the recorded SHA-256 pins, and checks the expected grid geometry. The pins are mirror-derived and must be reconciled with the official files if they differ.
- Git blob SHA-1 values in repository history and these SHA-256 values are different hash algorithms; they must not be compared as if they were the same digest.
- Competition data are excluded from Git. Do not commit licensed rasters or download them through a secondary mirror without provenance and legal approval.
