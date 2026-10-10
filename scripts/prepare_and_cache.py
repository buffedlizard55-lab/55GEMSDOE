#!/usr/bin/env python3
"""Build the cached tensor feature stack for the tensor-dimensionality lane.

One shared cache, built once from the authorised competition rasters, so every
downstream experiment reads identical bytes and no lane script re-derives the
FFT tensors (which is the expensive part).

Inputs (canonical paths in ``src/gems55/io55.py``)
    data/sample_submission.tif   -> the authoritative footprint (NaN outside)
    data/gems-geodawn-numerical-features.tif
        band 2  reduced-to-pole magnetic anomaly   (nT)
        band 13 isostatic gravity anomaly          (mGal)

Per field, per preregistered smoothing scale:
    1. nearest-neighbour gap fill inside the footprint
    2. optional along-track median levelling (off by default - measured)
    3. Gaussian band-pass (high-pass removes the regional field)
    4. magnetic field only: pseudogravity transform (vertical integration)
    5. FFT gradient tensor (6 independent components + 2 first derivatives)
    6. closed-form symmetric-3x3 eigen-decomposition
       -> dimensionality indicator I (Pedersen-Rasmussen), eigenvalue-ratio D,
          strike azimuth and horizontality of the intermediate eigenvector

Outputs
    cache/tensor_cache_<tag>.npz   float32/uint8/int16 products, one key per
                                   (field, scale, product) plus ``footprint``.

This script does not read ``labels.tif`` at any point, so the cache cannot leak
the catalogue into a holdout experiment.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems55 import fields55, io55, tensor55  # noqa: E402

BAND_MAG = 2
BAND_GRAV = 13


def _u8(x: np.ndarray) -> np.ndarray:
    return np.clip(np.nan_to_num(x, nan=0.0) * 255.0, 0, 255).astype(np.uint8)


def _az_i16(deg: np.ndarray) -> np.ndarray:
    """Azimuth in [0,180) deg stored as centidegrees in int16."""
    a = np.nan_to_num(np.asarray(deg, dtype=np.float64), nan=0.0) % 180.0
    return np.clip(np.round(a * 100.0), 0, 17999).astype(np.int16)


def field_products(
    raw: np.ndarray,
    valid: np.ndarray,
    res_m: float,
    scale_m: float,
    *,
    along_axis: int,
    highpass_m: float,
    destripe: bool,
    pad_frac: float,
    use_pseudogravity: bool,
    eig_chunk: int,
) -> dict[str, np.ndarray]:
    """All per-field tensor products at one smoothing scale."""
    import gc

    bp, _ = fields55.prepare_field(
        raw,
        valid,
        res_m,
        along_axis=along_axis,
        lowpass_m=scale_m,
        highpass_m=highpass_m,
        destripe=destripe,
        pad_frac=pad_frac,
    )
    if use_pseudogravity:
        # Band-pass first (kills the regional), then vertically integrate: the
        # spectrum already has no energy at k->0, so 1/|k| stays bounded.
        bp = tensor55.pseudogravity(bp, res_m, pad_frac=pad_frac)

    T = tensor55.gradient_tensor(
        bp,
        res_m,
        lowpass_m=None,
        highpass_m=None,
        taper_pad_frac=pad_frac,
        components=("Txx", "Tyy", "Txy", "Tzz", "Txz", "Tyz", "gx", "gy"),
    )
    del bp
    gc.collect()
    hg = np.hypot(T["gx"], T["gy"]).astype(np.float32)
    ridge_az = ((np.degrees(np.arctan2(T["gx"], T["gy"])) + 90.0) % 180.0).astype(np.float32)
    del T["gx"], T["gy"]
    lam, e2 = tensor55.sym3_eigh(T, chunk=eig_chunk)
    del T
    gc.collect()
    shape = hg.shape
    dim_inv = tensor55.dimensionality_invariant(lam).reshape(shape)
    dim_eig = tensor55.dimensionality_eigratio(lam).reshape(shape)
    del lam
    strike = tensor55.strike_eigenvector(e2).reshape(shape)
    plunge = tensor55.strike_plunge_weight(e2).reshape(shape)
    del e2
    gc.collect()
    return {
        "hg": hg,
        "ridge_az": ridge_az,
        "dim_inv": dim_inv.astype(np.float32),
        "dim_eig": dim_eig.astype(np.float32),
        "strike": strike,
        "plunge": plunge,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scales", type=float, nargs="+", default=[300.0, 900.0])
    ap.add_argument("--highpass-m", type=float, default=8000.0)
    ap.add_argument("--pad-frac", type=float, default=0.05)
    ap.add_argument("--eig-chunk", type=int, default=400_000)
    ap.add_argument("--destripe", action="store_true",
                    help="subtract the along-track median profile before band-passing")
    ap.add_argument("--along-axis", type=int, default=1,
                    help="numpy axis that runs ALONG the flight lines (1 = east-west lines)")
    ap.add_argument("--no-pseudogravity", action="store_true")
    ap.add_argument("--pseudogravity-only", action="store_true",
                    help="also build a direct-RTP (no pseudogravity) magnetic arm for ablation")
    ap.add_argument("--out", type=Path, default=ROOT / "cache" / "tensor_cache.npz")
    args = ap.parse_args()

    t0 = time.time()
    grid, _tmpl = io55.read_template()
    footprint = np.asarray(grid.footprint, dtype=bool)
    mag, vmag = io55.read_band(BAND_MAG)
    grav, vgrav = io55.read_band(BAND_GRAV)
    valid = footprint & vmag & vgrav
    print(f"footprint={footprint.sum()} valid(mag&grav&footprint)={valid.sum()}", flush=True)

    meta = {
        "built_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "res_m": io55.RES_M,
        "shape": list(grid.shape),
        "crs_epsg": io55.CRS_EPSG,
        "transform": list(grid.transform)[:6],
        "band_mag": BAND_MAG,
        "band_grav": BAND_GRAV,
        "scales_m": list(args.scales),
        "highpass_m": args.highpass_m,
        "pad_frac": args.pad_frac,
        "destripe": bool(args.destripe),
        "along_axis": int(args.along_axis),
        "pseudogravity": not args.no_pseudogravity,
        "n_valid": int(valid.sum()),
        "footprint_px": int(footprint.sum()),
    }

    arms = [("grav", grav, False)]
    if args.pseudogravity_only:
        arms.append(("mag", mag, True))
        arms.append(("magdirect", mag, False))
    else:
        arms.append(("mag", mag, not args.no_pseudogravity))

    payload: dict[str, np.ndarray] = {"footprint": footprint}
    for name, raw, use_pg in arms:
        for sc in args.scales:
            t = time.time()
            P = field_products(
                raw, valid, io55.RES_M, float(sc),
                along_axis=args.along_axis,
                highpass_m=args.highpass_m,
                destripe=args.destripe,
                pad_frac=args.pad_frac,
                use_pseudogravity=use_pg,
                eig_chunk=args.eig_chunk,
            )
            tag = f"{name}_s{int(sc)}"
            payload[f"{tag}_hg"] = P["hg"]
            payload[f"{tag}_ridge_az"] = _az_i16(P["ridge_az"])
            payload[f"{tag}_dim_inv"] = _u8(P["dim_inv"])
            payload[f"{tag}_dim_eig"] = _u8(P["dim_eig"])
            payload[f"{tag}_strike"] = _az_i16(P["strike"])
            payload[f"{tag}_plunge"] = _u8(P["plunge"])
            print(f"  {tag}: {time.time() - t:.1f}s  (pseudogravity={use_pg})", flush=True)
            del P

    args.out.parent.mkdir(parents=True, exist_ok=True)
    np.savez(args.out, **payload)
    meta_path = args.out.with_suffix(".json")
    meta_path.write_text(json.dumps(meta, indent=1))
    print(f"wrote {args.out} ({args.out.stat().st_size/1e6:.1f} MB) + {meta_path}")
    print(f"total {time.time()-t0:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
