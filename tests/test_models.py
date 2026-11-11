"""Verification tests: each model against a known answer or a hard physical bound.

Run with:  python3 -m pytest -q
"""
import math
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from eidolon import atmosphere as isa
from eidolon.geometry import Surface
from eidolon.lifting_line import LiftingLine
from eidolon.propeller import BEMTPropeller
from eidolon.aero import cf_turbulent, cf_laminar, cf_mixed
from eidolon.engines import ENGINES
from eidolon.landing_gear import sink_speed_cs23


def test_isa_against_icao_table():
    # ICAO Doc 7488: 1500 m -> 1.0581 kg/m3, 3000 m -> 0.9091 kg/m3, 5000 m -> 0.7361 kg/m3
    assert isa.density(0) == pytest.approx(1.225, rel=1e-4)
    assert isa.density(1500) == pytest.approx(1.0581, rel=2e-3)
    assert isa.density(3000) == pytest.approx(0.9091, rel=2e-3)
    assert isa.density(5000) == pytest.approx(0.7361, rel=2e-3)


def test_hot_day_lowers_density():
    dT = isa.isa_dT_for_oat(45.0, 0.0)
    assert dT == pytest.approx(30.0, abs=1e-6)
    assert isa.density(0, dT) == pytest.approx(1.225 * 288.15 / 318.15, rel=1e-6)


def test_lifting_line_rectangular_wing_textbook():
    # Anderson, Fundamentals of Aerodynamics fig. 5.20: rectangular AR 8 -> delta ~ 0.06
    w = Surface("rect", 10.0, 8.0, 1.0, 0.12, 0.12)
    e = LiftingLine(w).solve(5.0).e_span
    assert 0.92 < e < 0.96


def test_lifting_line_tapered_wing_near_elliptic():
    # taper ~0.35-0.45 gives the lowest induced drag of trapezoidal wings (delta < 0.01)
    w = Surface("t", 10.0, 8.0, 0.4, 0.12, 0.12)
    assert LiftingLine(w).solve(5.0).e_span > 0.985


def test_lifting_line_lift_slope_helmbold():
    w = Surface("t", 10.0, 8.0, 0.5, 0.12, 0.12)
    cla = LiftingLine(w, a0_per_rad=2 * math.pi).cl_alpha_per_rad()
    helmbold = 2 * math.pi * 8 / (2 + math.sqrt(4 + 64))
    assert cla == pytest.approx(helmbold, rel=0.04)


def test_propeller_never_beats_actuator_disk():
    p = BEMTPropeller(1.75, 3)
    for V in (20, 35, 50, 65):
        r = p.at_power(V, 2200, 55e3, 1500)
        assert 0 < r.eta < r.eta_ideal


def test_skin_friction_limits():
    re = 5e6
    assert cf_mixed(re, 0.0) == pytest.approx(cf_turbulent(re))
    assert cf_laminar(re) < cf_mixed(re, 0.4) < cf_turbulent(re)


def test_engine_lapse_sea_level_and_altitude():
    e = ENGINES["912iSc"]
    assert e.power_available_kw(0.0, rating="takeoff") == pytest.approx(73.5, rel=1e-6)
    assert e.power_available_kw(3000.0) < e.p_mcp_kw
    turbo = ENGINES["915iS"]
    assert turbo.power_available_kw(3000.0) == pytest.approx(turbo.p_mcp_kw, rel=1e-6)


def test_cs23_sink_speed_bounds():
    assert sink_speed_cs23(100.0) == pytest.approx(7 * 0.3048)
    assert sink_speed_cs23(5000.0) == pytest.approx(10 * 0.3048)


@pytest.fixture(scope="module")
def closed():
    from eidolon.design import eidolon_v1, hansa_closed
    return eidolon_v1(), hansa_closed()


def test_mass_closure(closed):
    e, h = closed
    for c in (e, h):
        M = c.model
        assert M.empty_kg + M.payload_kg + M.fuel_kg <= M.ac.mtow + 1e-6


def test_calibration_reproduces_hansa(closed):
    _, h = closed
    M, P = h.model, h.model.plane
    assert M.empty_kg == pytest.approx(540, abs=20)          # bottom-up + class allowance (LOO RMS ~14 kg)
    assert P.max_roc(M.W, 0, 0, "takeoff")[0] == pytest.approx(3.3, abs=0.05)


def test_eidolon_meets_requirements(closed):
    e, _ = closed
    M, P = e.model, e.model.plane
    assert float(P.v_stall(M.W, M.polar.cl_max_land)) * 3.6 <= 83.0            # CS-VLA 49
    assert P.max_roc(M.W, 0, 0, "takeoff")[0] >= 3.5
    assert P.takeoff_distance(M.W)[1] <= 450
    sm_aft = e.stab.h_np - e.env.h_aft
    assert 0.05 <= sm_aft <= 0.20
    assert e.rotation[0] <= e.rotation[1] * 1.001                                # nose lifts before V_LOF


def test_bottom_up_wing_spar_sized_by_bending():
    from eidolon.aircraft import eidolon
    from eidolon.structures import wing_structure
    ws = wing_structure(eidolon())
    assert ws.moment[0] > ws.moment[len(ws.moment) // 2] > 0          # bending grows toward the root
    assert abs(ws.shear[-1]) < 1e-6 * abs(ws.shear[0]) + 1.0           # free tip
    # cap area follows A = M / (sigma h): longer span -> heavier caps, thicker section -> lighter caps
    import copy
    long_ = copy.deepcopy(eidolon()); long_.wing.aspect_ratio *= 1.3
    thick = copy.deepcopy(eidolon()); thick.wing.t_c_root *= 1.2; thick.wing.t_c_tip *= 1.2
    caps = lambda a: wing_structure(a).masses["Wing spar caps (CFRP)"]
    assert caps(long_) > caps(eidolon()) > caps(thick)


def test_elevator_effectiveness_monotonic():
    from eidolon.stability import elevator_tau
    taus = [elevator_tau(c) for c in (0.2, 0.3, 0.4, 0.5)]
    assert all(a < b for a, b in zip(taus, taus[1:])) and taus[-1] < 1


def test_carbon_airframe_lighter_same_aerodynamics():
    from eidolon.design import eidolon_v1, eidolon_final
    from eidolon.engines import FUEL_DENSITY
    from eidolon.model import V_CRUISE, CRUISE_ALT
    g, c = eidolon_v1().model, eidolon_final().model
    assert 25.0 < g.empty_kg - c.empty_kg < 40.0                      # skins, ribs, fuselage, cowling, + lightning mesh
    assert c.fuel_kg == pytest.approx(c.ac.fuel_capacity_l * FUEL_DENSITY)   # tank full with 2 crew + bags
    fg = g.plane.fuel_per_100km(g.W, V_CRUISE, CRUISE_ALT)[0]
    fc = c.plane.fuel_per_100km(c.W, V_CRUISE, CRUISE_ALT)[0]
    assert fc == pytest.approx(fg, rel=0.005)                         # same wing, same MTOW: same drag


def test_cost_model_reproduces_hansa_price():
    from eidolon import cost
    k = cost.calibrate_labour(213.48)
    _, usd = cost.eastlake(cost.HANSA_EMPTY_KG, 213.48, k)
    assert usd * cost.INR_PER_USD == pytest.approx(cost.HANSA_PRICE_INR, rel=1e-6)
    from eidolon.aircraft import eidolon
    ac = eidolon(wing_area=13.25, span=11.5)
    p = {proc: cost.unit_cost(ac, 228.6, 530.0, k, proc)["total_usd"] for proc in ("glass", "infusion", "prepreg")}
    assert p["glass"] < p["infusion"] < p["prepreg"]
