"""Tensor-dimensionality lane: 3 holdout experiments + canary + strike test + submission writer.

Usage (after placing official rasters in data/ -- see data/README.md):
    python scripts/run_tensor_lane.py --out docs/downloads/<name>.tif --tag <name>

Every number this script prints is labelled HOLDOUT-DTI (evaluator = gems.metric v1, withheld positives,
95% block-bootstrap CI). Nothing here is an organiser-confirmed score.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage
from scipy.stats import fisher_exact

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gems import holdout, metric, submission, tensor  # noqa: E402

EVALUATOR = "gems.metric v1 (DrivenData distance-weighted Tversky, alpha=0.2, beta=0.8, R=300 m)"
DATA = Path("data")


def band(path, idx):
    with rasterio.open(path) as s:
        a = s.read(idx).astype(np.float64)
        nd = s.nodata
    bad = ~np.isfinite(a) | (a < -1e38)
    if nd is not None and np.isfinite(nd):
        bad |= a == nd
    a[bad] = np.nan
    return a


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="outputs/tensor_lane.tif")
    ap.add_argument("--tag", default="tensor-lane")
    ap.add_argument("--results", default="docs/results/tensor_lane_results.json")
    ap.add_argument("--reps", type=int, default=1000)
    args = ap.parse_args()

    feat = DATA / "gems-geodawn-numerical-features.tif"  # IR-55-026
    labp = DATA / "labels.tif"
    tmpl = DATA / "sample_submission.tif"
    for p in (feat, labp, tmpl):
        if not p.exists():
            raise SystemExit(f"missing {p}: place the official rasters first (data/README.md)")

    footprint, meta = submission.read_template(tmpl)
    with rasterio.open(labp) as s:
        lab = s.read(1)
    catalogue = lab == 1
    assert np.array_equal(footprint, lab != -1), "footprint must equal label validity mask"

    # Band indices verified from the band tags (see docs/data_dictionary.md)
    rtp = band(feat, 2)      # 'rtp' reduced-to-pole magnetic
    iso = band(feat, 13)     # 'iso_grav_anom' isostatic gravity anomaly
    # The template footprint (= label validity mask) defines the scored domain. Feature bands carry
    # real values in a few cells outside it (irregularity, counted below); they are set to NaN here.
    feat_outside_data = {"rtp_band2": int((np.isfinite(rtp) & ~footprint).sum()),
                         "iso_band13": int((np.isfinite(iso) & ~footprint).sum())}
    rtp = np.where(footprint, rtp, np.nan)
    iso = np.where(footprint, iso, np.nan)
    # Inside the footprint a few cells are nodata too (irregularity, see docs/irregularities.md).
    gaps_rtp = int((footprint & ~np.isfinite(rtp)).sum())
    gaps_iso = int((footprint & ~np.isfinite(iso)).sum())

    H, W = footprint.shape
    res = {"generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
           "evaluator": EVALUATOR, "tag": args.tag, "grid": {"H": H, "W": W, "cell_m": 100},
           "feature_gaps_inside_footprint": {"rtp_band2": gaps_rtp, "iso_band13": gaps_iso},
           "feature_values_outside_footprint": feat_outside_data}

    # ---- 1. derivatives and tensors (FFT, low-passed, per-grid block) -------------------------
    p_rtp = tensor.fill_and_lowpass(rtp, footprint)
    Dr = tensor.derivatives(p_rtp, pseudogravity=False)           # RTP gradients (ridge detector)
    rm, az_r, G = tensor.ridges(Dr["gx"], Dr["gy"], footprint)
    Tm = tensor.derivatives(p_rtp, pseudogravity=True)            # pseudogravity tensor (magnetic)
    I_m, az_m, conf_m = tensor.dimensionality_and_strike(Tm)
    del Tm, Dr, p_rtp
    p_iso = tensor.fill_and_lowpass(iso, footprint)
    Tg = tensor.derivatives(p_iso, pseudogravity=False)           # isostatic gravity tensor
    I_g, az_g, conf_g = tensor.dimensionality_and_strike(Tg)
    del Tg, p_iso

    # ---- 2. E-W flight-line striping mask ----------------------------------------------------
    flagged_rows, zrow = tensor.stripe_rows(rtp, footprint)
    stripe_px = np.repeat(flagged_rows[:, None], W, axis=1) & footprint
    rm = rm & ~stripe_px
    res["striping"] = {"rows_flagged": int(flagged_rows.sum()), "rows_total": int(H),
                       "stripe_pixels_in_footprint": int(stripe_px.sum())}

    gn = np.minimum(G / max(np.percentile(G[footprint], 99), 1e-9), 1.0)
    rel = (conf_m >= 0.5) & (I_m <= 0.5)
    agree = tensor.angle_diff180(az_m, az_r) <= 22.5
    I_comb = 0.5 * (I_m + I_g)

    # Experiments ---------------------------------------------------------------------------
    p1 = np.where(rm, gn, 0.0)                                              # E1 ridge baseline
    p2 = p1 * (1.0 - I_m)                                                   # E2 + dimensionality
    gate = np.where(agree & (conf_m >= 0.5), 1.0, 0.2)                      # strike agreement gate
    p3 = p1 * (1.0 - I_comb) * gate                                         # E3 full lane
    preds = {"E1_ridge_baseline": p1, "E2_plus_dimensionality": p2, "E3_full_tensor_lane": p3}
    for k in preds:
        preds[k] = np.where(footprint, np.clip(preds[k], 0, 1), 0.0).astype(np.float32)

    # ---- 3. hide-and-recover holdout over catalogue segments ---------------------------------
    seg_lab, n_seg = holdout.segments(catalogue)
    cent = np.array(ndimage.center_of_mass(catalogue, seg_lab, range(1, n_seg + 1)))
    fold_of_seg = holdout.quadrant_fold(cent[:, 0], cent[:, 1], H, W)
    fold_grid = holdout.quadrant_fold(*np.mgrid[0:H, 0:W], H, W)
    fold_names = ["NW", "NE", "SW", "SE"]
    res["holdout"] = {"n_catalogue_px": int(catalogue.sum()), "n_segments": int(n_seg),
                      "segments_per_fold": {f: int((fold_of_seg == f).sum()) for f in fold_names}}

    out = {}
    pix_acc = {k: {"TP": np.zeros((H, W), np.float32), "FP": np.zeros((H, W), np.float32), "FN": np.zeros((H, W), np.float32)} for k in preds}
    n_pos = 0
    for f in fold_names:
        seg_ids = np.where(fold_of_seg == f)[0] + 1
        withheld = np.isin(seg_lab, seg_ids)
        domain = footprint & (fold_grid == f)
        gt = withheld & domain
        n_pos += int(gt.sum())
        visible = catalogue & ~withheld                                      # all other faults are visible
        for k, p in preds.items():
            pm = np.where(visible, 0.0, p)                                   # mask visible faults pixel-exactly
            c = metric.components(pm, gt, domain)
            for key in ("TP", "FP", "FN"):
                pix_acc[k][key] += c[key + "_pix"]
    for k in preds:
        T = pix_acc[k]["TP"].sum(); P = pix_acc[k]["FP"].sum(); N = pix_acc[k]["FN"].sum()
        point, lo, hi = holdout.block_bootstrap_ci(pix_acc[k]["TP"], pix_acc[k]["FP"], pix_acc[k]["FN"],
                                                   reps=args.reps)
        out[k] = {"label": "HOLDOUT-DTI", "evaluator": EVALUATOR,
                  "dti": round(point, 4), "ci95": [round(lo, 4), round(hi, 4)],
                  "withheld_positive_px": n_pos, "TP_w": round(T, 3), "FP_w": round(P, 3), "FN_w": round(N, 3)}
    res["experiments"] = out

    # ---- 4. leakage canary: each feature alone, AUC on ridge pixels ------------------------
    near_cat = ndimage.binary_dilation(catalogue, np.ones((7, 7), bool))
    ridge_ok = rm & footprint
    pos = ridge_ok & near_cat
    neg = ridge_ok & ~near_cat
    feats = {"gradient_magnitude": G, "neg_dimensionality_mag": -I_m, "neg_dimensionality_grav": -I_g,
             "strike_agreement": agree.astype(float), "E1_score": p1, "E3_score": p3}
    canary = {}
    for name, arr in feats.items():
        a = holdout.auc(np.asarray(arr[pos], float), np.asarray(arr[neg], float))
        canary[name] = {"auc": round(a, 4), "leak_flag": bool(a > 0.90)}
    res["canary_auc_on_ridges"] = {"n_pos": int(pos.sum()), "n_neg": int(neg.sum()), "features": canary}

    # ---- 5. strike prediction test: withheld fault strikes vs random ridge orientation --------
    ang_ok = rel
    seg_hits, seg_n = 0, 0
    for sid in range(1, n_seg + 1):
        rr, cc = np.where(seg_lab == sid)
        if rr.size < 20:
            continue
        E = cc - cc.mean(); Nn = -(rr - rr.mean())
        cov = np.cov(np.vstack([E, Nn]))
        w, v = np.linalg.eigh(cov)
        vmaj = v[:, np.argmax(w)]
        fault_az = float(np.mod(np.degrees(np.arctan2(vmaj[0], vmaj[1])), 180))
        m = ang_ok[rr, cc]
        if not m.any():
            continue
        ang = np.radians(2 * az_m[rr, cc][m])
        field_az = float(np.mod(np.degrees(np.arctan2(np.sin(ang).mean(), np.cos(ang).mean())) / 2, 180))
        seg_n += 1
        seg_hits += int(tensor.angle_diff180(fault_az, field_az) <= 22.5)
    rnd = ridge_ok & ~near_cat & ang_ok
    r_n = int(rnd.sum())
    r_hits = int((tensor.angle_diff180(az_r[rnd], az_m[rnd]) <= 22.5).sum())
    table = [[seg_hits, seg_n - seg_hits], [r_hits, r_n - r_hits]]
    _, pval = fisher_exact(table, alternative="greater")
    res["strike_test"] = {
        "withheld_segments_tested": seg_n, "withheld_match_rate": round(seg_hits / max(seg_n, 1), 4),
        "random_ridge_pixels_tested": r_n, "random_ridge_match_rate": round(r_hits / max(r_n, 1), 4),
        "fisher_one_sided_p": float(pval),
        "note": "withheld-fault strike (PCA of segment) vs median tensor strike on the segment; "
                "random ridge = ridge orientation vs tensor strike at the same pixel, ridges >300 m from catalogue"}

    # ---- 6. submission candidate: the pre-registered best holdout variant -------------------
    for k, p in preds.items():   # every variant is kept locally (outputs/ is gitignored) for registry checks
        submission.write_submission(p, footprint, meta, Path(args.out).with_name(f"{Path(args.out).stem}_{k}.tif"))
    best = max(out, key=lambda k: out[k]["dti"])
    res["selected_for_file"] = best
    p_final = preds[best]
    rec = submission.write_submission(p_final, footprint, meta, args.out)
    val = submission.validate(args.out, footprint, meta)
    dots = int(np.sum((p_final > 0) & footprint))
    res["submission"] = {"file": Path(args.out).name, "variant": best, "sha256": rec["sha256"],
                         "bytes": rec["bytes"], "nonzero_pixels": dots, "validator": val}
    Path(args.results).parent.mkdir(parents=True, exist_ok=True)
    Path(args.results).write_text(json.dumps(res, indent=2, default=float))
    print(json.dumps(res, indent=2, default=float))


if __name__ == "__main__":
    main()
