"""Study 04 - Finite wing: span loading, stall progression, and a cross-check against XFLR5.

Checks
 * Lifting-line (Glauert) code vs the team's XFLR5 VLM2 run of the 11 m / 14.15 m^2 wing (no twist
   in that run) - lift-curve slope and zero-lift angle.
 * Effect of the -2 deg washout chosen by the team: where the wing stalls first.
 * Textbook check: a rectangular AR 8 wing must give span efficiency ~0.93-0.95 (Anderson fig. 5.20).
"""
from _common import ROOT, style, write_json
import copy
import numpy as np
import matplotlib.pyplot as plt

from eidolon.aircraft import eidolon
from eidolon.design import BASELINE
from eidolon.geometry import Surface
from eidolon.lifting_line import LiftingLine

OUT = style.out("04_wing")


def read_vlm(path):
    rows = []
    for line in path.read_text().splitlines():
        p = [x.strip() for x in line.split(",")]
        try:
            rows.append([float(v) for v in p[:6]])
        except ValueError:
            pass
    return np.array(rows)


def main():
    res = {}
    # ---------------- cross-check with XFLR5 (untwisted 11 m wing, as run on 27 Oct)
    w_x = eidolon("912iSc", 14.152, 11.0).wing
    w_x.twist_tip_deg = 0.0
    ll_x = LiftingLine(w_x, a0_per_rad=6.30, alpha0_deg=-3.04)
    vlm = read_vlm(ROOT / "results" / "aerodynamics" / "naca63415" / "polar3d.csv")
    a_v, cl_v, cdi_v = vlm[:, 0], vlm[:, 2], vlm[:, 3]
    cl_ll = np.array([ll_x.solve(a).CL for a in a_v])
    cdi_ll = np.array([ll_x.solve(a).CDi for a in a_v])
    slope_v = np.polyfit(a_v, cl_v, 1)[0]; slope_l = np.polyfit(a_v, cl_ll, 1)[0]
    res["xflr5_check"] = {"cl_alpha_per_deg_xflr5_vlm2": slope_v, "cl_alpha_per_deg_llt": slope_l,
                          "difference_pct": 100 * (slope_l - slope_v) / slope_v,
                          "alpha0_xflr5": float(-np.polyfit(a_v, cl_v, 1)[1] / slope_v),
                          "alpha0_llt": float(-np.polyfit(a_v, cl_ll, 1)[1] / slope_l)}

    fig, axs = plt.subplots(1, 2, figsize=(11, 4))
    axs[0].plot(a_v, cl_v, "o", color=style.HANSA, ms=6, label="XFLR5 VLM2 (team run, 27 Oct)")
    axs[0].plot(a_v, cl_ll, color=style.EIDOLON, label="Lifting-line, this code")
    axs[0].set_xlabel("alpha [deg]"); axs[0].set_ylabel("CL"); axs[0].set_title("Lift curve: two independent methods")
    axs[0].legend()
    axs[1].plot(cl_v, cdi_v * 1e4, "o", color=style.HANSA, ms=6, label="XFLR5 VLM2")
    axs[1].plot(cl_ll, cdi_ll * 1e4, color=style.EIDOLON, label="Lifting-line")
    axs[1].set_xlabel("CL"); axs[1].set_ylabel("CDi [counts]"); axs[1].set_title("Induced drag")
    axs[1].legend()
    style.note(fig, f"Lift slope: XFLR5 {slope_v:.4f}/deg vs LLT {slope_l:.4f}/deg "
               f"({res['xflr5_check']['difference_pct']:+.1f} %). Untwisted 11.0 m x 14.15 m2 wing, NACA 63-415.")
    style.save(fig, OUT / "llt_vs_xflr5.png")

    # ---------------- textbook check
    rect = Surface("rect", 10.0, 8.0, 1.0, 0.12, 0.12)
    res["rectangular_AR8_e_span"] = LiftingLine(rect).solve(5).e_span

    # ---------------- Eidolon v1 wing: washout and stall pattern
    ac = eidolon(**BASELINE)
    clmax_r, clmax_t = ac.cl_max_2d_clean, ac.cl_max_2d_clean - 0.08
    fig, ax = plt.subplots(figsize=(9, 4.2))
    for tw, col, lab in ((0.0, style.HANSA, "no twist"), (-2.0, style.EIDOLON, "-2 deg washout (chosen)"),
                         (-4.0, style.SERIES[2], "-4 deg washout")):
        w = copy.deepcopy(ac.wing); w.twist_tip_deg = tw
        ll = LiftingLine(w)
        CLmax, a_st, eta_st = ll.stall(clmax_r, clmax_t)
        r = ll.solve(a_st)
        eta = np.concatenate([r.eta, [1.0]]); cl = np.concatenate([r.cl_local, [0.0]])
        ax.plot(eta, cl, color=col, label=f"{lab}: first stall at {eta_st:.0%} semispan, CLmax {CLmax:.2f}, "
                                          f"e = {ll.solve(2).e_span:.3f}")
        res[f"twist_{tw:+.0f}"] = {"CLmax_critical_section": CLmax, "alpha_stall": a_st,
                                   "eta_first_stall": eta_st, "e_span_cruise": ll.solve(2).e_span}
    e = np.linspace(0, 1, 50)
    ax.plot(e, clmax_r + (clmax_t - clmax_r) * e, color=style.INK2, lw=1.2, ls="--", label="local section clmax")
    ail = ac.flaps.span_fraction
    ax.axvspan(ail, 0.97, color=style.GRID, alpha=0.5, lw=0)
    ax.text((ail + 0.97) / 2, 0.25, "aileron", ha="center", color=style.INK2, fontsize=9)
    ax.set_xlabel("spanwise station  2y/b"); ax.set_ylabel("local cl at wing stall")
    ax.set_ylim(0, 1.8)
    ax.set_title("Stall starts inboard, so the ailerons keep working")
    ax.legend(fontsize=8.2, loc="lower left")
    style.note(fig, "Critical-section method on the lifting-line solution. Section clmax 1.50 root / 1.42 tip [A].")
    style.save(fig, OUT / "stall_progression.png")

    # ---------------- cool factor: spin-resistant drooped outboard leading edge ('cuff', NASA Langley
    # stall/spin research on light aircraft, 1970s-80s; later used on the Cirrus SR20/22).
    # Model: outboard of 58 % semispan the drooped LE raises section clmax by 0.30 [A]; the cuff
    # discontinuity's vortex acts as a fence. Metric: the share of the aileron span that is still
    # unstalled when the wing is pulled DEEPER than its first stall (what keeps roll control and resists
    # autorotation, i.e. the start of a spin).
    def aileron_unstalled(wing, d_clmax, d_alpha):
        ll = LiftingLine(wing)
        clmax = clmax_r + (clmax_t - clmax_r) * ll.eta + np.where(ll.eta >= 0.58, d_clmax, 0.0)
        a0 = None
        for a in np.arange(0, 25, 0.05):
            if (ll.solve(a).cl_local / clmax).max() >= 1:
                a0 = a; break
        r = ll.solve(a0 + d_alpha)
        ail = (ll.eta >= ac.flaps.span_fraction) & (ll.eta <= 0.97)
        return float(np.mean(r.cl_local[ail] < clmax[ail])), a0
    cuff = {}
    d_alphas = np.arange(0, 8.1, 1.0)
    fig, ax = plt.subplots(figsize=(8, 4))
    for d_cl, col, lab in ((0.0, style.HANSA, "-2 deg washout only"), (0.30, style.EIDOLON, "-2 deg washout + drooped outboard LE")):
        vals = [aileron_unstalled(ac.wing, d_cl, da)[0] for da in d_alphas]
        cuff[lab] = dict(zip([float(x) for x in d_alphas], vals))
        ax.plot(d_alphas, np.array(vals) * 100, color=col, marker="o", ms=5, label=lab)
    ax.set_xlabel("Angle of attack beyond the first stall [deg]"); ax.set_ylabel("Aileron span still unstalled [%]")
    ax.set_ylim(-5, 105); ax.legend(fontsize=8.5)
    ax.set_title("Drooped outboard leading edge keeps the ailerons flying")
    style.note(fig, "Lifting-line critical-section model; cuff = +0.30 section clmax outboard of 58 % semispan [A], cruise drag +3 counts [A]. "
               "Ref: NASA Langley stall/spin research (outboard leading-edge droop).")
    style.save(fig, OUT / "leading_edge_cuff.png")
    res["leading_edge_cuff"] = {"aileron_unstalled_fraction_vs_dalpha": cuff, "assumed_cd0_penalty": 0.0003,
                                "assumed_dclmax_outboard": 0.30}
    write_json(OUT / "wing_summary.json", res)
    print(res["xflr5_check"], res["rectangular_AR8_e_span"])


if __name__ == "__main__":
    main()
