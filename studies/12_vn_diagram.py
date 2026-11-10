"""Study 12 - Flight envelope (V-n) to CS-23 utility category (+4.4 / -1.76 g, spin training)."""
from _common import ROOT, style, write_json
import numpy as np
import matplotlib.pyplot as plt

from eidolon.design import eidolon_v1
from eidolon.loads import vn
from eidolon import atmosphere as isa

OUT = style.out("12_vn")


def main():
    c = eidolon_v1(); M = c.model; ac = M.ac
    v = vn(M.W, ac.wing.area, ac.wing.mac, M.lift.cl_alpha_wing, M.polar.cl_max_clean,
           VC_cruise=M.plane.v_max(M.W, 0.0) * 0.95)
    fig, ax = plt.subplots(figsize=(9, 5))
    V = np.linspace(0, v.VD, 300)
    q = 0.5 * isa.RHO0 * V**2
    n_up = np.minimum(q * M.polar.cl_max_clean / (M.W / ac.wing.area), v.n_pos)
    n_dn = np.maximum(-q * 0.8 / (M.W / ac.wing.area), v.n_neg)
    ax.plot(V * 3.6, n_up, color=style.EIDOLON, lw=2.4, label="manoeuvre envelope")
    ax.plot(V * 3.6, n_dn, color=style.EIDOLON, lw=2.4)
    ax.plot([v.VD * 3.6, v.VD * 3.6], [0, v.n_pos], color=style.EIDOLON, lw=2.4)
    for sgn in (1, -1):
        ax.plot([0, v.VC * 3.6, v.VD * 3.6], [1, 1 + sgn * v.gust_c, 1 + sgn * v.gust_d], color=style.HANSA, ls="--", lw=1.4,
                label="gust lines (15.24 / 7.62 m/s)" if sgn == 1 else None)
    for name, val in (("V_S1", v.VS1), ("V_A", v.VA), ("V_C", v.VC), ("V_D", v.VD)):
        ax.axvline(val * 3.6, color=style.GRID, lw=1)
        ax.text(val * 3.6, v.n_pos + 0.25, f"{name}\n{val*3.6:.0f}", ha="center", fontsize=8.5, color=style.INK2)
    ax.axhline(0, color=style.INK2, lw=0.8)
    ax.set_ylim(-2.6, 5.5); ax.set_xlim(0, v.VD * 3.6 * 1.05)
    ax.set_xlabel("Equivalent airspeed [km/h]"); ax.set_ylabel("Load factor n")
    ax.set_title(f"V-n diagram, MTOW {ac.mtow:.0f} kg: limit +{v.n_pos} / {v.n_neg:.2f} g (ultimate x1.5)")
    ax.legend(fontsize=8.5, loc="lower left")
    style.note(fig, f"CS-23.333-341. Gust alleviation K_g = {v.kg:.3f}. Manoeuvre governs above the gust lines at all speeds" if max(1 + v.gust_c, 1 + v.gust_d) < v.n_pos else "Gust exceeds manoeuvre load somewhere: check.")
    style.save(fig, OUT / "vn_diagram.png")
    write_json(OUT / "vn.json", {k: (val * 3.6 if k.startswith("V") else val) for k, val in vars(v).items()})


if __name__ == "__main__":
    main()
