#!/usr/bin/env python3
"""Retired fail-closed entry point. See README.md and docs/run-card.json."""
from __future__ import annotations


def main() -> None:
    raise SystemExit(
        "The static pages are curated from reviewed evidence; the old generator used a mismatched data filename and can overwrite governed Markdown. No data were downloaded, no experiment was run, and no output was written."
    )


if __name__ == "__main__":
    main()
