#!/usr/bin/env python3
"""Retired fail-closed status/run-card generator.

The old generator wrote ``download_allowed: true`` and described the H55 160k
artifact as an audit download despite a negative holdout and duplicate stop. The
reviewed, fail-closed cards are committed in ``docs/run-card.json`` and
``docs/status.json``. Do not regenerate them from the historical local evidence.
"""
from __future__ import annotations


def main() -> None:
    raise SystemExit(
        "Retired: historical H55 results are not promotion-grade and no download is cleared. "
        "No files were written; validate the reviewed card with scripts/make_runcard.py."
    )


if __name__ == "__main__":
    main()
