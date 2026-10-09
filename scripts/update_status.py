#!/usr/bin/env python3
"""Retired fail-closed entry point. See README.md and docs/run-card.json."""
from __future__ import annotations


def main() -> None:
    raise SystemExit(
        "Status cannot be promoted from local historical evidence; this script previously wrote unsafe download/submit claims. No data were downloaded, no experiment was run, and no output was written."
    )


if __name__ == "__main__":
    main()
