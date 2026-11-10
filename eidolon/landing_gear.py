"""Self-sensing composite leaf-spring main gear.

1. Landing energy (CS-23.473): limit descent velocity v = 4.4 (W/S)^0.25 ft/s (7-10 ft/s),
   wing lift = 2/3 W during the impact, so the gear absorbs  E = 1/2 m v^2 + (W/3) delta.
2. Spring sizing: width-tapered cantilever (constant surface stress, 'uniform-strength' leaf):
      U = sigma^2 Vol / (6 E)    (one third of the material at full stress-energy density)
      tip deflection  delta = sigma L^2 / (E t)  ->  t = sigma L^2 / (E delta)
      root width      b0 = 6 F L / (sigma t^2)
   Material merit index for minimum mass per stored energy:  sigma^2 / (E rho)  (Ashby).
3. Piezo sensing: a PVDF film bonded where the spring strain is a known fraction of peak.
   Open-circuit voltage  V = g31 * E_pvdf * strain * t_film.  Peak strain ~ peak force ~ v_sink
   (linear spring: F = sqrt(2 k E) and E ~ v^2), so the sensor reads sink rate directly.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

G = 9.80665

# design (limit-load) allowables after knock-downs [A]; elastic moduli typical handbook values
MATERIALS = {
    "S-glass/epoxy UD": dict(E=50e9, sigma=700e6, rho=2000.0),
    "E-glass/epoxy UD": dict(E=40e9, sigma=550e6, rho=1950.0),
    "Carbon/epoxy UD (T700)": dict(E=125e9, sigma=900e6, rho=1550.0),
    "Spring steel (4340)": dict(E=205e9, sigma=930e6, rho=7850.0),
    "Aluminium 7075-T6": dict(E=71e9, sigma=330e6, rho=2810.0),
}

PVDF = dict(g31=0.216, E=2.5e9, t=28e-6, eps_r=12.0)   # TE Connectivity LDT0-028K class film


def sink_speed_cs23(wing_loading_n_m2: float) -> float:
    ws_psf = wing_loading_n_m2 * 0.020885
    v_fps = min(max(4.4 * ws_psf ** 0.25, 7.0), 10.0)
    return v_fps * 0.3048


@dataclass
class LeafDesign:
    material: str
    energy_per_leg_J: float
    deflection_m: float
    peak_force_N: float
    load_factor: float
    thickness_m: float
    root_width_m: float
    mass_per_leg_kg: float
    merit: float


def size_leaf(W: float, ws: float, material: str, L: float = 0.75, n_gear: float = 3.0,
              v_sink: float | None = None) -> LeafDesign:
    m = MATERIALS[material]
    v = v_sink or sink_speed_cs23(ws)
    mass = W / G
    # energy per main leg, iterate deflection so that the peak load factor equals n_gear
    delta = 0.15
    for _ in range(60):
        E_leg = 0.5 * (0.5 * mass * v**2 + (W / 3) * delta)
        F = 2 * E_leg / delta                       # linear spring peak force
        delta_new = 2 * E_leg / (n_gear * W / 2)
        if abs(delta_new - delta) < 1e-6:
            break
        delta = 0.5 * delta + 0.5 * delta_new
    t = m["sigma"] * L**2 / (m["E"] * delta)
    b0 = 6 * F * L / (m["sigma"] * t**2)
    vol = 0.5 * b0 * t * L
    return LeafDesign(material, E_leg, delta, F, F / (W / 2), t, b0, vol * m["rho"],
                      m["sigma"] ** 2 / (m["E"] * m["rho"]))


def pvdf_voltage(strain: float) -> float:
    return PVDF["g31"] * PVDF["E"] * strain * PVDF["t"]


def pvdf_energy_uJ(strain: float, area_m2: float = 1.0e-3) -> float:
    C = PVDF["eps_r"] * 8.854e-12 * area_m2 / PVDF["t"]
    return 0.5 * C * pvdf_voltage(strain) ** 2 * 1e6
