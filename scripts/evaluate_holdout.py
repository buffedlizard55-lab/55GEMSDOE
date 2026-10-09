#!/usr/bin/env python3
"""Retired fail-closed entry point. See README.md and docs/run-card.json."""
from __future__ import annotations


def main() -> None:
    raise SystemExit(
        "No experiment is authorized: the recorded budget is exhausted and the authorized shared evaluator/feature cache is not present. The former local driver is retired; no result was generated. No data were downloaded, no experiment was run, and no output was written."
    )


if __name__ == "__main__":
    main()
