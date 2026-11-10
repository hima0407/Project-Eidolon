"""Study 10 - Horizontal-tail sizing, wing position and CG envelope.

The tail is the smallest that satisfies all three longitudinal criteria (eidolon.stability):
static margin >= 12 % MAC at the aft CG, landing-flare control at the forward CG, and
nose-wheel lift-off below V_LOF at the forward CG (with propeller slipstream on the tail).
"""
from _common import ROOT, style, write_json
import numpy as np
import matplotlib.pyplot as plt

from eidolon.design import eidolon_v1

OUT = style.out("10_stability")


def main():
    c = eidolon_v1()
    ac, env, st, rows = c.model.ac, c.env, c.stab, c.tail_rows
    vh = np.array([r["vh"] for r in rows])
    fig, axs = plt.subplots(1, 2, figsize=(12.5, 4.6))
    ax = axs[0]
    ax.plot(vh, [r["h_np"] for r in rows], color=style.INK2, lw=1.4, label="neutral point")
    ax.fill_between(vh, [r["h_fwd"] for r in rows], [r["h_aft"] for r in rows], color=style.EIDOLON, alpha=0.25,
                    label="CG range (wing placed for 12 % SM at aft CG)")
    ax.plot(vh, [r["h_flare"] for r in rows], color=style.SERIES[2], label="forward limit: landing flare")
    ax.set_xlabel("Horizontal-tail volume coefficient  V_h"); ax.set_ylabel("x / MAC")
    ax.axvline(ac.vh, color=style.EIDOLON, ls="--", lw=1.2)
    ax.text(ac.vh + 0.015, -0.035, f"chosen V_h = {ac.vh:.2f}  (Raymer GA statistic 0.70)", fontsize=8.5)
    ax.set_title("Stability & control window vs tail size")
    ax.legend(fontsize=8.5, loc="upper left")
    ax2 = axs[1]
    ax2.plot(vh, [r["v_rot"] * 3.6 for r in rows], color=style.HANSA, label="nose-wheel lift-off speed (fwd CG)")
    ax2.plot(vh, [r["v_lof"] * 3.6 for r in rows], color=style.INK2, ls="--", label="lift-off speed 1.1 V_S,TO")
    ax2.set_ylim(0, 200)
    ax2.axvline(ac.vh, color=style.EIDOLON, ls="--", lw=1.2)
    ax2.set_xlabel("V_h"); ax2.set_ylabel("speed [km/h]")
    ax2.set_title("Take-off rotation sizes the tail")
    ax2.legend(fontsize=8.5)
    style.note(fig, "Rotation criterion includes propeller slipstream over the tail (momentum theory). eidolon/stability.py")
    style.save(fig, OUT / "tail_sizing.png")

    # ---- CG envelope (mass vs %MAC)
    fig, ax = plt.subplots(figsize=(7.5, 5))
    pts = list(env.cases.items())
    for i, (name, (m, x, h)) in enumerate(pts):
        ax.plot(100 * h, m, "o", ms=9, color=style.SERIES[i % 8], mec="white", label=name)
    ax.axvline(100 * (st.h_np - 0.05), color=style.BAD, lw=1.5, ls="--", label="5 % SM limit")
    ax.axvline(100 * st.h_np, color=style.INK2, lw=1.2, label=f"neutral point {100*st.h_np:.1f} % MAC")
    ax.axhline(ac.mtow, color=style.INK2, lw=0.8, ls=":")
    ax.set_xlabel("CG position [% MAC]"); ax.set_ylabel("Mass [kg]")
    ax.set_title(f"CG envelope: {100*env.h_fwd:.1f} - {100*env.h_aft:.1f} % MAC")
    ax.legend(fontsize=7.8, loc="lower left")
    style.note(fig, "Seats and fuel sit close to the CG, so loading moves the CG only ~6 % MAC.")
    style.save(fig, OUT / "cg_envelope.png")
    write_json(OUT / "stability_summary.json", {
        "vh": ac.vh, "vv": ac.vv, "htail_area_m2": ac.htail.area, "vtail_area_m2": ac.vtail.area,
        "tail_arm_m": ac.tail_arm_h, "wing_x_le_root_m": ac.wing.x_le_root, "x_main_gear_m": env.x_main_gear,
        "neutral_point_pct_mac": 100 * st.h_np, "cg_fwd_pct_mac": 100 * env.h_fwd, "cg_aft_pct_mac": 100 * env.h_aft,
        "static_margin_aft_pct": 100 * (st.h_np - env.h_aft), "static_margin_fwd_pct": 100 * (st.h_np - env.h_fwd),
        "deps_dalpha": st.deps_dalpha, "rotation_speed_kmh": c.rotation[0] * 3.6, "v_lof_kmh": c.rotation[1] * 3.6,
        "cases": {k: {"mass": v[0], "x_m": v[1], "pct_mac": 100 * v[2]} for k, v in env.cases.items()}})


if __name__ == "__main__":
    main()
