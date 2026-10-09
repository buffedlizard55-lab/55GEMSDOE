#!/usr/bin/env python3
"""Fail-closed structural and candidate-policy validator for GeoTIFF outputs.

Re-reads written bytes and compares against the canonical template/labels through
``src/gems55/io55.py``. This is a local validator, not an organizer portal receipt.
The documented null/NaN outside-footprint rule is enforced literally; zero-filled
inactive cells are not accepted as a cleared format encoding here.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems55 import io55  # noqa: E402


def validate(path: Path) -> tuple[bool, list[tuple[str, bool, str]]]:
    checks: list[tuple[str, bool, str]] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        checks.append((name, bool(ok), detail))

    if not path.is_file():
        ck("file exists", False, str(path))
        return False, checks

    try:
        grid, _template = io55.read_template()
        labels = io55.read_labels()
    except Exception as exc:
        ck("canonical organizer template and labels available", False, f"{type(exc).__name__}: {exc}")
        for name, ok, detail in checks:
            print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f" -- {detail}" if detail else ""))
        return False, checks

    try:
        with rasterio.open(path) as src:
            a = src.read(1)
            ck("single band", src.count == 1, f"count={src.count}")
            ck("float32", src.dtypes[0] == "float32", f"dtype={src.dtypes[0]}")
            ck("CRS matches canonical template", src.crs is not None and src.crs.to_epsg() == grid.crs,
               f"crs={src.crs}")
            ck("shape matches canonical template", (src.height, src.width) == grid.shape,
               f"shape={src.height}x{src.width} expected={grid.height}x{grid.width}")
            ck("transform matches canonical template", tuple(src.transform)[:6] == tuple(grid.transform)[:6],
               f"transform={tuple(src.transform)[:6]}")
            ck("resolution matches canonical template",
               np.allclose(src.res, (io55.RES_M, io55.RES_M), rtol=0.0, atol=1e-9),
               f"resolution={src.res} expected={(io55.RES_M, io55.RES_M)}")
            ck("null/NaN exactly outside template footprint",
               np.array_equal(np.isnan(a), ~grid.footprint),
               f"nan={int(np.isnan(a).sum())} expected={int((~grid.footprint).sum())}")
            inside = a[grid.footprint]
            ck("finite predictions throughout footprint", bool(np.isfinite(inside).all()),
               f"nonfinite_inside={int((~np.isfinite(inside)).sum())}")
            finite_inside = inside[np.isfinite(inside)]
            in_range = bool(finite_inside.size and finite_inside.min() >= 0.0 and finite_inside.max() <= 1.0)
            ck("finite footprint values in [0,1]", in_range,
               f"min={finite_inside.min() if finite_inside.size else 'NA'} max={finite_inside.max() if finite_inside.size else 'NA'}")
            positive = np.isfinite(a) & (a > 0.0)
            ck("positive predictions exist", bool(positive.any()), f"positive_cells={int(positive.sum())}")
            on_mapped = int((positive & (labels == 1)).sum())
            ck("no positive predictions on mapped catalogue pixels", on_mapped == 0,
               f"overlap={on_mapped}")
    except Exception as exc:
        ck("GeoTIFF is readable", False, f"{type(exc).__name__}: {exc}")

    for name, ok, detail in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f" -- {detail}" if detail else ""))
    return all(ok for _, ok, _ in checks), checks


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("tif", nargs="+", type=Path)
    args = ap.parse_args()
    results = [validate(path) for path in args.tif]
    all_ok = all(ok for ok, _ in results)
    print("\nRESULT:", "ALL LOCAL CHECKS PASSED" if all_ok else "NOT CLEARED — CHECKS FAILED OR CANONICAL DATA MISSING")
    print("This local check is not an organizer portal validation or score receipt.")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
