import subprocess
import sys
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin
from gems import submission


def _meta():
    return {"crs": rasterio.crs.CRS.from_epsg(32611), "transform": from_origin(243350, 4508550, 100, 100),
            "height": 30, "width": 40}


def test_roundtrip_passes_validator(tmp_path):
    fp = np.zeros((30, 40), bool); fp[5:25, 5:35] = True
    pred = np.random.default_rng(0).random((30, 40)) * 1.5 - 0.2  # out-of-range on purpose
    out = submission.write_submission(pred, fp, _meta(), tmp_path / "s.tif")
    res = submission.validate(out["path"], fp, _meta())
    assert res["all_passed"], res
    assert res["values_in_0_1_inside"]


def test_validator_rejects_out_of_range(tmp_path):
    fp = np.ones((30, 40), bool)
    path = tmp_path / "bad.tif"
    with rasterio.open(path, "w", driver="GTiff", height=30, width=40, count=1, dtype="float32",
                       crs=_meta()["crs"], transform=_meta()["transform"], nodata=np.nan) as d:
        arr = np.full((30, 40), 0.5, np.float32); arr[0, 0] = 1.7
        d.write(arr, 1)
    assert not submission.validate(path, fp, _meta())["values_in_0_1_inside"]


def test_validator_rejects_nan_inside(tmp_path):
    fp = np.ones((30, 40), bool)
    path = tmp_path / "nan.tif"
    with rasterio.open(path, "w", driver="GTiff", height=30, width=40, count=1, dtype="float32",
                       crs=_meta()["crs"], transform=_meta()["transform"], nodata=np.nan) as d:
        arr = np.full((30, 40), 0.5, np.float32); arr[3, 3] = np.nan
        d.write(arr, 1)
    assert not submission.validate(path, fp, _meta())["no_nan_inside_footprint"]


def test_cli_missing_official_inputs_fails_closed_with_actionable_message(tmp_path):
    root = Path(__file__).resolve().parents[1]
    candidate = root / "docs/downloads/h56-multiscale-tensor-persistence-40000dots-20261009T162812Z-zeros.tif"
    result = subprocess.run(
        [sys.executable, str(root / "scripts/validate_submission.py"), str(candidate),
         "--template", str(tmp_path / "missing-template.tif"),
         "--labels", str(tmp_path / "missing-labels.tif")],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 2
    assert "BLOCKED: full submission validation needs" in result.stderr
    assert "MISSING" in result.stderr
    assert "Traceback" not in result.stderr
