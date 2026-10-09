#!/usr/bin/env python3
"""Retired analysis: the former catalogue-proxy DTI calculation was invalid.

The old script assumed TP_w + FP_w equals the number of predicted pixels and
used that identity to report proxy DTI values and infer hidden-label size. The
official metric defines TP_w and FP_w separately, so that shortcut is not valid.
Those historical JSON files are retained with a retraction notice. Do not rerun
or cite this experiment. For an actual score comparison, use the canonical
whole-segment holdout in ``scripts/evaluate_holdout.py``.
"""


def main() -> None:
    raise SystemExit(
        "RETRACTED: invalid TP_w + FP_w = prediction-mass shortcut. "
        "See docs/irregularities.md IR-55-034 and docs/leaderboard-analysis.md. "
        "Use scripts/evaluate_holdout.py for labeled HOLDOUT-DTI."
    )


if __name__ == "__main__":
    main()
