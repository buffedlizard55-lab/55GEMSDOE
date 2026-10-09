#!/usr/bin/env python3
"""Experiment 1 (evaluation): leakage canaries + whole-segment holdout + strike test.

Protocol (lane brief):
  * holdout = hide-and-recover: withhold WHOLE 8-connected fault components with
    a buffer collar; the candidate surface is label-free by construction
    (bands 2 + 13 only), so no per-fold refit is needed or allowed; visible
    catalogue pixels are masked pixel-exactly from the emission domain;
  * pooled DTI (alpha=0.2, beta=0.8, 300 m triangular kernel) over all folds;
  * 95% CI = percentile bootstrap over 10 km spatial blocks of the pooled
    additive TP/FP/FN contribution maps (pooled-score contribution uncertainty);
  * leakage canary: every product alone vs the labels; AUC > 0.90 = leakage;
  * strike test: withheld faults' strikes should match the tensor strike more
    often than random locations match their local ridge orientation.

BUFFER SIZING (IR-55-044): the emission domain excludes the withheld truth
plus a ``--buffer-px`` collar.  The kernel credit radius is 3 px, so a 3 px
collar makes TP_w identically zero for every candidate (the historical
"buffer=3" records were vacuous).  The default is 1 px: the candidate may not
emit on the hidden fault or its immediate 1-px halo, but near-miss credit
(offsets at distance >= sqrt(2)) is still possible.  ``--buffer-px 0`` is the
unbiased real-scenario estimate (the real submission cannot exclude the hidden
faults' locations); both are reported, policy selection uses the pooled proxy
(see eval_proxy.py) with this holdout as confirmation.

Every score-like number is labeled HOLDOUT-DTI with the evaluator version and
the withheld-positive count.  The evaluator is a local transcription
(``gems55.dti55/2.0-local``), regression-tested against a brute-force
reference; it is not an organizer receipt.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gems55 import dti55, holdout55, io55, tensor55  # noqa: E402
from policies import POLICIES, build_emission  # noqa: E402

EVID = ROOT / "evidence"
OUT = ROOT / "outputs"
EVALUATOR = dti55.EVALUATOR_VERSION


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-folds", type=int, default=4)
    ap.add_argument("--buffer-px", type=int, default=1,
                    help="collar around withheld truth excluded from emission "
                         "(must be < 3: the kernel credit radius is 3 px)")
    ap.add_argument("--policies", type=str, default=None,
                    help="comma-separated policy names to evaluate (default: all)")
    ap.add_argument("--out", type=Path, default=EVID / "holdout_tensor_lane_e1.json")
    args = ap.parse_args()
    if args.buffer_px >= 3:
        raise SystemExit("buffer-px must be < 3 (kernel credit radius is 3 px; "
                         "a 3 px collar makes TP_w identically zero)")

    t_start = time.time()
    z = np.load(OUT / "surface.npz")
    grid, _ = io55.read_template()
    footprint = grid.footprint
    labels = io55.read_labels()
    cat = labels == 1
    score = z["score"]

    policies = POLICIES
    if args.policies:
        wanted = {s.strip() for s in args.policies.split(",") if s.strip()}
        policies = [p for p in POLICIES if p["name"] in wanted]
        if not policies:
            raise SystemExit(f"no matching policies in {sorted(wanted)}")

    # ------------------------------------------------------------------ #
    # Leakage canary: each product alone vs the catalogue labels.
    # ------------------------------------------------------------------ #
    print("[canary] per-product AUC vs catalogue labels (leakage limit 0.90)", flush=True)
    canary = {}
    y_full = cat[footprint]
    for key in ("score", "ridge", "ridge_mag", "ridge_grav", "dim", "dim_inv", "dim_eig",
                "agree", "plunge", "dtheta", "coh_x", "coh_y"):
        a = float(holdout55.auc(z[key][footprint], y_full))
        canary[key] = a
        flag = "LEAKAGE" if a > 0.90 else "ok"
        print(f"  {key:<10} AUC={a:.4f}  {flag}", flush=True)

    # ------------------------------------------------------------------ #
    # Whole-segment hide-and-recover folds.
    # ------------------------------------------------------------------ #
    folds = holdout55.make_segment_folds(labels, footprint, n_folds=args.n_folds,
                                         buffer_px=args.buffer_px)
    total_withheld = int(sum(int(f.truth.sum()) for f in folds))
    print(f"[holdout] {len(folds)} whole-segment folds, buffer={args.buffer_px}px, "
          f"withheld positives={total_withheld}", flush=True)

    # ------------------------------------------------------------------ #
    # Emission policies x folds -> pooled DTI + block-bootstrap CI.
    # ------------------------------------------------------------------ #
    pooled = {p["name"]: {"tp_w": 0.0, "fp_w": 0.0, "fn_w": 0.0, "n_truth": 0,
                          "tp_map": np.zeros(grid.shape, np.float32),
                          "fp_map": np.zeros(grid.shape, np.float32),
                          "fn_map": np.zeros(grid.shape, np.float32),
                          "folds": []}
              for p in policies}
    # matched uniform random control at the median emitted mass of the binary policies
    rng = np.random.default_rng(12345)
    for fold in folds:
        elig = footprint & ~cat & ~fold.withheld  # pixel-exact visible mask + hidden truth+collar
        print(f"[holdout] fold {fold.name}: truth={int(fold.truth.sum())} "
              f"eligible={int(elig.sum())}", flush=True)
        # random control sized to the top10pct policy's emitted mass on this fold
        probe_pol = next((p for p in policies if p["kind"] == "top_pct" and p["pct"] == 10),
                         next((p for p in policies if p["kind"] == "top_pct"), policies[0]))
        probe = build_emission(score, elig, probe_pol)
        n_rand = int((probe > 0).sum())
        if "random_matched_mass" not in pooled:
            pooled["random_matched_mass"] = {"tp_w": 0.0, "fp_w": 0.0, "fn_w": 0.0,
                                             "n_truth": 0,
                                             "tp_map": np.zeros(grid.shape, np.float32),
                                             "fp_map": np.zeros(grid.shape, np.float32),
                                             "fn_map": np.zeros(grid.shape, np.float32),
                                             "folds": []}
        # Build each arm's prediction lazily: holding every arm's full-grid
        # float64 raster at once would exhaust the sandbox memory budget.
        for pol in policies:
            pred = build_emission(score, elig, pol)
            t0 = time.time()
            name = pol["name"]
            r = dti55.dti(pred, fold.truth)
            tp_m, fp_m, fn_m = dti55.weighted_contribution_maps(pred, fold.truth)
            p = pooled[name]
            p["tp_w"] += r.tp_w
            p["fp_w"] += r.fp_w
            p["fn_w"] += r.fn_w
            p["n_truth"] += r.n_truth
            p["tp_map"] += tp_m
            p["fp_map"] += fp_m
            p["fn_map"] += fn_m
            p["folds"].append({"fold": fold.name, "dti": r.dti,
                               "tp_w": r.tp_w, "fp_w": r.fp_w, "fn_w": r.fn_w,
                               "n_pred_pos": r.n_pred_pos})
            print(f"  {name:<18} DTI={r.dti:.6f} tp={r.tp_w:.1f} fp={r.fp_w:.1f} "
                  f"fn={r.fn_w:.1f} pos={r.n_pred_pos} ({time.time()-t0:.1f}s)", flush=True)
            del pred, tp_m, fp_m, fn_m
        # matched-mass uniform random control (built once, evaluated once)
        rand_dots = holdout55.emit_dots(score, elig, n_rand, random=True, seed=12345)
        rand_pred = rand_dots.astype(np.float64)
        r = dti55.dti(rand_pred, fold.truth)
        tp_m, fp_m, fn_m = dti55.weighted_contribution_maps(rand_pred, fold.truth)
        p = pooled["random_matched_mass"]
        p["tp_w"] += r.tp_w
        p["fp_w"] += r.fp_w
        p["fn_w"] += r.fn_w
        p["n_truth"] += r.n_truth
        p["tp_map"] += tp_m
        p["fp_map"] += fp_m
        p["fn_map"] += fn_m
        p["folds"].append({"fold": fold.name, "dti": r.dti,
                           "tp_w": r.tp_w, "fp_w": r.fp_w, "fn_w": r.fn_w,
                           "n_pred_pos": r.n_pred_pos})
        print(f"  {'random_matched_mass':<18} DTI={r.dti:.6f} tp={r.tp_w:.1f} "
              f"fp={r.fp_w:.1f} fn={r.fn_w:.1f} pos={r.n_pred_pos}", flush=True)
        del rand_dots, rand_pred, tp_m, fp_m, fn_m

    results = {}
    for name, p in pooled.items():
        dti_val = dti55.dti_from_totals(p["tp_w"], p["fp_w"], p["fn_w"])
        ci = dti55.block_bootstrap_ci(p["tp_map"], p["fp_map"], p["fn_map"],
                                      block_px=100, n_boot=2000, seed=0)
        results[name] = {
            "pooled_dti": dti_val,
            "ci95": ci["ci95"],
            "ci_method": ci["method"] + f" (block={ci['block_px']}px, n_blocks={ci['n_blocks']}, B={ci['n_boot']})",
            "tp_w": p["tp_w"], "fp_w": p["fp_w"], "fn_w": p["fn_w"],
            "n_truth": p["n_truth"],
            "per_fold": p["folds"],
        }
        print(f"[pooled] {name:<18} HOLDOUT-DTI={dti_val:.6f}  "
              f"95%CI=[{ci['ci95'][0]:.6f}, {ci['ci95'][1]:.6f}]", flush=True)

    # ------------------------------------------------------------------ #
    # Strike test: withheld fault strikes vs tensor strike, against random.
    # ------------------------------------------------------------------ #
    print("[strike] withheld-fault strike agreement vs random control", flush=True)
    strike_rows = []
    rng2 = np.random.default_rng(7)
    for fold in folds:
        comps = holdout55.strike_of_segments(fold.truth, min_px=25)
        if not comps:
            continue
        lab, n = ndimage.label(fold.truth, structure=np.ones((3, 3), np.uint8))
        ys, xs = np.nonzero(fold.truth)
        ids = lab[ys, xs]
        comp_az = {c["id"]: c["azimuth_deg"] for c in comps}
        strike_t = z["strike"][ys, xs]          # tensor strike at truth pixels
        ridge_t = z["ridge_az"][ys, xs]         # local ridge azimuth at truth pixels
        d_fault = np.full(ys.size, 90.0, dtype=np.float32)
        for cid, az in comp_az.items():
            sel = ids == cid
            d_fault[sel] = tensor55.angular_difference_deg(
                strike_t[sel], np.full(int(sel.sum()), az))
        a = float((d_fault < 20.0).mean())
        c_agr = float((tensor55.angular_difference_deg(strike_t, ridge_t) < 20.0).mean())
        elig = footprint & ~cat & ~fold.withheld
        idx = np.nonzero(elig.ravel())[0]
        take = rng2.choice(idx, size=min(200_000, idx.size), replace=False)
        yy, xx = np.unravel_index(take, footprint.shape)
        b = float((tensor55.angular_difference_deg(
            z["strike"][yy, xx], z["ridge_az"][yy, xx]) < 20.0).mean())
        strike_rows.append({
            "fold": fold.name,
            "n_components_ge25px": len(comps),
            "n_truth_px": int(fold.truth.sum()),
            "frac_withheld_px_strike_match<20deg": a,
            "frac_withheld_px_ridge_az_match<20deg": c_agr,
            "frac_random_px_ridge_az_match<20deg": b,
        })
        print(f"  {fold.name}: withheld-strike match={a:.3f}  "
              f"random-ridge match={b:.3f}  (withheld ridge-az match={c_agr:.3f})", flush=True)

    # ------------------------------------------------------------------ #
    # Assemble the evidence record.
    # ------------------------------------------------------------------ #
    record = {
        "evidence_class": "HOLDOUT-DTI",
        "experiment": "E1 tensor-dimensionality lane: label-free surface + emission-policy holdout",
        "evaluator_version": EVALUATOR,
        "evaluator_note": "repository-local transcription, regression-tested vs brute force; not the organizer executable",
        "metric": {"alpha": dti55.ALPHA, "beta": dti55.BETA,
                   "kernel": "triangular", "kernel_radius_m": 300.0, "kernel_radius_px": dti55.R_PX},
        "holdout_protocol": {
            "design": "whole 8-connected component hide-and-recover",
            "n_folds": len(folds),
            "buffer_px": args.buffer_px,
            "buffer_note": "collar around withheld truth excluded from emission; must be < 3 px (kernel radius)",
            "visible_catalogue_masking": "pixel-exact (all catalogue pixels excluded from emission)",
            "surface_refit_per_fold": "none (surface is label-free by construction: bands 2+13 only)",
            "pooling": "TP_w/FP_w/FN_w summed across folds before the ratio",
        },
        "withheld_positive_count": total_withheld,
        "catalogue_positive_count": int(cat.sum()),
        "leakage_canary": {
            "limit": 0.90,
            "auc_vs_catalogue_by_product": canary,
            "verdict": "LEAKAGE" if any(v > 0.90 for v in canary.values()) else "PASS_NO_LEAKAGE",
        },
        "arms": results,
        "strike_test": {
            "claim": "withheld faults' strikes match the tensor eigenvector strike more often than random locations match their local ridge orientation",
            "rows": strike_rows,
        },
        "elapsed_s": round(time.time() - t_start, 1),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(record, indent=2) + "\n")
    print(f"\nwrote {args.out} ({time.time()-t_start:.0f}s total)", flush=True)

    print("\n=== HOLDOUT-DTI summary (evaluator %s, %d withheld positives, buffer=%dpx) ==="
          % (EVALUATOR, total_withheld, args.buffer_px))
    for name in sorted(results, key=lambda n: -results[n]["pooled_dti"]):
        r = results[name]
        print(f"  {name:<18} {r['pooled_dti']:.6f}  CI95=[{r['ci95'][0]:.6f}, {r['ci95'][1]:.6f}]")


if __name__ == "__main__":
    main()
