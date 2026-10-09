#!/usr/bin/env python3
"""Retired analysis: prior catalogue-proxy DTI outputs are retracted.

The former final forensic script used TP_w + FN_w = |G| correctly, then made the
unsupported substitution TP_w + FP_w = N. That is not an identity of the official
metric and invalidates its proxy-DTI values, score thresholds, and inferred
hidden-label size. The historical JSON is preserved with an explicit retraction
notice. The public leaderboard snapshot is recorded separately and cannot map a
participant score to a raster filename. Use scripts/evaluate_holdout.py for
HOLDOUT-DTI; never use this script for score claims.
"""


def main() -> None:
    raise SystemExit(
        "RETRACTED: invalid prediction-mass algebra; no leaderboard-to-raster "
        "mapping exists. See docs/irregularities.md IR-55-034 and "
        "docs/leaderboard-analysis.md."
    )


if __name__ == "__main__":
    main()
