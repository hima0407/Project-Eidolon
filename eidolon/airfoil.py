"""Airfoil coordinates, section properties and XFLR5 polar parsing."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
AIRFOIL_DIR = ROOT / "xflr5" / "airfoils"


def load_dat(name_or_path) -> np.ndarray:
    """Load a Selig- or Lednicer-format .dat file. Returns (N,2) array, TE->upper->LE->lower->TE."""
    p = Path(name_or_path)
    if not p.exists():
        p = AIRFOIL_DIR / f"{name_or_path}.dat"
    rows = []
    for line in p.read_text(errors="ignore").splitlines():
        parts = line.replace(",", " ").split()
        if len(parts) < 2:
            continue
        try:
            x, y = float(parts[0]), float(parts[1])
        except ValueError:
            continue
        rows.append((x, y))
    xy = np.array(rows)
    if xy[0, 0] > 1.5:          # Lednicer header line with point counts
        nu, nl = int(xy[0, 0]), int(xy[0, 1])
        up, lo = xy[1:1 + nu], xy[1 + nu:1 + nu + nl]
        xy = np.vstack([up[::-1], lo[1:]])
    xy[:, 0] = (xy[:, 0] - xy[:, 0].min()) / (xy[:, 0].max() - xy[:, 0].min())
    return xy


def naca4(code: str, n: int = 81) -> np.ndarray:
    """Analytic NACA 4-digit section (closed trailing edge), Selig ordering."""
    m, p, t = int(code[0]) / 100, int(code[1]) / 10, int(code[2:]) / 100
    beta = np.linspace(0, np.pi, n)
    x = 0.5 * (1 - np.cos(beta))
    yt = 5 * t * (0.2969 * np.sqrt(x) - 0.1260 * x - 0.3516 * x**2 + 0.2843 * x**3 - 0.1036 * x**4)
    if m == 0:
        yc = np.zeros_like(x); dyc = np.zeros_like(x)
    else:
        yc = np.where(x < p, m / p**2 * (2 * p * x - x**2), m / (1 - p)**2 * ((1 - 2 * p) + 2 * p * x - x**2))
        dyc = np.where(x < p, 2 * m / p**2 * (p - x), 2 * m / (1 - p)**2 * (p - x))
    th = np.arctan(dyc)
    xu, yu = x - yt * np.sin(th), yc + yt * np.cos(th)
    xl, yl = x + yt * np.sin(th), yc - yt * np.cos(th)
    return np.vstack([np.column_stack([xu[::-1], yu[::-1]]), np.column_stack([xl[1:], yl[1:]])])


def split_surfaces(xy: np.ndarray):
    """Return (x, y_upper, y_lower) on a common cosine-spaced x grid."""
    i_le = int(np.argmin(xy[:, 0]))
    up = xy[:i_le + 1][::-1]
    lo = xy[i_le:]
    xg = 0.5 * (1 - np.cos(np.linspace(0, np.pi, 201)))
    yu = np.interp(xg, up[:, 0], up[:, 1])
    yl = np.interp(xg, lo[:, 0], lo[:, 1])
    if yu.mean() < yl.mean():
        yu, yl = yl, yu
    return xg, yu, yl


@dataclass
class SectionProps:
    t_c: float            # max thickness / chord
    x_t: float            # chordwise position of max thickness
    area_total: float     # section area / c^2
    area_box: float       # area between front and rear spar / c^2 (fuel bay)


def section_properties(xy: np.ndarray, front_spar=0.15, rear_spar=0.65) -> SectionProps:
    x, yu, yl = split_surfaces(xy)
    t = yu - yl
    i = int(np.argmax(t))
    m = (x >= front_spar) & (x <= rear_spar)
    return SectionProps(float(t[i]), float(x[i]), float(np.trapezoid(t, x)), float(np.trapezoid(t[m], x[m])))


@dataclass
class Polar2D:
    name: str
    re: float
    alpha: np.ndarray
    cl: np.ndarray
    cd: np.ndarray
    cm: np.ndarray
    xtr_top: np.ndarray
    xtr_bot: np.ndarray

    @property
    def cl_alpha_per_rad(self) -> float:
        m = (self.alpha > -2) & (self.alpha < 4)
        return float(np.polyfit(np.deg2rad(self.alpha[m]), self.cl[m], 1)[0])

    @property
    def alpha0_deg(self) -> float:
        m = (self.alpha > -4) & (self.alpha < 4)
        k, b = np.polyfit(self.alpha[m], self.cl[m], 1)
        return float(-b / k)

    @property
    def cm0(self) -> float:
        return float(np.interp(self.alpha0_deg, self.alpha, self.cm))

    def cd_at_cl(self, cl):
        m = self.alpha < self.alpha[np.argmax(self.cl)]
        return np.interp(cl, self.cl[m], self.cd[m])


def read_xflr5_polar(path) -> Polar2D:
    """Parse an XFLR5/XFOIL text polar (the format exported by Polars -> Export)."""
    text = Path(path).read_text(errors="ignore").splitlines()
    name, re = Path(path).stem, np.nan
    data = []
    for line in text:
        if "Calculated polar for" in line:
            name = line.split(":", 1)[1].strip()
        if "Re =" in line:
            seg = line.split("Re =")[1].split("Ncrit")[0].replace(" ", "")
            re = float(seg.replace("e", "e")) if "e" in seg else float(seg)
        parts = line.split()
        if len(parts) >= 7:
            try:
                data.append([float(v) for v in parts[:7]])
            except ValueError:
                pass
    d = np.array(data)
    return Polar2D(name, re, d[:, 0], d[:, 1], d[:, 2], d[:, 4], d[:, 5], d[:, 6])
