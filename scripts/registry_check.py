#!/usr/bin/env python3
"""Retired fail-closed entry point. See README.md and docs/run-card.json."""
from __future__ import annotations


def main() -> None:
    raise SystemExit(
        "This legacy checker duplicates uniqueness logic; use the fail-closed scripts/verify_unique.py only after the authorized registry is available. No data were downloaded, no experiment was run, and no output was written."
    )


if __name__ == "__main__":
    main()
