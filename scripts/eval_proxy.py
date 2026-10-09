#!/usr/bin/env python3
"""Score tensor-lane emission policies against the independent-fault proxy.

The scored test population is expert-labelled NEW faults that are absent from
the public catalogue (verified from the official problem description).  The
only local stand-in for that population is the template project's proxy
catalogue: USGS SGMC (Data Series 1052, DOI 10.3133/ds1052) SGMC_Structure
fault polylines rasterised on the competition grid, code 2 = proxy fault with
NO training label within R = 300 m (61,664 px, sha256-pinned, grid-verified).
SGMC structure is mostly pre-Quaternary bedrock mapping from an independent
compilation (state geologic maps), i.e. the same "missing from the catalogue"
class as the scored faults.

Every number here is PROXY-DTI (population: SGMC code-2 proxy faults; NOT the
hidden test labels; NOT an organizer score).  Baselines (zeros, blanket ones,
catalogue copy, matched-mass uniform random) are reported so the measurement
cannot be read as vacuous.  The emission domain is the real submission domain:
template footprint minus the mapped catalogue, pixel-exact.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gems55 import dti55, holdout55, io55  # noqa: E402
from policies import POLICIES, build_emission  # noqa: E402

PROXY_TIF = ROOT / "data" / "proxy" / "proxy_catalogue.tif"
PROXY_SHA256 = "7563e187171f7210d70295f958b0b2714c1fa504afa35f9a4688fc99b1e1122a"
EVALUATOR = dti55.EVALUATOR_VERSION


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=ROOT / "evidence" / "proxy_tensor_lane_e1.json")
    args = ap.parse_args()

    t0 = time.time()
    # --- verify the proxy raster against the committed pin and grid -------
    digest = hashlib.sha256(PROXY_TIF.read_bytes()).hexdigest()
    if digest != PROXY_SHA256:
        raise SystemExit(f"proxy catalogue sha256 mismatch: {digest}")
    grid, _ = io55.read_template()
    footprint = grid.footprint
    with rasterio.open(PROXY_TIF) as src:
        proxy = src.read(1)
        assert (src.height, src.width) == grid.shape
        assert src.crs.to_epsg() == grid.crs
        assert tuple(src.transform)[:6] == tuple(grid.transform)[:6]
    truth = proxy == 2
    n_truth = int(truth.sum())
    print(f"[proxy] code-2 truth px = {n_truth} (sha256 verified)", flush=True)

    labels = io55.read_labels()
    cat = labels == 1
    elig = footprint & ~cat  # the real submission emission domain
    z = np.load(ROOT / "outputs" / "surface.npz")
    score = z["score"]

    results = {}
    for pol in POLICIES:
        pred = build_emission(score, elig, pol)
        r = dti55.dti(pred, truth)
        # matched-mass uniform random control over the same domain
        n_pos = int((pred > 0).sum())
        rand = holdout55.emit_dots(score, elig, n_pos, random=True, seed=99)
        rr = dti55.dti(rand.astype(np.float64), truth)
        results[pol["name"]] = {
            "dti": r.dti, "tp_w": r.tp_w, "fp_w": r.fp_w, "fn_w": r.fn_w,
            "coverage_frac_of_truth": r.tp_w / n_truth,
            "emitted_px": n_pos, "mass": float(pred[pred > 0].sum()),
            "random_matched_mass_dti": rr.dti,
            "random_matched_mass_tp_w": rr.tp_w,
        }
        print(f"  {pol['name']:<18} PROXY-DTI={r.dti:.6f} cov={r.tp_w/n_truth:.3f} "
              f"fp={r.fp_w:.0f} emitted={n_pos} random={rr.dti:.6f}", flush=True)
        del pred, rand

    # ------------------------- baselines ---------------------------------
    support = np.ones(grid.shape, dtype=bool)  # official metric sums over the whole raster
    baselines = {
        "zeros": np.zeros(grid.shape),
        "blanket_ones": support.astype(np.float64),
        "catalogue_copy": cat.astype(np.float64),
    }
    base_res = {}
    for name, b in baselines.items():
        r = dti55.dti(b, truth)
        base_res[name] = {"dti": r.dti, "tp_w": r.tp_w, "fp_w": r.fp_w, "fn_w": r.fn_w,
                          "emitted_px": int((b > 0).sum())}
        print(f"  baseline {name:<16} PROXY-DTI={r.dti:.6f}", flush=True)

    record = {
        "evidence_class": "PROXY-DTI",
        "experiment": "E1 tensor-lane emission policies vs the independent-fault proxy",
        "evaluator_version": EVALUATOR,
        "population": {
            "name": "USGS SGMC SGMC_Structure proxy, code 2 (no training label within 300 m)",
            "source_doi": "https://doi.org/10.3133/ds1052",
            "data_doi": "https://doi.org/10.5066/F7WH2N65",
            "proxy_tif": str(PROXY_TIF.relative_to(ROOT)),
            "proxy_sha256": digest,
            "truth_px": n_truth,
            "caveat": "an independent published catalogue, not the hidden expert labels; compare policies, not leaderboards",
        },
        "emission_domain": "template footprint minus mapped catalogue (pixel-exact) = the real submission domain",
        "metric": {"alpha": dti55.ALPHA, "beta": dti55.BETA,
                   "kernel": "triangular", "kernel_radius_m": 300.0},
        "policies": results,
        "baselines": base_res,
        "elapsed_s": round(time.time() - t0, 1),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(record, indent=2) + "\n")
    print(f"\nwrote {args.out}")

    print("\n=== PROXY-DTI summary (SGMC code-2, %d truth px) ===" % n_truth)
    for name in sorted(results, key=lambda n: -results[n]["dti"]):
        r = results[name]
        print(f"  {name:<18} {r['dti']:.6f}  cov={r['coverage_frac_of_truth']:.3f} "
              f"emitted={r['emitted_px']:<8} random={r['random_matched_mass_dti']:.6f}")
    for name, r in base_res.items():
        print(f"  [baseline] {name:<14} {r['dti']:.6f}")


if __name__ == "__main__":
    main()
