#!/usr/bin/env python3
"""Retired legacy runner; intentionally cannot generate or publish results.

The former implementation depended on the private ``gems`` evaluator/writer
fork and used a quadrant holdout. It is not promotion-grade and is retained only
as a historical result pointer. Use ``src/gems55`` tools after the authorized
shared-template, data, budget, and all clearance prerequisites are satisfied.
"""
from __future__ import annotations

import sys


def main() -> None:
    raise SystemExit(
        "run_tensor_lane.py is retired: it used a private evaluator/writer fork and invalid folds. "
        "No experiment or raster was produced. See docs/results.md and docs/run-card.json."
    )


if __name__ == "__main__":
    main()
