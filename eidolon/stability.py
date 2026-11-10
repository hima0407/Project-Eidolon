"""Longitudinal static stability and CG envelope.

Neutral point (stick-fixed), e.g. Etkin & Reid / Raymer sec. 16.3:
    h_n = [ h_ac,w - dCm_fus/dCL + eta_h (S_h/S)(l_h/c)(a_h/a)(1 - de/da) ]
          / [ 1 + eta_h (S_h/S)(a_h/a)(1 - de/da) ]
with h measured in MAC from the MAC leading edge,
    a, a_h   finite-surface lift slopes (Helmbold / DATCOM),
    de/da    = 2 a / (pi AR)  (downwash at the tail, elliptic-loading estimate)
    dCm_fus/dalpha = K_f W_f^2 L_f / (c S)   (Gilruth-Munk, Raymer eq. 16.25, per degree)
Static margin SM = h_n - h_cg; target 5-20 % MAC across the loading envelope.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .aircraft import Aircraft, OCCUPANT_KG
from .engines import FUEL_DENSITY


def lift_slope_helmbold(AR: float, sweep_c2_deg: float = 0.0, a0: float = 2 * math.pi * 0.95) -> float:
    """DATCOM/Helmbold finite-wing lift slope [1/rad]."""
    k = a0 / (2 * math.pi)
    tan2 = math.tan(math.radians(sweep_c2_deg)) ** 2
    return 2 * math.pi * AR / (2 + math.sqrt(4 + AR**2 * (1 + tan2) / k**2))


def k_fus(x_c4_over_L: float) -> float:
    """Raymer Fig. 16.14 (empirical pitching moment factor) fitted: K_f per degree."""
    return 0.0011 + 0.0315 * x_c4_over_L**1.6


@dataclass
class StabilityResult:
    x_np: float          # neutral point, m from prop plane
    h_np: float          # in MAC fraction
    cl_alpha_w: float
    cl_alpha_h: float
    deps_dalpha: float
    dcm_fus: float


def neutral_point(ac: Aircraft, cl_alpha_wing: float | None = None) -> StabilityResult:
    w, ht, f = ac.wing, ac.htail, ac.fuselage
    a = cl_alpha_wing or lift_slope_helmbold(w.aspect_ratio)
    # fuselage lift carry-over: (1 + 2.15 d/b) factor on wing-body lift slope (Raymer eq. 12.6 style) is ~ +2-4 %
    a_wb = a * (1 + 0.5 * (f.width / w.span))
    a_h = lift_slope_helmbold(ht.aspect_ratio, ht.sweep_c4_deg) * ac.ht_endplate
    deps = 2 * a / (math.pi * w.aspect_ratio)
    # tail height above the wing plane reduces downwash (simple DATCOM-like factor)
    dz = abs(ht.z_root - w.z_root) / (w.span / 2)
    deps *= 1 / (1 + 2.0 * dz)
    c = w.mac
    x_lemac = w.x_le_mac
    h_ac = (w.x_ac - x_lemac) / c
    x_c4_root = w.x_le_root + 0.25 * w.c_root
    kf = k_fus(x_c4_root / f.length)
    dcm_fus_deg = kf * f.width**2 * f.length / (c * w.area)
    dcm_fus = dcm_fus_deg * 180 / math.pi            # per rad
    l_h = ht.x_ac - x_lemac                         # from MAC leading edge
    vbar = ac.eta_h * ht.area / w.area * (a_h / a_wb) * (1 - deps)
    h_n = (h_ac - dcm_fus / a_wb + vbar * l_h / c) / (1 + vbar)
    return StabilityResult(x_lemac + h_n * c, h_n, a_wb, a_h, deps, dcm_fus)


def component_stations(ac: Aircraft, mass_items: dict) -> dict:
    """Assign an x-station to each mass item (empty aircraft). Works for both mass methods."""
    w, ht, vt, f = ac.wing, ac.htail, ac.vtail, ac.fuselage
    x_wing = w.x_le_mac + 0.40 * w.mac
    fixed = {
        "Engine (data sheet)": ac.x_engine, "Propeller + governor": 0.08, "Cooling, mount, cowling": 0.75,
        "Exhaust + intake + airbox": 0.65, "Horizontal tail": ht.x_le_root + 0.42 * ht.c_root,
        "Vertical tail": vt.x_le_root + 0.42 * vt.c_root, "Fuselage": 0.42 * f.length,
        "Nose gear": ac.x_nose_gear, "Flight controls": 0.50 * f.length, "Hydraulics/brakes": 1.6,
        "Avionics (glass)": ac.x_panel, "Electrical": 1.25, "Furnishings": ac.x_seat, "Cabin heat & vent": 1.3,
        "Fuselage shell (sandwich)": 0.45 * f.length, "Tail-cone longerons": 0.70 * f.length,
        "Floor + keel + wing carry-through box": w.x_le_mac + 0.3 * w.mac, "Bulkheads + firewall": 1.4,
        "Seat structure (9 g crash loads)": ac.x_seat, "Canopy (PC 3 mm) + frame": ac.x_seat - 0.1,
        "Fuselage paint": 0.45 * f.length, "Nose gear (leg, fork, wheel, shimmy damper)": ac.x_nose_gear,
        "Wheel fairings + leg fairings": None, "Flight controls (dual sticks, pedals, pushrods, cables)": 0.45 * f.length,
        "Electrical (battery, wiring, breakers)": 1.3, "Avionics (2 EFIS, radio, transponder, ELT, antennas)": ac.x_panel,
        "Brake system": 1.8, "Cabin heat + ventilation": 1.3, "Seats, belts, upholstery, baggage net": ac.x_seat,
        "Instruments, placards, misc. hardware": ac.x_panel + 0.3, "Certified-trainer class allowance": 0.40 * f.length,
    }
    st = {}
    for k in mass_items:
        if k in fixed:
            st[k] = fixed[k]
        elif k.startswith("Main") or k == "Wheel fairings + leg fairings":
            st[k] = None                               # main gear: placed after the aft CG is known
        else:                                          # wing items, fuel system, tank sealing, design features
            st[k] = x_wing
    return st


@dataclass
class CGEnvelope:
    cases: dict            # name -> (mass, x_cg, h_cg)
    h_fwd: float
    h_aft: float
    x_main_gear: float
    empty_x: float


def cg_envelope(ac: Aircraft, mass_items: dict, fuel_kg_max: float) -> CGEnvelope:
    w = ac.wing
    st = component_stations(ac, mass_items)
    m_known = {k: v for k, v in mass_items.items() if st.get(k) is not None}
    m_mg = sum(v for k, v in mass_items.items() if st.get(k) is None)
    # first pass: main gear at the wing a.c. +0.35 MAC
    x_mg = w.x_le_mac + 0.62 * w.mac
    for _ in range(3):
        M = sum(m_known.values()) + m_mg
        mx = sum(v * st[k] for k, v in m_known.items()) + m_mg * x_mg
        x_empty = mx / M
        x_fuel = w.x_le_mac + 0.42 * w.mac
        occ = OCCUPANT_KG
        cases = {}
        def add(name, items):
            mm = M + sum(m for m, _ in items)
            xx = (mx + sum(m * x for m, x in items)) / mm
            cases[name] = (mm, xx, (xx - w.x_le_mac) / w.mac)
        add("Empty", [])
        add("Solo light pilot (60 kg), min fuel", [(60, ac.x_seat), (5, x_fuel)])
        add("Solo pilot, full fuel", [(occ, ac.x_seat), (fuel_kg_max, x_fuel)])
        add("Two crew, no fuel", [(2 * occ, ac.x_seat)])
        add("Two crew + baggage, design fuel", [(2 * occ, ac.x_seat), (ac.baggage_kg, ac.x_baggage),
                                                (max(ac.mtow - M - 2 * occ - ac.baggage_kg, 0), x_fuel)])
        add("Two heavy crew (95 kg) + 20 kg bag, fuel to MTOW",
            [(190, ac.x_seat), (20, ac.x_baggage), (max(ac.mtow - M - 210, 0), x_fuel)])
        hs = [c[2] for c in cases.values() if c[0] <= ac.mtow + 1]
        x_aft = max(c[1] for c in cases.values())
        x_mg = x_aft + ac.x_main_gear_offset
    return CGEnvelope(cases, min(hs), max(hs), x_mg, x_empty)


def position_wing(ac: Aircraft, mass_items: dict, fuel_kg: float, target_h_mid: float = 0.25):
    """Slide the wing (and with it the fuel and main gear) so the mid CG sits at target_h_mid MAC."""
    from .aircraft import place_tails
    vh, vv = ac.vh, ac.vv
    for _ in range(30):
        env = cg_envelope(ac, mass_items, fuel_kg)
        h_mid = 0.5 * (env.h_fwd + env.h_aft)
        dx = (h_mid - target_h_mid) * ac.wing.mac
        ac.wing.x_le_root += dx * 1.0
        place_tails(ac, vh, vv)
        if abs(dx) < 1e-4:
            break
    return ac, cg_envelope(ac, mass_items, fuel_kg)


# --------------------------------------------------------------------------- tail sizing
def scissor(ac: Aircraft, cl_max_land: float, cl_alpha_wing: float, sm_min: float = 0.10,
            cm_ac_land: float = -0.22, cl_h_max: float = -0.85, sh_s=None, rotation=None):
    """Scissor ('X') plot for horizontal-tail sizing.

    Aft limit (stability):  h_aft = h_n(S_h) - SM_min
    Fwd limit (control, landing flare at CLmax, elevator fully up):
        Cm_cg = Cm_ac,wb + CL (h - h_ac) - eta (S_h/S)(l_h/c) CL_h,max = 0   (CL_h,max < 0)
        ->  h_fwd = h_ac + (-Cm_ac,wb + eta (S_h/S)(l_h/c) CL_h,max) / CL_max
    cm_ac_land: wing-body Cm_ac with landing flap (63-415 cm0 ~ -0.075, slotted flap ~ -0.13,
                fuselage ~ -0.02) [A];  cl_h_max: tail CL with full up-elevator, in ground effect [A].
    """
    import copy
    from .aircraft import G
    from . import atmosphere as isa
    if sh_s is None:
        sh_s = np.linspace(0.08, 0.30, 45)
    w = ac.wing
    h_ac = 0.25
    aft, fwd = [], []
    for r in sh_s:
        a = copy.deepcopy(ac)
        a.htail.area = r * w.area
        sr = neutral_point(a, cl_alpha_wing)
        aft.append(sr.h_np - sm_min)
        l_h = (a.htail.x_ac - w.x_ac) / w.mac
        # Cm_cg = cm_ac + CL (h - h_ac) + eta r l_h CL_h  (CL_h negative) = 0
        h = h_ac + (-cm_ac_land + ac.eta_h * r * l_h * cl_h_max) / cl_max_land
        # take-off rotation about the main-gear contact at V_R = Vs_TO (flaps T/O), Raymer/Sadraey style:
        #  -W (x_mg - x_cg) - L_wb (x_mg - x_ac) + Cm_ac,TO q S c + |L_h| (x_h - x_mg) = 0
        if rotation is not None:
            cl_to, x_mg = rotation
            W = ac.weight
            vr = math.sqrt(2 * W / (isa.RHO0 * w.area * cl_to))
            q = 0.5 * isa.RHO0 * vr**2
            L_wb = q * w.area * 0.6
            # propeller slipstream over the inboard tail: q_s/q = 1 + T/(q A_p) (momentum theory),
            # take-off thrust ~ 0.2 W at V_R, ~45 % of the tail span immersed [A]
            A_p = math.pi * ac.prop.diameter**2 / 4
            slip = 1 + 0.2 * W / (q * A_p)
            f_imm = min(1.0, ac.prop.diameter / a.htail.span)
            eta_rot = ac.eta_h * (f_imm * slip + (1 - f_imm))
            Lh = eta_rot * q * r * w.area * abs(cl_h_max) / 1.1           # 10 % margin for pitch acceleration
            rhs = -L_wb * (x_mg - w.x_ac) + (-0.12) * q * w.area * w.mac + Lh * (a.htail.x_ac - x_mg)
            x_cg = x_mg - rhs / W
            h = max(h, (x_cg - w.x_le_mac) / w.mac)     # the more restrictive (aft-most) forward limit
        fwd.append(h)
    return np.asarray(sh_s), np.asarray(aft), np.asarray(fwd)


def size_htail(ac: Aircraft, mass_items: dict, fuel_kg: float, cl_max_land: float, cl_alpha_wing: float,
               sm_min: float = 0.10, margin: float = 0.03, cl_max_to: float | None = None):
    """Smallest tail whose stability/control window contains the CG range (+margin each side)."""
    from .aircraft import place_tails
    env = cg_envelope(ac, mass_items, fuel_kg)
    width = env.h_aft - env.h_fwd + 2 * margin
    sh_s, aft, fwd = scissor(ac, cl_max_land, cl_alpha_wing, sm_min)
    window = aft - fwd
    ok = np.where(window >= width)[0]
    r = float(sh_s[ok[0]]) if len(ok) else float(sh_s[-1])
    # set tail area through V_h, re-place, then position wing so CG range is centred in the window
    l_h = ac.tail_arm_h
    vh = r * ac.wing.area * l_h / (ac.wing.area * ac.wing.mac)
    place_tails(ac, vh, ac.vv)
    i = ok[0] if len(ok) else -1
    target_mid = 0.5 * (aft[i] + fwd[i])
    ac, env = position_wing(ac, mass_items, fuel_kg, target_mid)
    return ac, env, (sh_s, aft, fwd, r)


def rotation_check(ac: Aircraft, env: CGEnvelope, cl_max_to: float, cl_h_max: float | None = None,
                   cl_ground: float = 0.6, cm_ac_to: float = -0.12):
    """Lowest speed at which the elevator can lift the nose wheel at the forward CG.

    Moments about the main-wheel contact (nose-up positive):
        -W (x_mg - x_cg,fwd) + q [ -S CL_g (x_mg - x_ac) + Cm_ac S c + eta_s S_h |CL_h| (x_h - x_mg) ] = 0
    eta_s includes the propeller slipstream on the immersed part of the tail (momentum theory,
    T ~ 0.2 W at rotation [A]). Requirement: V_rot <= V_LOF = 1.1 Vs_TO.
    """
    from . import atmosphere as isa
    if cl_h_max is None:
        cl_h_max = elevator_cl_h_max(ac)
    w, ht = ac.wing, ac.htail
    W = ac.weight
    x_cg = w.x_le_mac + env.h_fwd * w.mac
    d = env.x_main_gear - x_cg
    A_p = math.pi * ac.prop.diameter**2 / 4
    f_imm = ac.slipstream_immersion if ac.slipstream_immersion is not None else min(1.0, ac.prop.diameter / ht.span)
    q = 300.0
    for _ in range(50):
        slip = 1 + 0.2 * W / (q * A_p)
        eta_s = ac.eta_h * (f_imm * slip + (1 - f_imm))
        per_q = (-w.area * cl_ground * (env.x_main_gear - w.x_ac) + cm_ac_to * w.area * w.mac
                 + eta_s * ht.area * abs(cl_h_max) * (ht.x_ac - env.x_main_gear))
        q_new = W * d / per_q if per_q > 0 else 1e5
        if abs(q_new - q) < 0.1:
            break
        q = 0.5 * q + 0.5 * q_new
    v_rot = math.sqrt(2 * q / isa.RHO0)
    v_lof = 1.1 * math.sqrt(2 * W / (isa.RHO0 * w.area * cl_max_to))
    return v_rot, v_lof


def size_tail_and_wing(ac: Aircraft, mass_items: dict, fuel_kg: float, cl_max_land: float,
                       cl_max_to: float, cl_alpha_wing: float, sm_aft: float = 0.12,
                       cm_ac_land: float = -0.22, cl_h_max: float | None = None):
    """Smallest V_h that satisfies all three longitudinal criteria, with the wing positioned so the
    aft CG has exactly ``sm_aft`` static margin:
      1. stability   SM >= sm_aft at the aft CG (by construction)
      2. flare       landing-flare control at the forward CG (scissor control line)
      3. rotation    nose-wheel lift-off speed <= V_LOF at the forward CG
    Returns (aircraft, envelope, table of the sweep)."""
    import copy
    from .aircraft import place_tails
    if cl_h_max is None:
        cl_h_max = elevator_cl_h_max(ac)
    rows = []
    chosen = None
    for vh in np.arange(0.40, 1.01, 0.025):
        a = copy.deepcopy(ac)
        place_tails(a, vh, a.vv)
        for _ in range(25):
            env = cg_envelope(a, mass_items, fuel_kg)
            sr = neutral_point(a, cl_alpha_wing)
            dh = (sr.h_np - sm_aft) - env.h_aft
            a.wing.x_le_root -= dh * a.wing.mac
            place_tails(a, vh, a.vv)
            if abs(dh) < 1e-4:
                break
        env = cg_envelope(a, mass_items, fuel_kg)
        sr = neutral_point(a, cl_alpha_wing)
        r = a.htail.area / a.wing.area
        l_h = (a.htail.x_ac - a.wing.x_ac) / a.wing.mac
        h_flare = 0.25 + (-cm_ac_land + a.eta_h * r * l_h * cl_h_max) / cl_max_land
        v_rot, v_lof = rotation_check(a, env, cl_max_to, cl_h_max)
        ok = (env.h_fwd >= h_flare) and (v_rot <= v_lof)
        rows.append(dict(vh=vh, sh=a.htail.area, h_np=sr.h_np, h_fwd=env.h_fwd, h_aft=env.h_aft,
                         h_flare=h_flare, v_rot=v_rot, v_lof=v_lof, ok=ok, x_le=a.wing.x_le_root))
        if ok and chosen is None:
            chosen = (a, env)
    if chosen is None:
        chosen = (a, env)
    return chosen[0], chosen[1], rows


def elevator_tau(chord_ratio: float) -> float:
    """Thin-airfoil flap effectiveness  tau = 1 - (theta - sin theta)/pi,  cos theta = 2E - 1."""
    th = math.acos(2 * chord_ratio - 1)
    return 1 - (th - math.sin(th)) / math.pi


def elevator_cl_h_max(ac: Aircraft, delta_max_deg: float = 25.0, k_viscous: float = 0.60) -> float:
    """Most negative tail CL with full up-elevator (in ground effect), sign negative (download).

    |CL_h| = 0.10 + a_h * tau * delta * k, capped at 1.25 (tail stall). k = 0.6 covers the loss of
    flap effectiveness at large deflection and the hinge gap [A] (calibrated so ce/c 0.38 -> 0.85).
    """
    a_h = lift_slope_helmbold(ac.htail.aspect_ratio, ac.htail.sweep_c4_deg) * ac.ht_endplate
    cl = 0.10 + a_h * elevator_tau(ac.elevator_chord_ratio) * math.radians(delta_max_deg) * k_viscous
    return -min(cl, 1.25)
