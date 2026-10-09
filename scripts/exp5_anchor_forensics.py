#!/usr/bin/env python3
"""Retired forensic script; it cannot produce score or target-size claims.

The former script mislabeled unreceipted rasters as organizer-confirmed, used a
false count-only DTI denominator, and called visible-catalogue matching a hidden
score proxy. Its derived records are withdrawn; see docs/irregularities.md.
"""
from __future__ import annotations


def main() -> None:
    raise SystemExit(
        "exp5_anchor_forensics.py is retired because its metric algebra and score "
        "attribution were invalid. No experiment or result was produced."
    )


if __name__ == "__main__":
    main()
