#!/usr/bin/env bash
# Recover the official DOE GEMS competition rasters into data/.
#
# The organiser data page (https://www.drivendata.org/competitions/306/
# competition-doe-gems/data/) requires a DrivenData login.  If you have
# credentials, download training_features.tif, labels.tif, sample_submission.tif
# and 1m_DEM_links.csv there and drop them into data/.
#
# Otherwise this script recovers the same files from prior repositories under the
# same GitHub account and verifies them by git blob SHA (content-addressed, so an
# identical SHA means identical bytes):
#   sample_submission.tif  7d865a9921a40ed2ea4c742a6a25b1fa2f357c5a  1,599,597 B
#   labels.tif             4ad3c1f3f19823e40924589bee7e51e44ae3a2e7    425,830 B
#   features               5 parts, 418,912,844 B reassembled
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p data/parts

blob() { # repo path dest
  local sha
  sha=$(gh api "repos/buffedlizard55-lab/$1/contents/$2" --jq '.sha')
  gh api "repos/buffedlizard55-lab/$1/git/blobs/$sha" \
     -H "Accept: application/vnd.github.raw" > "$3"
  echo "  $3  sha=$sha  $(stat -c%s "$3") bytes"
}

[ -f data/sample_submission.tif ] || blob GEMSDOE10 data/sample_submission.tif data/sample_submission.tif
[ -f data/labels.tif ]            || blob GEMSDOE10 data/labels.tif            data/labels.tif
if [ ! -f data/training_features.tif ] && [ ! -f data/gems-geodawn-numerical-features.tif ]; then
  for p in 000 001 002 003 004; do
    blob GEMSDOE2 "data/bridge/gems-geodawn-numerical-features.tif.part-$p" "data/parts/part-$p"
  done
  cat data/parts/part-00{0,1,2,3,4} > data/training_features.tif
fi
python3 - <<'PY'
import sys
sys.path.insert(0, "src")
from gems55 import io55
grid, tmpl = io55.read_template()
lab = io55.read_labels()
assert (grid.width, grid.height) == (3292, 3730)
assert grid.crs == 32611
assert tuple(grid.transform)[:6] == (100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)
print("data/ verified:", grid.width, "x", grid.height, "EPSG:32611",
      int((lab == 1).sum()), "catalogue px")
PY
