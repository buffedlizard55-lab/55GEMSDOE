#!/usr/bin/env python3
"""Retired fail-closed historical-page generator.

The previous generator published direct links to uncleared audit rasters and
reported them as downloadable. The curated historical audit is
``docs/h55-160k-audit.html``; artifacts remain outside ``docs/``. This entry point
must not regenerate a download CTA.
"""
from __future__ import annotations


def main() -> None:
    raise SystemExit(
        "Retired: historical TIFF/ZIP artifacts are not cleared and must not be linked. "
        "No page was written; see docs/h55-160k-audit.html."
    )


if __name__ == "__main__":
    main()
