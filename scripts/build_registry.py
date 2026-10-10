#!/usr/bin/env python3
"""Retired fail-closed entry point. See README.md and docs/run-card.json."""
from __future__ import annotations


def main() -> None:
    raise SystemExit(
        "This downloader used owner-maintained mirrors without established provenance/legal approval; do not download a registry corpus here. No data were downloaded, no experiment was run, and no output was written."
    )


if __name__ == "__main__":
    main()
