"""Study 03 - Why NACA 63-415 for the wing.

Evidence used:
 1. Geometry from the coordinate files in xflr5/airfoils/: thickness, its location, and the
    spar-box area that sets wing fuel volume and spar depth (bending stiffness ~ depth^2).
 2. XFLR5 (XFOIL) polars. If the team's matched batch (xflr5/polars/*.txt, Re 2-4.5 M) is
    present it is used; otherwise only the NACA 63-415 Re = 6 M polar already in the repo is plotted
    and the comparison is flagged as incomplete.
Criteria (see docs/DESIGN_DECISIONS.md, D2): cruise cd at CL 0.35, laminar extent, clmax,
|cm0| (trim drag), thickness (structure + fuel), gentle stall.
"""
from _common import ROOT, style, write_json, write_csv
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

from eidolon.airfoil import load_dat, section_properties, read_xflr5_polar

OUT = style.out("03_airfoil")
CANDIDATES = ["naca63415", "naca23012", "naca2412", "naca4412"]
LABEL = {"naca63415": "NACA 63-415", "naca23012": "NACA 23012", "naca2412": "NACA 2412",
         "naca4412": "NACA 4412", "n63412": "NACA 63-412 (tip)"}
COL = {"naca63415": style.EIDOLON, "naca23012": style.HANSA, "naca2412": style.SERIES[2],
       "naca4412": style.SERIES[3], "n63412": style.SERIES[6]}


def find_polars():
    out = {}
    for p in sorted((ROOT / "xflr5" / "polars").glob("*.txt")) if (ROOT / "xflr5" / "polars").exists() else []:
        try:
            pol = read_xflr5_polar(p)
        except Exception:
            continue
        key = next((k for k in CANDIDATES if k.replace("naca", "") in p.stem.replace("-", "").replace("_", "")), None)
        if key:
            out.setdefault(key, []).append(pol)
    base = ROOT / "xflr5" / "results" / "naca63415" / "polar2d.txt"
    if base.exists() and "naca63415" not in out:
        out["naca63415"] = [read_xflr5_polar(base)]
    return out


def main():
    # ---- geometry
    props = {}
    fig, ax = plt.subplots(figsize=(9, 3.2))
    for k in CANDIDATES + ["n63412"]:
        xy = load_dat(k)
        sp = section_properties(xy)
        props[k] = sp
        if k != "n63412":
            ax.plot(xy[:, 0], xy[:, 1], color=COL[k], lw=2.2 if k == "naca63415" else 1.4,
                    label=f"{LABEL[k]}  t/c {sp.t_c:.0%} at {sp.x_t:.0%}c")
    ax.axvspan(0.15, 0.65, color=style.GRID, alpha=0.4, lw=0)
    ax.text(0.40, -0.075, "spar box / fuel bay 15-65 % c", ha="center", fontsize=8.5, color=style.INK2)
    ax.set_aspect("equal"); ax.set_ylim(-0.09, 0.13); ax.set_xlim(-0.02, 1.02)
    ax.set_xlabel("x/c"); ax.set_ylabel("y/c")
    ax.legend(loc="upper right", ncol=2, fontsize=8.5)
    ax.set_title("Candidate sections at true scale")
    style.note(fig, "Coordinates: xflr5/airfoils/*.dat in this repository.")
    style.save(fig, OUT / "airfoil_shapes.png")

    rows = [(LABEL[k], p.t_c, p.x_t, p.area_box) for k, p in props.items()]
    write_csv(OUT / "section_properties.csv", ["section", "t_c", "x_tmax", "box_area_per_c2"], rows)

    # ---- polars
    polars = find_polars()
    complete = all(k in polars for k in CANDIDATES)
    fig, axs = plt.subplots(1, 3, figsize=(13, 4.2))
    summary = {}
    for k, pols in polars.items():
        for pol in pols:
            ls = "-" if pol.re >= 4e6 else ("--" if pol.re >= 2.5e6 else ":")
            lab = f"{LABEL[k]}  Re {pol.re/1e6:.1f} M"
            axs[0].plot(pol.cd * 1e4, pol.cl, ls, color=COL[k], label=lab)
            axs[1].plot(pol.alpha, pol.cl, ls, color=COL[k])
            axs[2].plot(pol.cl, 0.5 * (pol.xtr_top + pol.xtr_bot), ls, color=COL[k])
            summary[lab] = {"cd_at_cl_0.35_counts": float(pol.cd_at_cl(0.35) * 1e4),
                            "clmax_in_range": float(pol.cl.max()), "alpha0_deg": pol.alpha0_deg,
                            "cm0": pol.cm0, "cl_alpha_per_rad": pol.cl_alpha_per_rad}
    axs[0].axhspan(0.25, 0.45, color=style.EIDOLON, alpha=0.08, lw=0)
    axs[0].text(5, 0.47, "cruise CL band", fontsize=8.5, color=style.INK2)
    axs[0].set_xlabel("cd [counts, 1e-4]"); axs[0].set_ylabel("cl"); axs[0].set_title("Drag polar")
    axs[0].set_xlim(40, 200)
    axs[1].set_xlabel("alpha [deg]"); axs[1].set_ylabel("cl"); axs[1].set_title("Lift curve")
    axs[2].set_xlabel("cl"); axs[2].set_ylabel("mean transition x/c"); axs[2].set_title("Laminar extent")
    axs[2].set_ylim(0, 1)
    axs[0].legend(fontsize=8, loc="lower right")
    if not complete:
        fig.text(0.5, 1.03, "Incomplete: only the polars found in xflr5/polars/ and xflr5/results/ are shown - "
                 "run the matched XFLR5 batch (docs/HOW_TO_RUN_XFLR5.md)", ha="center", color=style.BAD, fontsize=9)
    style.note(fig, "XFOIL (via XFLR5 v6.62), free transition, Ncrit = 9, M = 0. Numerical results, not wind-tunnel data.")
    style.save(fig, OUT / "airfoil_polars.png")
    write_json(OUT / "airfoil_summary.json", {"geometry": {LABEL[k]: vars(p) for k, p in props.items()},
                                              "polars": summary, "matched_comparison_complete": complete})


if __name__ == "__main__":
    main()
