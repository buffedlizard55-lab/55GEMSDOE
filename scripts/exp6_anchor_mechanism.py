#!/usr/bin/env python3
"""Retired analysis: prior catalogue-proxy DTI outputs are retracted.

This one-off script inherited the invalid TP_w + FP_w = prediction-mass
shortcut from exp5. Its old numerical DTI claims must not be used to explain the
public leaderboard or promote a raster. The repository has no competition data
in the current checkout, and this script is intentionally fail-closed. Use the
canonical segment holdout and its per-feature leakage canary instead.
"""


def main() -> None:
    raise SystemExit(
        "RETRACTED: this script's proxy-DTI analysis is invalid. "
        "See docs/irregularities.md IR-55-034 and docs/leaderboard-analysis.md."
    )


if __name__ == "__main__":
    main()
