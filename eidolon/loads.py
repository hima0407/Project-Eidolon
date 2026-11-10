"""V-n diagram to CS-23 (utility category) - manoeuvre envelope plus gust lines.

CS-23.335 design speeds:  V_C >= 33 sqrt(W/S) [kt, W/S in lb/ft^2],  V_D >= 1.50 V_C,min (utility)
CS-23.337 limit load factors (utility): n+ = 4.4, n- = -0.4 n+ = -1.76
CS-23.341 gust load factor:  n = 1 +/- K_g U_de V a / (2 W/S)   (EAS, rho0)
          K_g = 0.88 mu / (5.3 + mu),  mu = 2 (W/S) / (rho c a g)
          U_de = 15.24 m/s at V_C, 7.62 m/s at V_D
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from . import atmosphere as isa

KT = 0.514444


@dataclass
class VnResult:
    VS1: float
    VA: float
    VC: float
    VD: float
    n_pos: float
    n_neg: float
    gust_c: float
    gust_d: float
    kg: float


def vn(W: float, S: float, mac: float, cl_alpha: float, cl_max: float, cl_min: float = -0.8,
       n_pos: float = 4.4, VC_cruise: float | None = None) -> VnResult:
    ws = W / S
    ws_psf = ws * 0.020885
    VC_min = 33 * math.sqrt(ws_psf) * KT
    VC = max(VC_min, VC_cruise or 0)
    VD = max(1.50 * VC_min, 1.25 * VC)
    VS1 = math.sqrt(2 * ws / (isa.RHO0 * cl_max))
    VA = VS1 * math.sqrt(n_pos)
    mu = 2 * ws / (isa.RHO0 * mac * cl_alpha * 9.80665)
    kg = 0.88 * mu / (5.3 + mu)
    g = lambda U, V: kg * isa.RHO0 * U * V * cl_alpha / (2 * ws)
    return VnResult(VS1, VA, VC, VD, n_pos, -0.4 * n_pos, g(15.24, VC), g(7.62, VD), kg)
