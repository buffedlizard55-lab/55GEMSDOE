#!/usr/bin/env python3
"""Export the exact continuous surface that submission_writer.py will place dots on.

Used for the protocol's pre-placement registry check.  The composition is shared
with the holdout evaluator and final writer (src/gems55/surfaces55.py).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems55 import io55, surfaces55  # noqa: E402

CACHE = ROOT / "data" / "cache"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="baseline")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--flank-support-px", type=float, default=0.0)
    ap.add_argument("--un-eroded", action="store_true")
    args = ap.parse_args()

    grid, _ = io55.read_template()
    labels = io55.read_labels()
    z = np.load(CACHE / f"lane_{args.tag}.npz")
    surf = surfaces55.tensor_surface(
        cached_score=z["score"], ridge=z["ridge"], dimensionality=z["dim"],
        strike_agreement=z["agree"], plunge_weight=z["plunge"],
        striping=z["striping"], footprint=z["footprint"], catalogue=(labels == 1),
        flank_support_px=args.flank_support_px, un_eroded=args.un_eroded,
    )
    if not np.array_equal(z["footprint"], grid.footprint):
        raise SystemExit("cached footprint differs from the official template")
    z.close()
    io55.write_submission(surf, args.out, grid, outside="zeros")
    print(f"wrote {args.out}; positive/eligible surface px={(surf > 0).sum():,}; "
          f"un_eroded={args.un_eroded}; flank_support_px={args.flank_support_px}")


if __name__ == "__main__":
    main()
