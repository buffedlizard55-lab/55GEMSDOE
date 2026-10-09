#!/usr/bin/env bash
# Optional recovery from owner-maintained sibling-repository mirrors.
#
# This does NOT download from DrivenData and does NOT establish organizer
# provenance. Prefer the authenticated official data page after accepting its
# rules. Mirror use is disabled unless explicitly opted into with
# GEMS_ALLOW_UNOFFICIAL_MIRROR=1.
set -euo pipefail
cd "$(dirname "$0")/.."

need_mirror=0
for f in data/sample_submission.tif data/labels.tif data/gems-geodawn-numerical-features.tif; do
  [ -f "$f" ] || need_mirror=1
done
if [ "$need_mirror" = 1 ] && [ "${GEMS_ALLOW_UNOFFICIAL_MIRROR:-0}" != "1" ]; then
  echo "Refusing unofficial mirror download. Retrieve authorized files from DrivenData, or explicitly opt in for local audit only with GEMS_ALLOW_UNOFFICIAL_MIRROR=1." >&2
  exit 2
fi
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
if [ ! -f data/gems-geodawn-numerical-features.tif ]; then
  for p in 000 001 002 003 004; do
    blob GEMSDOE2 "data/bridge/gems-geodawn-numerical-features.tif.part-$p" "data/parts/part-$p"
  done
  cat data/parts/part-00{0,1,2,3,4} > data/gems-geodawn-numerical-features.tif
fi
python3 scripts/prepare_data.py
