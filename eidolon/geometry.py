"""Planform and body geometry.

Coordinates: x aft from the propeller plane, y to starboard, z up. Metres.
Wetted-area formulas follow Torenbeek (Synthesis of Subsonic Airplane Design,
1982, App. F) and Raymer (Aircraft Design: A Conceptual Approach, 6th ed., ch. 7).
"""
from __future__ import annotations

from dataclasses import dataclass, field
import math


@dataclass
class Surface:
    """A trapezoidal lifting surface (wing, horizontal or vertical tail)."""
    name: str
    area: float                  # reference (projected) area [m^2]; for a VT: one panel
    aspect_ratio: float
    taper: float
    t_c_root: float
    t_c_tip: float
    sweep_c4_deg: float = 0.0
    dihedral_deg: float = 0.0
    twist_tip_deg: float = 0.0   # negative = washout
    x_le_root: float = 0.0       # x of root leading edge
    z_root: float = 0.0
    x_t: float = 0.30            # chordwise max-thickness position
    vertical: bool = False
    airfoil_root: str = "naca0012"
    airfoil_tip: str = "naca0012"

    # --- derived planform ---
    @property
    def span(self) -> float:
        """Full span (for a vertical tail: its height)."""
        return math.sqrt(self.area * self.aspect_ratio)

    @property
    def semispan(self) -> float:
        return self.span if self.vertical else self.span / 2

    @property
    def c_root(self) -> float:
        return 2 * self.area / (self.span * (1 + self.taper)) if not self.vertical else \
            2 * self.area / (self.span * (1 + self.taper))

    @property
    def c_tip(self) -> float:
        return self.c_root * self.taper

    @property
    def mac(self) -> float:
        lam = self.taper
        return (2 / 3) * self.c_root * (1 + lam + lam**2) / (1 + lam)

    @property
    def y_mac(self) -> float:
        lam = self.taper
        return self.semispan / 3 * (1 + 2 * lam) / (1 + lam)

    @property
    def sweep_le_rad(self) -> float:
        # tan(L_le) = tan(L_c4) + (1-lam) c_r / (4 * semispan) * ... (standard conversion)
        return math.atan(math.tan(math.radians(self.sweep_c4_deg))
                         + 0.25 * (self.c_root - self.c_tip) / self.semispan)

    @property
    def x_le_mac(self) -> float:
        return self.x_le_root + self.y_mac * math.tan(self.sweep_le_rad)

    @property
    def x_ac(self) -> float:
        """Aerodynamic centre, quarter-MAC (subsonic)."""
        return self.x_le_mac + 0.25 * self.mac

    @property
    def t_c_mean(self) -> float:
        return 0.5 * (self.t_c_root + self.t_c_tip)

    def chord_at(self, eta):
        """Chord at fraction eta of the semispan."""
        return self.c_root * (1 - (1 - self.taper) * eta)

    def exposed_area(self, body_width: float) -> float:
        """Area outside a body of given width (wing passes through the fuselage)."""
        if self.vertical:
            return self.area
        eta0 = (body_width / 2) / self.semispan
        c0 = self.chord_at(eta0)
        return (c0 + self.c_tip) * (self.semispan - body_width / 2)

    def wetted_area(self, body_width: float = 0.0) -> float:
        """Torenbeek: S_wet = 2 S_exp (1 + 0.25 (t/c)_r (1 + tau*lam)/(1 + lam)), tau = (t/c)_t/(t/c)_r."""
        tau = self.t_c_tip / self.t_c_root
        k = 1 + 0.25 * self.t_c_root * (1 + tau * self.taper) / (1 + self.taper)
        return 2 * self.exposed_area(body_width) * k


@dataclass
class Fuselage:
    length: float
    width: float
    height: float
    cabin_width_internal: float = 1.07

    @property
    def d_equiv(self) -> float:
        return math.sqrt(self.width * self.height)

    @property
    def fineness(self) -> float:
        return self.length / self.d_equiv

    @property
    def wetted_area(self) -> float:
        """Torenbeek eq. F-? for a streamlined body: pi D L (1 - 2/f)^(2/3) (1 + 1/f^2)."""
        f = self.fineness
        return math.pi * self.d_equiv * self.length * (1 - 2 / f) ** (2 / 3) * (1 + 1 / f**2)

    @property
    def frontal_area(self) -> float:
        return math.pi / 4 * self.width * self.height


@dataclass
class LandingGear:
    layout: str = "tricycle"
    main_tyre_d: float = 0.38        # 5.00-5 tyre
    main_tyre_w: float = 0.13
    nose_tyre_d: float = 0.33        # 4.00-6 / 14x5
    nose_tyre_w: float = 0.11
    wheel_fairings: bool = True
    main_leg: str = "faired composite leaf"   # or "flat spring leg"
    main_leg_length: float = 0.75   # exposed leg length [m]
    main_leg_chord: float = 0.09    # frontal width of the leg seen by the flow [m]
    main_leg_thickness: float = 0.022
    nose_leg_faired: bool = True
    nose_leg_length: float = 0.55
    nose_leg_width: float = 0.06


@dataclass
class Flaps:
    kind: str = "single slotted"    # plain | split | single slotted | fowler
    span_fraction: float = 0.62     # flapped span / semispan, measured from root
    chord_fraction: float = 0.28
    deflection_landing_deg: float = 30.0
    deflection_takeoff_deg: float = 15.0


@dataclass
class Propeller:
    diameter: float = 1.75
    blades: int = 3
    constant_speed: bool = True
    chord_scale: float = 1.0       # blade chord relative to the MTV-21-A-class baseline
