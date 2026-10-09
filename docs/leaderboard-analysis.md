# Leaderboard claims and the 0.2778 anchor

## Evidence class

The number `0.2778`, the named H33 entry, and higher values such as `0.3195` and
`0.3774` were supplied in the owner brief or sibling reports. The official
DrivenData leaderboard page was fetched during this review but returned only a
client-side loading state; no submission-page receipt was available. Therefore
these are **UNVERIFIED CLAIMS**, not **ORGANIZER-CONFIRMED** scores, and they are
not used as targets or as measurements in the run card.

The official problem page is the source for the metric contract:
<https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/>.
The organizer discussion says the leaderboard DTI is pooled over the relevant
pixels rather than a mean of per-chunk scores:
<https://community.drivendata.org/t/leaderboard-aggregation-pooled-over-public-test-pixels-or-mean-of-per-chunk-scores/11550>.

## What can be concluded locally

The official distance-weighted Tversky structure is:

```text
DTI = TP_w / (TP_w + 0.2 FP_w + 0.8 FN_w)
```

With a sparse unit-dot output, lower false-positive cost can make coverage more
important than density. That is a metric-algebra observation, not evidence that a
particular anchor or candidate will score on hidden new-fault labels. A local
fault-catalogue holdout is useful for comparing hypotheses, but it cannot convert
a user-supplied leaderboard number into an organizer receipt.

## Current H56 result

H56 multiscale tensor persistence scored **HOLDOUT-DTI 0.01728**, 95% CI
[0.01613, 0.01847], with 60,988 withheld positives. The current same-evaluator
one-scale ridge × strike-agreement comparator scored **HOLDOUT-DTI 0.01852**, 95%
CI [0.01782, 0.01940]. No `ORGANIZER-CONFIRMED` value exists in this repository.
See `docs/results.md`, `docs/run-card.json`, and the official links above.
