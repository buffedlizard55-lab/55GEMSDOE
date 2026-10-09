#!/usr/bin/env python3
"""Validate canonical competition files in ``data/`` without network access.

Expected names and grid constants come from ``src/gems55/io55.py``. The SHA-256
pins are copied from the owner-maintained sibling mirror manifest; they are useful
for byte-integrity checks but are NOT organizer-authenticated provenance. See
``data/SOURCES.md``. Do not fetch the mirror automatically from this script.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems55 import io55  # noqa: E402

# Canonical io55 filenames. These SHA-256 values are sibling-mirror pins, not
# independent proof that a file came from the organizer.
PINS = {
    io55.FEATURES_TIF.name: "4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5",
    io55.LABELS_TIF.name: "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093",
    io55.TEMPLATE_TIF.name: "2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _same_grid(src: rasterio.io.DatasetReader) -> bool:
    return (
        (src.width, src.height) == (io55.WIDTH, io55.HEIGHT)
        and src.crs is not None
        and src.crs.to_epsg() == io55.CRS_EPSG
        and tuple(src.transform)[:6] == tuple(io55.TRANSFORM)[:6]
        and np.allclose(src.res, (io55.RES_M, io55.RES_M), rtol=0.0, atol=1e-9)
    )


def validate() -> bool:
    ok = True
    paths = {
        io55.FEATURES_TIF.name: io55.FEATURES_TIF,
        io55.LABELS_TIF.name: io55.LABELS_TIF,
        io55.TEMPLATE_TIF.name: io55.TEMPLATE_TIF,
    }
    for name, path in paths.items():
        if not path.is_file():
            print(f"MISSING  {path}")
            ok = False
            continue

        digest = sha256_file(path)
        hash_ok = digest == PINS[name]
        try:
            with rasterio.open(path) as src:
                grid_ok = _same_grid(src)
                if name == io55.FEATURES_TIF.name:
                    content_ok = src.count == 19 and all(dt == "float32" for dt in src.dtypes)
                    detail = f"bands={src.count} dtypes={src.dtypes}"
                else:
                    content_ok = src.count == 1
                    detail = f"bands={src.count} dtype={src.dtypes[0]} nodata={src.nodata}"
        except Exception as exc:  # unreadable raster is a hard failure
            print(f"INVALID  {path}: {type(exc).__name__}: {exc}")
            ok = False
            continue

        file_ok = hash_ok and grid_ok and content_ok
        ok &= file_ok
        print(
            f"{'OK      ' if file_ok else 'FAIL    '} {path} "
            f"sha256={digest} pin_match={hash_ok} grid_match={grid_ok} "
            f"content_match={content_ok} {detail}"
        )
    if ok:
        print("All canonical files match the local grid contract and current SHA-256 pins.")
        print("Reminder: the pins are sibling-mirror hashes, not organizer provenance.")
    else:
        print("Preparation blocked: retrieve authorized files from the official data page, then resolve missing/mismatched checks.")
    return ok


def main() -> None:
    sys.exit(0 if validate() else 1)


if __name__ == "__main__":
    main()
