#!/usr/bin/env python3
"""Compatibility wrapper for the canonical run-card exporter."""
from __future__ import annotations

import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
runpy.run_path(str(ROOT / "scripts" / "make_run_card.py"), run_name="__main__")
