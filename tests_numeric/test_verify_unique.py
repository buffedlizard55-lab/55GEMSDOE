"""Regression test for including local archived predecessors in uniqueness checks."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gems55 import io55  # noqa: E402
import verify_unique  # noqa: E402


def _write_tif(path: Path, data: np.ndarray, transform) -> None:
    import rasterio

    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=data.shape[0],
        width=data.shape[1],
        count=1,
        dtype="float32",
        crs="EPSG:32611",
        transform=transform,
    ) as dst:
        dst.write(data.astype(np.float32), 1)


def test_uniqueness_checker_scans_registry_and_additional_local_rasters(tmp_path, monkeypatch):
    rasterio = pytest.importorskip("rasterio")
    from rasterio.transform import Affine

    shape = (40, 50)
    transform = Affine(100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)
    grid = io55.Grid(
        height=shape[0],
        width=shape[1],
        crs=32611,
        transform=transform,
        footprint=np.ones(shape, dtype=bool),
    )
    monkeypatch.setattr(verify_unique.io55, "read_template", lambda: (grid, None))

    registry_dir = tmp_path / "registry"
    evidence_dir = tmp_path / "evidence"
    monkeypatch.setattr(verify_unique, "REG", registry_dir)
    monkeypatch.setattr(verify_unique, "EVID", evidence_dir)

    candidate = np.zeros(shape, dtype=np.float32)
    candidate[5, 5] = candidate[34, 44] = 1.0
    registry = np.zeros(shape, dtype=np.float32)
    registry[15, 20] = registry[20, 30] = registry[25, 25] = 1.0
    historical = np.zeros(shape, dtype=np.float32)
    historical[10, 35] = historical[30, 10] = 1.0
    surface = np.random.default_rng(4).random(shape).astype(np.float32)

    candidate_path = tmp_path / "candidate.tif"
    registry_path = registry_dir / "shared-prior.tif"
    historical_path = tmp_path / "local-historical.tif"
    surface_path = tmp_path / "surface.tif"
    _write_tif(candidate_path, candidate, transform)
    _write_tif(registry_path, registry, transform)
    _write_tif(historical_path, historical, transform)
    _write_tif(surface_path, surface, transform)

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "verify_unique.py",
            str(candidate_path),
            "--surface",
            str(surface_path),
            "--additional",
            str(historical_path),
            "--out",
            str(evidence_dir / "unique.json"),
        ],
    )
    with pytest.raises(SystemExit) as exit_code:
        verify_unique.main()
    assert exit_code.value.code == 0

    report = json.loads((evidence_dir / "unique.json").read_text())
    assert report["registry_rasters_total"] == report["registry_rasters_scanned"] == 1
    assert report["local_historical_rasters_total"] == report["local_historical_rasters_scanned"] == 1
    assert report["comparison_rasters_total"] == report["comparison_rasters_scanned"] == 2
    assert {row["source"] for row in report["rows"]} == {"registry", "local_historical"}
    assert report["strict_verdict"] == "PASS-UNIQUE"
    assert report["strict_duplicate_rows"] == 0
