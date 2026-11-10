"""One plotting style for every figure in the repository.

Colours are a validated categorical palette (fixed order, never cycled); identity
follows the entity: Eidolon is always blue, Hansa-NG always orange.
"""
from __future__ import annotations

import logging
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#8a8984"
GRID = "#e6e5e0"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
EIDOLON = SERIES[0]
HANSA = SERIES[1]
GOOD = "#1baf7a"
BAD = "#e34948"
ENGINE_COLORS = {"912ULS": SERIES[3], "912iSc": SERIES[0], "914": SERIES[4], "915iS": SERIES[2], "UL520iS": SERIES[6]}


def apply():
    plt.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "font.family": ["Inter", "Helvetica Neue", "Arial", "DejaVu Sans"],
        "font.size": 10.5, "axes.titlesize": 12.5, "axes.titleweight": "semibold",
        "axes.titlelocation": "left", "axes.titlepad": 10,
        "axes.labelcolor": INK2, "axes.edgecolor": GRID, "axes.linewidth": 0.8,
        "xtick.color": INK2, "ytick.color": INK2, "xtick.major.size": 0, "ytick.major.size": 0,
        "xtick.major.pad": 6, "ytick.major.pad": 6,
        "axes.grid": True, "axes.axisbelow": True, "grid.color": GRID, "grid.linewidth": 0.7,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.spines.left": False, "axes.spines.bottom": True,
        "lines.linewidth": 2.0, "lines.solid_capstyle": "round",
        "legend.frameon": False, "legend.fontsize": 9.5,
        "text.color": INK, "axes.prop_cycle": matplotlib.cycler(color=SERIES),
        "savefig.dpi": 200, "savefig.bbox": "tight", "savefig.pad_inches": 0.25,
    })


def out(study: str) -> Path:
    p = RESULTS / study
    p.mkdir(parents=True, exist_ok=True)
    return p


def note(fig, text: str):
    """Small provenance footer on every figure."""
    fig.text(0.01, -0.02, text, fontsize=8, color=MUTED, ha="left", va="top")


def save(fig, path: Path):
    fig.savefig(path)
    plt.close(fig)
    print(f"  wrote {path.relative_to(ROOT)}")


apply()
