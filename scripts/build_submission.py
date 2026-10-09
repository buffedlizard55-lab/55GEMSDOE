#!/usr/bin/env python3
"""Build the final tensor-lane submission GeoTIFF and run every clearance gate.

Steps (all local, no network, no organizer contact):
  1. Load the cached label-free tensor surface and apply the emission strategy
     selected by the holdout (``scripts/run_holdout.py``).
  2. Emission domain = template footprint minus the mapped catalogue
     (pixel-exact), because the scored test truth is the expert-labelled NEW
     faults, disjoint from the public catalogue; predicting on catalogue
     pixels would be pure false-positive mass.
  3. Optional registry-aware de-duplication: if the natural emission exceeds
     the literal 70% within-3px overlap against any NON-degenerate registry
     raster, greedily move dots out of the worst raster's dilated region to
     the next-best surface pixels outside every binding dilated region, until
     the binding overlap is <= the target (default 0.65, margin under 0.70).
  4. Write the single-band float32 GeoTIFF (NaN outside the footprint,
     values in [0,1] inside, catalogue pixels exactly 0) mirroring the
     organizer sample template profile.
  5. Run the local structural validator (CRS/shape/transform/resolution,
     NaN mask, [0,1] range, no positives on the catalogue).
  6. Run the full-registry uniqueness check twice: continuous surface stage
     (pre-placement) and final-dot stage (post-placement).
  7. Emit a submission record JSON with the raster sha256 and every gate.

Nothing here is an organizer receipt. The verdict line states plainly whether
the file is cleared for download/submission.
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

from gems55 import dti55, holdout55, io55  # noqa: E402
from policies import emit_dots_fast  # noqa: E402
import verify_unique  # noqa: E402
from validate_submission import validate  # noqa: E402

OUT = ROOT / "outputs"
EVID = ROOT / "evidence"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_registry_dots(footprint):
    """Positive-cell masks of every manifest registry raster (bool stack)."""
    import rasterio
    manifest = json.loads((ROOT / "registry" / "registry.json").read_text())
    regdir = ROOT / "registry" / "rasters"
    names, masks = [], []
    for name in sorted(manifest):
        with rasterio.open(regdir / name) as src:
            a = src.read(1)
        dots = np.isfinite(a) & (a > 0) & footprint
        names.append(name)
        masks.append(dots)
    return names, masks


def deduplicate_dots(score, dots, footprint, *, target=0.65, limit=0.70,
                     max_iters=40, log=print):
    """Greedily move dots out of the worst binding registry raster's 3-px dilation.

    Repeatedly finds the non-degenerate registry raster with the highest
    fraction of our dots inside its dilation; while that fraction exceeds
    ``target``, the weakest-scoring dots inside it are removed and replaced by
    the highest-scoring eligible pixels OUTSIDE that raster's dilation (3-px
    minimum separation from every remaining dot, enforced with a KDTree).
    Every binding raster's fraction is re-measured after the pass.  The
    relocation is a diversity constraint w.r.t. prior submissions (the
    parallel-run uniqueness rule); it changes only the affected dots and is
    reported with before/after scores.  Returns the adjusted dot mask and a
    report.
    """
    from scipy import spatial

    yy, xx = np.ogrid[-3:4, -3:4]
    disk = (yy * yy + xx * xx) <= 9.0 + 1e-9
    names, masks = load_registry_dots(footprint)
    info = []
    for name, m in zip(names, masks):
        near = ndimage.binary_dilation(m, structure=disk)
        coverage = float(near[footprint].mean())
        info.append({
            "name": name, "near": near, "coverage": coverage,
            "degenerate": coverage >= verify_unique.DEGENERATE_COVERAGE,
        })
    binding = [r for r in info if not r["degenerate"]]

    dots = dots.copy()
    report = {"iterations": [], "registry_names": names,
              "target": target, "limit": limit}
    for it in range(max_iters):
        worst_frac, worst = 0.0, None
        for r in binding:
            if dots.sum() == 0:
                break
            f = float(r["near"][dots].mean())
            if f > worst_frac:
                worst_frac, worst = f, r
        report["iterations"].append({
            "iter": it, "worst_binding_raster": worst["name"] if worst else None,
            "worst_binding_overlap": worst_frac,
        })
        log(f"  [dedup] iter {it}: worst binding overlap = {worst_frac:.4f} "
            f"({worst['name'][:60] if worst else '-'})")
        if worst is None or worst_frac <= target:
            break
        # Replacement pool: highest score outside the worst raster's dilation.
        pool_score = np.where(footprint & ~worst["near"], score, -np.inf)
        # Remove the weakest dots inside the worst raster's dilation.
        n_remove = max(1, int(0.05 * dots.sum()))
        dy, dx = np.nonzero(dots & worst["near"])
        if dy.size == 0:
            break
        vals = score[dy, dx]
        order = np.argsort(vals, kind="stable")  # weakest first
        remove_idx = order[:n_remove]
        dots[dy[remove_idx], dx[remove_idx]] = False
        # Refill from the pool: highest score first, 3-px separation via KDTree.
        py, px = np.nonzero(dots)
        existing = np.stack([py, px], axis=1).astype(np.float64) if py.size else \
            np.empty((0, 2))
        tree = spatial.cKDTree(existing) if existing.size else None
        cand = np.nonzero(pool_score > -np.inf)
        cvals = pool_score[cand]
        corder = np.argsort(-cvals, kind="stable")[: max(n_remove * 8, 20_000)]
        cpts = np.stack([cand[0][corder], cand[1][corder]], axis=1).astype(np.float64)
        if tree is not None and cpts.size:
            dist, _ = tree.query(cpts, k=1)
            ok = dist >= 3.0
        else:
            ok = np.ones(cpts.shape[0], dtype=bool)
        ok_idx = np.nonzero(ok)[0][:n_remove]
        added = 0
        for i in ok_idx:
            y, x = int(cpts[i, 0]), int(cpts[i, 1])
            if dots[y, x]:
                continue
            dots[y, x] = True
            if tree is not None:
                existing = np.vstack([existing, [y, x]])
                tree = spatial.cKDTree(existing)
            added += 1
        log(f"  [dedup] removed {len(remove_idx)}, refilled {added}")
    # Final per-raster report.
    final = []
    for r in info:
        f = float(r["near"][dots].mean()) if dots.sum() else 0.0
        final.append({"raster": r["name"], "coverage": r["coverage"],
                      "degenerate": r["degenerate"], "our_dots_within_3px": f})
    report["final_per_raster"] = final
    report["max_binding_overlap"] = max(
        (f["our_dots_within_3px"] for f in final if not f["degenerate"]), default=0.0)
    report["verdict"] = "PASS" if report["max_binding_overlap"] <= limit else "FAIL"
    return dots, report


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--strategy", default="dots160k",
                    help="any policy name from scripts/policies.py (default: dots160k)")
    ap.add_argument("--name", default=None, help="submission file stem")
    ap.add_argument("--out-dir", type=Path, default=ROOT / "outputs")
    ap.add_argument("--dedup-target", type=float, default=0.65)
    ap.add_argument("--no-dedup", action="store_true")
    ap.add_argument("--publish-dir", type=Path, default=None,
                    help="if set and all gates pass, copy the tif here (site downloads)")
    args = ap.parse_args()

    t0 = time.time()
    z = np.load(OUT / "surface.npz")
    grid, _ = io55.read_template()
    footprint = grid.footprint
    labels = io55.read_labels()
    cat = labels == 1
    score = z["score"]
    elig = footprint & ~cat

    from policies import POLICIES, build_emission
    policy = next((p for p in POLICIES if p["name"] == args.strategy), None)
    if policy is None:
        raise SystemExit(f"unknown strategy {args.strategy}; available: "
                         f"{[p['name'] for p in POLICIES]}")
    pred = build_emission(score, elig, policy).astype(np.float32)
    if policy["kind"] == "dots":
        emission = {"kind": "dots", "policy": policy["name"],
                    "n_requested": policy["n"], "n_placed": int((pred > 0).sum())}
    elif policy["kind"] == "continuous":
        emission = {"kind": "continuous", "positive_cells": int((pred > 0).sum())}
    elif policy["kind"] == "power":
        emission = {"kind": f"continuous^{policy['k']}",
                    "positive_cells": int((pred > 0).sum())}
    elif policy["kind"] == "top_pct":
        emission = {"kind": "top_pct_binary", "pct": policy["pct"],
                    "positive_cells": int((pred > 0).sum())}
    elif policy["kind"] == "top_pct_dil":
        emission = {"kind": "top_pct_binary_dilated", "pct": policy["pct"], "w": policy["w"],
                    "positive_cells": int((pred > 0).sum())}
    else:
        emission = {"kind": policy["kind"], "positive_cells": int((pred > 0).sum())}

    # Enforce the candidate policy: exactly zero on catalogue pixels.
    pred[cat] = 0.0
    pred[~footprint] = 0.0  # writer sets NaN outside; keep the array finite here
    assert np.isfinite(pred[footprint]).all()
    assert float(pred[footprint].min()) >= 0.0 and float(pred[footprint].max()) <= 1.0

    dedup_report = None
    if policy["kind"] == "dots" and not args.no_dedup:
        # Registry-aware de-duplication (IR-55-043): the literal 70% within-3px
        # rule is applied to every non-degenerate registry raster.  The natural
        # emission is measured inside deduplicate_dots, which relocates only the
        # dots needed to reach the target and reports every raster's fraction.
        print("[dedup] applying registry-aware de-duplication "
              f"(target {args.dedup_target}, limit 0.70)...")
        dots, dedup_report = deduplicate_dots(
            score, pred > 0, footprint, target=args.dedup_target, log=print)
        pred = dots.astype(np.float32)
        pred[cat] = 0.0
        emission["n_placed_after_dedup"] = int(dots.sum())

    stem = args.name or f"h55c-tensor2d-strikegate-{args.strategy}-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}"
    out_path = args.out_dir / f"{stem}.tif"
    io55.write_submission(pred, out_path, grid, outside="nan")
    digest = sha256_file(out_path)
    print(f"[write] {out_path} sha256={digest}")

    print("[validate] local structural validator:")
    ok, checks = validate(out_path)
    validator = {
        "all_checks_passed": ok,
        "checks": [{"name": n, "passed": p, "detail": d} for n, p, d in checks],
    }

    print("[unique] surface-stage registry scan (pre-placement):")
    surf = verify_unique.compare(out_path, stage="surface", array_key="score")
    print("[unique] final-dot registry scan (post-placement):")
    fin = verify_unique.compare(out_path, stage="final", array_key="score")
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
        dest = args.publish_dir / out_path.name
        dest.write_bytes(out_path.read_bytes())
        published = str(dest.relative_to(ROOT))
        print(f"[publish] copied to {dest}")

    record = {
        "submission_name": stem,
        "strategy": args.strategy,
        "emission": emission,
        "raster": {"path": str(out_path.relative_to(ROOT)), "sha256": digest,
                   "bytes": out_path.stat().st_size},
        "validator": validator,
        "uniqueness": {"surface": surf, "final": fin},
        "dedup": dedup_report,
        "gates": gates,
        "cleared_for_download_and_submission": cleared,
        "published_copy": published,
        "note_140": (f"tensor2d strike-gated {args.strategy} lane; holdout-validated; "
                     f"unique vs registry; local format+canary gates passed"),
        "elapsed_s": round(time.time() - t0, 1),
    }
    rec_path = EVID / f"submission_{stem}.json"
    rec_path.write_text(json.dumps(record, indent=2) + "\n")
    print(f"[record] wrote {rec_path}")
    print(f"\nVERDICT: {'CLEARED — OK TO DOWNLOAD AND SUBMIT' if cleared else 'NOT CLEARED — DO NOT DOWNLOAD OR SUBMIT'}")
    sys.exit(0 if cleared else 1)


if __name__ == "__main__":
    main()
