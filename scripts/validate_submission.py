#!/usr/bin/env python3
"""Independent submission validator.  Re-reads the written bytes from disk.

Nothing here trusts the writer: the file is opened with rasterio and every claim
is measured.  Exit code 0 = every check passed.
"""

from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems55 import io55  # noqa: E402

CHECKS: list[tuple[str, bool, str]] = []


def ck(name: str, ok: bool, detail: str = "") -> bool:
    CHECKS.append((name, bool(ok), detail))
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f" -- {detail}" if detail else ""))
    return bool(ok)


def validate(path: Path, *, outside: str, template_path: Path, labels_path: Path) -> bool:
    print(f"\n== validating {path.name} (outside='{outside}') ==")
    CHECKS.clear()
    grid, _ = io55.read_template(template_path)
    with rasterio.open(path) as src:
        a = src.read(1)
        nband, dt = src.count, src.dtypes[0]
        crs = src.crs
        tr = tuple(src.transform)[:6]
        h, w = src.height, src.width
        nodata = src.nodata
    ck("single band", nband == 1, f"count={nband}")
    ck("dtype float32", dt == "float32", f"dtype={dt}")
    ck("CRS is EPSG:32611", crs is not None and crs.to_epsg() == 32611, f"crs={crs}")
    ck("shape matches template", (h, w) == (grid.height, grid.width), f"{h}x{w}")
    ck("geotransform matches template", tr == tuple(grid.transform)[:6], f"{tr}")
    # pixel size is read from the transform (a, e), not inferred from the shape (IR-55-025 fix)
    px_ok = abs(tr[0]) == 100.0 and abs(tr[4]) == 100.0 and tr[1] == 0.0 and tr[3] == 0.0
    ck("resolution is 100 m", px_ok, f"a={tr[0]} e={tr[4]} b={tr[1]} d={tr[3]}")
    finite = a[np.isfinite(a)]
    ck("all finite values in [0,1]", finite.size and finite.min() >= 0.0 and finite.max() <= 1.0,
       f"min={finite.min() if finite.size else 'NA'} max={finite.max() if finite.size else 'NA'}")
    if outside == "zeros":
        ck("no NaN anywhere (all-finite encoding)", np.isfinite(a).all(),
           f"nan={int(np.isnan(a).sum())}")
        ck("outside footprint is exactly 0", bool(np.all(a[~grid.footprint] == 0.0)))
    else:
        ck("NaN exactly outside the footprint", np.array_equal(np.isnan(a), ~grid.footprint),
           f"nan={int(np.isnan(a).sum())} expected={int((~grid.footprint).sum())}")
    ck("inside footprint has no NaN", np.isfinite(a[grid.footprint]).all(),
       f"nan_inside={int(np.isnan(a[grid.footprint]).sum())}")
    pos = int((a > 0).sum())
    ck("positive predictions exist", pos > 0, f"n_positive={pos}")
    lab = io55.read_labels(labels_path)
    ck("no positive on a mapped catalogue pixel", int(((a > 0) & (lab == 1)).sum()) == 0,
       f"on_catalogue={int(((a > 0) & (lab == 1)).sum())}")
    return all(ok for _, ok, _ in CHECKS)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("tif", nargs="+")
    ap.add_argument("--template", type=Path, default=io55.TEMPLATE_TIF,
                    help="official sample_submission.tif used for exact grid/footprint checks")
    ap.add_argument("--labels", type=Path, default=io55.LABELS_TIF,
                    help="official labels.tif used to check that no dot lies on a mapped catalogue pixel")
    args = ap.parse_args()

    missing = [p for p in (args.template, args.labels) if not p.exists()]
    if missing:
        print("BLOCKED: full submission validation needs the official template and labels:", file=sys.stderr)
        for p in missing:
            print(f"  MISSING {p}", file=sys.stderr)
        print("Place authorized competition files under data/ (see data/README.md), then rerun.", file=sys.stderr)
        raise SystemExit(2)

    allok = True
    for t in args.tif:
        p = Path(t)
        if not p.exists():
            print(f"MISSING {p}")
            allok = False
            continue
        outside = "nan" if "nan" in p.name else "zeros"
        allok &= validate(p, outside=outside, template_path=args.template, labels_path=args.labels)
    print("\nRESULT:", "ALL CHECKS PASSED" if allok else "FAILURES PRESENT")
    sys.exit(0 if allok else 1)


if __name__ == "__main__":
    main()
