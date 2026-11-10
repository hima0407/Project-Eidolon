"""International Standard Atmosphere (troposphere, 0-11 km) with a temperature offset.

A hot day is modelled the usual way: pressure follows the ISA pressure-altitude
law, temperature is shifted by ``dT`` and density follows from the gas law.
Reference: ICAO Doc 7488 (Manual of the ICAO Standard Atmosphere).
"""
from __future__ import annotations

import numpy as np

G0 = 9.80665          # m/s^2
R_AIR = 287.05287     # J/(kg K)
T0 = 288.15           # K
P0 = 101325.0         # Pa
RHO0 = 1.225          # kg/m^3
LAPSE = 0.0065        # K/m
GAMMA = 1.4


def temperature(h, dT: float = 0.0):
    """Static temperature [K] at geopotential altitude h [m]."""
    return T0 - LAPSE * np.asarray(h, dtype=float) + dT


def pressure(h):
    """Static pressure [Pa]; independent of dT (h is pressure altitude)."""
    return P0 * (1.0 - LAPSE * np.asarray(h, dtype=float) / T0) ** (G0 / (R_AIR * LAPSE))


def density(h, dT: float = 0.0):
    """Air density [kg/m^3]."""
    return pressure(h) / (R_AIR * temperature(h, dT))


def sigma(h, dT: float = 0.0):
    """Density ratio rho/rho0."""
    return density(h, dT) / RHO0


def viscosity(h, dT: float = 0.0):
    """Dynamic viscosity [Pa s], Sutherland's law."""
    T = temperature(h, dT)
    return 1.458e-6 * T ** 1.5 / (T + 110.4)


def speed_of_sound(h, dT: float = 0.0):
    return np.sqrt(GAMMA * R_AIR * temperature(h, dT))


def reynolds(V, L, h, dT: float = 0.0):
    """Reynolds number for speed V [m/s] and length L [m]."""
    return density(h, dT) * V * L / viscosity(h, dT)


def isa_dT_for_oat(oat_celsius: float, h: float) -> float:
    """Temperature offset that gives outside air temperature ``oat_celsius`` at altitude h."""
    return (oat_celsius + 273.15) - (T0 - LAPSE * h)
