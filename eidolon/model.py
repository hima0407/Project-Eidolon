"""Assemble a complete analysis model (aero + mass + propulsion) for one aircraft.

Mass: bottom-up, load-sized structure plus a certified-trainer class allowance measured on three
published aircraft (eidolon/structures.py, studies/01_mass_estimation.py). Raymer x MASS_CAL is kept
as a cross-check (mass_method="raymer").
The two performance calibration factors are fitted once on the Hansa-NG and then applied
unchanged to Eidolon (see studies/02_calibrate_on_hansa.py):
    MASS_CAL  - (cross-check only) Raymer statistical items so Hansa-NG empty mass = 540 kg
    DRAG_CAL  - additive unmodelled CD0 so Hansa-NG max cruise = 200 km/h at the
                assumed cruise power setting (CRUISE_POWER_FRACTION of take-off power at CRUISE_ALT)
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from .aero import build_polar
from .aircraft import Aircraft, G
from .engines import ENGINES
from .performance import Plane
from .propeller import BEMTPropeller, PropMap
from .weights import raymer_ga, payload_kg, max_fuel_kg

CRUISE_ALT = 1500.0              # m, Eidolon design cruise altitude (requirements.md)
CRUISE_POWER_FRACTION = 0.75     # 'max cruise' read as 75 % of rated power [A], tested 65-85 %
V_CRUISE = 200 / 3.6             # m/s

# fitted by studies/02_calibrate_on_hansa.py (written to results/02_calibration/calibration.json);
# the defaults below are used only if that file has not been generated yet
MASS_CAL = 1.3523
DRAG_CAL = 0.00825
CLIMB_CAL = 0.8658

import json as _json
from pathlib import Path as _Path
_CAL = _Path(__file__).resolve().parents[1] / "results" / "02_calibration" / "calibration.json"
if _CAL.exists():
    _c = _json.loads(_CAL.read_text())
    MASS_CAL, DRAG_CAL, CLIMB_CAL = _c["mass_cal"], _c["drag_cal"], _c["climb_cal"]


@lru_cache(maxsize=32)
def prop_map(diameter: float, blades: int, chord_scale: float = 1.0) -> PropMap:
    return PropMap(BEMTPropeller(diameter, blades, chord_scale=chord_scale))


@dataclass
class Model:
    ac: Aircraft
    plane: Plane
    polar: object
    drag: object
    lift: object
    mass: object
    empty_kg: float
    fuel_kg: float          # max fuel with full design payload
    payload_kg: float

    @property
    def W(self):
        return self.ac.mtow * G


def build(ac: Aircraft, drag_cal: float | None = None, mass_cal: float | None = None,
          eta_install: float = 0.92, extra_empty_kg: float = 0.0, climb_factor: float | None = None,
          mass_method: str = "bottom_up", allowance_kg: float | None = None) -> Model:
    """mass_method: 'bottom_up' (default, eidolon.structures: load-sized items + measured class
    allowance) or 'raymer' (statistical equations x MASS_CAL, kept as an independent cross-check)."""
    drag_cal = DRAG_CAL if drag_cal is None else drag_cal
    mass_cal = MASS_CAL if mass_cal is None else mass_cal
    eng = ENGINES[ac.engine_key]
    polar, db, lm = build_polar(ac, calibration=drag_cal, engine=eng)
    if mass_method == "raymer":
        m = raymer_ga(ac, calibration=mass_cal)
        if extra_empty_kg:
            m.items["Design features (explicit)"] = extra_empty_kg
    else:
        from .structures import empty_mass_model, MassAdapter
        extra = {"Design features (explicit)": extra_empty_kg} if extra_empty_kg else None
        m = MassAdapter(empty_mass_model(ac, extra, allowance_kg))
    empty = m.empty
    fuel = max_fuel_kg(ac, empty)
    pm = prop_map(ac.prop.diameter, ac.prop.blades, round(ac.prop.chord_scale, 3))
    cf = CLIMB_CAL if climb_factor is None else climb_factor
    plane = Plane(ac.name, ac.wing.area, polar, eng, pm, eta_install, cf)
    return Model(ac, plane, polar, db, lm, m, empty, fuel, payload_kg(ac))
