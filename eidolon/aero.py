"""Aircraft-level aerodynamics: component drag build-up, lift, CLmax, drag polar.

Method: Raymer, Aircraft Design (6th ed.), sec. 12.5 'component build-up':
    CD0 = sum(Cf_c * FF_c * Q_c * Swet_c) / Sref + CD_misc + CD_L&P
Skin friction with a laminar run: the laminar part is replaced by the Blasius value
(Schlichting's mixed-flow correction, the 'equivalent turbulent start' approach is
not needed at this level).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from . import atmosphere as isa
from .aircraft import Aircraft
from .lifting_line import LiftingLine


# ---------------------------------------------------------------- skin friction
def cf_turbulent(re, mach=0.0):
    return 0.455 / (np.log10(re) ** 2.58 * (1 + 0.144 * mach**2) ** 0.65)


def cf_laminar(re):
    return 1.328 / np.sqrt(re)


def cf_mixed(re_L, x_tr):
    """Mean skin-friction coefficient with laminar flow over the first x_tr of the length.

    Cf = Cf_turb(Re_L) - x_tr * (Cf_turb(Re_tr) - Cf_lam(Re_tr)),  Re_tr = x_tr Re_L.
    """
    if x_tr <= 0:
        return cf_turbulent(re_L)
    re_tr = max(x_tr * re_L, 1e3)
    return cf_turbulent(re_L) - x_tr * (cf_turbulent(re_tr) - cf_laminar(re_tr))


# ---------------------------------------------------------------- form factors
def ff_wing(t_c, x_t, mach=0.15, sweep_m_rad=0.0):
    return (1 + 0.6 / x_t * t_c + 100 * t_c**4) * (1.34 * mach**0.18 * math.cos(sweep_m_rad) ** 0.28)


def ff_body(fineness):
    return 1 + 60 / fineness**3 + fineness / 400


# ---------------------------------------------------------------- drag build-up
@dataclass
class DragBreakdown:
    items: dict = field(default_factory=dict)   # name -> CD contribution
    sref: float = 1.0

    @property
    def cd0(self) -> float:
        return sum(self.items.values())


def drag_buildup(ac: Aircraft, V: float, h: float, dT: float = 0.0, calibration: float = 0.0,
                 engine_power_kw: float = 75.0, cooling: str = "liquid/air") -> DragBreakdown:
    """Parasite drag coefficient referenced to the wing area."""
    S = ac.wing.area
    mach = V / float(isa.speed_of_sound(h, dT))
    out = {}

    def surf(s, x_lam, Q, label):
        L = s.mac
        re = float(isa.reynolds(V, L, h, dT))
        cf = cf_mixed(re, x_lam)
        ff = ff_wing(s.t_c_mean, s.x_t, max(mach, 0.05))
        swet = s.wetted_area(ac.fuselage.width if label == "Wing" else 0.0)
        if label == "Vertical tail":
            swet = 2 * s.area * (1 + 0.25 * s.t_c_root)
        out[label] = cf * ff * Q * swet / S

    surf(ac.wing, ac.wing_laminar_fraction, ac.interference_wing, "Wing")
    surf(ac.htail, ac.tail_laminar_fraction, ac.interference_tail, "Horizontal tail")
    surf(ac.vtail, ac.tail_laminar_fraction, ac.interference_tail, "Vertical tail")

    f = ac.fuselage
    re_f = float(isa.reynolds(V, f.length, h, dT))
    out["Fuselage"] = cf_mixed(re_f, ac.fuselage_laminar_fraction) * ff_body(f.fineness) \
        * ac.interference_fuse * f.wetted_area / S
    out["Canopy"] = ac.canopy_dq_m2 / S

    # Landing gear, Raymer Table 12.6 drag-area-per-frontal-area (D/q)/A
    g = ac.gear
    wheel = 0.13 if g.wheel_fairings else 0.25            # faired wheel vs. regular wheel & tyre
    gear_dq = 2 * wheel * g.main_tyre_d * g.main_tyre_w + wheel * g.nose_tyre_d * g.nose_tyre_w
    if g.main_leg == "flat spring leg":
        gear_dq += 2 * 1.40 * g.main_leg_length * g.main_leg_thickness       # bare flat spring leg
    else:
        gear_dq += 2 * 0.05 * g.main_leg_length * g.main_leg_chord          # streamline strut 1/6<t/c<1/3
    gear_dq += (0.05 * g.nose_leg_length * g.nose_leg_width * 1.6) if g.nose_leg_faired \
        else (0.60 * g.nose_leg_length * g.nose_leg_width)                  # fork, faired axle and strut
    out["Landing gear"] = gear_dq / S

    # Cooling drag, Raymer eq. 12.43 (piston): D/q = 4.9e-7 * bhp * T^2 / (sigma V)  [ft^2, R, ft/s]
    T_R = float(isa.temperature(h, dT)) * 1.8
    sig = float(isa.sigma(h, dT))
    dq_ft2 = 4.9e-7 * (engine_power_kw / 0.7457) * T_R**2 / (sig * V / 0.3048)
    if cooling == "air":
        dq_ft2 *= 1.5                      # [A] air-cooled flat engines need more cooling mass flow
    out["Engine cooling"] = dq_ft2 * 0.0929 / S

    if ac.le_cuff:
        out["Leading-edge cuff"] = 0.0003
    if ac.ventral_strake_m2:
        re_s = float(isa.reynolds(V, 0.6, h, dT))
        out["Ventral strake"] = cf_turbulent(re_s) * 1.1 * 2 * ac.ventral_strake_m2 / S
    base = sum(out.values())
    out["Leakage & protuberances"] = ac.leakage_fraction * base
    if calibration != 0.0:
        # additive: the same unmodelled drag increment for every aircraft of the class (conservative
        # for comparisons - a multiplicative factor would scale Eidolon's savings up as well)
        out["Unmodelled (fitted on Hansa-NG)"] = calibration
    return DragBreakdown(out, S)


# ---------------------------------------------------------------- lift & polar
def oswald_raymer(AR: float) -> float:
    """Raymer eq. 12.48, straight-wing aircraft."""
    return 1.78 * (1 - 0.045 * AR**0.68) - 0.64


def oswald_nita_scholz(e_span: float, d_fus: float, span: float, k_d0: float = 0.864) -> float:
    """Nita & Scholz (DLRK 2012): e = e_theo * (1 - 2 (d_f/b)^2) * k_e,D0 (GA value 0.864)."""
    return e_span * (1 - 2 * (d_fus / span) ** 2) * k_d0


@dataclass
class LiftModel:
    cl_alpha_wing: float       # per rad, from LLT
    e_span: float
    e_oswald: float
    cl_max_clean: float
    cl_max_to: float
    cl_max_land: float
    alpha_first_stall_eta: float


FLAP_DCLMAX_2D = {"plain": 0.9, "split": 0.9, "single slotted": 1.3, "fowler": 1.3 * 1.15}


def lift_model(ac: Aircraft, a0=6.30, alpha0=-3.0) -> LiftModel:
    ll = LiftingLine(ac.wing, a0, alpha0)
    cla = ll.cl_alpha_per_rad()
    e_span = ll.solve(2.0).e_span
    cl_root = ac.cl_max_2d_clean
    cl_tip = ac.cl_max_2d_clean - 0.08          # thinner tip section and lower Re [A]
    CLmax_cs, _, eta_stall = ll.stall(cl_root, cl_tip)
    CLmax_raymer = 0.9 * cl_root                 # Raymer eq. 12.15 for unswept wings
    CLmax_clean = 0.5 * (CLmax_cs + CLmax_raymer)
    # trim loss: tail download, ~ (x_cg - x_ac)/l_h; take 4 % [A], plus fuselage blanking 3 % [A]
    CLmax_clean *= 0.93
    fl = ac.flaps
    # Raymer eq. 12.21: dCLmax = 0.9 dClmax (S_flapped/S) cos(L_hinge); dClmax scaled by deflection/40deg
    eta_in = ac.fuselage.width / 2 / ac.wing.semispan
    eta_out = fl.span_fraction
    c_in, c_out = ac.wing.chord_at(eta_in), ac.wing.chord_at(eta_out)
    s_flapped = (c_in + c_out) * (eta_out - eta_in) * ac.wing.semispan
    frac = s_flapped / ac.wing.area
    dcl2d = FLAP_DCLMAX_2D[fl.kind] * (fl.chord_fraction / 0.25) ** 0.5
    d_land = 0.9 * dcl2d * frac * min(1.0, fl.deflection_landing_deg / 40) ** 0.7 * 0.93
    d_to = 0.9 * dcl2d * frac * min(1.0, fl.deflection_takeoff_deg / 40) ** 0.7 * 0.93
    e_os = oswald_raymer(ac.wing.aspect_ratio)
    return LiftModel(cla, e_span, e_os, CLmax_clean, CLmax_clean + d_to, CLmax_clean + d_land, eta_stall)


@dataclass
class Polar:
    cd0: float
    k: float
    cl_max_clean: float
    cl_max_to: float
    cl_max_land: float
    def cd(self, cl):
        return self.cd0 + self.k * np.asarray(cl) ** 2


def build_polar(ac: Aircraft, calibration=0.0, V_ref=55.6, h_ref=1500.0, engine=None) -> tuple:
    from .engines import ENGINES
    eng = engine or ENGINES[ac.engine_key]
    db = drag_buildup(ac, V_ref, h_ref, calibration=calibration,
                      engine_power_kw=0.7 * eng.p_mcp_kw, cooling=eng.cooling)
    lm = lift_model(ac)
    k = 1 / (math.pi * lm.e_oswald * ac.wing.aspect_ratio)
    return Polar(db.cd0, k, lm.cl_max_clean, lm.cl_max_to, lm.cl_max_land), db, lm
