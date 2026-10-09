#!/usr/bin/env python3
"""Confirmatory prediction of the tensor-dimensionality lane.

The lane's stated test: *withheld faults' strikes should match the field's
strike more often than random ridges' do.*

Design (preregistered)
----------------------
Group A — withheld catalogue faults.  For every whole 8-connected catalogue
component assigned to a holdout fold and containing at least ``--min-px``
pixels:
  * ``seg_az``  principal-axis (total least squares) azimuth of the component's
    pixel coordinates, i.e. the strike a mapper drew;
  * ``ten_az``  circular median, over the component's own pixels, of the
    gradient-tensor intermediate-eigenvector azimuth;
  * ``delta``   smaller angle between the two, in [0, 90] degrees.

Group B — random ridges.  The lane's own detected ridge network (the pixels in
the top ``--ridge-pct`` percent of the corroborated ridge score) that lies at
least ``--clean-px`` pixels away from every mapped catalogue pixel.  Its
8-connected components with at least ``--min-px`` pixels are measured in exactly
the same way.  These are ridges a gradient detector really finds; they are the
correct comparison class because the lane's claim is not "ridges exist" but
"ridges that are faults are more strike-extended / more self-consistent than
ridges in general".

H1 (one-sided): the fraction of Group A with ``delta <= 20 deg`` exceeds the
same fraction in Group B.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from gems55 import holdout55, io55, tensor55  # noqa: E402
import evaluate_holdout as EH  # noqa: E402


def circular_median_az(az_deg: np.ndarray) -> float:
    """Median of an undirected (mod 180) azimuth set via doubled-angle vectors."""
    a = np.asarray(az_deg, dtype=np.float64) % 180.0
    th = np.deg2rad(2.0 * a)
    v = np.array([np.cos(th).mean(), np.sin(th).mean()])
    if np.linalg.norm(v) < 1e-12:
        return float("nan")
    return float(np.rad2deg(np.arctan2(v[1], v[0])) / 2.0 % 180.0)


def components(mask: np.ndarray, min_px: int) -> tuple[np.ndarray, int]:
    lab, n = ndimage.label(mask, structure=np.ones((3, 3), dtype=np.uint8))
    if n == 0:
        return lab, 0
    counts = np.bincount(lab.ravel(), minlength=n + 1)
    keep = np.zeros(n + 1, dtype=bool)
    keep[1:] = counts[1:] >= min_px
    lab = np.where(keep[lab], lab, 0)
    return lab, int(keep[1:].sum())


def component_deltas(lab: np.ndarray, n: int, strike: np.ndarray,
                     min_px: int) -> list[dict]:
    out = []
    ys, xs = np.nonzero(lab)
    if ys.size == 0:
        return out
    ids = lab[ys, xs]
    order = np.argsort(ids, kind="stable")
    ys, xs, ids = ys[order], xs[order], ids[order]
    bounds = np.searchsorted(ids, np.unique(ids))
    starts = bounds[:-1]
    ends = bounds[1:]
    for s, e in zip(starts, ends):
        cnt = e - s
        if cnt < min_px:
            continue
        y = ys[s:e].astype(np.float64)
        x = xs[s:e].astype(np.float64)
        c = np.stack([x - x.mean(), y - y.mean()], axis=1)
        cov = c.T @ c / cnt
        w, v = np.linalg.eigh(cov)
        pc = v[:, -1]
        seg_az = float(np.degrees(np.arctan2(pc[0], pc[1])) % 180.0)
        ten_az = circular_median_az(strike[ys[s:e], xs[s:e]])
        if not np.isfinite(ten_az):
            continue
        d = float(tensor55.angular_difference_deg(
            np.array([seg_az]), np.array([ten_az]))[0])
        out.append({"n_px": int(cnt), "seg_az": seg_az, "ten_az": ten_az,
                    "delta_deg": d, "elongation": float(np.sqrt(w[-1] / max(w[0], 1e-12)))})
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", type=Path, default=EH.CACHE)
    ap.add_argument("--n-folds", type=int, default=4)
    ap.add_argument("--buffer-px", type=int, default=3)
    ap.add_argument("--min-px", type=int, default=12)
    ap.add_argument("--ridge-pct", type=float, default=0.5)
    ap.add_argument("--clean-px", type=int, default=6)
    ap.add_argument("--tol-deg", type=float, default=20.0)
    ap.add_argument("--out", type=Path, default=ROOT / "evidence" / "strike_test55.json")
    args = ap.parse_args()

    grid, _ = io55.read_template()
    labels = io55.read_labels()
    footprint = np.asarray(grid.footprint, dtype=bool)
    C = EH.load_cache(args.cache)
    S = EH.build_arm_surfaces(C, footprint)
    valid = S["_valid"]
    strike = S["_strike"]

    folds = holdout55.make_segment_folds(labels, footprint, n_folds=args.n_folds,
                                         buffer_px=args.buffer_px)
    truth = np.zeros(footprint.shape, dtype=bool)
    for f in folds:
        truth |= f.truth

    # Group A: withheld catalogue fault components, pooled over folds.
    A = []
    labA, nA = components(truth, args.min_px)
    A = component_deltas(labA, nA, strike, args.min_px)

    # Group B: the lane's own ridge network, away from every mapped fault.
    ridge = S["ridge_only"]
    elig = valid & np.isfinite(ridge) & (ridge > 0)
    n = int(elig.sum())
    k = max(1, int(round(n * args.ridge_pct / 100.0)))
    thr = float(np.partition(ridge[elig], n - k)[n - k])
    net = elig & (ridge >= thr)
    clean = net & ~ndimage.binary_dilation(labels == 1, iterations=args.clean_px)
    labB, nB = components(clean, args.min_px)
    B = component_deltas(labB, nB, strike, args.min_px)

    def frac(rows, tol):
        return float(np.mean([r["delta_deg"] <= tol for r in rows])) if rows else float("nan")

    res = {
        "evidence_class": "HOLDOUT-PREDICTION-TEST",
        "test": "withheld fault segments agree in strike with the tensor field more often than random detected ridges do",
        "tol_deg": args.tol_deg,
        "min_px": args.min_px,
        "group_A_withheld_fault_components": {
            "n": len(A),
            "median_delta_deg": float(np.median([r["delta_deg"] for r in A])) if A else float("nan"),
            "mean_delta_deg": float(np.mean([r["delta_deg"] for r in A])) if A else float("nan"),
            "fraction_within_tol": frac(A, args.tol_deg),
        },
        "group_B_random_ridge_components": {
            "n": len(B),
            "ridge_pct": args.ridge_pct,
            "clean_px": args.clean_px,
            "median_delta_deg": float(np.median([r["delta_deg"] for r in B])) if B else float("nan"),
            "mean_delta_deg": float(np.mean([r["delta_deg"] for r in B])) if B else float("nan"),
            "fraction_within_tol": frac(B, args.tol_deg),
        },
    }
    fa, fb = frac(A, args.tol_deg), frac(B, args.tol_deg)
    # two-proportion z test (independent components; a rough yardstick, not a
    # spatial-block interval)
    if len(A) and len(B):
        p = (fa * len(A) + fb * len(B)) / (len(A) + len(B))
        se = np.sqrt(p * (1 - p) * (1 / len(A) + 1 / len(B)))
        z = (fa - fb) / se if se > 0 else float("nan")
    else:
        z = float("nan")
    res["difference_A_minus_B"] = float(fa - fb) if len(A) and len(B) else float("nan")
    res["two_proportion_z"] = float(z)
    res["verdict"] = ("SUPPORTED" if (fa - fb) > 0 and z > 1.96
                      else "NOT_SUPPORTED" if (fa - fb) <= 0 else "INCONCLUSIVE")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
