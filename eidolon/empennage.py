"""Empennage configuration: presets, spin-recovery and deep-stall screening.

Spin recovery - Tail Damping Power Factor (Bowman, NASA TN D-6575, 1971; reproduced in Raymer ch. 16):
    TDPF = TDR * URVC
    TDR  = S_F L^2 / (S (b/2)^2)              fuselage side area below the horizontal tail (damping)
    URVC = sum(S_R,i L_i) / (S (b/2))         rudder area NOT blanketed by the horizontal tail's wake
  The blanketed region in a spin is bounded by lines from the HT trailing edge at 60 deg and from the
  HT leading edge at 30 deg (relative wind from below). TDPF is a screening criterion from spin-tunnel
  statistics, not a guarantee; light trainers typically want TDPF >~ 200e-6 [A].
Deep stall - the HT enters the separated wing wake at the angle of attack where the line from the wing
  trailing edge to the tail is aligned with the local flow:  alpha_wake (1 - de/da) = atan(dz/dx).
  A wake crossing in the post-stall range (alpha_stall + 5 deg .. 45 deg) means a deep-stall risk
  (the classic T-tail problem); a crossing near or below the stall gives buffet warning and a tail
  that is clear of the wake beyond the stall.
"""
from __future__ import annotations

import copy
import math

import numpy as np

from .aircraft import Aircraft, place_tails

TDPF_REQUIRED = 200e-6

PRESETS = {
    "Conventional (low, fin above)": dict(tail_config="conventional", ht_height_frac=0.0, ht_forward_shift=0.0,
                                         eta_h=0.90, interference_tail=1.05, ht_endplate=1.00,
                                         ht_mass_factor=1.00, vt_mass_factor=1.00, slipstream_immersion=None,
                                         ventral_strake_m2=0.0),
    "Conventional + ventral strake": dict(tail_config="conventional", ht_height_frac=0.0, ht_forward_shift=0.0,
                                         eta_h=0.90, interference_tail=1.05, ht_endplate=1.00, ht_mass_factor=1.00,
                                         vt_mass_factor=1.00, slipstream_immersion=None, ventral_strake_m2=0.18),
    "Cruciform (HT at 40 % fin)": dict(tail_config="cruciform", ht_height_frac=0.40, eta_h=0.95, interference_tail=1.06,
                                         ht_endplate=1.04, ht_mass_factor=1.00, vt_mass_factor=1.10, slipstream_immersion=0.30, ventral_strake_m2=0.0),
    "T-tail": dict(tail_config="T-tail", ht_height_frac=0.95, eta_h=1.00, interference_tail=1.04, ht_endplate=1.12,
                                         ht_mass_factor=1.00, vt_mass_factor=1.22, slipstream_immersion=0.0, ventral_strake_m2=0.0),
    "H-tail (twin fins at HT tips)": dict(tail_config="H-tail", ht_height_frac=0.0, eta_h=0.92, interference_tail=1.09,
                                         ht_endplate=1.10, ht_mass_factor=1.15, vt_mass_factor=1.12, slipstream_immersion=None, ventral_strake_m2=0.0),
    "V-tail": dict(tail_config="V-tail", ht_height_frac=0.0, eta_h=0.93, interference_tail=1.02, ht_endplate=1.00,
                                         ht_mass_factor=1.03, vt_mass_factor=1.03, slipstream_immersion=None, ventral_strake_m2=0.0),
}
NOTES = {
    "T-tail": "out of the slipstream: loses propwash for take-off rotation; heavier fin (Raymer: +20 % for Ht/Hv = 1); deep-stall check",
    "V-tail": "ruddervator mixing; adverse roll with rudder; spin recovery historically weak (Bonanza 35); TDPF not defined",
    "H-tail (twin fins at HT tips)": "end-plate gain, but four junctions and two fins to build and inspect",
}


def apply(ac: Aircraft, preset: str) -> Aircraft:
    a = copy.deepcopy(ac)
    for k, v in PRESETS[preset].items():
        setattr(a, k, v)
    place_tails(a, a.vh, a.vv)
    return a


def fuselage_depth(ac: Aircraft, x: np.ndarray):
    """Tail-cone bottom and top z [m] at station x (same body lines as the 3-D model)."""
    from .geometry3d import fuselage_profiles
    xc, wc, tc, bc = fuselage_profiles(ac.fuselage.length, ac.fuselage.width, 1.05)
    return np.interp(x, xc, bc, left=bc[0], right=np.nan), np.interp(x, xc, tc, left=tc[0], right=np.nan)


def tdpf(ac: Aircraft, x_cg: float) -> dict:
    """Bowman's tail damping power factor for the side-view geometry of ``ac``."""
    if ac.tail_config == "V-tail":
        return {"TDPF": np.nan, "TDR": np.nan, "URVC": np.nan, "unshielded_rudder_m2": np.nan, "S_F": np.nan}
    w, ht, vt = ac.wing, ac.htail, ac.vtail
    S, bh = w.area, w.span / 2
    x_le_h, x_te_h, z_h = ht.x_le_root, ht.x_le_root + ht.c_root, ht.z_root
    # fuselage (plus ventral strake) side area below the HT, from HT LE aft
    xs = np.linspace(x_le_h, ac.fuselage.length, 60)
    zb, zt = fuselage_depth(ac, xs)
    depth = np.clip(np.minimum(zt, z_h) - zb, 0, None)
    depth = np.nan_to_num(depth)
    S_F = float(np.trapezoid(depth, xs)) + ac.ventral_strake_m2
    x_F = float(np.trapezoid(depth * xs, xs) / max(np.trapezoid(depth, xs), 1e-9)) if S_F > ac.ventral_strake_m2 else ac.fuselage.length - 0.4
    if ac.ventral_strake_m2:
        x_F = (x_F * (S_F - ac.ventral_strake_m2) + (ac.fuselage.length - 0.5) * ac.ventral_strake_m2) / S_F
    L_F = x_F - x_cg
    TDR = S_F * L_F**2 / (S * bh**2)
    # rudder: aft 35 % of the fin chord, from fin root to 95 % height (H-tail: two fins at the HT tips,
    # half the area each, root at the HT; both sit outboard of the HT wake in a spin)
    n = 80
    zz = np.linspace(vt.z_root, vt.z_root + 0.95 * vt.span, n)
    dz_cell = zz[1] - zz[0]
    unsh, moment = 0.0, 0.0
    for z in zz:
        f = (z - vt.z_root) / vt.span
        c = vt.c_root * (1 - (1 - vt.taper) * f)
        x_le = vt.x_le_root + (z - vt.z_root) * math.tan(vt.sweep_le_rad)
        xr = np.linspace(x_le + 0.65 * c, x_le + c, 12)
        dxr = xr[1] - xr[0]
        h = z - z_h
        if ac.tail_config == "H-tail" or h <= 0:
            shielded = np.zeros_like(xr, dtype=bool)
        else:
            shielded = (xr >= x_te_h + h / math.tan(math.radians(60))) & (xr <= x_le_h + h / math.tan(math.radians(30)))
        a = (~shielded).sum() * dxr * dz_cell
        unsh += a
        moment += a * (xr[~shielded].mean() - x_cg if (~shielded).any() else 0.0)
    # rudder portion below the HT on a ventral extension of the conventional-forward layout
    if ac.ventral_strake_m2:
        a = 0.6 * ac.ventral_strake_m2
        unsh += a; moment += a * (ac.fuselage.length - 0.3 - x_cg)
    URVC = moment / (S * bh)
    return {"TDPF": TDR * URVC, "TDR": TDR, "URVC": URVC, "unshielded_rudder_m2": unsh, "S_F": S_F}


def wake_crossing_alpha(ac: Aircraft, deps_dalpha: float) -> float:
    """Angle of attack [deg] at which the HT is immersed in the wing wake."""
    w, ht = ac.wing, ac.htail
    x_te = w.x_le_mac + w.mac
    dz = ht.z_root - (w.z_root + 0.02)
    dx = ht.x_le_root + 0.25 * ht.c_root - x_te
    return math.degrees(math.atan2(dz, dx)) / (1 - deps_dalpha)
