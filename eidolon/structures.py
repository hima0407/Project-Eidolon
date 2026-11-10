"""Bottom-up (physics-based) mass estimate.

Why a second mass method: Raymer's statistical equations know only gross parameters
(area, aspect ratio, load factor...). They cannot tell a deep 15 % laminar wing with carbon
spar caps from a 12 % glass wing. Here every structural item is SIZED from its load, so the
mass follows Eidolon's actual geometry and materials. Every item is then given an
uncertainty band according to how it was obtained, and the empty mass becomes a distribution
(eidolon.structures.monte_carlo).

Wing (per semispan, n_ult = 1.5 x 4.4 = 6.6, zero fuel = no fuel bending relief, conservative):
    spanwise lift shape   from the lifting-line solution (washout included)
    shear, bending        V(y) = int_y^{b/2} (L' - n g m') dy,   M(y) = int_y^{b/2} V dy
    spar caps (CFRP UD)   A_cap(y) = M(y) / (h_eff(y) sigma_c),   h_eff = 0.85 (t/c) c
    shear web (CFRP +-45) t_web(y) = max(V / (h tau), t_min)
    skins (GFRP sandwich) areal density x wetted area   (minimum-gauge driven for a light aircraft)
    ribs, rear spar, control surfaces, fittings, sealing, paint: explicit allowances
Tails: spar sized for the CS-23 manoeuvring tail load at V_A (CL_h 1.0, x1.5), sandwich skins.
Fuselage: composite sandwich shell by area (cabin / tail cone), floor, bulkheads, firewall,
    seat structure for 9 g crash loads, canopy, tail-cone bending check.
Systems, furnishings, gear: catalogue / bottom-up items.
Material allowables are design (ultimate, after environmental and damage-tolerance knock-downs)
values typical of light composite aircraft practice [A].
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from . import atmosphere as isa
from .aircraft import Aircraft, G
from .engines import ENGINES, FUEL_DENSITY
from .lifting_line import LiftingLine
from .weights import powerplant_kg

MAT = {
    "cfrp_ud": dict(rho=1550.0, sigma=550e6),       # spar caps, compression-critical design ultimate
    "cfrp_biax": dict(rho=1500.0, tau=120e6),       # +-45 shear webs
    "skin_wing": 2.05,                              # kg/m2: 2x(2 plies 200 g/m2 glass) faces + 5 mm foam + resin/adhesive
    "skin_tail": 1.55,                              # kg/m2: lighter sandwich
    "skin_cabin": 2.60,                             # kg/m2: thicker faces, local carbon reinforcement
    "skin_cone": 2.10,
    "paint": 0.22,                                  # kg/m2 filler + primer + paint
}
T_WEB_MIN = 0.8e-3
CAP_MIN = 40e-6                                     # m2 minimum cap area at the tip (handling, fittings)


@dataclass
class Item:
    name: str
    group: str
    mass: float
    spread: float        # +- fraction (1 sigma)
    basis: str           # how it was obtained


@dataclass
class MassModel:
    items: list = field(default_factory=list)

    def add(self, *a):
        self.items.append(Item(*a))

    @property
    def total(self):
        return sum(i.mass for i in self.items)

    def group(self, g):
        return sum(i.mass for i in self.items if i.group == g)

    def groups(self):
        out = {}
        for i in self.items:
            out[i.group] = out.get(i.group, 0.0) + i.mass
        return out

    def as_dict(self):
        return {i.name: i.mass for i in self.items}


# ------------------------------------------------------------------------------------ wing
@dataclass
class WingStructure:
    y: np.ndarray
    shear: np.ndarray
    moment: np.ndarray
    cap_area: np.ndarray
    web_t: np.ndarray
    masses: dict


def wing_structure(ac: Aircraft, n_ult: float | None = None, iterations: int = 4) -> WingStructure:
    w = ac.wing
    n = n_ult or 1.5 * ac.n_limit
    W = ac.weight
    half = w.span / 2
    y = np.linspace(ac.fuselage.width / 2, half, 80)
    eta = y / half
    c = w.chord_at(eta)
    tc = w.t_c_root + (w.t_c_tip - w.t_c_root) * eta
    h = 0.85 * tc * c
    # lift shape from the lifting line at a high CL (washout included)
    ll = LiftingLine(w)
    r = ll.solve(10.0)
    gam = np.interp(eta, r.eta, r.cl_local * r.c_local, right=0.0)
    gam[-1] = 0.0
    lift = gam / np.trapezoid(gam, y) * (n * W / 2)           # N/m on the exposed semispan (body lift ignored)
    m_lin = np.full_like(y, 8.0)                               # first guess, kg/m
    for _ in range(iterations):
        q = lift - n * G * m_lin
        V = np.array([np.trapezoid(q[i:], y[i:]) for i in range(len(y))])
        M = np.array([np.trapezoid(V[i:], y[i:]) for i in range(len(y))])
        A = np.maximum(M / (h * MAT["cfrp_ud"]["sigma"]), CAP_MIN)
        tw = np.maximum(np.abs(V) / (h * MAT["cfrp_biax"]["tau"]), T_WEB_MIN)
        cap_lin = 2 * A * MAT["cfrp_ud"]["rho"]
        web_lin = tw * h * MAT["cfrp_biax"]["rho"]
        skin_lin = MAT["skin_wing"] * 2.04 * c                 # upper + lower surface, arc length ~1.02 c each
        rib_lin = 0.32 * c * tc * c / 0.45 * 2.0 * 1.0         # foam-sandwich ribs every 0.45 m, 2 kg/m2 [A]
        m_lin = cap_lin + web_lin + skin_lin + rib_lin
    semi = lambda f: float(np.trapezoid(f, y))
    caps = 2 * semi(cap_lin)
    # caps continue through the fuselage as the carry-through at root size
    caps += 2 * A[0] * MAT["cfrp_ud"]["rho"] * ac.fuselage.width
    webs = 2 * semi(web_lin)
    skins = 2 * semi(skin_lin)
    ribs = 2 * semi(rib_lin)
    rear_spar = 0.35 * webs + 2 * semi(0.0012 * 0.5 * tc * c * MAT["cfrp_biax"]["rho"] * np.ones_like(y))
    fl = ac.flaps
    S_ctrl = 2 * semi(np.where(eta < 0.97, 0.26 * c, 0.0))      # flaps + ailerons ~26 % chord over the span
    ctrl = 3.1 * S_ctrl                                         # kg/m2 incl. hinges, horns, mass balance [A]
    fittings = 2.0 + 1.0e-5 * M[0] / h[0]                       # root lugs/pins sized by cap force, + misc
    sealing = 0.035 * ac.fuel_capacity_l                        # integral-tank sealing, baffles, sumps
    paint = MAT["paint"] * w.wetted_area(ac.fuselage.width)
    masses = {"Wing spar caps (CFRP)": caps, "Wing shear webs": webs, "Wing skins (sandwich)": skins,
              "Wing ribs": ribs, "Wing rear spar": rear_spar, "Flaps + ailerons": ctrl,
              "Wing root fittings": fittings, "Tank sealing": sealing, "Wing paint": paint}
    return WingStructure(y, V, M, A, tw, masses)


def tail_mass(ac: Aircraft, surf, V_A: float, horizontal: bool = True) -> tuple:
    """Spar sized for a CS-23-style manoeuvring tail load (CL_h 1.0 at V_A, x1.5), sandwich skins."""
    q = 0.5 * isa.RHO0 * V_A**2
    L_ult = 1.5 * q * surf.area * 1.0
    semi = surf.semispan
    root_M = L_ult / (2 if horizontal else 1) * semi * 0.42   # elliptic-ish loading centroid
    h = 0.85 * surf.t_c_root * surf.c_root
    cap = 2 * (root_M / (h * MAT["cfrp_ud"]["sigma"])) * MAT["cfrp_ud"]["rho"] * semi * 0.5 * (2 if horizontal else 1)
    skin = MAT["skin_tail"] * 2.04 * surf.area
    ribs_ctrl = 0.9 * surf.area                       # ribs, elevator/rudder spar, hinges, horns [A]
    paint = MAT["paint"] * 2.04 * surf.area
    return cap + skin + ribs_ctrl + paint, {"spar": cap, "skin": skin, "ribs+ctrl": ribs_ctrl, "paint": paint}


def fuselage_mass(ac: Aircraft, tail_load_N: float) -> dict:
    f = ac.fuselage
    S = f.wetted_area
    x_cabin_end = ac.x_baggage + 0.45
    frac_cabin = min(0.62, x_cabin_end / f.length * 1.05)
    shell = MAT["skin_cabin"] * S * frac_cabin + MAT["skin_cone"] * S * (1 - frac_cabin)
    # tail-cone bending check: thin-walled ellipse, CFRP longeron strips if the sandwich face is not enough
    arm = ac.htail.x_ac - x_cabin_end
    M = tail_load_N * arm
    d = 0.55                                           # cone depth at the cabin end [m]
    face_area = M / (0.5 * d * 250e6)                  # glass face allowable 250 MPa
    longerons = max(0.0, face_area - 2 * 0.0007 * 0.25) * 2 * arm * MAT["cfrp_ud"]["rho"]
    return {"Fuselage shell (sandwich)": shell, "Tail-cone longerons": longerons,
            "Floor + keel + wing carry-through box": 9.0, "Bulkheads + firewall": 7.5,
            "Seat structure (9 g crash loads)": 6.0, "Canopy (PC 3 mm) + frame": 9.5,
            "Fuselage paint": MAT["paint"] * S}


def bottom_up(ac: Aircraft, extra: dict | None = None) -> MassModel:
    mm = MassModel()
    ws = wing_structure(ac)
    spreads = {"Wing spar caps (CFRP)": 0.10, "Wing shear webs": 0.12, "Wing skins (sandwich)": 0.12,
               "Wing ribs": 0.25, "Wing rear spar": 0.25, "Flaps + ailerons": 0.15, "Wing root fittings": 0.30,
               "Tank sealing": 0.30, "Wing paint": 0.20}
    for k, v in ws.masses.items():
        mm.add(k, "Wing", v, spreads[k], "sized from 6.6 g bending/shear" if "spar" in k or "web" in k else "areal / allowance")
    VS1 = math.sqrt(2 * ac.wing_loading / (isa.RHO0 * 1.25))
    VA = VS1 * math.sqrt(ac.n_limit)
    mh, _ = tail_mass(ac, ac.htail, VA, True)
    mv, _ = tail_mass(ac, ac.vtail, VA, False)
    mm.add("Horizontal tail", "Tail", mh * ac.ht_mass_factor, 0.15, "spar sized for tail load at V_A")
    mm.add("Vertical tail", "Tail", mv * ac.vt_mass_factor, 0.15, "spar sized for tail load at V_A")
    if ac.ventral_strake_m2:
        mm.add("Ventral strake", "Tail", 2.6 * ac.ventral_strake_m2, 0.2, "sandwich panel")
    tail_load = 1.5 * 0.5 * isa.RHO0 * VA**2 * ac.htail.area
    for k, v in fuselage_mass(ac, tail_load).items():
        mm.add(k, "Fuselage", v, 0.12 if "shell" in k else 0.20, "area x sandwich density" if "shell" in k else "bottom-up allowance")
    # landing gear (main legs from the leaf-spring sizing at a fatigue-conscious 450 MPa)
    from .landing_gear import size_leaf, MATERIALS
    m_leaf = 2 * size_leaf(ac.weight, ac.wing_loading, "S-glass/epoxy UD").mass_per_leg_kg * (700 / 450) ** 2
    mm.add("Main gear legs (S-glass leaf)", "Landing gear", m_leaf, 0.20, "sized: CS-23.473 energy")
    mm.add("Main wheels, tyres, brakes, axles", "Landing gear", 2 * 4.3, 0.05, "catalogue (5.00-5 wheel + disc brake)")
    mm.add("Nose gear (leg, fork, wheel, shimmy damper)", "Landing gear", 8.5, 0.15, "catalogue-class")
    mm.add("Wheel fairings + leg fairings", "Landing gear", 4.0 if ac.gear.wheel_fairings else 0.0, 0.25, "composite shells")
    # powerplant (same bottom-up items as weights.powerplant_kg) + fuel system
    eng = ENGINES[ac.engine_key]
    for k, v in powerplant_kg(eng).items():
        mm.add(k, "Powerplant", v, 0.03 if "data sheet" in k else 0.15, "data sheet" if "data sheet" in k else "allowance")
    mm.add("Exhaust + intake + airbox", "Powerplant", 4.0, 0.20, "allowance")
    mm.add("Fuel system (pumps, lines, valves, gauging)", "Powerplant", 3.0 + 0.03 * ac.fuel_capacity_l, 0.20, "allowance")
    # systems & furnishings (catalogue-class, typical for a Rotax glass-cockpit trainer)
    for name, m, sp in (("Flight controls (dual sticks, pedals, pushrods, cables)", 9.5, 0.15),
                        ("Electrical (battery, wiring, breakers)", 12.0, 0.15),
                        ("Avionics (2 EFIS, radio, transponder, ELT, antennas)", 11.0, 0.10),
                        ("Brake system", 1.5, 0.20), ("Cabin heat + ventilation", 2.5, 0.25),
                        ("Seats, belts, upholstery, baggage net", 15.0, 0.15),
                        ("Instruments, placards, misc. hardware", 4.0, 0.30)):
        mm.add(name, "Systems & furnishings", m, sp, "catalogue / allowance")
    for k, v in (extra or {}).items():
        mm.add(k, "Design features", v, 0.20, "explicit")
    return mm


def monte_carlo(mm: MassModel, n: int = 5000, seed: int = 7, common_offset: float = 0.0,
                offset_sigma: float = 0.0):
    """Sample every item independently (normal, sigma = spread x mass, truncated at 0)."""
    rng = np.random.default_rng(seed)
    masses = np.array([i.mass for i in mm.items]); sig = np.array([i.spread for i in mm.items]) * masses
    draws = np.maximum(rng.normal(masses, sig, size=(n, len(masses))), 0).sum(axis=1)
    if common_offset or offset_sigma:
        draws += rng.normal(common_offset, offset_sigma, size=n)
    return draws


# ------------------------------------------------------------------ certified-trainer class allowance
# Mass that every certified two-seat composite trainer carries and a load-sized bottom-up list does
# not capture (damage-tolerant skin gauges, crashworthiness, lightning/UV protection, interior trim,
# harness, unusable fuel, oil and coolant, certification equipment). Measured as the gap between the
# published empty mass and this bottom-up model on Hansa-NG, Aquila A210 and Diamond DV20
# (studies/01_mass_estimation.py, which overwrites these defaults via results/01_mass/class_allowance.json).
CLASS_ALLOWANCE_KG = 148.8
CLASS_ALLOWANCE_SD = 11.5
import json as _json
from pathlib import Path as _Path
_CA = _Path(__file__).resolve().parents[1] / "results" / "01_mass" / "class_allowance.json"
if _CA.exists():
    _d = _json.loads(_CA.read_text())
    CLASS_ALLOWANCE_KG, CLASS_ALLOWANCE_SD = _d["mean_kg"], _d["loo_rms_kg"]


class MassAdapter:
    """Gives a MassModel the .items / .empty interface the rest of the pipeline uses."""
    def __init__(self, mm: MassModel):
        self.model = mm
        self.items = mm.as_dict()

    @property
    def empty(self):
        return sum(self.items.values())


def empty_mass_model(ac: Aircraft, extra: dict | None = None, allowance: float | None = None) -> MassModel:
    mm = bottom_up(ac, extra)
    a = CLASS_ALLOWANCE_KG if allowance is None else allowance
    mm.add("Certified-trainer class allowance", "Class allowance", a,
           CLASS_ALLOWANCE_SD / max(a, 1e-9), "measured on 3 certified trainers (leave-one-out)")
    return mm
