"""Point and mission performance for a propeller aircraft.

Steady level flight:      P_req = D V = (q S CD0 + k W^2 / (q S)) V
Power available:          P_av  = eta_installed(V) * P_shaft(h, dT)
Rate of climb:            ROC   = (P_av - P_req) / W                 (quasi-steady, small angle)
Service ceiling:          altitude where max ROC = 0.508 m/s (100 ft/min)
Range:                    numerical integration of dW/dx = -g * FF / V at constant TAS & altitude
                          (Breguet is reported alongside as a closed-form check)
Take-off ground roll:     integrate m dV/dt = T - D - mu (W - L) to V_LOF = 1.1 V_s,TO,
                          then airborne distance to 15 m (Raymer sec. 17.8)
Landing:                  approach 1.3 V_s0 over 15 m on a 3 deg path, flare, braked roll
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from . import atmosphere as isa
from .aero import Polar
from .engines import Engine, FUEL_DENSITY
from .propeller import BEMTPropeller, PropMap

G = 9.80665
ROC_CEILING = 0.508


@dataclass
class Plane:
    """Minimal performance view of an aircraft: polar + mass + engine + propeller."""
    name: str
    S: float
    polar: Polar
    engine: Engine
    pmap: PropMap
    eta_install: float = 0.92       # spinner/fuselage blockage, scrubbing, blade Re [A] (Gudmundsson ch. 14)
    climb_factor: float = 1.0       # high-power/low-speed excess-power factor, fitted on Hansa-NG ROC

    def _rpm(self, rating):
        return self.engine.prop_rpm_max if rating == "takeoff" else self.engine.prop_rpm_cruise * 1.08

    def eta(self, V, h=0.0, dT=0.0, rating="mcp", throttle=1.0):
        p = self.p_shaft(h, dT, rating) * throttle
        rho = float(isa.density(h, dT))
        Vs = np.atleast_1d(np.asarray(V, dtype=float))
        out = np.array([self.pmap.operating_point(v, self._rpm(rating), p, rho)[0] for v in Vs])
        out = out * self.eta_install * (self.climb_factor if rating == "takeoff" else 1.0)
        return out if np.ndim(V) else float(out[0])

    def thrust(self, V, h=0.0, dT=0.0, rating="takeoff", extra_power_w=0.0):
        p = self.p_shaft(h, dT, rating) + extra_power_w
        return self.pmap.operating_point(V, self._rpm(rating), p, float(isa.density(h, dT)))[1] \
            * self.eta_install * self.climb_factor

    def bsfc(self, power_fraction):
        """Part-power BSFC: flat above 55 % power, rising below it [A] (typical piston behaviour)."""
        return self.engine.bsfc_g_kwh * (1 + 0.8 * max(0.0, 0.55 - power_fraction))

    def p_shaft(self, h=0.0, dT=0.0, rating="mcp"):
        return float(self.engine.power_available_kw(h, dT, rating)) * 1e3

    def p_req(self, V, W, h=0.0, dT=0.0, cd0_extra=0.0):
        q = 0.5 * isa.density(h, dT) * np.asarray(V) ** 2
        cl = W / (q * self.S)
        return (q * self.S * (self.polar.cd0 + cd0_extra + self.polar.k * cl**2)) * V

    def p_av(self, V, h=0.0, dT=0.0, rating="mcp"):
        return self.eta(V, h, dT, rating) * self.p_shaft(h, dT, rating)

    def v_stall(self, W, clmax, h=0.0, dT=0.0):
        return np.sqrt(2 * W / (isa.density(h, dT) * self.S * clmax))

    # ---------------------------------------------------------------- point performance
    def roc_curve(self, W, h=0.0, dT=0.0, rating="mcp"):
        vs = float(self.v_stall(W, self.polar.cl_max_clean, h, dT))
        V = np.linspace(1.15 * vs, 75, 200)
        return V, (self.p_av(V, h, dT, rating) - self.p_req(V, W, h, dT)) / W

    def max_roc(self, W, h=0.0, dT=0.0, rating="mcp"):
        V, roc = self.roc_curve(W, h, dT, rating)
        i = int(np.argmax(roc))
        return float(roc[i]), float(V[i])

    def v_max(self, W, h=0.0, dT=0.0, rating="mcp", power_fraction=1.0):
        V = np.linspace(30, 95, 651)
        if power_fraction == 1.0:
            excess = self.p_av(V, h, dT, rating) - self.p_req(V, W, h, dT)
        else:   # power_fraction is a fraction of *sea-level rated* power (POH convention), cruise rpm
            p = min(self.p_shaft(0.0, 0.0, "takeoff") * power_fraction, self.p_shaft(h, dT, "mcp"))
            thr = p / self.p_shaft(h, dT, "mcp")
            excess = self.eta(V, h, dT, "mcp", thr) * p - self.p_req(V, W, h, dT)
        ok = np.where(excess >= 0)[0]
        return float(V[ok[-1]]) if len(ok) else np.nan

    def ceiling(self, W, dT=0.0, target=ROC_CEILING):
        hs = np.arange(0, 9001, 250.0)
        roc = np.array([self.max_roc(W, h, dT)[0] for h in hs])
        if roc[-1] > target:
            return float(hs[-1])
        return float(np.interp(-target, -roc, hs))

    def cruise_power(self, V, W, h=0.0, dT=0.0):
        """Shaft power needed for level flight at V (constant-speed prop, cruise rpm)."""
        p_req = float(self.p_req(V, W, h, dT))
        # efficiency depends weakly on power; two fixed-point passes
        frac = 0.65
        for _ in range(4):
            frac = min(max(p_req / (self.eta(V, h, dT, "mcp", frac) * self.p_shaft(h, dT)), 0.15), 1.2)
        return p_req / self.eta(V, h, dT, "mcp", frac), frac

    # ---------------------------------------------------------------- mission performance
    def range_km(self, W0, fuel_kg, V, h, dT=0.0, reserve_min=45.0, allowance_kg=None):
        """Range at constant TAS and altitude, with taxi/TO/climb allowance and timed reserve."""
        if allowance_kg is None:
            allowance_kg = 2.5          # taxi + take-off + climb to 1500 m, ~3.5 L [A]
        p_res, fr = self.cruise_power(V, W0 - fuel_kg * G * 0.8, h, dT)
        reserve_kg = self.bsfc(fr) * (p_res / 1e3) * (reserve_min / 60) / 1e3
        burn = fuel_kg - allowance_kg - reserve_kg
        if burn <= 0:
            return 0.0, reserve_kg
        W, x, dw = W0 - allowance_kg * G, 0.0, burn / 40
        for _ in range(40):
            p, fr = self.cruise_power(V, W - 0.5 * dw * G, h, dT)
            ff = self.bsfc(fr) * p / 3.6e9                   # kg/s
            x += V * dw / ff
            W -= dw * G
        return x / 1e3, reserve_kg

    def fuel_per_100km(self, W, V, h, dT=0.0):
        p, fr = self.cruise_power(V, W, h, dT)
        lph = self.bsfc(fr) * p / 1e6 / FUEL_DENSITY
        return float(lph / (V * 3.6) * 100), float(lph), float(p)

    def best_range_speed(self, W, h, dT=0.0):
        V = np.linspace(30, 70, 81)
        fpk = [self.fuel_per_100km(W, v, h, dT)[0] for v in V]
        return float(V[int(np.argmin(fpk))])

    def endurance_h(self, W0, fuel_kg, h, dT=0.0):
        """Maximum endurance (minimum fuel-flow speed). Returns (hours, speed)."""
        V = np.linspace(25, 60, 71)
        best = None
        for v in V:
            p, fr = self.cruise_power(v, W0 - 0.5 * fuel_kg * G, h, dT)
            ff = self.bsfc(fr) * p / 1e6
            if best is None or ff < best[0]:
                best = (ff, v)
        return float(fuel_kg / best[0]), best[1]

    def speed_at_power(self, W, h, power_fraction, dT=0.0):
        return self.v_max(W, h, dT, "takeoff", power_fraction)

    def range_at_power(self, W0, fuel_kg, h, power_fraction, reserve_min=45.0):
        V = self.speed_at_power(W0 - 0.5 * fuel_kg * G, h, power_fraction)
        return self.range_km(W0, fuel_kg, V, h, reserve_min=reserve_min)[0], V

    def takeoff_distance(self, W, h=0.0, dT=0.0, mu=0.04, screen=15.0, extra_power_w=0.0):
        """Ground roll + airborne distance to a 15 m screen; returns (ground, total, V_LOF)."""
        rho = float(isa.density(h, dT))
        clmax = self.polar.cl_max_to
        v_lof = 1.1 * float(self.v_stall(W, clmax, h, dT))
        cl_g = 0.6                     # ground-run attitude lift coefficient [A]
        m = W / G
        V, x, dt = 0.5, 0.0, 0.02
        while V < v_lof and x < 5000:
            q = 0.5 * rho * V**2
            T = self.thrust(V, h, dT, "takeoff", extra_power_w)
            D = q * self.S * (self.polar.cd0 + 0.008 + self.polar.k * cl_g**2)   # +flaps/gear-down increment [A]
            L = q * self.S * cl_g
            a = (T - D - mu * (W - L)) / m
            V += a * dt; x += V * dt
        # airborne: transition arc + climb (Raymer eqs. 17.107-17.111)
        v_tr = 1.15 * float(self.v_stall(W, clmax, h, dT))
        R = v_tr**2 / (0.2 * G)
        T = self.thrust(v_tr, h, dT, "takeoff", extra_power_w)
        D = 0.5 * rho * v_tr**2 * self.S * (self.polar.cd0 + 0.008 + self.polar.k * (clmax / 1.15**2) ** 2)
        gamma = max((T - D) / W, 0.02)
        h_tr = R * (1 - np.cos(gamma))
        if h_tr >= screen:
            s_air = np.sqrt(R**2 - (R - screen) ** 2)
        else:
            s_air = R * np.sin(gamma) + (screen - h_tr) / np.tan(gamma)
        return x, x + s_air, v_lof

    def landing_distance(self, W, h=0.0, dT=0.0, mu_brake=0.35, screen=15.0):
        rho = float(isa.density(h, dT))
        vs0 = float(self.v_stall(W, self.polar.cl_max_land, h, dT))
        v_a, v_td = 1.3 * vs0, 1.15 * vs0
        gam = np.deg2rad(3.0)
        h_flare = 1.5                                            # flare initiation height [A]
        s_a = (screen - h_flare) / np.tan(gam)
        s_a += (v_a**2 - v_td**2) / (2 * G * 0.10)                # float: decelerate at D/W ~ 0.10 [A]
        s_free = 1.0 * v_td                                      # 1 s free roll
        # braked roll with aerodynamic drag, idle thrust ~0
        V, x, dt, m = v_td, 0.0, 0.02, W / G
        while V > 0.5:
            q = 0.5 * rho * V**2
            D = q * self.S * (self.polar.cd0 + 0.015 + self.polar.k * 0.3**2)
            L = q * self.S * 0.3
            a = -(D + mu_brake * max(W - L, 0)) / m
            V += a * dt; x += V * dt
        return s_a + s_free + x, vs0
