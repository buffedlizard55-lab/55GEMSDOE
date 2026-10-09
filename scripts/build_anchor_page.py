#!/usr/bin/env python3
"""Retired page generator; it used an invalid count-only DTI denominator.

The generated page attributed a score without an organizer receipt, called a
visible-catalogue proxy an estimate of hidden-set DTI, and converted it to a
hidden-truth-size projection. Those claims are withdrawn in docs/irregularities.md
and docs/leaderboard-analysis.html. This script intentionally writes nothing.
"""
from __future__ import annotations


def main() -> None:
    raise SystemExit(
        "build_anchor_page.py is retired: the old page used invalid metric algebra "
        "and unsupported score attribution. No page was generated. See "
        "docs/leaderboard-analysis.html and docs/run-card.json."
    )


if __name__ == "__main__":
    main()
