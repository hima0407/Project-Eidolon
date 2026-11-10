"""Blade-element momentum theory (BEMT) for a constant-speed propeller.

Per radial station (Glauert propeller formulation, e.g. McCormick, Aerodynamics of
V/STOL Flight, ch. 4):
    phi = atan( V(1+a) / (Omega r (1-a')) ),  alpha = beta - phi
    a   = 1 / ( 4F sin^2(phi) / (sigma Cn) - 1 )
    a'  = 1 / ( 4F sin(phi) cos(phi) / (sigma Ct) + 1 )
    F   = Prandtl tip * hub loss factor
    dT  = 1/2 rho W^2 B c Cn dr,  dQ = 1/2 rho W^2 B c Ct r dr
Constant speed: collective pitch beta_75 is found (bisection) so that absorbed power
equals the shaft power at the given rpm.

Upper-bound check (used in tests and in the validation study): no real propeller can
beat the actuator-disk ideal efficiency  eta_i = 2 / (1 + sqrt(1 + T/(q A))).

Previous project code (scripts/propulsion_bemt.py) used an airfoil model with no stall
and was run at 230 km/h / 3000 m. This module adds stall, compressibility, an ideal-pitch
twist law and a momentum-theory sanity bound.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from . import atmosphere as isa


@dataclass
class PropResult:
    V: float
    rpm: float
    beta75_deg: float
    thrust: float
    torque: float
    power: float
    eta: float
    eta_ideal: float
    J: float
    tip_mach: float


class BEMTPropeller:
    def __init__(self, diameter: float = 1.75, blades: int = 3, n_stations: int = 40,
                 hub_ratio: float = 0.18, cl_max: float = 1.25, cd_min: float = 0.0085,
                 design_pitch_ratio: float = 1.0, chord_scale: float = 1.0):
        self.D, self.R, self.B = diameter, diameter / 2, blades
        self.rR = np.linspace(hub_ratio + 0.02, 0.985, n_stations)
        self.r = self.rR * self.R
        self.dr = np.gradient(self.r)
        self.r_hub = hub_ratio * self.R
        # planform: elliptic-ish, max c/R ~0.15 near 0.45R (matches the team's MTV-21-A estimate)
        self.c = self.R * 0.150 * np.sin(np.pi * (self.rR - 0.10) / 0.95) * (1 - 0.25 * self.rR) / 0.92
        if blades == 2:
            self.c *= 1.30           # same activity factor, two wider blades [A]
        self.c *= chord_scale        # wider blades for more power (higher activity factor)
        self.cl_max, self.cd_min = cl_max, cd_min
        # ideal constant-pitch twist: tan(beta) = P / (2 pi r)
        P = design_pitch_ratio * self.D
        self.beta_shape = np.arctan(P / (2 * np.pi * self.r))
        self.beta_shape -= np.interp(0.75, self.rR, self.beta_shape)

    # thin-section blade aerodynamics (Clark-Y / ARA-D class) with stall and compressibility
    def _section(self, alpha, mach):
        pg = 1 / np.sqrt(np.clip(1 - mach**2, 0.2, 1.0))
        cl_lin = 2 * np.pi * 0.95 * (alpha + np.deg2rad(4.0)) * pg
        cl_stall = self.cl_max * pg
        a_st = cl_stall / (2 * np.pi * 0.95 * pg) - np.deg2rad(4.0)
        post = cl_stall - 1.2 * (alpha - a_st)      # soft post-stall drop
        cl = np.where(alpha <= a_st, cl_lin, np.maximum(post, 0.6 * cl_stall))
        cl = np.maximum(cl, -0.6)
        cd = self.cd_min + 0.010 * (cl - 0.45) ** 2 + np.where(alpha > a_st, 0.8 * (alpha - a_st), 0.0)
        cd = cd + np.where(mach > 0.75, 0.6 * (mach - 0.75) ** 2 * 10, 0.0)    # drag rise [A]
        return cl, cd

    def evaluate(self, V: float, rpm: float, beta75_deg: float, h: float = 0.0, dT: float = 0.0) -> PropResult:
        V = max(V, 0.3)
        rho = float(isa.density(h, dT)); a_snd = float(isa.speed_of_sound(h, dT))
        n = rpm / 60; Om = 2 * np.pi * n
        r, c, B = self.r, self.c, self.B
        beta = self.beta_shape + np.deg2rad(beta75_deg)
        sigma = B * c / (2 * np.pi * r)
        a = np.full_like(r, 0.1); ap = np.full_like(r, 0.01)
        for _ in range(200):
            Va, Vt = V * (1 + a), Om * r * (1 - ap)
            phi = np.arctan2(Va, Vt)
            W = np.hypot(Va, Vt)
            cl, cd = self._section(beta - phi, W / a_snd)
            sp, cp = np.sin(phi), np.cos(phi)
            f_t = B / 2 * (self.R - r) / (r * np.abs(sp) + 1e-9)
            f_h = B / 2 * (r - self.r_hub) / (self.r_hub * np.abs(sp) + 1e-9)
            F = (2 / np.pi) ** 2 * np.arccos(np.exp(-np.clip(f_t, 0, 60))) * np.arccos(np.exp(-np.clip(f_h, 0, 60)))
            F = np.maximum(F, 1e-3)
            Cn, Ct = cl * cp - cd * sp, cl * sp + cd * cp
            a_new = 1 / np.maximum(4 * F * sp**2 / np.maximum(sigma * Cn, 1e-9) - 1, 1e-3)
            a_new = np.where(Cn <= 0, 0.0, np.minimum(a_new, 25.0 / V))   # cap induced velocity at 25 m/s
            ap_new = 1 / (4 * F * sp * cp / np.maximum(sigma * Ct, 1e-9) + 1)
            if np.max(np.abs(a_new - a)) < 1e-6 and np.max(np.abs(ap_new - ap)) < 1e-6:
                break
            a = 0.6 * a + 0.4 * a_new; ap = 0.6 * ap + 0.4 * ap_new
        dT_ = 0.5 * rho * W**2 * B * c * Cn
        dQ_ = 0.5 * rho * W**2 * B * c * Ct * r
        T = float(np.sum(dT_ * self.dr)); Q = float(np.sum(dQ_ * self.dr))
        P = Q * Om
        eta = T * V / P if P > 0 and T > 0 else 0.0
        A = np.pi * self.R**2
        q = 0.5 * rho * V**2
        eta_i = 2 / (1 + np.sqrt(1 + max(T, 0) / (q * A))) if V > 1 else 0.0
        tip_m = np.hypot(V, Om * self.R) / a_snd
        return PropResult(V, rpm, beta75_deg, T, Q, P, eta, eta_i, V / (n * self.D), tip_m)

    def at_power(self, V: float, rpm: float, p_shaft_w: float, h: float = 0.0, dT: float = 0.0) -> PropResult:
        """Constant-speed operation: pitch is set so the propeller absorbs p_shaft_w."""
        lo, hi = -5.0, 60.0
        for _ in range(45):
            mid = 0.5 * (lo + hi)
            if self.evaluate(V, rpm, mid, h, dT).power > p_shaft_w:
                hi = mid
            else:
                lo = mid
        return self.evaluate(V, rpm, 0.5 * (lo + hi), h, dT)

    def efficiency_map(self, V_array, rpm, p_shaft_w, h=0.0, dT=0.0):
        return np.array([self.at_power(V, rpm, p_shaft_w, h, dT).eta for V in V_array])


class PropellerTable:
    """Cached eta(V) at a given shaft power/rpm/altitude so performance loops stay fast."""
    def __init__(self, prop: BEMTPropeller, rpm: float, p_shaft_w: float, h: float = 0.0, dT: float = 0.0):
        self.V = np.linspace(2.0, 90.0, 45)
        res = [prop.at_power(V, rpm, p_shaft_w, h, dT) for V in self.V]
        self.eta = np.array([r.eta for r in res])
        self.thrust = np.array([r.thrust for r in res])

    def __call__(self, V):
        return np.interp(V, self.V, self.eta)

    def T(self, V):
        return np.interp(V, self.V, self.thrust)


class PropMap:
    """Non-dimensional propeller map  C_T(J, beta75), C_P(J, beta75)  built once per geometry.

    C_T = T / (rho n^2 D^4),  C_P = P / (rho n^3 D^5),  J = V / (n D),  eta = J C_T / C_P.
    For a constant-speed propeller the operating point is fixed by (J, C_P): pitch is
    whatever absorbs the power. The map is built at sea level and a representative rpm,
    so compressibility is that of a typical tip Mach number (~0.6).
    """
    def __init__(self, prop: BEMTPropeller, rpm_ref: float = 2250.0):
        self.prop = prop
        self.D = prop.D
        self.J = np.concatenate([[0.004, 0.02, 0.05], np.linspace(0.1, 1.5, 29)])
        self.beta = np.linspace(5, 50, 37)
        n = rpm_ref / 60
        CT = np.zeros((len(self.J), len(self.beta))); CP = np.zeros_like(CT)
        rho = float(isa.density(0.0))
        for i, J in enumerate(self.J):
            for j, b in enumerate(self.beta):
                r = prop.evaluate(J * n * self.D, rpm_ref, b, 0.0)
                CT[i, j] = r.thrust / (rho * n**2 * self.D**4)
                CP[i, j] = r.power / (rho * n**3 * self.D**5)
        self.CT, self.CP = CT, CP

    def operating_point(self, V, rpm, p_shaft_w, rho):
        """Return (eta, thrust) for constant-speed operation."""
        n = rpm / 60
        J = max(V / (n * self.D), self.J[0])
        cp_target = p_shaft_w / (rho * n**3 * self.D**5)
        # interpolate rows in J
        i = int(np.clip(np.searchsorted(self.J, J) - 1, 0, len(self.J) - 2))
        t = (J - self.J[i]) / (self.J[i + 1] - self.J[i])
        cp_row = (1 - t) * self.CP[i] + t * self.CP[i + 1]
        ct_row = (1 - t) * self.CT[i] + t * self.CT[i + 1]
        # CP increases with beta (monotone in the useful range): find beta for cp_target
        k = int(np.argmax(cp_row))
        cp_u, ct_u = cp_row[:k + 1], ct_row[:k + 1]
        ct = float(np.interp(cp_target, cp_u, ct_u))
        T = ct * rho * n**2 * self.D**4
        eta = J * ct / cp_target if V > 1 else 0.0
        return max(min(eta, 0.95), 0.0), T
