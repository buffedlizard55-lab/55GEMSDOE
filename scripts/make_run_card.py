#!/usr/bin/env python3
"""Retired fail-closed entry point. See README.md and docs/run-card.json."""
from __future__ import annotations


def main() -> None:
    raise SystemExit(
        "The old generator derives publication claims from invalid historical evidence; use the reviewed docs/run-card.json and scripts/make_runcard.py validator. No data were downloaded, no experiment was run, and no output was written."
    )


if __name__ == "__main__":
    main()
