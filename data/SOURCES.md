# Provenance of the local data copies

1. Sibling repository: https://github.com/buffedlizard55-lab/GEMSDOE (folder `data/bridge/`, 6 files: 5 parts + `manifest.json`).
   Fetched with `git clone --filter=blob:none --sparse` on 2026-10-09 (commit read at clone time).
2. Reassembled with `cat` in part order and checked with `sha256sum`. All five parts and the three whole-file hashes
   match `data/bridge/manifest.json` (values listed in data/README.md).
3. The sibling manifest says the originals came from Dropbox mirrors linked on the DrivenData data tab. **Those mirrors
   were not reachable from this sandbox**, so the hash chain stops at the sibling repo.
4. Copies were moved into `data/` (gitignored). Nothing from `data/` is committed in this repository.
