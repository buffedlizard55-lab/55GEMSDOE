#!/usr/bin/env python3
"""Retired legacy page generator; intentionally writes nothing.

The former generator could publish unreceipted leaderboard values as scored
outcomes, relied on withdrawn/invalid anchor-proxy DTI calculations, and had
unsafe success-oriented download/submit copy. Use ``scripts/build_site.py`` for
the current status pages. Its generated status is audit-only / DO NOT SUBMIT.
See ``docs/irregularities.md`` IR-55-051 and the corrected anchor page.
"""
from __future__ import annotations


def main() -> None:
    raise SystemExit(
        "build_pages55.py is retired: its score inferences and clearance copy are "
        "withdrawn. It wrote no files. Use scripts/build_site.py for the current "
        "H57 audit-only status."
    )


if __name__ == "__main__":
    main()
