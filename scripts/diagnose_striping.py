#!/usr/bin/env python3
"""Measure the airborne survey-line direction and the striping strength.

Writes evidence/striping_diagnostic.json.  Every number in the run card that
talks about flight lines comes from here.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems55 import fields55, io55, tensor55  # noqa: E402

OUT = ROOT / "evidence" / "striping_diagnostic.json"


def long_lag_coherence(field: np.ndarray, valid: np.ndarray, lag: int) -> dict[str, float]:
    """Pearson correlation between the field and itself shifted by ``lag`` pixels.

    Computed along x (east-west) and along y (north-south).  Airborne line
    artefacts are coherent along the flight-line direction over tens of
    kilometres, so the along-track coherence at a long lag identifies the
    flight-line direction directly and independently of the spectrum.
    """
    a = np.where(valid, field, np.nan)
    out = {}
    for axis, name in ((1, "along_x_east_west"), (0, "along_y_north_south")):
        s1 = np.take(a, np.arange(0, a.shape[axis] - lag), axis=axis)
        s2 = np.take(a, np.arange(lag, a.shape[axis]), axis=axis)
        both = np.isfinite(s1) & np.isfinite(s2)
        x1, x2 = s1[both], s2[both]
        out[f"coherence_{name}"] = float(
            np.corrcoef(x1 - x1.mean(), x2 - x2.mean())[0, 1]
        )
        out[f"n_{name}"] = int(both.sum())
    return out


def synth_convention_check() -> dict:
    """Prove the azimuth convention: a field varying only in y => E-W flight lines."""
    ny = nx = 512
    yy = np.arange(ny)[:, None] * np.ones((1, nx))
    f = np.sin(2 * np.pi * yy / 23.0)
    v = np.ones_like(f, dtype=bool)
    d = fields55.measure_striping_axis(f, v, 100.0)
    out = {k: v for k, v in d.items() if k not in ("spectral_azimuth_deg", "spectral_energy")}
    out["expected_flight_line_axis_numpy"] = 1
    out["convention_ok"] = out["flight_line_axis_numpy"] == 1
    return out


def main() -> None:
    grid, _ = io55.read_template()
    res = io55.RES_M
    out: dict = {"grid": {"width": grid.width, "height": grid.height, "res_m": res}}
    out["synthetic_convention_check"] = synth_convention_check()

    for name, band in (("rtp_mag", io55.BAND_RTP_MAG), ("iso_grav", io55.BAND_ISO_GRAV)):
        f, v = io55.read_band(band)
        spec = fields55.measure_striping_axis(f, v, res)
        spec.pop("spectral_azimuth_deg"), spec.pop("spectral_energy")
        coh = long_lag_coherence(f, v, lag=60)
        bp, _ = fields55.prepare_field(f, v, res, along_axis=0, lowpass_m=400.0, highpass_m=6000.0)
        coh_bp = long_lag_coherence(bp, v, lag=60)
        out[name] = {"spectral": spec, "coherence_raw": coh, "coherence_bandpassed": coh_bp}

    # decision: the flight-line axis is the one with the higher long-lag coherence
    votes = []
    for name in ("rtp_mag", "iso_grav"):
        cb = out[name]["coherence_bandpassed"]
        votes.append("east-west" if cb["coherence_along_x_east_west"] > cb["coherence_along_y_north_south"] else "north-south")
        votes_spec = out[name]["spectral"]["flight_line_direction"]
        out[name]["agreement_spectral_vs_coherence"] = votes_spec == votes[-1]
    out["decision"] = {
        "flight_line_direction_long_lag_coherence": votes,
        "flight_line_direction_spectral": [out[n]["spectral"]["flight_line_direction"] for n in ("rtp_mag", "iso_grav")],
        "lane_brief_asserts": "east-west",
        "measurement_used": "north-south" if votes.count("north-south") >= votes.count("east-west") else "east-west",
        "brief_contradicted": votes.count("north-south") > votes.count("east-west"),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2))
    print(json.dumps(out["decision"], indent=2))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
