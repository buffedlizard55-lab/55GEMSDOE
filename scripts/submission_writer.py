#!/usr/bin/env python3
"""Retired fail-closed entry point. See README.md and docs/run-card.json."""
from __future__ import annotations


def main() -> None:
    raise SystemExit(
        "No experiment budget, holdout clearance, uniqueness pass, or format approval exists; no raster or archive may be generated for download/submission. No data were downloaded, no experiment was run, and no output was written."
    )


if __name__ == "__main__":
    main()
