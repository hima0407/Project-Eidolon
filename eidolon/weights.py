"""Component mass estimate: Raymer general-aviation statistical equations.

Raymer, Aircraft Design: A Conceptual Approach, 6th ed., sec. 15.3.3 (eqs. 15.46-15.58),
evaluated in imperial units (lb, ft, psf) as published, then converted to kg.
Composite fudge factors from Raymer Table 15.4 ('advanced composites').
A single calibration factor is fitted on the Hansa-NG (published empty mass 540 kg,
also an all-composite two-seat trainer) and applied unchanged to Eidolon.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from . import atmosphere as isa
from .aircraft import Aircraft, OCCUPANT_KG
from .engines import ENGINES, FUEL_DENSITY

LB = 0.45359237
FT = 0.3048
COMPOSITE = {"wing": 0.85, "tail": 0.83, "fuselage": 0.90, "gear": 0.95}


@dataclass
class MassBreakdown:
    items: dict = field(default_factory=dict)      # kg
    calibration: float = 1.0

    @property
    def empty(self) -> float:
        return sum(self.items.values())


def raymer_ga(ac: Aircraft, v_cruise: float = 55.6, h_cruise: float = 1500.0, calibration: float = 1.0,
              avionics_uninstalled_lb: float = 30.0) -> MassBreakdown:
    w, ht, vt, f = ac.wing, ac.htail, ac.vtail, ac.fuselage
    Wdg = ac.mtow / LB
    Nz = 1.5 * ac.n_limit
    q = 0.5 * float(isa.density(h_cruise)) * v_cruise**2 * 0.020885   # Pa -> psf
    Sw = w.area / FT**2
    Wfw = ac.fuel_capacity_l * FUEL_DENSITY / LB
    lam = w.taper
    cosL = math.cos(math.radians(w.sweep_c4_deg))
    tc = w.t_c_root

    W_wing = 0.036 * Sw**0.758 * Wfw**0.0035 * (w.aspect_ratio / cosL**2) ** 0.6 * q**0.006 \
        * lam**0.04 * (100 * tc / cosL) ** -0.3 * (Nz * Wdg) ** 0.49

    Sht = ht.area / FT**2
    cosLh = math.cos(math.radians(ht.sweep_c4_deg))
    W_ht = 0.016 * (Nz * Wdg) ** 0.414 * q**0.168 * Sht**0.896 * (100 * ht.t_c_root / cosL) ** -0.12 \
        * (ht.aspect_ratio / cosLh**2) ** 0.043 * ht.taper**-0.02

    Svt = vt.area / FT**2
    cosLv = math.cos(math.radians(vt.sweep_c4_deg))
    W_vt = 0.073 * (1 + 0.2 * 0.0) * (Nz * Wdg) ** 0.376 * q**0.122 * Svt**0.873 \
        * (100 * vt.t_c_root / cosLv) ** -0.49 * (vt.aspect_ratio / cosLv**2) ** 0.357 * vt.taper**0.039

    Sf = f.wetted_area / FT**2
    Lt = ac.tail_arm_h / FT
    LD = f.length / f.d_equiv
    W_fus = 0.052 * Sf**1.086 * (Nz * Wdg) ** 0.177 * Lt**-0.051 * LD**-0.072 * q**0.241

    Nl = 1.5 * 3.0
    Wl = Wdg
    W_mlg = 0.095 * (Nl * Wl) ** 0.768 * (ac.gear.main_leg_length / FT / 12) ** 0.409 * 1.0
    W_nlg = 0.125 * (Nl * Wl) ** 0.566 * (ac.gear.nose_leg_length / FT / 12) ** 0.845

    eng = ENGINES[ac.engine_key]

    Vt = ac.fuel_capacity_l / 3.785411784
    W_fs = 2.49 * Vt**0.726 * (1 / (1 + 0.0)) ** 0.363 * 2**0.242 * 1**0.157
    W_fc = 0.053 * (f.length / FT) ** 1.536 * (w.span / FT) ** 0.371 * (Nz * Wdg * 1e-4) ** 0.80
    W_hyd = 0.001 * Wdg
    W_av = 2.117 * avionics_uninstalled_lb**0.933
    W_el = 12.57 * (W_fs + W_av) ** 0.51
    W_furn = 0.0582 * Wdg - 65
    W_heat = 0.265 * Wdg**0.52 * ac.occupants**0.68 * W_av**0.17 * 0.17**0.08 * 0.5   # cabin heat only [A]

    items = {
        "Wing": W_wing * COMPOSITE["wing"],
        "Horizontal tail": W_ht * COMPOSITE["tail"],
        "Vertical tail": W_vt * COMPOSITE["tail"],
        "Fuselage": W_fus * COMPOSITE["fuselage"],
        "Main gear": W_mlg * COMPOSITE["gear"],
        "Nose gear": W_nlg * COMPOSITE["gear"],
        "Fuel system": W_fs,
        "Flight controls": W_fc,
        "Hydraulics/brakes": W_hyd,
        "Avionics (glass)": W_av,
        "Electrical": W_el,
        "Furnishings": W_furn,
        "Cabin heat & vent": W_heat,
    }
    items = {k: v * LB * calibration for k, v in items.items()}
    # powerplant is built bottom-up from manufacturer data (not statistical, not calibrated)
    items = {**powerplant_kg(eng), **items}
    return MassBreakdown(items, calibration)


def powerplant_kg(eng) -> dict:
    """Firewall-forward mass, bottom-up. Engine from the data sheet; the rest are [A] allowances
    typical of Rotax/UL installations (constant-speed composite propeller, cooling, mount, cowling)."""
    prop = 11.0 if eng.p_takeoff_kw < 90 else (13.5 if eng.p_takeoff_kw < 120 else 17.0)
    cooling = 6.0 if eng.cooling != "air" else 3.5          # radiators+coolant+oil  vs. baffles+oil cooler
    mount = 3.5 if eng.mass_kg < 90 else 4.5
    return {"Engine (data sheet)": eng.mass_kg, "Propeller + governor": prop + 1.5,
            "Cooling, mount, cowling": cooling + mount + 6.0}


GROUPS = {
    "Structure": ["Wing", "Horizontal tail", "Vertical tail", "Fuselage", "Main gear", "Nose gear"],
    "Powerplant": ["Engine (data sheet)", "Propeller + governor", "Cooling, mount, cowling", "Fuel system"],
    "Systems": ["Flight controls", "Hydraulics/brakes", "Avionics (glass)", "Electrical", "Cabin heat & vent"],
    "Furnishings": ["Furnishings"],
}


def grouped(m: MassBreakdown) -> dict:
    out = {g: sum(m.items.get(k, 0.0) for k in ks) for g, ks in GROUPS.items()}
    extra = {k: v for k, v in m.items.items() if not any(k in ks for ks in GROUPS.values())}
    out.update(extra)
    return out


def calibrate_on(ac, target_empty_kg: float, **kw) -> float:
    """Single factor on the statistical items so the model reproduces a known empty mass."""
    m = raymer_ga(ac, calibration=1.0, **kw)
    pp = sum(powerplant_kg(ENGINES[ac.engine_key]).values())
    return (target_empty_kg - pp) / (m.empty - pp)


def payload_kg(ac: Aircraft) -> float:
    return ac.occupants * OCCUPANT_KG + ac.baggage_kg


def max_fuel_kg(ac: Aircraft, empty_kg: float) -> float:
    """Fuel that fits under MTOW with full payload, limited by tank capacity."""
    by_mass = ac.mtow - empty_kg - payload_kg(ac)
    return max(0.0, min(by_mass, ac.fuel_capacity_l * FUEL_DENSITY))
