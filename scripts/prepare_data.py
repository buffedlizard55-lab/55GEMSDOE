"""Check that the official rasters are in data/ and match the pinned sha256 (no network access).

Pins come from the sibling repo manifest (see data/SOURCES.md). A mismatch is an irregularity, not a silent pass.
"""
import sys
from pathlib import Path

import rasterio

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gems.submission import sha256_file  # noqa: E402

PINS = {
    # on-disk name is the competition's name (io55.FEATURES_TIF); the sibling-repo alias
    # training_features.tif carried the same pin (IR-55-026: naming mismatch, fixed once here)
    "gems-geodawn-numerical-features.tif": "4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5",
    "labels.tif": "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093",
    "sample_submission.tif": "2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc",
}


def main():
    ok = True
    for name, pin in PINS.items():
        p = Path("data") / name
        if not p.exists():
            print(f"MISSING  {p}")
            ok = False
            continue
        h = sha256_file(p)
        status = "OK      " if h == pin else "MISMATCH"
        ok &= h == pin
        with rasterio.open(p) as s:
            print(f"{status} {p} sha256={h[:12]}… shape={s.height}x{s.width} bands={s.count} crs={s.crs} res={s.res}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
