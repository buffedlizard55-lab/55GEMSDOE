#!/usr/bin/env python3
"""Export the canonical current run card to the legacy evidence location.

The old quadrant-run assembler is intentionally retired. `docs/run-card.json`
is the single current run card; this compatibility command never invents scores.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    source = ROOT / "docs" / "run-card.json"
    target = ROOT / "evidence" / "runcard.json"
    card = json.loads(source.read_text())
    target.write_text(json.dumps(card, indent=2) + "\n")
    print(f"copied canonical run card to {target.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
