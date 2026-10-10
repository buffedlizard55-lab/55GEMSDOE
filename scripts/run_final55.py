#!/usr/bin/env python3
"""Final tensor-lane run: pooled holdout DTI with a spatial-block 95% CI,
plus the full-region competition raster.

Stage 1 (holdout, honest)
    For every fold: emit the candidate dots with the fold's visible catalogue
    pixels masked, then accumulate the additive DTI contribution maps
    (TP at truth cells, FN at truth cells, FP at prediction cells inside the
    fold's own bin).  The bins partition the footprint, so pooling the four
    folds counts every prediction cell and every truth cell exactly once.

Stage 2 (uncertainty)
    Spatial-block bootstrap over the pooled additive maps.  Blocks are
    ``--block-px`` squares (default 40 px = 4 km), which is larger than the
    300 m kernel and comparable to a fault-segment spacing, so the resample
    respects the dominant spatial dependence.  This is a percentile interval on
    the pooled ratio, not a fold-level t interval.

Stage 3 (deliverable)
    Re-emit with the SAME arm, dot count and separation over the whole
    footprint, masking every mapped catalogue pixel (the competition's ground
    truth is a set of NEW faults, so a dot on a mapped fault can only be a
    false positive).  Write the single-band float32 GeoTIFF.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from gems55 import dti55, io55  # noqa: E402
import evaluate_holdout as EH  # noqa: E402


def pooled_maps(ev: EH.PooledEvaluator, preds: list[np.ndarray]) -> tuple[np.ndarray, ...]:
    """Pooled per-pixel additive maps for TP_w, FP_w and FN_w."""
    shape = preds[0].shape
    tp = np.zeros(shape, dtype=np.float64)
    fn = np.zeros(shape, dtype=np.float64)
    fp = np.zeros(shape, dtype=np.float64)
    for k, (p, part, fold) in enumerate(zip(preds, ev.parts, ev.folds)):
        del k
        flat = np.asarray(p, dtype=np.float32).ravel()
        vals = np.where(part["nbr_ok"],
                        flat[part["nbr_idx"]].astype(np.float64) * part["nbr_w"], 0.0)
        M = vals.max(axis=1)
        ys, xs = np.nonzero(fold.truth)
        tp[ys, xs] = M
        fn[ys, xs] = 1.0 - M
        w64 = dti55.kernel_credit(fold.truth, dti55.R_PX)
        tmp = np.zeros(shape, dtype=np.float64)
        bin_flat = part["bin_flat"]
        fp.ravel()[bin_flat] += flat[bin_flat].astype(np.float64) * part["one_minus_w_bin"]
    return tp, fp, fn


def block_bootstrap(tp: np.ndarray, fp: np.ndarray, fn: np.ndarray, *, block_px: int,
                    n_boot: int, seed: int) -> dict:
    ny, nx = tp.shape
    nby = (ny + block_px - 1) // block_px
    nbx = (nx + block_px - 1) // block_px
    sums = np.zeros((nby * nbx, 3), dtype=np.float64)
    for iy in range(nby):
        for ix in range(nbx):
            sl = (slice(iy * block_px, min((iy + 1) * block_px, ny)),
                  slice(ix * block_px, min((ix + 1) * block_px, nx)))
            b = iy * nbx + ix
            sums[b] = (tp[sl].sum(), fp[sl].sum(), fn[sl].sum())
    keep = np.sum(np.abs(sums), axis=1) > 0
    sums = sums[keep]
    rng = np.random.default_rng(seed)
    draws = rng.integers(0, sums.shape[0], size=(n_boot, sums.shape[0]))
    tot = sums[draws].sum(axis=1)
    scores = tot[:, 0] / (tot[:, 0] + dti55.ALPHA * tot[:, 1] + dti55.BETA * tot[:, 2] + dti55.EPS)
    return {
        "ci95": [float(np.quantile(scores, 0.025)), float(np.quantile(scores, 0.975))],
        "method": (f"percentile bootstrap of {sums.shape[0]} spatial blocks of "
                   f"{block_px}x{block_px} px over the pooled additive DTI contribution maps"),
        "n_blocks": int(sums.shape[0]), "block_px": int(block_px), "n_boot": int(n_boot),
        "bootstrap_seed": int(seed),
    }


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", type=Path, default=EH.CACHE)
    ap.add_argument("--arm", type=str, default="tensor_full")
    ap.add_argument("--n-dots", type=int, default=16000)
    ap.add_argument("--min-sep", type=float, default=3.0)
    ap.add_argument("--n-folds", type=int, default=4)
    ap.add_argument("--buffer-px", type=int, default=3)
    ap.add_argument("--block-px", type=int, default=40)
    ap.add_argument("--n-boot", type=int, default=2000)
    ap.add_argument("--control-reps", type=int, default=5)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--skip-raster", action="store_true")
    args = ap.parse_args()

    t0 = time.time()
    grid, _tmpl = io55.read_template()
    labels = io55.read_labels()
    footprint = np.asarray(grid.footprint, dtype=bool)
    C = EH.load_cache(args.cache)
    S = EH.build_arm_surfaces(C, footprint)
    surf = S[args.arm]
    valid = S["_valid"]

    folds = EH.holdout55.make_segment_folds(labels, footprint, n_folds=args.n_folds,
                                            buffer_px=args.buffer_px)
    nrows = max(1, int(np.floor(np.sqrt(len(folds)))))
    ncols = int(np.ceil(len(folds) / nrows))
    bins = EH.spatial_bins(footprint, nrows, ncols)[:len(folds)]
    ev = EH.PooledEvaluator(folds, bins, footprint.shape)

    def run(score: np.ndarray, random: bool = False, seed: int = 0):
        preds = []
        for k, f in enumerate(folds):
            elig = valid & ~f.visible
            if random:
                ref = EH.emit_dots(score, elig, n_dots=args.n_dots, min_sep_px=args.min_sep)
                n_sel = int((ref > 0).sum())
                idx = np.nonzero(elig.ravel())[0]
                rng = np.random.default_rng(seed + k)
                out = np.zeros(score.shape, dtype=np.float32)
                out.ravel()[rng.choice(idx, size=min(n_sel, idx.size), replace=False)] = 1.0
                preds.append(out)
            else:
                preds.append(EH.emit_dots(score, elig, n_dots=args.n_dots,
                                          min_sep_px=args.min_sep))
        return preds

    preds = run(surf)
    tp, fp, fn = pooled_maps(ev, preds)
    TP, FP, FN = float(tp.sum()), float(fp.sum()), float(fn.sum())
    dti = dti55.dti_from_totals(TP, FP, FN)
    boot = block_bootstrap(tp, fp, fn, block_px=args.block_px, n_boot=args.n_boot,
                           seed=args.seed)

    ctrl = []
    for rep in range(args.control_reps):
        p = run(surf, random=True, seed=1000 * (rep + 1))
        t2, f2, n2 = pooled_maps(ev, p)
        ctrl.append(dti55.dti_from_totals(float(t2.sum()), float(f2.sum()), float(n2.sum())))
    ctrl = np.asarray(ctrl, dtype=float)

    # ---- also score a ridge-only comparator at the identical budget ------- #
    comp = {}
    for name in ("ridge_only", "ridge_x_dim"):
        p = run(S[name])
        t2, f2, n2 = pooled_maps(ev, p)
        comp[name] = dti55.dti_from_totals(float(t2.sum()), float(f2.sum()), float(n2.sum()))

    out = {
        "evidence_class": "HOLDOUT-DTI",
        "evaluator_version": dti55.EVALUATOR_VERSION,
        "arm": args.arm,
        "n_dots": int(args.n_dots),
        "min_sep_px": float(args.min_sep),
        "withheld_positive_count": int(sum(int(f.truth.sum()) for f in folds)),
        "n_folds": len(folds),
        "buffer_px": args.buffer_px,
        "metric": {"alpha": dti55.ALPHA, "beta": dti55.BETA, "kernel": "triangular",
                   "radius_m": dti55.R_PX * io55.RES_M},
        "candidate": {
            "dti": dti, "tp_w": TP, "fp_w": FP, "fn_w": FN,
            "mean_pred_cells": float(np.mean([int((p > 0).sum()) for p in preds])),
        },
        "candidate_ci95": boot["ci95"],
        "ci_method": boot["method"],
        "n_blocks": boot["n_blocks"],
        "random_control": {
            "reps": int(args.control_reps),
            "dti_mean": float(ctrl.mean()), "dti_std": float(ctrl.std(ddof=1)),
            "dti_min": float(ctrl.min()), "dti_max": float(ctrl.max()),
            "all": [float(x) for x in ctrl],
        },
        "lift_over_random": float(dti / max(ctrl.mean(), 1e-12)),
        "comparators_same_budget": comp,
        "cache": str(args.cache),
        "elapsed_s": time.time() - t0,
    }
    print(json.dumps(out, indent=1))

    if not args.skip_raster:
        mapped = (labels == 1) & footprint
        dots = EH.emit_dots(surf, valid & ~mapped, n_dots=args.n_dots,
                            min_sep_px=args.min_sep)
        pred = np.where(dots > 0, 1.0, 0.0).astype(np.float32)
        assert not np.any((pred > 0) & ~footprint)
        assert not np.any((pred > 0) & mapped)
        arr = np.where(footprint, pred, np.nan).astype(np.float32)
        outdir = ROOT / "docs" / "downloads"
        outdir.mkdir(parents=True, exist_ok=True)
        tag = f"gems55-{args.arm}-n{args.n_dots}-sep{args.min_sep:g}"
        stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
        path = outdir / f"{tag}-{stamp}-nan.tif"
        import rasterio
        with rasterio.open(path, "w", driver="GTiff", height=grid.height, width=grid.width,
                           count=1, dtype="float32",
                           crs=rasterio.crs.CRS.from_epsg(io55.CRS_EPSG),
                           transform=grid.transform, compress="lzw",
                           nodata=float("nan")) as dst:
            dst.write(arr, 1)
        out["raster"] = {
            "file": str(path.relative_to(ROOT)),
            "sha256": sha256(path),
            "size_bytes": int(path.stat().st_size),
            "n_positive_cells": int((arr > 0).sum()),
            "footprint_px": int(footprint.sum()),
            "positive_fraction_of_footprint": float((arr > 0).sum() / footprint.sum()),
            "mapped_fault_pixels_masked": int(mapped.sum()),
            "built_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        print(json.dumps(out["raster"], indent=1))

    op = ROOT / "evidence" / f"final_{args.arm}_n{args.n_dots}.json"
    op.write_text(json.dumps(out, indent=1))
    print(f"wrote {op}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
