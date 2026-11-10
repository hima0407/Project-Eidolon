"""Prandtl lifting-line theory solved with Glauert's Fourier-series method.

Gamma(theta) = 2 b V sum A_n sin(n theta),  y = -(b/2) cos(theta)
Collocation of the monoplane equation at N stations:
    sum_n A_n sin(n theta) (n mu + sin theta) = mu (alpha - alpha0) sin theta,
    mu = c(theta) a0 / (4 b)
Results: CL = pi AR A1,  CDi = pi AR sum n A_n^2,  e_span = 1/(1 + delta),
         delta = sum_{n>1} n (A_n/A1)^2.
Valid for straight, moderate/high aspect-ratio wings in attached flow
(Anderson, Fundamentals of Aerodynamics, ch. 5).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .geometry import Surface


@dataclass
class LLTResult:
    alpha_deg: float
    CL: float
    CDi: float
    e_span: float
    eta: np.ndarray      # spanwise station 0 (root) .. 1 (tip)
    cl_local: np.ndarray
    c_local: np.ndarray


class LiftingLine:
    def __init__(self, wing: Surface, a0_per_rad: float = 6.30, alpha0_deg: float = -3.0,
                 n_terms: int = 40):
        self.wing = wing
        self.N = n_terms
        # odd terms only (symmetric loading); collocation on one half (0, pi/2]
        self.n = np.arange(1, 2 * n_terms, 2)
        self.theta = np.linspace(np.pi / 2, 0.0, n_terms + 1)[:-1]  # root .. near tip
        self.eta = np.abs(np.cos(self.theta))
        self.c = wing.chord_at(self.eta)
        self.a0 = a0_per_rad
        self.alpha0 = np.deg2rad(alpha0_deg)
        b = wing.span
        mu = self.c * a0_per_rad / (4 * b)
        st = np.sin(self.theta)
        sn = np.sin(np.outer(self.theta, self.n))
        self.M = sn * (self.n[None, :] * mu[:, None] + st[:, None])
        self.mu, self.st = mu, st

    def twist(self, eta):
        return np.deg2rad(self.wing.twist_tip_deg) * eta

    def solve(self, alpha_deg: float) -> LLTResult:
        w = self.wing
        alpha = np.deg2rad(alpha_deg) + self.twist(self.eta)
        rhs = self.mu * (alpha - self.alpha0) * self.st
        A = np.linalg.solve(self.M, rhs)
        AR = w.aspect_ratio
        CL = np.pi * AR * A[0]
        CDi = np.pi * AR * np.sum(self.n * A**2)
        delta = np.sum(self.n[1:] * (A[1:] / A[0])**2) if abs(A[0]) > 1e-12 else 0.0
        gamma_hat = 2 * w.span * (np.sin(np.outer(self.theta, self.n)) @ A)   # Gamma / V
        cl_local = 2 * gamma_hat / self.c
        return LLTResult(alpha_deg, CL, CDi, 1 / (1 + delta), self.eta, cl_local, self.c)

    def cl_alpha_per_rad(self) -> float:
        return (self.solve(4.0).CL - self.solve(0.0).CL) / np.deg2rad(4.0)

    def stall(self, clmax_root: float, clmax_tip: float):
        """Critical-section estimate: wing CLmax when the first station reaches its clmax.

        Returns (CLmax, alpha_stall_deg, eta_first_stall). Conservative by ~5-10 % for
        moderately tapered wings, which is why Raymer's 0.9*clmax rule is reported alongside.
        """
        clmax = clmax_root + (clmax_tip - clmax_root) * self.eta
        for a in np.arange(0.0, 25.0, 0.05):
            r = self.solve(a)
            ratio = r.cl_local / clmax
            if ratio.max() >= 1.0:
                return r.CL, a, float(self.eta[int(np.argmax(ratio))])
        return np.nan, np.nan, np.nan
