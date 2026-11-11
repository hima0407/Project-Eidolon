"""Design closure: one function that turns a configuration into a converged, sized aircraft.

Loop (2-3 passes converge to < 0.1 kg and < 1 mm):
    geometry -> mass (Raymer, calibrated) -> CG envelope -> tail size + wing position
             -> drag / lift / propulsion -> performance
"""
from __future__ import annotations

from dataclasses import dataclass

from .aircraft import Aircraft, eidolon, hansa_ng, G
from .engines import ENGINES
from .model import build, Model, CRUISE_ALT, V_CRUISE
from .stability import size_tail_and_wing, neutral_point, cg_envelope, rotation_check

# Eidolon v1 configuration chosen by studies/05 (wing sizing) and studies/08 (engine trade)
BASELINE = dict(engine_key="912iSc", wing_area=13.25, span=11.5)


@dataclass
class Closed:
    model: Model
    env: object
    stab: object
    tail_rows: list
    rotation: tuple


def prop_for(ac: Aircraft):
    """Direct-drive engines turn the propeller faster: limit static tip Mach to ~0.80."""
    eng = ENGINES[ac.engine_key]
    import math
    d_tip = 0.80 * 340.3 / (math.pi * eng.prop_rpm_max / 60)
    ac.prop.diameter = round(min(1.75, d_tip), 2)
    ac.prop.blades = 3 if eng.p_takeoff_kw > 80 or ac.prop.diameter < 1.7 else ac.prop.blades
    # keep the take-off power coefficient C_P = P/(rho n^3 D^5) absorbable: scale blade chord
    cp_ratio = (eng.p_takeoff_kw / 73.5) / ((eng.prop_rpm_max / (5800 / 2.43)) ** 3 * (ac.prop.diameter / 1.75) ** 5)
    ac.prop.chord_scale = max(1.0, cp_ratio ** 0.75)
    return ac


def close(ac: Aircraft, size_tail: bool = True, passes: int = 3, **build_kw) -> Closed:
    prop_for(ac)
    M = build(ac, **build_kw)
    rows, env = [], None
    for _ in range(passes):
        if size_tail:
            ac, env, rows = size_tail_and_wing(ac, M.mass.items, ac.fuel_capacity_l * 0.72,
                                               M.polar.cl_max_land, M.polar.cl_max_to, M.lift.cl_alpha_wing)
        M = build(ac, **build_kw)
    env = cg_envelope(ac, M.mass.items, ac.fuel_capacity_l * 0.72)
    st = neutral_point(ac, M.lift.cl_alpha_wing)
    rot = rotation_check(ac, env, M.polar.cl_max_to)
    return Closed(M, env, st, rows, rot)


def eidolon_v1(engine_key: str | None = None, **kw) -> Closed:
    cfg = dict(BASELINE)
    if engine_key:
        cfg["engine_key"] = engine_key
    return close(eidolon(**cfg), **kw)


def eidolon_final(engine_key: str | None = None, **kw) -> Closed:
    """The final aircraft: v1 geometry with the carbon sandwich airframe (study 20)."""
    cfg = dict(BASELINE)
    if engine_key:
        cfg["engine_key"] = engine_key
    ac = eidolon(**cfg)
    ac.airframe = "carbon"
    return close(ac, **kw)


def hansa_closed(**kw) -> Closed:
    """Hansa-NG: geometry as published / assumed, tail not re-sized (it is a real aircraft)."""
    ac = hansa_ng()
    M = build(ac, **kw)
    # same placement rule as Eidolon (12 % SM at aft CG) so neither aircraft gets a CG advantage
    from .stability import position_wing
    for _ in range(25):
        env = cg_envelope(ac, M.mass.items, ac.fuel_capacity_l * 0.72)
        st = neutral_point(ac, M.lift.cl_alpha_wing)
        dh = (st.h_np - 0.12) - env.h_aft
        ac.wing.x_le_root -= dh * ac.wing.mac
        from .aircraft import place_tails
        place_tails(ac, 0.65, 0.040)
        if abs(dh) < 1e-4:
            break
    M = build(ac, **kw)
    env = cg_envelope(ac, M.mass.items, ac.fuel_capacity_l * 0.72)
    st = neutral_point(ac, M.lift.cl_alpha_wing)
    return Closed(M, env, st, [], rotation_check(ac, env, M.polar.cl_max_to))


def headline(c: Closed, fuel_full_tanks: bool = False) -> dict:
    """The numbers that go on the comparison slide."""
    M, P = c.model, c.model.plane
    ac = M.ac
    W = M.W
    pol = M.polar
    f100, lph, pcr = P.fuel_per_100km(W, V_CRUISE, CRUISE_ALT)
    rng, _ = P.range_km(W, M.fuel_kg, V_CRUISE, CRUISE_ALT)
    full = ac.fuel_capacity_l * 0.72
    W_full = (M.empty_kg + full + 1 * 77 + 0) * G  # single pilot, full tanks
    rng_full, v_full = P.range_at_power(W_full, full, CRUISE_ALT, 0.55)
    roc, vy = P.max_roc(W, 0, 0, "takeoff")
    to_g, to_15, vlof = P.takeoff_distance(W)
    ld, vs0 = P.landing_distance(W)
    return {
        "MTOW [kg]": ac.mtow,
        "Empty mass [kg]": M.empty_kg,
        "Fuel with 2 x 77 kg + 10 kg [kg]": M.fuel_kg,
        "Wing area [m2]": ac.wing.area,
        "Span [m]": ac.wing.span,
        "Aspect ratio": ac.wing.aspect_ratio,
        "CD0": pol.cd0,
        "Oswald e": M.lift.e_oswald,
        "L/D max": 0.5 / (pol.cd0 * pol.k) ** 0.5,
        "Cruise speed @75% 1500 m [km/h]": P.speed_at_power(W, CRUISE_ALT, 0.75) * 3.6,
        "Max level speed SL [km/h]": P.v_max(W, 0.0) * 3.6,
        "Power for 200 km/h @1500 m [kW]": pcr / 1e3,
        "Fuel flow @200 km/h [L/h]": lph,
        "Fuel per 100 km @200 km/h [L]": f100,
        "Range @200 km/h, design payload, 45 min reserve [km]": rng,
        "Range @55% power, full tanks, solo [km]": rng_full,
        "Max ROC SL [m/s]": roc,
        "Vy [km/h]": vy * 3.6,
        "Service ceiling [m]": P.ceiling(W),
        "Stall, landing flap [km/h]": vs0 * 3.6,
        "Stall, clean [km/h]": float(P.v_stall(W, pol.cl_max_clean)) * 3.6,
        "Take-off to 15 m [m]": to_15,
        "Landing from 15 m [m]": ld,
        "Static margin, aft CG [%MAC]": 100 * (c.stab.h_np - c.env.h_aft),
    }
