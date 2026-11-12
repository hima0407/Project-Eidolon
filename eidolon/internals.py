"""Internal components for the CAD and the X-ray view, placed at the stations the design model uses.

Every item is a part in the same format as eidolon.oml.build_oml ({"plane", "rings", "mirror", ...}), so it
lofts in Fusion 360 and meshes to STL exactly like the outer skin. Wing internals (spars, ribs, tanks,
carry-through box) are chord slices of the real NACA 63-415 -> 63-412 sections. Boxes are rectangle lofts
("polyline": True). x-stations come from the aircraft definition and the CG envelope; component sizes,
tank span and the CG marker height are schematic.
"""
from __future__ import annotations

import math
import numpy as np

from .oml import surface_panel

COLORS = {
    "int_engine": "#f2a541", "int_firewall": "#e8664f", "int_battery": "#f2d94e", "int_panel": "#7fb0f0",
    "int_seat_pan": "#d8d4cb", "int_seat_back": "#d8d4cb", "int_crew_torso": "#e9e6de", "int_crew_head": "#e9e6de",
    "int_stick": "#3a3f45", "int_baggage": "#b9a5e0", "int_main_spar": "#2a63c9", "int_rear_spar": "#4f8ef7",
    "int_ribs": "#7fa6e0", "int_fuel_tank": "#35c2a6", "int_carry_through": "#2a63c9", "int_pushrod": "#5fd3e8",
    "int_gear_sensor": "#ff9f43", "int_cg_marker": "#ff3b3b", "int_np_marker": "#ffffff",
}


def _box(cx, cy, cz, dx, dy, dz, mirror=False):
    """Rectangle loft along x (two rings), as a part."""
    def ring(x):
        return np.array([[x, cy - dy / 2, cz - dz / 2], [x, cy + dy / 2, cz - dz / 2],
                         [x, cy + dy / 2, cz + dz / 2], [x, cy - dy / 2, cz + dz / 2]])
    return {"plane": "x", "rings": [ring(cx - dx / 2), ring(cx + dx / 2)], "mirror": mirror, "polyline": True}


def _ball(cx, cy, cz, r, mirror=False, n=24, k=7):
    rings = []
    for a in np.linspace(-0.92, 0.92, k):
        x = cx + r * a; rr = r * math.sqrt(1 - a * a)
        t = np.linspace(0, 2 * math.pi, n, endpoint=False)
        rings.append(np.column_stack([np.full(n, x), cy + rr * np.cos(t), cz + rr * np.sin(t)]))
    return {"plane": "x", "rings": rings, "mirror": mirror, "closed_loop": True}


def _wing_slice(w, eta0, eta1, c0, c1, n):
    return {"plane": "y", "rings": surface_panel(w, eta0, eta1, c0, c1, n), "mirror": True}


def _section_at(rings, x):
    xs = np.array([np.asarray(r)[:, 0].mean() for r in rings])
    return np.asarray(rings[int(np.argmin(abs(xs - x)))])


def internal_parts(ac, env, stab, oml_parts) -> dict:
    w = ac.wing
    P = {}
    # ---- powerplant and cabin
    P["int_engine"] = _box(ac.x_engine, 0.0, -0.05, 0.56, 0.58, 0.46)
    fw = _section_at(oml_parts["fuselage"]["rings"], 1.05)
    c = fw.mean(axis=0); fw_in = c + (fw - c) * np.array([1.0, 0.96, 0.96])
    P["int_firewall"] = {"plane": "x", "rings": [fw_in, fw_in + np.array([0.015, 0, 0])], "mirror": False, "closed_loop": True}
    P["int_battery"] = _box(1.30, 0.26, -0.22, 0.18, 0.14, 0.17)
    P["int_panel"] = _box(ac.x_panel, 0.0, 0.20, 0.04, 0.96, 0.26)
    ys = 0.27
    P["int_seat_pan"] = _box(ac.x_seat, ys, -0.45, 0.46, 0.42, 0.07, mirror=True)
    P["int_seat_back"] = _box(ac.x_seat + 0.27, ys, -0.13, 0.07, 0.42, 0.60, mirror=True)
    P["int_crew_torso"] = _box(ac.x_seat + 0.08, ys, 0.00, 0.24, 0.34, 0.48, mirror=True)
    P["int_crew_head"] = _ball(ac.x_seat + 0.06, ys, 0.40, 0.105, mirror=True)
    P["int_stick"] = _box(ac.x_seat - 0.38, ys, -0.28, 0.03, 0.03, 0.34, mirror=True)
    P["int_baggage"] = _box(ac.x_baggage, 0.0, -0.28, 0.40, 0.80, 0.40)
    # ---- wing structure: chord slices of the real sections
    eta_body = (ac.fuselage.width / 2 - 0.02) / w.semispan
    P["int_main_spar"] = _wing_slice(w, 0.0, 0.97, 0.285, 0.315, 6)
    P["int_rear_spar"] = _wing_slice(w, 0.0, 0.97, 0.640, 0.660, 6)
    P["int_carry_through"] = _wing_slice(w, 0.0, eta_body, 0.315, 0.640, 2)
    P["int_fuel_tank"] = _wing_slice(w, 0.65 / w.semispan, 1.55 / w.semispan, 0.33, 0.62, 3)
    rib = []
    for y in np.arange(0.62, w.semispan - 0.1, 0.5):
        e = y / w.semispan
        rib.append(surface_panel(w, e, e + 0.012 / w.semispan, 0.03, 0.70, 2))
    P["int_ribs"] = {"plane": "y", "rings": None, "mirror": True, "multi": rib}
    # ---- controls, sensors, markers
    path = [(ac.x_seat - 0.38, -0.42), (3.6, -0.30), (5.0, -0.05), (6.65, 0.18)]
    rr = []
    for x, z in path:
        rr.append(np.array([[x, -0.012, z - 0.012], [x, 0.012, z - 0.012], [x, 0.012, z + 0.012], [x, -0.012, z + 0.012]]))
    P["int_pushrod"] = {"plane": "x", "rings": rr, "mirror": False, "polyline": True}
    P["int_gear_sensor"] = _box(env.x_main_gear + 0.035, 0.80, -0.80, 0.004, 0.10, 0.06, mirror=True)
    xs = [m[1] for m in env.cases.values()]
    P["int_cg_marker"] = _ball(0.5 * (min(xs) + max(xs)), 0.0, -0.18, 0.05)
    P["int_np_marker"] = _ball(w.x_le_mac + stab.h_np * w.mac, 0.0, -0.18, 0.04)
    for k in P:
        P[k]["color"] = COLORS[k]
    return P


def expand(parts: dict) -> dict:
    """Split multi-body items (ribs) into single-loft parts: {name: part}."""
    out = {}
    for k, p in parts.items():
        if p.get("multi"):
            for i, rings in enumerate(p["multi"]):
                q = {kk: vv for kk, vv in p.items() if kk != "multi"}; q["rings"] = rings
                out[f"{k}_{i + 1:02d}"] = q
        else:
            out[k] = p
    return out
