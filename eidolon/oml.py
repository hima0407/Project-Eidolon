"""Outer mould line v2: one description of every surface, used for BOTH the mesh and the Fusion 360 B-rep.

Every part is a stack of closed, planar section rings (each ring lies in a plane x = const,
y = const or z = const). The mesh is a loft through the rings (eidolon.geometry3d.loft); the
Fusion 360 script (cad/fusion/eidolon_fusion.py) sketches the same rings as fitted splines on
offset construction planes and lofts them into solids. So the CAD model, the renders and the
analysis can never disagree.

Separate bodies: wing panels (main box, flaps, ailerons, drooped-LE outboard panel, tip), tail
surfaces with elevators and rudder, fuselage, canopy, dorsal fin, ventral strake, spinner,
propeller blade (patterned x3), main and nose gear with fairings. Coordinates in metres,
x aft from the propeller plane, y starboard, z up.
"""
from __future__ import annotations

import math

import numpy as np

from .airfoil import load_dat, naca4, split_surfaces
from .geometry3d import fuselage_profiles

N_AF = 34          # points per surface in a section ring


def _af(name):
    try:
        return load_dat(name)
    except Exception:
        return naca4(name.replace("naca", ""))


def chord_ring(xy, x0=0.0, x1=1.0, droop=0.0, n=N_AF, te_gap=0.004):
    """Closed 2-D ring of the airfoil between chord stations x0..x1 (unit chord).

    Upper surface from x1 to x0, then lower surface back to x1. A cut at x0 > 0 or x1 < 1 is closed by
    the straight vertical edge. ``droop`` drops and extends the leading edge (outboard LE cuff).
    """
    x, yu, yl = split_surfaces(xy)
    if droop:
        k = np.clip(1 - x / 0.16, 0, None) ** 2
        yu = yu - droop * k
        yl = yl - droop * k * 1.15
        x = x - 0.03 * np.clip(1 - x / 0.16, 0, None) ** 2   # 3 % chord extension at the nose
    beta = np.linspace(0, np.pi, n)
    s = 0.5 * (1 - np.cos(beta))
    xs = x0 + (x1 - x0) * s
    up = np.interp(xs, x, yu); lo = np.interp(xs, x, yl)
    if x1 >= 0.999:                      # finite trailing-edge thickness for a clean B-rep
        mid = 0.5 * (up[-1] + lo[-1]); up[-1] = mid + te_gap / 2; lo[-1] = mid - te_gap / 2
    upper = np.column_stack([xs[::-1], up[::-1]])
    if x0 <= 1e-9:                                 # LE is a smooth point shared by both surfaces
        lower = np.column_stack([xs[1:], lo[1:]])
    else:                                          # nose of a control surface: rounded through both points
        lower = np.column_stack([xs, lo])
    return np.vstack([upper, lower])               # open at x1: closed by the straight TE / hinge-cut edge


def surface_panel(surf, eta0, eta1, x0, x1, n_span=6, vertical=False, droop=0.0, tip_round=False,
                  airfoil_override=None):
    """Rings for a spanwise panel of a trapezoidal surface between chord fractions x0..x1."""
    root = _af(airfoil_override or surf.airfoil_root); tip = _af(airfoil_override or surf.airfoil_tip)
    etas = np.linspace(eta0, eta1, n_span)
    rings = []
    tan_le = math.tan(surf.sweep_le_rad); dih = math.radians(surf.dihedral_deg)
    for k, e in enumerate(etas):
        c = surf.chord_at(e)
        scale_t = 1.0
        if tip_round:                                 # elliptic rounding of the last 4 % of span
            f = (e - eta0) / max(eta1 - eta0, 1e-9)
            c_scale = math.sqrt(max(1 - f**2, 0.02))
            scale_t = c_scale
            x_shift = (1 - c_scale) * c * 0.55
            c *= c_scale
        else:
            x_shift = 0.0
        xr, xu, yl_ = split_surfaces(root); _, tu, tl = split_surfaces(tip)
        blend = np.column_stack([np.concatenate([xr[::-1], xr[1:]]),
                                 np.concatenate([((1 - e) * xu + e * tu)[::-1], ((1 - e) * yl_ + e * tl)[1:]])])
        ring2 = chord_ring(blend, x0, x1, droop=droop)
        tw = math.radians(surf.twist_tip_deg * e)
        xs = (ring2[:, 0] - 0.25) * c
        zs = ring2[:, 1] * c * scale_t
        xrot = xs * math.cos(tw) + zs * math.sin(tw)
        zrot = -xs * math.sin(tw) + zs * math.cos(tw)
        span_pos = e * surf.semispan
        x_c4 = surf.x_le_root + span_pos * tan_le + 0.25 * surf.chord_at(e) + x_shift
        if vertical:
            pts = np.column_stack([x_c4 + xrot, zrot, np.full_like(xrot, surf.z_root + span_pos)])
        else:
            pts = np.column_stack([x_c4 + xrot, np.full_like(xrot, span_pos),
                                   surf.z_root + span_pos * math.tan(dih) + zrot])
        rings.append(pts)
    return rings


def superellipse_ring(x, half_w, z_bot, z_top, p_top=2.6, p_bot=2.2, n=48):
    th = np.linspace(0, 2 * np.pi, n, endpoint=False)
    zc, hz = 0.5 * (z_top + z_bot), 0.5 * (z_top - z_bot)
    c, s = np.cos(th), np.sin(th)
    p = np.where(s >= 0, p_top, p_bot)
    y = half_w * np.sign(c) * np.abs(c) ** (2 / p)
    z = zc + hz * np.sign(s) * np.abs(s) ** (2 / p)
    return np.column_stack([np.full(n, x), y, z])


def body_lines(ac, n=38):
    f = ac.fuselage
    xc, wc, tc, bc = fuselage_profiles(f.length, f.width, 1.05)
    xs = np.concatenate([np.linspace(xc[0], 1.4, 12)[:-1], np.linspace(1.4, f.length - 0.02, n - 11)])
    sm = lambda yc: np.convolve(np.pad(np.interp(xs, xc, yc), 2, mode="edge"), np.ones(5) / 5, mode="valid")
    return xs, sm(wc), sm(tc), sm(bc)


def build_oml(ac, env):
    """Return {part: {"plane": 'x'|'y'|'z', "rings": [...], "mirror": bool, "pattern": int}}."""
    from .propeller import BEMTPropeller
    parts = {}
    w, ht, vt = ac.wing, ac.htail, ac.vtail
    xs, W, T, B = body_lines(ac)
    zt = lambda x: float(np.interp(x, xs, T)); zb = lambda x: float(np.interp(x, xs, B))
    hw = lambda x: float(np.interp(x, xs, W))
    # ---- fuselage
    rings = []
    for x, wi, ti, bi in zip(xs, W, T, B):
        f = x / ac.fuselage.length
        rings.append(superellipse_ring(x, max(wi, 0.02), bi, ti, p_top=2.2 + 0.8 * math.sin(math.pi * min(f * 1.6, 1)),
                                       p_bot=2.1 + 0.6 * math.sin(math.pi * min(f * 1.6, 1))))
    parts["fuselage"] = {"plane": "x", "rings": rings, "mirror": False}
    # ---- canopy (closed half-shell sitting slightly inside the fuselage top)
    rings = []
    x0, x1 = 1.30, 3.35
    for s in np.linspace(0.02, 0.98, 16):
        x = x0 + (x1 - x0) * s
        prof = math.sin(math.pi * s ** 0.80) ** 0.85
        half = 0.47 * max(prof, 0.08) ** 0.45 * min(hw(x) / 0.58, 1)
        base = zt(x) - 0.06
        th = np.linspace(0, np.pi, 36)
        top = base + 0.06 + 0.33 * prof
        arc = np.column_stack([np.full(36, x), half * np.cos(th), base + (top - base) * np.sin(th) ** 0.85])
        rings.append(arc)
    parts["canopy"] = {"plane": "x", "rings": rings, "mirror": False}
    # ---- wing (starboard; mirrored)
    w.z_root = zb(w.x_le_root + 0.4 * w.c_root) + 0.15
    eta_body = (ac.fuselage.width / 2 - 0.02) / w.semispan
    fl_out = ac.flaps.span_fraction
    cuff_start = 0.58
    hinge = 1 - 0.27
    parts["wing_inboard"] = {"plane": "y", "rings": surface_panel(w, 0.0, cuff_start, 0.0, hinge, 6), "mirror": True}
    parts["wing_outboard_cuffed"] = {"plane": "y", "rings": surface_panel(w, cuff_start, 0.955, 0.0, hinge, 5, droop=0.012 if ac.le_cuff else 0.0), "mirror": True}
    parts["wing_tip"] = {"plane": "y", "rings": surface_panel(w, 0.955, 0.999, 0.0, 1.0, 5, droop=0.012 if ac.le_cuff else 0.0, tip_round=True), "mirror": True}
    parts["flap"] = {"plane": "y", "rings": surface_panel(w, eta_body, fl_out - 0.005, hinge + 0.012, 1.0, 4), "mirror": True}
    parts["wing_te_filler"] = {"plane": "y", "rings": surface_panel(w, fl_out - 0.005, fl_out + 0.012, hinge + 0.012, 1.0, 2), "mirror": True}
    parts["aileron"] = {"plane": "y", "rings": surface_panel(w, fl_out + 0.012, 0.955, hinge + 0.012, 1.0, 4), "mirror": True}
    # ---- horizontal tail + elevators
    ht.z_root = ac.cone_top_z + ac.ht_height_frac * vt.span - 0.02
    eh = 1 - ac.elevator_chord_ratio
    parts["stabiliser"] = {"plane": "y", "rings": surface_panel(ht, 0.0, 0.94, 0.0, eh, 4), "mirror": True}
    parts["stabiliser_tip"] = {"plane": "y", "rings": surface_panel(ht, 0.94, 0.999, 0.0, 1.0, 4, tip_round=True), "mirror": True}
    parts["elevator"] = {"plane": "y", "rings": surface_panel(ht, 0.02, 0.94, eh + 0.015, 1.0, 3), "mirror": True}
    # ---- fin + rudder, dorsal fillet, ventral strake
    vt.z_root = zt(vt.x_le_root + 0.3) - 0.05
    parts["fin"] = {"plane": "z", "rings": surface_panel(vt, 0.0, 0.94, 0.0, 0.63, 4, vertical=True), "mirror": False}
    parts["fin_tip"] = {"plane": "z", "rings": surface_panel(vt, 0.94, 0.999, 0.0, 1.0, 4, vertical=True, tip_round=True), "mirror": False}
    parts["rudder"] = {"plane": "z", "rings": surface_panel(vt, 0.0, 0.94, 0.65, 1.0, 3, vertical=True), "mirror": False}
    rings = []
    af = _af("naca0012")
    for f in np.linspace(0, 1, 4):
        z = vt.z_root - 0.04 + f * 0.30
        x_te = vt.x_le_root + (z - vt.z_root) * math.tan(vt.sweep_le_rad) + 0.30 * vt.c_root
        x_le = vt.x_le_root + (z - vt.z_root) * math.tan(vt.sweep_le_rad) - 1.25 * vt.c_root * (1 - f) ** 1.6
        c = max(x_te - x_le, 0.05)
        r2 = chord_ring(af, 0.0, 1.0)
        rings.append(np.column_stack([x_le + r2[:, 0] * c, r2[:, 1] * c * 0.5 * min(1.0, 0.45 / c + 0.2), np.full(len(r2), z)]))
    parts["dorsal_fin"] = {"plane": "z", "rings": rings, "mirror": False}
    if ac.ventral_strake_m2:
        rings = []
        span_s = 0.26
        c_root = ac.ventral_strake_m2 / span_s * 1.33
        x_root = ac.fuselage.length - c_root - 0.15
        for f in np.linspace(0, 1, 4):
            z = zb(x_root + 0.4 * c_root) + 0.04 - f * span_s
            c = c_root * (1 - 0.5 * f)
            r2 = chord_ring(_af("naca0012"), 0.0, 1.0)
            rings.append(np.column_stack([x_root + 0.5 * c_root * f + r2[:, 0] * c, r2[:, 1] * c * 0.8, np.full(len(r2), z)]))
        parts["ventral_strake"] = {"plane": "z", "rings": rings, "mirror": False}
    # ---- spinner
    rings = []
    for s in np.linspace(0.03, 1.0, 10):
        x = -0.30 + 0.42 * s
        r = 0.175 * (1 - (1 - s) ** 2.2) ** 0.55
        th = np.linspace(0, 2 * np.pi, 40, endpoint=False)
        rings.append(np.column_stack([np.full(40, x), r * np.cos(th), r * np.sin(th)]))
    parts["spinner"] = {"plane": "x", "rings": rings, "mirror": False}
    # ---- propeller blade along +y, patterned about x
    bp = BEMTPropeller(ac.prop.diameter, ac.prop.blades, chord_scale=ac.prop.chord_scale)
    R = ac.prop.diameter / 2
    rings = []
    paf = _af("naca2412") if False else naca4("4412")
    for rr in np.linspace(0.16, 0.985, 8):
        r = rr * R
        c = float(np.interp(rr, bp.rR, bp.c))
        if rr > 0.9:
            c *= math.sqrt(max(1 - ((rr - 0.9) / 0.09) ** 2, 0.15))
        beta = math.atan(math.tan(math.radians(24)) * 0.75 / rr)
        r2 = chord_ring(paf, 0.0, 1.0)
        xa = (r2[:, 0] - 0.35) * c; za = r2[:, 1] * c * (1.0 if rr > 0.3 else 1.6)
        # chord in the x-z plane, inclined by beta to the plane of rotation (z)
        X = -0.02 + xa * math.sin(beta) - za * math.cos(beta)
        Z = xa * math.cos(beta) + za * math.sin(beta)
        rings.append(np.column_stack([X, np.full(len(X), r), Z]))
    parts["propeller_blade"] = {"plane": "y", "rings": rings, "mirror": False, "pattern": ac.prop.blades}
    # ---- landing gear
    x_mg = env.x_main_gear
    z_ground = -0.875 - 0.42
    r_w = ac.gear.main_tyre_d / 2
    z_axle = z_ground + r_w
    y_tr = 1.05
    rings = []
    for f in np.linspace(0, 1, 6):
        y = 0.36 + (y_tr - 0.36) * f
        z = (zb(x_mg) + 0.10) + (z_axle + 0.05 - zb(x_mg) - 0.10) * (f ** 1.25)
        cch = 0.20 - 0.07 * f; t = 0.034 - 0.012 * f
        r2 = chord_ring(_af("naca0012"), 0.0, 1.0)
        rings.append(np.column_stack([x_mg - 0.35 * cch + r2[:, 0] * cch, np.full(len(r2), y), z + r2[:, 1] / 0.12 * t * 0.5]))
    parts["main_gear_leg"] = {"plane": "y", "rings": rings, "mirror": True}

    def pant(xc, yc, zc, L, half_w, h, n=8):
        out = []
        prof = _af("naca0012")
        xx, yu, _ = split_surfaces(prof)
        for s in np.linspace(0.015, 0.985, n):
            th_ = float(np.interp(s, xx, yu)) / 0.06
            th = np.linspace(0, 2 * np.pi, 32, endpoint=False)
            rr_w, rr_h = half_w * max(th_, 0.05), h * max(th_, 0.05)
            out.append(np.column_stack([np.full(32, xc - 0.35 * L + s * L), yc + rr_w * np.cos(th), zc + rr_h * np.sin(th)]))
        return out
    parts["main_wheel_fairing"] = {"plane": "x", "rings": pant(x_mg + 0.08, y_tr, z_axle + 0.03, 0.78, 0.115, 0.25), "mirror": True}
    x_ng = ac.x_nose_gear
    rn = ac.gear.nose_tyre_d / 2
    rings = []
    for f in np.linspace(0, 1, 5):
        z = zb(x_ng) + 0.08 - (zb(x_ng) + 0.08 - (z_ground + rn + 0.05)) * f
        c = 0.15 - 0.03 * f
        r2 = chord_ring(_af("naca0012"), 0.0, 1.0)
        rings.append(np.column_stack([x_ng - 0.3 * c + r2[:, 0] * c, r2[:, 1] * c * 1.4, np.full(len(r2), z)]))
    parts["nose_gear_leg"] = {"plane": "z", "rings": rings[::-1], "mirror": False}
    parts["nose_wheel_fairing"] = {"plane": "x", "rings": pant(x_ng + 0.03, 0.0, z_ground + rn + 0.02, 0.62, 0.09, 0.21), "mirror": False}
    meta = {"z_ground": z_ground, "y_track": y_tr, "x_main_gear": x_mg, "wheelbase": x_mg - x_ng}
    return parts, meta


COLORS = {"fuselage": "#f1f1ee", "canopy": "#1f2c3a", "wing_inboard": "#f4f4f1", "wing_outboard_cuffed": "#f4f4f1",
          "wing_tip": "#f4f4f1", "flap": "#e8e8e4", "wing_te_filler": "#e8e8e4", "aileron": "#e8e8e4",
          "stabiliser": "#f4f4f1", "stabiliser_tip": "#f4f4f1", "elevator": "#e8e8e4", "fin": "#2a78d6",
          "fin_tip": "#2a78d6", "rudder": "#1f5fae", "dorsal_fin": "#2a78d6", "ventral_strake": "#2a78d6",
          "spinner": "#2a78d6", "propeller_blade": "#2a2d31", "main_gear_leg": "#3a3f45", "main_wheel_fairing": "#f1f1ee",
          "nose_gear_leg": "#3a3f45", "nose_wheel_fairing": "#f1f1ee", "livery_stripe": "#2a78d6"}


def to_mesh(parts):
    """Triangle soups per part (mirrored and patterned copies included)."""
    from .geometry3d import loft
    out = {}
    for k, p in parts.items():
        t = loft([np.asarray(r) for r in p["rings"]])
        if p.get("mirror"):
            m = t.copy(); m[:, :, 1] *= -1; m = m[:, ::-1, :]
            t = np.concatenate([t, m])
        n = p.get("pattern", 0)
        if n:
            cps = []
            for i in range(n):
                a = 2 * math.pi * i / n + 0.35
                R = np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])
                cps.append(t @ R.T)
            t = np.concatenate(cps)
        out[k] = t
    return out


def livery_stripe(ac, parts_mesh=None):
    """Thin ribbon just outside the fuselage side: a cheat line from cowl to tail (mesh only)."""
    xs, W, T, B = body_lines(ac)
    tris = []
    sel = (xs > 0.6) & (xs < ac.fuselage.length - 0.35)
    xx = xs[sel]
    for side in (1, -1):
        for i in range(len(xx) - 1):
            quad = []
            for x in (xx[i], xx[i + 1]):
                f = (x - 0.6) / (ac.fuselage.length - 0.95)
                zc = float(np.interp(x, xs, B)) * 0.15 + float(np.interp(x, xs, T)) * 0.85 - 0.18 - 0.05 * f
                width = 0.07 * (1 - 0.6 * f)
                yw = float(np.interp(x, xs, W)) * 1.012 + 0.003
                for dz in (-width / 2, width / 2):
                    # project the stripe onto the superellipse side by sampling the ring at height dz
                    quad.append((x, side * yw * math.sqrt(max(1 - ((zc + dz - 0.5 * (np.interp(x, xs, T) + np.interp(x, xs, B))) /
                                                                     (0.5 * (np.interp(x, xs, T) - np.interp(x, xs, B)))) ** 2, 0.2)) ** 0.45, zc + dz))
            a, b, c, d = [np.array(q) for q in quad]
            tris += [(a, c, d), (a, d, b)]
    return np.array(tris)
