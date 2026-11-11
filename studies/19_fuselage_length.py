"""Study 19 - Fuselage length trade: eight re-closed aircraft, body length 6.5-7.9 m.

Cabin and stations are fixed (the seats sit on the CG); only the tail cone changes. Each point is
re-closed: tails re-sized for 12 % static margin, landing flare and nose-wheel rotation, wing
re-positioned, mass and drag recomputed. Fuselage drag follows Torenbeek's wetted area and Raymer's
form factor, FF = 1 + 60/f^3 + f/400, f = L/D:  a shorter body has less skin but a bluffer shape and a
shorter tail arm (bigger tail); a longer one is the reverse plus more structure.
"""
from _common import style, write_json
import numpy as np
import matplotlib.pyplot as plt

from eidolon.aircraft import eidolon, place_tails
from eidolon.design import BASELINE, close
from eidolon.model import V_CRUISE, CRUISE_ALT

OUT = style.out("19_fuselage")
LENGTHS = [6.5, 6.7, 6.9, 7.1, 7.3, 7.5, 7.7, 7.9]


def evaluate(L):
    ac = eidolon(**BASELINE)
    ac.fuselage.length = L
    place_tails(ac, 0.65, 0.040)
    c = close(ac); M = c.model; P = M.plane; W = M.W
    return dict(length_m=L, fineness=M.ac.fuselage.fineness, wetted_m2=M.ac.fuselage.wetted_area,
                f100=P.fuel_per_100km(W, V_CRUISE, CRUISE_ALT)[0], range_km=P.range_km(W, M.fuel_kg, V_CRUISE, CRUISE_ALT)[0],
                empty_kg=M.empty_kg, ht_area_m2=M.ac.htail.area, cd0=M.polar.cd0,
                fuselage_drag_area_m2=M.drag.items["Fuselage"] * M.ac.wing.area)


def main():
    rows = [evaluate(L) for L in LENGTHS]
    L = np.array(LENGTHS)
    fig, axs = plt.subplots(1, 3, figsize=(16, 4.3))
    for ax, (key, t, fmt) in zip(axs, [("f100", "Fuel at 200 km/h [L/100 km]", "{:.3f}"), ("range_km", "Range, 2 crew + 10 kg [km]", "{:.0f}"),
                                      ("ht_area_m2", "Horizontal tail needed [m²]", "{:.2f}")]):
        y = np.array([r[key] for r in rows])
        ax.plot(L, y, color=style.EIDOLON, lw=2, marker="o", ms=8, mec=style.SURFACE, mew=2)
        ax.axvline(7.1, color=style.INK2, lw=1, ls=(0, (4, 3)))
        ax.annotate("7.10 m chosen: " + fmt.format(y[3]), (7.1, y[3]), xytext=(10, 12), textcoords="offset points", fontsize=11, color=style.INK)
        ax.set_title(t, fontsize=12.5); ax.set_xlabel("Fuselage body length [m]")
        pad = (y.max() - y.min()) * 0.25; ax.set_ylim(y.min() - pad, y.max() + pad)
    fig.tight_layout(w_pad=2.5)
    style.note(fig, "Each point is a re-closed aircraft: tail re-sized for 12 % static margin and rotation, wing re-positioned, mass and drag "
                    "recomputed. Cabin and stations fixed; only the tail cone changes. studies/19_fuselage_length.py")
    style.save(fig, OUT / "fuselage_trade.png")
    write_json(OUT / "fuselage_trade.json", {"rows": rows, "chosen_m": 7.10,
                                             "objective": "minimum fuel per 100 km at 200 km/h (as the wing carpet)"})
    for r in rows:
        print({k: round(float(v), 4) for k, v in r.items()})


if __name__ == "__main__":
    main()
