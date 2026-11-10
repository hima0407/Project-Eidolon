"""Aircraft definitions: Project Eidolon and the Hansa-NG benchmark.

Hansa-NG published data (CSIR-NAL Hansa-NG brochure, 2020):
  MTOW 750 kg, empty 540 kg, useful 210 kg, 95 L usable fuel, span 10.47 m,
  wing area 12.47 m^2, length 7.658 m, height 2.614 m, cabin width 1.07 m,
  Rotax 912 iSc 100 hp, MTV-21-A/175-05 propeller, max cruise 200 km/h (108 KTAS),
  stall 80 km/h (flaps 20 deg), max ROC 3.3 m/s (650 ft/min), ceiling 10,000 ft,
  take-off 450 m, landing 600 m, range 926 km (500 nm) with 45 min reserve,
  endurance 6 h.
Everything NAL does not publish (taper, airfoil, tail sizes, gear details) is an
assumption marked [A] and is given generic light-trainer values, so the benchmark
is not tuned to lose.
"""
from __future__ import annotations

import copy
import math
from dataclasses import dataclass, field

from .geometry import Surface, Fuselage, LandingGear, Flaps, Propeller

G = 9.80665
OCCUPANT_KG = 77.0      # 170 lb standard occupant (FAA AC 120-27 / CS-23 practice)


@dataclass
class Aircraft:
    name: str
    mtow: float
    wing: Surface
    htail: Surface
    vtail: Surface
    fuselage: Fuselage
    gear: LandingGear
    flaps: Flaps
    prop: Propeller
    engine_key: str
    fuel_capacity_l: float
    wing_laminar_fraction: float       # mean of upper/lower transition x/c in cruise
    tail_laminar_fraction: float
    fuselage_laminar_fraction: float
    cl_max_2d_clean: float             # section clmax at landing Reynolds number
    interference_wing: float = 1.0     # Raymer Q factors
    interference_tail: float = 1.04
    interference_fuse: float = 1.0
    canopy_dq_m2: float = 0.0          # extra canopy drag area beyond the fuselage body [m^2]
    leakage_fraction: float = 0.05     # leakage + protuberances, fraction of CD0 (Raymer: 2-5 %, props up to 10 %)
    n_limit: float = 4.4               # limit manoeuvre load factor (CS-23 utility)
    occupants: int = 2
    baggage_kg: float = 10.0
    # longitudinal stations [m, from propeller plane] used for CG
    x_engine: float = 0.55
    x_firewall: float = 1.05
    x_panel: float = 1.55
    x_seat: float = 2.25
    x_baggage: float = 2.95
    x_nose_gear: float = 0.80
    x_main_gear_offset: float = 0.30   # main gear behind aft CG limit
    eta_h: float = 0.90                # tail dynamic-pressure ratio
    notes: dict = field(default_factory=dict)

    # --- convenience ---
    @property
    def weight(self) -> float:
        return self.mtow * G

    @property
    def wing_loading(self) -> float:
        return self.weight / self.wing.area

    @property
    def tail_arm_h(self) -> float:
        return self.htail.x_ac - self.wing.x_ac

    @property
    def tail_arm_v(self) -> float:
        return self.vtail.x_ac - self.wing.x_ac

    @property
    def vh(self) -> float:
        return self.htail.area * self.tail_arm_h / (self.wing.area * self.wing.mac)

    @property
    def vv(self) -> float:
        return self.vtail.area * self.tail_arm_v / (self.wing.area * self.wing.span)

    def copy(self, **changes) -> "Aircraft":
        a = copy.deepcopy(self)
        for k, v in changes.items():
            setattr(a, k, v)
        return a


def place_tails(ac: Aircraft, vh: float, vv: float) -> Aircraft:
    """Size the tails from volume coefficients with their roots placed at the fuselage end.

    Raymer Table 6.4 (general aviation, single engine): V_h = 0.70, V_v = 0.04.
    Iterates because tail area moves the tail a.c.
    """
    L = ac.fuselage.length
    for _ in range(20):
        ht, vt = ac.htail, ac.vtail
        ht.x_le_root = L - ht.c_root - 0.05
        vt.x_le_root = L - vt.c_root - 0.05
        lh, lv = ht.x_ac - ac.wing.x_ac, vt.x_ac - ac.wing.x_ac
        ht.area = vh * ac.wing.area * ac.wing.mac / lh
        vt.area = vv * ac.wing.area * ac.wing.span / lv
    return ac


def eidolon(engine_key: str = "912iSc", wing_area: float = 14.15, span: float = 11.0) -> Aircraft:
    """Project Eidolon baseline.

    Wing geometry is the team's locked XFLR5 wing (span 11.0 m, S 14.152 m^2,
    MAC 1.312 m -> taper ~0.6, -2 deg washout, NACA 63-415 root blending to 63-412 tip).
    """
    ar = span**2 / wing_area
    wing = Surface("wing", wing_area, ar, 0.60, 0.15, 0.12, sweep_c4_deg=0.0, dihedral_deg=5.0,
                   twist_tip_deg=-2.0, x_le_root=1.95, z_root=-0.45, x_t=0.35,
                   airfoil_root="naca63415", airfoil_tip="n63412")
    ht = Surface("htail", 2.6, 4.6, 0.70, 0.12, 0.12, sweep_c4_deg=4.0, x_t=0.30,
                 airfoil_root="naca0012", airfoil_tip="naca0012", z_root=0.10)
    vt = Surface("vtail", 1.3, 1.35, 0.55, 0.10, 0.09, sweep_c4_deg=25.0, x_t=0.30, vertical=True,
                 airfoil_root="naca0012", airfoil_tip="naca0009", z_root=0.30)
    fus = Fuselage(length=7.10, width=1.16, height=1.28)
    gear = LandingGear(wheel_fairings=True, main_leg="faired composite leaf", nose_leg_faired=True)
    ac = Aircraft(
        name="Eidolon", mtow=750.0, wing=wing, htail=ht, vtail=vt, fuselage=fus, gear=gear,
        flaps=Flaps("single slotted", 0.62, 0.28, 30.0, 15.0), prop=Propeller(1.75, 3, True),
        engine_key=engine_key, fuel_capacity_l=100.0,
        wing_laminar_fraction=0.35, tail_laminar_fraction=0.25, fuselage_laminar_fraction=0.05,
        cl_max_2d_clean=1.50, interference_wing=1.0, interference_tail=1.04, interference_fuse=1.0,
        canopy_dq_m2=0.025,
        notes={
            "wing_laminar_fraction": "[XFLR5 polar] NACA 63-415 at cruise CL~0.35 shows Xtr ~0.35-0.5 top, ~0.3-0.4 bottom (free transition, Ncrit 9); 0.35 keeps margin for real-surface contamination",
            "cl_max_2d_clean": "[A] Abbott & von Doenhoff: NACA 63-415 smooth clmax ~1.6 at Re 6e6; 1.50 used at landing Re ~2.5e6",
            "canopy": "[A] bubble canopy increment 0.025 m^2 (same value for both aircraft)",
        })
    return place_tails(ac, vh=0.65, vv=0.040)


def hansa_ng() -> Aircraft:
    """CSIR-NAL Hansa-NG as published, with generic assumptions where data is missing."""
    span, area = 10.47, 12.47
    wing = Surface("wing", area, span**2 / area, 0.60, 0.15, 0.12, dihedral_deg=5.0,
                   twist_tip_deg=-2.0, x_le_root=1.95, z_root=-0.45, x_t=0.30,
                   airfoil_root="naca23012", airfoil_tip="naca23012")
    ht = Surface("htail", 2.4, 4.4, 0.70, 0.12, 0.12, sweep_c4_deg=4.0, x_t=0.30, z_root=0.10)
    vt = Surface("vtail", 1.3, 1.5, 0.55, 0.10, 0.09, sweep_c4_deg=25.0, x_t=0.30, vertical=True, z_root=0.30)
    fus = Fuselage(length=7.40, width=1.17, height=1.30)
    gear = LandingGear(wheel_fairings=True, main_leg="flat spring leg", nose_leg_faired=False)
    ac = Aircraft(
        name="Hansa-NG", mtow=750.0, wing=wing, htail=ht, vtail=vt, fuselage=fus, gear=gear,
        flaps=Flaps("single slotted", 0.62, 0.25, 20.0, 10.0), prop=Propeller(1.75, 3, True),
        engine_key="912iSc", fuel_capacity_l=95.0,
        wing_laminar_fraction=0.15, tail_laminar_fraction=0.15, fuselage_laminar_fraction=0.05,
        cl_max_2d_clean=1.55, canopy_dq_m2=0.025,
        notes={
            "published": "CSIR-NAL Hansa-NG brochure (2020)",
            "assumed": "[A] taper, airfoil family, tail sizes, gear details, laminar fractions are generic light-trainer values",
            "fuselage_length": "[A] body length 7.40 m (overall 7.658 m includes spinner and rudder overhang)",
        })
    return place_tails(ac, vh=0.65, vv=0.040)


# Published Hansa-NG figures used as calibration / validation targets
HANSA_PUBLISHED = {
    "empty_mass_kg": 540.0,
    "max_cruise_kmh": 200.0,
    "stall_kmh_flaps20": 80.0,
    "roc_ms": 3.3,
    "ceiling_m": 3048.0,
    "takeoff_m": 450.0,
    "landing_m": 600.0,
    "range_km": 926.0,
    "endurance_h": 6.0,
    "fuel_l": 95.0,
    "source": "CSIR-NAL, Hansa-NG brochure (Jan 2020), nal.res.in",
}
