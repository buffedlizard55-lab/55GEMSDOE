#!/usr/bin/env python3
"""Verify data/ against the official contract and build the cached lane surface."""
from __future__ import annotations
import subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import rasterio
from gems55 import io55

def main() -> None:
    for f in (io55.TEMPLATE_TIF, io55.LABELS_TIF, io55.feature_path()):
        if not f.exists():
            sys.exit(f"missing {f}; run scripts/download_competition_data.sh first")
    grid, tmpl = io55.read_template()
    lab = io55.read_labels()
    with rasterio.open(io55.FEATURES_TIF) as s:
        assert s.count == 19 and set(s.dtypes) == {"float32"}
        assert (s.width, s.height) == (grid.width, grid.height)
        assert s.crs.to_epsg() == 32611
        assert tuple(s.transform)[:6] == tuple(grid.transform)[:6]
    assert lab.shape == grid.shape
    print(f"grid      {grid.width}x{grid.height} EPSG:{grid.crs} 100 m")
    print(f"footprint {int(grid.footprint.sum()):,} px   catalogue {int((lab==1).sum()):,} px")
    print("cache: scripts/build_lane.py --tag v1")
    subprocess.run([sys.executable, str(ROOT/"scripts"/"build_lane.py"), "--tag", "v1"], check=True)

if __name__ == "__main__":
    main()
