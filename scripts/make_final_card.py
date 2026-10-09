#!/usr/bin/env python3
"""Retired H55 run-card generator.

The historical H55 summary was reviewed and its score metadata corrected from
stored per-fold evidence. This legacy generator predates those corrections, emits
unqualified secondary DTI values, and also attempts a full template/labels
validator run. Do not use it to overwrite the reviewed audit card. The original
measured artifacts remain under evidence/; the current checkout lacks the inputs
needed for a fresh validator, holdout, or uniqueness pass.
"""

from __future__ import annotations

import sys


def main() -> None:
    print(
        "BLOCKED: scripts/make_final_card.py is retired. It predates the reviewed "
        "H55 HOLDOUT-DTI/CI metadata and must not overwrite docs/run-card-h55-160k.json. "
        "See the checked-in card and evidence/exp9_distance_band_v1_n40000.json, "
        "evidence/exp10_mass_sweep_v1.json. No experiment was rerun.",
        file=sys.stderr,
    )
    raise SystemExit(2)


if __name__ == "__main__":
    main()
