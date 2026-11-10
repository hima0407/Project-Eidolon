"""Parametric outer-mould-line (OML) mesh generated from the closed design.

Every dimension comes from the design closure (wing area/span/taper/twist/dihedral and real
airfoil coordinates, tail sizes and positions, fuselage length, propeller diameter, gear
position), so the 3-D model can never drift from the numbers. Output: binary STL per component
(import into Fusion 360: Insert > Insert Mesh, then Mesh > Convert to BRep for editing).
Coordinates: x aft from the propeller plane, y starboard, z up; metres.
"""
from __future__ import annotations

import math
import struct
from pathlib import Path

import numpy as np

from .airfoil import load_dat, naca4


# ------------------------------------------------------------------ mesh helpers
def loft(sections, close_ends=True):
    """Triangles between consecutive closed rings of equal point count. sections: list of (N,3)."""
    tris = []
    S = len(sections)
    n = len(sections[0])
    for i in range(S - 1):
        a, b = sections[i], sections[i + 1]
        for j in range(n):
            k = (j + 1) % n
            tris.append((a[j], b[j], b[k]))
            tris.append((a[j], b[k], a[k]))
    if close_ends:
        for ring, flip in ((sections[0], True), (sections[-1], False)):
            c = ring.mean(axis=0)
            for j in range(n):
                k = (j + 1) % n
                tris.append((c, ring[k], ring[j]) if flip else (c, ring[j], ring[k]))
    return np.array(tris)


def write_stl(path: Path, tris: np.ndarray, name="eidolon"):
    tris = np.asarray(tris, dtype=np.float32)
    with open(path, "wb") as f:
        f.write(name.encode()[:80].ljust(80, b" "))
        f.write(struct.pack("<I", len(tris)))
        for t in tris:
            n = np.cross(t[1] - t[0], t[2] - t[0])
            ln = np.linalg.norm(n)
            n = n / ln if ln > 0 else n
            f.write(struct.pack("<12fH", *n, *t[0], *t[1], *t[2], 0))


def _resample(xy, n=61):
    """Resample an airfoil to n points per surface (cosine), closed ring TE-upper-LE-lower."""
    from .airfoil import split_surfaces
    x, yu, yl = split_surfaces(xy)
    xs = 0.5 * (1 - np.cos(np.linspace(0, np.pi, n)))
    up = np.interp(xs, x, yu); lo = np.interp(xs, x, yl)
    ring = np.concatenate([np.column_stack([xs[::-1], up[::-1]]), np.column_stack([xs[1:-1], lo[1:-1]])])
    return ring


# ------------------------------------------------------------------ components
def lifting_surface(s, mirror=True, n_span=24, n_af=45, y_offset=0.0):
    def section(name):
        try:
            return load_dat(name)
        except Exception:
            return naca4(name.replace("naca", ""))
    root = _resample(section(s.airfoil_root), n_af)
    tip = _resample(section(s.airfoil_tip), n_af)
    eta = 0.5 * (1 - np.cos(np.linspace(0, np.pi, n_span)))
    eta = np.unique(np.concatenate([eta, [0.0, 1.0]]))
    tan_le = math.tan(s.sweep_le_rad)
    dih = math.radians(s.dihedral_deg)
    secs = []
    for e in eta:
        c = s.chord_at(e)
        af = (1 - e) * root + e * tip
        tw = math.radians(s.twist_tip_deg * e)
        xs = (af[:, 0] - 0.25) * c
        zs = af[:, 1] * c
        xr = xs * math.cos(tw) + zs * math.sin(tw)
        zr = -xs * math.sin(tw) + zs * math.cos(tw)
        span_pos = e * s.semispan
        x0 = s.x_le_root + span_pos * tan_le + 0.25 * c
        if s.vertical:
            pts = np.column_stack([x0 + xr, zr, s.z_root + span_pos + 0 * xr])
        else:
            pts = np.column_stack([x0 + xr, y_offset + span_pos * math.cos(dih) + 0 * xr,
                                   s.z_root + span_pos * math.sin(dih) + zr])
        secs.append(pts)
    tris = loft(secs)
    if mirror and not s.vertical:
        m = tris.copy(); m[:, :, 1] *= -1; m = m[:, ::-1, :]
        tris = np.concatenate([tris, m])
    return tris


def fuselage_profiles(L, w_max, h_body):
    """Smooth half-width, top and bottom lines of the body (no canopy)."""
    x_c = np.array([0.10, 0.25, 0.55, 1.00, 1.40, 2.00, 2.80, 3.40, 4.20, 5.20, 6.20, L])
    w_c = np.array([0.17, 0.30, 0.44, 0.54, 0.58, 0.58, 0.56, 0.46, 0.32, 0.20, 0.11, 0.012]) * (w_max / 1.16)
    t_c = np.array([0.15, 0.24, 0.32, 0.40, 0.44, 0.45, 0.43, 0.36, 0.28, 0.24, 0.235, 0.20])
    b_c = np.array([-0.15, -0.30, -0.42, -0.55, -0.62, -0.64, -0.60, -0.48, -0.32, -0.16, -0.01, 0.17]) * (h_body / 1.05)
    return x_c, w_c, t_c, b_c


def fuselage(L, w_max, h_body, n_x=70, n_r=56, p=2.5):
    x_c, w_c, t_c, b_c = fuselage_profiles(L, w_max, h_body)
    xs = np.linspace(x_c[0], L, n_x)
    from numpy import interp
    def smooth(xc, yc):
        y = interp(xs, xc, yc)
        k = np.ones(7) / 7
        ys = np.convolve(np.pad(y, 3, mode="edge"), k, mode="valid")
        return ys
    W, T, B = smooth(x_c, w_c), smooth(x_c, t_c), smooth(x_c, b_c)
    th = np.linspace(0, 2 * np.pi, n_r, endpoint=False)
    secs = []
    for x, w, t, b in zip(xs, W, T, B):
        zc, hz = 0.5 * (t + b), 0.5 * (t - b)
        c, s = np.cos(th), np.sin(th)
        y = w * np.sign(c) * np.abs(c) ** (2 / p)
        z = zc + hz * np.sign(s) * np.abs(s) ** (2 / p)
        secs.append(np.column_stack([x + 0 * y, y, z]))
    return loft(secs), (xs, W, T, B)


def ellipsoid(c, r, n_u=36, n_v=20, squash_bottom=False):
    u = np.linspace(0, 2 * np.pi, n_u, endpoint=False)
    v = np.linspace(-np.pi / 2, np.pi / 2, n_v)[1:-1]
    # treat x as the polar axis: rebuild with x varying
    secs = []
    for vv in v:
        rr = np.cos(vv)
        secs.append(np.column_stack([c[0] + r[0] * np.sin(vv) + 0 * u, c[1] + r[1] * rr * np.cos(u),
                                     c[2] + r[2] * rr * np.sin(u) * (1 if not squash_bottom else 1)]))
    return loft(secs)


def canopy(x0, x1, z_base, half_w, h, n_x=30, n_r=40):
    xs = np.linspace(x0, x1, n_x)
    secs = []
    th = np.linspace(0, np.pi, n_r)
    for x in xs:
        s = (x - x0) / (x1 - x0)
        prof = math.sin(math.pi * s ** 0.85) ** 0.9   # blunt windscreen, long tapering rear
        prof = max(prof, 1e-3)
        y = half_w * prof ** 0.5 * np.cos(th)
        z = z_base - 0.04 + h * prof * np.sin(th)
        secs.append(np.column_stack([x + 0 * y, y, z]))
    return loft(secs)


def spinner(x_tip, x_base, r, n=40, m=16):
    th = np.linspace(0, 2 * np.pi, n, endpoint=False)
    secs = []
    for s in np.linspace(0.02, 1.0, m):
        rr = r * math.sqrt(s) ** 1.0 * (1 - (1 - s) ** 2) ** 0.35
        x = x_tip + (x_base - x_tip) * s
        secs.append(np.column_stack([x + 0 * th, rr * np.cos(th), rr * np.sin(th)]))
    return loft(secs)


def propeller(x_plane, R, blades, chord_fn, beta75_deg=22.0, r_hub=0.15):
    af = _resample(naca4("4412"), 21)
    tris = []
    rs = np.linspace(r_hub, R * 0.99, 14)
    for b in range(blades):
        phi = 2 * math.pi * b / blades + 0.3
        secs = []
        for r in rs:
            c = chord_fn(r / R) * R
            beta = math.atan(math.tan(math.radians(beta75_deg)) * 0.75 * R / r)
            xa = (af[:, 0] - 0.35) * c
            ya = af[:, 1] * c
            # blade chord lies in the plane of rotation rotated by beta
            xb = x_plane + xa * math.sin(beta) - ya * math.cos(beta)
            tb = xa * math.cos(beta) + ya * math.sin(beta)
            y = r * math.cos(phi) - tb * math.sin(phi)
            z = r * math.sin(phi) + tb * math.cos(phi)
            secs.append(np.column_stack([xb, y, z]))
        tris.append(loft(secs))
    return np.concatenate(tris)


def leaf_leg(x, y0, z0, y1, z1, w0=0.085, w1=0.045, t=0.03):
    """Tapered flat leaf from fuselage (y0,z0) to axle (y1,z1), faired cross-section."""
    secs = []
    th = np.linspace(0, 2 * np.pi, 20, endpoint=False)
    for s in np.linspace(0, 1, 12):
        yy, zz = y0 + (y1 - y0) * s, z0 + (z1 - z0) * s
        w = w0 + (w1 - w0) * s
        # section in x (chord, streamlined) and normal to leg
        d = np.array([0, y1 - y0, z1 - z0]); d /= np.linalg.norm(d)
        nrm = np.array([0, -d[2], d[1]])
        xs = x + w * 1.6 * np.cos(th) - 0.02
        off = t * 0.5 * np.sin(th)
        secs.append(np.column_stack([xs, yy + off * nrm[1], zz + off * nrm[2]]))
    return loft(secs)


def build_aircraft_mesh(ac, env, beta75=22.0) -> dict:
    """Return {component: triangles} for the closed aircraft."""
    from .propeller import BEMTPropeller
    f = ac.fuselage
    h_body = 1.05
    parts = {}
    parts["fuselage"], prof = fuselage(f.length, f.width, h_body)
    xs, W, T, B = prof
    z_top_at = lambda x: float(np.interp(x, xs, T))
    z_bot_at = lambda x: float(np.interp(x, xs, B))
    parts["canopy"] = canopy(1.22, 3.30, z_top_at(2.0), 0.50, 0.36)
    # wing: low wing, root at fuselage bottom region
    ac.wing.z_root = z_bot_at(ac.wing.x_le_root + 0.4) + 0.16
    parts["wing"] = lifting_surface(ac.wing)
    ac.htail.z_root = z_top_at(ac.htail.x_le_root + 0.3) - 0.06
    parts["horizontal_tail"] = lifting_surface(ac.htail)
    ac.vtail.z_root = z_top_at(ac.vtail.x_le_root + 0.3) - 0.05
    parts["vertical_tail"] = lifting_surface(ac.vtail, mirror=False)
    parts["spinner"] = spinner(-0.30, 0.10, 0.17)
    bp = BEMTPropeller(ac.prop.diameter, ac.prop.blades, chord_scale=ac.prop.chord_scale)
    chord_fn = lambda rR: float(np.interp(rR, bp.rR, bp.c / bp.R))
    parts["propeller"] = propeller(0.0, ac.prop.diameter / 2, ac.prop.blades, chord_fn, beta75)
    # landing gear: main leaf legs + wheel pants, nose leg + pant
    x_mg = env.x_main_gear
    wheel_r = ac.gear.main_tyre_d / 2
    z_ground = -0.875 - 0.42                      # propeller tip clearance 0.42 m (> 0.18 m CS-23.925)
    z_axle = z_ground + wheel_r
    y_track = 1.05
    gear = []
    for sgn in (1, -1):
        gear.append(leaf_leg(x_mg, sgn * 0.38, z_bot_at(x_mg) + 0.08, sgn * y_track, z_axle + 0.06))
        gear.append(ellipsoid((x_mg + 0.05, sgn * y_track, z_axle + 0.02), (0.36, 0.11, 0.24)))
    x_ng = ac.x_nose_gear
    gear.append(leaf_leg(x_ng, 0.0001, z_bot_at(x_ng) + 0.05, 0.0, z_ground + ac.gear.nose_tyre_d / 2 + 0.05, 0.05, 0.04, 0.05))
    gear.append(ellipsoid((x_ng + 0.03, 0.0, z_ground + ac.gear.nose_tyre_d / 2 + 0.02), (0.30, 0.085, 0.21)))
    parts["landing_gear"] = np.concatenate(gear)
    parts["_meta"] = {"z_ground": z_ground, "y_track": y_track, "x_main_gear": x_mg, "wheelbase": x_mg - x_ng}
    return parts
