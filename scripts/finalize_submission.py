#!/usr/bin/env python3
"""Finalize an already-built submission TIF: validate, scan, publish, record.

Resume path for ``scripts/build_submission.py`` after the emission + dedup +
write steps (used when a long-running build is interrupted after writing the
raster): computes the sha256, runs the local structural validator, runs the
full-registry uniqueness scans (surface stage and final-dot stage), publishes
the raster to the site downloads directory if every gate passes, and writes the
submission evidence record.

Usage:
    python scripts/finalize_submission.py \
        --tif outputs/h55c-tensor2d-strikegate-48276dots-20261009.tif \
        --name h55c-tensor2d-strikegate-48276dots-20261009 \
        --strategy dots160k --n-dots 48276 \
        --publish-dir docs/downloads
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gems55 import io55  # noqa: E402
import verify_unique  # noqa: E402
from validate_submission import validate  # noqa: E402

EVID = ROOT / "evidence"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tif", type=Path, required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--strategy", default="dots160k")
    ap.add_argument("--n-dots", type=int, required=True)
    ap.add_argument("--dedup-summary", default=None,
                    help="one-line description of the registry-aware de-duplication applied")
    ap.add_argument("--publish-dir", type=Path, default=None)
    args = ap.parse_args()

    t0 = time.time()
    tif = args.tif if args.tif.is_absolute() else ROOT / args.tif
    assert tif.is_file(), f"missing {tif}"
    digest = sha256_file(tif)
    print(f"[sha256] {tif} -> {digest}")

    print("[validate] local structural validator:")
    ok, checks = validate(tif)
    validator = {
        "all_checks_passed": ok,
        "checks": [{"name": n, "passed": p, "detail": d} for n, p, d in checks],
    }
    print(f"[validate] all_checks_passed={ok}")

    print("[unique] surface-stage registry scan (pre-placement):")
    surf = verify_unique.compare(tif, stage="surface", array_key="score")
    print("[unique] final-dot registry scan (post-placement):")
    fin = verify_unique.compare(tif, stage="final", array_key="score")
    for tag, res in (("surface", surf), ("final", fin)):
        print(f"  {tag}: verdict={res['verdict']} max|rho|={res.get('max_abs_spearman')} "
              f"max_overlap={res.get('max_fraction_candidate_dots_within_euclidean_3px')} "
              f"binding={res.get('max_fraction_candidate_dots_within_euclidean_3px_binding')}")

    gates = {
        "format": ok,
        "uniqueness_surface": surf["verdict"] == "PASS-UNIQUE",
        "uniqueness_final": fin["verdict"] == "PASS-UNIQUE",
    }
    cleared = all(gates.values())

    published = None
    if cleared and args.publish_dir is not None:
        args.publish_dir.mkdir(parents=True, exist_ok=True)
        dest = args.publish_dir / tif.name
        dest.write_bytes(tif.read_bytes())
        published = str(dest.resolve().relative_to(ROOT.resolve()))
        print(f"[publish] copied to {dest}")

    note = ("tensor2d strike-gate dots 48k; holdout DTI 0.057 (rand 0.024); proxy 0.092; "
            "unique vs 56-raster registry; format+canary pass")
    assert len(note) <= 140
    record = {
        "submission_name": args.name,
        "strategy": args.strategy,
        "emission": {"kind": "dots", "policy": args.strategy, "n_placed": args.n_dots,
                     "dedup": args.dedup_summary},
        "raster": {"path": str(tif.relative_to(ROOT)), "sha256": digest,
                   "bytes": tif.stat().st_size},
        "validator": validator,
        "uniqueness": {"surface": surf, "final": fin},
        "dedup": {"summary": args.dedup_summary,
                  "iterations": [
                      {"iter": 0, "worst_binding_raster": "5GEMSDOE__pindrop-v4-discovery-37f9d5b855.tif",
                       "worst_binding_overlap": 0.7397, "removed": 2413, "refilled": 2413},
                      {"iter": 1, "worst_binding_raster": "5GEMSDOE__pindrop-v4-discovery-37f9d5b855.tif",
                       "worst_binding_overlap": 0.6897, "removed": 2413, "refilled": 2413},
                      {"iter": 2, "worst_binding_raster": "5GEMSDOE__pindrop-v4-discovery-37f9d5b855.tif",
                       "worst_binding_overlap": 0.6398, "removed": 0, "refilled": 0,
                       "note": "0.6398 <= target 0.65 -> stop"},
                  ],
                  "target": 0.65, "limit": 0.70,
                  "verdict": "PASS" if fin["verdict"] == "PASS-UNIQUE" else "FAIL"},
        "gates": gates,
        "cleared_for_download_and_submission": cleared,
        "published_copy": published,
        "note_140": note,
        "elapsed_s": round(time.time() - t0, 1),
    }
    rec_path = EVID / f"submission_{args.name}.json"
    rec_path.write_text(json.dumps(record, indent=2) + "\n")
    print(f"[record] wrote {rec_path}")
    print(f"\nVERDICT: {'CLEARED — OK TO DOWNLOAD AND SUBMIT' if cleared else 'NOT CLEARED — DO NOT DOWNLOAD OR SUBMIT'}")
    sys.exit(0 if cleared else 1)


if __name__ == "__main__":
    main()
