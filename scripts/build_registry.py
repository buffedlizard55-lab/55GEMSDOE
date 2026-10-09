#!/usr/bin/env python3
"""Re-materialise the prior scored GEMSDOE rasters used as the uniqueness control.

Prior rasters are used ONLY as a uniqueness / lane-drift reference for the run
brief (rank correlation < 0.90 and < 70% of our dots within 3 px of any one
registry raster).  No pixel of any prior raster is copied into the deliverable.

Source of truth: ``registry/registry.json`` (committed).  Each entry records the
sibling repository, the in-repo path, and the byte size.  This script downloads
every entry by content address (GitHub blob SHA via the API), checks the byte
count against the index, checks the grid, and writes the local copies to
``registry/rasters/`` (gitignored).

History: the previous version of this script rebuilt the index from
``/tmp/trees/*.tsv`` listings that exist only in the session that wrote them.
That made the registry impossible to re-create on a fresh checkout (IR-55-16).
The committed index is now authoritative; the old tree listing is not needed.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems55 import io55  # noqa: E402

OUT = ROOT / "registry" / "rasters"
INDEX = ROOT / "registry" / "registry.json"


def gh_json(args: list[str]) -> dict:
    out = subprocess.run(["gh", *args], capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    index = json.loads(INDEX.read_text())
    grid, _ = io55.read_template()
    try:
        import rasterio
    except ImportError:  # pragma: no cover
        sys.exit("rasterio is required")

    ok = 0
    for name, meta in sorted(index.items()):
        dest = OUT / name
        if not dest.exists() or dest.stat().st_size != meta["size"]:
            info = gh_json(["api", f"repos/buffedlizard55-lab/{meta['repo']}/contents/{meta['path']}"])
            raw = subprocess.run(
                ["gh", "api", f"repos/buffedlizard55-lab/{meta['repo']}/git/blobs/{info['sha']}",
                 "-H", "Accept: application/vnd.github.raw"],
                capture_output=True, check=True,
            ).stdout
            if len(raw) != meta["size"]:
                print(f"  FAIL {name}: downloaded {len(raw)} B, index says {meta['size']} B")
                continue
            dest.write_bytes(raw)
        with rasterio.open(dest) as s:
            if (s.width, s.height) != (grid.width, grid.height):
                print(f"  FAIL {name}: grid {s.width}x{s.height}")
                continue
            a = np.nan_to_num(s.read(1), nan=0.0)
        n_pos = int((a > 0).sum())
        if n_pos != meta["n_pos"]:
            print(f"  NOTE {name}: n_pos {n_pos} != index {meta['n_pos']}")
        ok += 1
        print(f"  ok   {name[:70]:70s} n_pos={n_pos}")
    print(f"registry materialised: {ok}/{len(index)} rasters in {OUT.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
