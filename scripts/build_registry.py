#!/usr/bin/env python3
"""Download prior scored GEMSDOE rasters from GitHub and check lane uniqueness.

Prior rasters are used ONLY as an educational / control reference for the
uniqueness test required by the run brief (rank correlation < 0.90 and < 70% of
our dots within 3 px of any one registry raster).  No pixel of any prior raster
is copied into this project's deliverable.
"""
from __future__ import annotations
import json, subprocess, sys, re
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems55 import io55  # noqa: E402

TREES = Path("/tmp/trees")
OUT = ROOT / "registry" / "rasters"
OUT.mkdir(parents=True, exist_ok=True)

SCORED_KEYS = [
 "h33-2-b2","7f00890a","hgb88-topk03","pindrop-v4","dual-family-union","237f0063",
 "lidarscarp-ridge-top2pct","Hedge-v2","2314b599","structural-area06","r7-nms3-dem10",
 "conj_alteration_mag","geom-horse-ensemble","F-ensemble-2pct","H19-C","h19-4","h19-5",
 "h16-continuation","h20-dem10","ctx-ridge","h28-dotted","r13-lattice","h16-1-topo",
 "h18-3a","h18-4-usgs","h20-1-sarnnpu","h20-5-continuous","h23-a-dti","h23-b-dti",
 "h30-arrangement","dotted-h19-5-d1-5","dotted-h19-5-d2-8","dilcond-oof","topo-gap-closure",
 "poisson300m-offcat","h27-4-solo-d28","analog-tip-stepover","h34-scatter","h35-06",
 "anderson-geothermal-pinn","h6-physics-dotted-80k","D-step-3p0","xscale-worm",
 "sup01-hgb21","h51-km-faultzone","gate_ortho","h27-4-r1-solo","h32-1-prethin",
 "h36-1-rung30","h38-1-hf-euler","efd28-repro","wormrank-d28","r11f-scarp-radiometric",
 "h59-cover-ds-belief","h46-twostageAB","h8-tiprelay","h54c-manifest-edge","h52-coincidence",
]

def gh(*a):
    return subprocess.run(["gh", *a], capture_output=True, text=True).stdout

# build an index: repo -> path -> (sha, size)
index = []
for f in sorted(TREES.glob("*.tsv")):
    repo = f.stem
    for line in f.read_text().splitlines():
        parts = line.split("\t")
        if len(parts) != 2:
            continue
        size, path = parts
        if not path.lower().endswith(".tif"):
            continue
        try:
            sz = int(size)
        except ValueError:
            continue
        if sz > 20_000_000 or sz < 50_000:
            continue
        base = Path(path).name
        for k in SCORED_KEYS:
            if k.lower() in base.lower():
                index.append((repo, path, sz, base, k))
                break

seen = {}
for repo, path, sz, base, k in index:
    seen.setdefault(k, (repo, path, sz, base))
print(f"{len(seen)} distinct scored entries locatable on GitHub", flush=True)

grid, _ = io55.read_template()
meta = {}
for k, (repo, path, sz, base) in sorted(seen.items()):
    dest = OUT / f"{repo}__{base}"
    if not dest.exists():
        sha = json.loads(gh("api", f"repos/buffedlizard55-lab/{repo}/contents/{path}"))["sha"]
        raw = subprocess.run(
            ["gh", "api", f"repos/buffedlizard55-lab/{repo}/git/blobs/{sha}",
             "-H", "Accept: application/vnd.github.raw"], capture_output=True)
        if raw.returncode != 0 or len(raw.stdout) != sz:
            print(f"  SKIP {repo}/{path} (download {len(raw.stdout)} != {sz})", flush=True)
            continue
        dest.write_bytes(raw.stdout)
    try:
        import rasterio
        with rasterio.open(dest) as s:
            if (s.width, s.height) != (grid.width, grid.height):
                print(f"  SKIP {dest.name} shape {s.width}x{s.height}", flush=True); continue
            a = s.read(1)
    except Exception as e:
        print(f"  SKIP {dest.name} {e}", flush=True); continue
    meta[dest.name] = {
        "repo": repo, "path": path, "scored_key": k, "size": sz,
        "n_pos": int((np.nan_to_num(a, nan=0.0) > 0).sum()),
        "dtype": str(a.dtype),
    }
    print(f"  ok {dest.name:70s} n_pos={meta[dest.name]['n_pos']:7d}", flush=True)

(ROOT / "registry" / "registry.json").write_text(json.dumps(meta, indent=2))
print("wrote registry with", len(meta), "rasters")
