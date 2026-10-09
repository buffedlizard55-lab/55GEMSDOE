#!/usr/bin/env python3
"""Fetch the registry raster corpus listed in ``registry/registry.json``.

Each manifest row names an owner-maintained sibling repository and path. The
rasters are prior parallel-run submissions used ONLY as a uniqueness control
(see the lane protocol: rank-correlation and 3-px dot-overlap thresholds). They
are not competition inputs and are never redistributed outside this checkout:
``registry/rasters/`` is gitignored.

The script verifies each downloaded byte count against the manifest and refuses
to write a raster whose size disagrees. It performs no scoring and no network
access beyond the GitHub contents API.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "registry" / "registry.json"
OUTDIR = ROOT / "registry" / "rasters"
OWNER = "buffedlizard55-lab"


def gh_raw(repo: str, path: str) -> bytes:
    """Return the raw bytes of ``path`` in ``repo`` via the GitHub contents API."""
    meta = subprocess.run(
        ["gh", "api", f"repos/{OWNER}/{repo}/contents/{path}", "--jq", ".sha"],
        capture_output=True, text=True, check=True,
    )
    sha = meta.stdout.strip()
    blob = subprocess.run(
        ["gh", "api", f"repos/{OWNER}/{repo}/git/blobs/{sha}",
         "-H", "Accept: application/vnd.github.raw"],
        capture_output=True, check=True,
    )
    return blob.stdout


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only-missing", action="store_true", default=True)
    ap.add_argument("--all", action="store_true", help="re-download even if present")
    args = ap.parse_args()

    manifest = json.loads(MANIFEST.read_text())
    OUTDIR.mkdir(parents=True, exist_ok=True)
    failures: list[str] = []
    for name in sorted(manifest):
        row = manifest[name]
        dest = OUTDIR / name
        expected = int(row["size"])
        if dest.is_file() and dest.stat().st_size == expected and not args.all:
            continue
        try:
            data = gh_raw(row["repo"], row["path"])
        except subprocess.CalledProcessError as exc:
            failures.append(f"{name}: gh api failed: {exc.stderr.strip()[:200]}")
            continue
        if len(data) != expected:
            failures.append(f"{name}: got {len(data)} bytes, manifest says {expected}")
            continue
        dest.write_bytes(data)
        print(f"  {name}  {len(data)} bytes  <- {row['repo']}:{row['path']}")
    present = sorted(p.name for p in OUTDIR.glob("*.tif"))
    print(f"\nregistry rasters present: {len(present)}/{len(manifest)}")
    if failures:
        print("FAILURES:")
        for f in failures:
            print("  " + f)
        sys.exit(1)
    missing = sorted(set(manifest) - set(present))
    if missing:
        print("MISSING:", missing)
        sys.exit(1)
    print("All manifest-listed registry rasters are present with verified sizes.")


if __name__ == "__main__":
    main()
