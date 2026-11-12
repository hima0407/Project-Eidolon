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
    ws = M.W / ac.wing.area
    # negative side: stall line, then n- up to V_C, then linear to n-(V_D) (CS-23.333(b))
    n_dn = np.where(V <= v.VC, np.maximum(-q * 0.8 / ws, v.n_neg),
                    v.n_neg + (v.n_neg_vd - v.n_neg) * (V - v.VC) / (v.VD - v.VC))
    ax.plot(V * 3.6, n_up, color=style.EIDOLON, lw=2.4, label="manoeuvre envelope")
    ax.plot(V * 3.6, n_dn, color=style.EIDOLON, lw=2.4)
    ax.plot([v.VD * 3.6, v.VD * 3.6], [v.n_neg_vd, v.n_pos], color=style.EIDOLON, lw=2.4)
    # the angle of attack is hidden in the diagram: on the stall line the wing is at CL_max; along the
    # flat 4.4 g line the same lift needs less CL (less alpha) as speed rises, CL = n W / (q S)
    a_w = M.lift.cl_alpha_wing
    alpha_pts = {}
    for name, Vp in (("V_A", v.VA), ("V_C", v.VC), ("V_D", v.VD)):
        cl = v.n_pos * ws / (0.5 * isa.RHO0 * Vp**2)
        alpha_pts[name] = {"CL": cl, "alpha_above_zero_lift_deg": float(np.degrees(cl / a_w))}
        ax.plot(Vp * 3.6, v.n_pos, "o", ms=6, color=style.EIDOLON, mec="white")
        right = name == "V_C"
        ax.text(Vp * 3.6 + (4 if right else -4), v.n_pos - 0.55, f"CL {cl:.2f}\nα {np.degrees(cl / a_w):.0f}°",
                ha="left" if right else "right", fontsize=8.5, color=style.INK2)
    for sgn in (1, -1):
        ax.plot([0, v.VC * 3.6, v.VD * 3.6], [1, 1 + sgn * v.gust_c, 1 + sgn * v.gust_d], color=style.HANSA, ls="--", lw=1.4,
                label="gust lines (15.24 / 7.62 m/s)" if sgn == 1 else None)
    for name, val, ha, dx in (("V_S1", v.VS1, "center", 0), ("V_A", v.VA, "right", -3), ("V_C", v.VC, "left", 3), ("V_D", v.VD, "center", 0)):
        ax.axvline(val * 3.6, color=style.GRID, lw=1)
        ax.text(val * 3.6 + dx, v.n_pos + 0.25, f"{name}\n{val*3.6:.0f}", ha=ha, fontsize=8.5, color=style.INK2)
    ax.axhline(0, color=style.INK2, lw=0.8)
    ax.set_ylim(-2.6, 5.5); ax.set_xlim(0, v.VD * 3.6 * 1.05)
    ax.set_xlabel("Equivalent airspeed [km/h]"); ax.set_ylabel("Load factor n")
    ax.set_title(f"V-n diagram, MTOW {ac.mtow:.0f} kg: limit +{v.n_pos} / {v.n_neg:.2f} g (ultimate x1.5)")
    ax.legend(fontsize=8.5, loc="lower left")
    style.note(fig, "α = angle of attack above zero lift needed for 4.4 g at that speed: the diagram's left edge is the stall (CL_max); "
               "\nthe flat top needs less α as speed rises. Negative limit -1.76 g up to V_C, then linear to -1.0 g at V_D (utility). "
               f"\nGust (K_g = {v.kg:.3f}) at V_C: n = {1 + v.gust_c:.2f} / {1 - v.gust_c:.2f}. "
               f"The negative gust exceeds -1.76 g; the spar sized for +6.6 g carries it reversed at {1.5 * (v.gust_c - 1) / 6.6:.0%} of its stress.")
    style.save(fig, OUT / "vn_diagram.png")
    write_json(OUT / "vn.json", {**{k: (val * 3.6 if k.startswith("V") else val) for k, val in vars(v).items()},
                                 "points_on_4g4_line": alpha_pts})


if __name__ == "__main__":
    main()
