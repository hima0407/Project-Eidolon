"""Study 17 - Structural analysis of the closed design: wing loads, spar, stiffness, tail cone, margins.

Uses the same load-sized model as the mass estimate (eidolon/structures.py):
    lift shape from the lifting line, scaled to n_ult = 1.5 x 4.4 = 6.6, minus wing inertia (no fuel relief)
    V(y) = int_y^{b/2} (L' - n g m') dy,   M(y) = int_y^{b/2} V dy
    A_cap = M / (h_eff sigma_allow),       h_eff = 0.85 (t/c) c,  sigma_allow = 550 MPa (CFRP UD, design ult.)
    t_web = V / (h tau),  tau = 120 MPa,   minimum gauges: 40 mm2 cap, 0.8 mm web
Tip deflection at LIMIT load (ultimate / 1.5) from the caps alone: kappa = M / (E I), I = 2 A (h/2)^2,
E = 125 GPa [A]. Skins add stiffness, so this is conservative.
Tail cone: CS-23-style tail load (CL_h 1.0 at V_A, x1.5) on the arm from the HT a.c. to the cabin end,
carried by two glass sandwich face strips (0.7 mm x 250 mm) on a 0.55 m deep section, allowable 250 MPa.
Run for the first closure (glass skins) and the final aircraft (carbon skins, study 20).
"""
from _common import style, write_json
import math
import numpy as np
import matplotlib.pyplot as plt

from eidolon import atmosphere as isa
from eidolon import structures as st
from eidolon.design import eidolon_v1, eidolon_final

OUT = style.out("17_structures")
E_UD = 125e9   # [A] UD carbon/epoxy modulus


def analyse(c):
    ac = c.model.ac
    ws = st.wing_structure(ac)
    y, V, M, A, tw = ws.y, ws.shear, ws.moment, ws.cap_area, ws.web_t
    half = ac.wing.span / 2
    eta = y / half
    chord = ac.wing.chord_at(eta)
    tc = ac.wing.t_c_root + (ac.wing.t_c_tip - ac.wing.t_c_root) * eta
    h = 0.85 * tc * chord
    I = 2 * A * (h / 2) ** 2
    kappa = (M / 1.5) / (E_UD * I)
    slope = np.concatenate([[0], np.cumsum(0.5 * (kappa[1:] + kappa[:-1]) * np.diff(y))])
    defl = np.concatenate([[0], np.cumsum(0.5 * (slope[1:] + slope[:-1]) * np.diff(y))])
    VS1 = math.sqrt(2 * ac.wing_loading / (isa.RHO0 * 1.25))
    VA = VS1 * math.sqrt(ac.n_limit)
    tail_load = 1.5 * 0.5 * isa.RHO0 * VA**2 * ac.htail.area
    arm = ac.htail.x_ac - (ac.x_baggage + 0.45)
    M_cone = tail_load * arm
    sigma_face = M_cone / (0.5 * 0.55 * 2 * 0.0007 * 0.25)
    first_min_cap = float(y[np.argmax(A <= st.CAP_MIN * 1.0001)])
    caps = ws.masses["Wing spar caps (CFRP)"]
    return dict(
        root_shear_kN=V[0] / 1e3, root_moment_kNm=M[0] / 1e3, cap_force_kN=M[0] / h[0] / 1e3,
        root_spar_depth_mm=h[0] * 1e3, root_cap_area_mm2=A[0] * 1e6, root_web_mm=tw[0] * 1e3,
        cap_min_gauge_from_y_m=first_min_cap, web_min_gauge_span_fraction=float(np.mean(tw <= st.T_WEB_MIN * 1.0001)),
        tip_deflection_limit_mm=defl[-1] * 1e3, tip_deflection_pct_semispan=100 * defl[-1] / half,
        extra_cap_kg_for_6pct=caps * (100 * defl[-1] / half / 6.0 - 1),
        tail_load_ult_kN=tail_load / 1e3, V_A_kmh=VA * 3.6, cone_moment_kNm=M_cone / 1e3,
        cone_face_stress_MPa=sigma_face / 1e6, cone_margin=250e6 / sigma_face - 1,
        wing_items=dict(ws.masses), groups=c.model.mass.model.groups(), empty_kg=c.model.empty_kg,
        _y=y, _V=V / 1e3, _M=M / 1e3, _A=A * 1e6, _defl=defl * 1e3)


def main():
    res = {"first closure (glass skins)": analyse(eidolon_v1()), "final (carbon skins)": analyse(eidolon_final())}
    g = res["first closure (glass skins)"]
    y = g["_y"]
    fig, axs = plt.subplots(1, 4, figsize=(16, 4.1))
    panels = [("Shear force, ultimate [kN]", g["_V"], f"{g['root_shear_kN']:.1f} kN at root"),
              ("Bending moment, ultimate [kN·m]", g["_M"], f"{g['root_moment_kNm']:.1f} kN·m at root"),
              ("Spar-cap area, each cap [mm²]", g["_A"], f"{g['root_cap_area_mm2']:.0f} mm² at root\nminimum gauge outboard of {g['cap_min_gauge_from_y_m']:.1f} m"),
              ("Deflection at limit load [mm]", g["_defl"], f"{g['tip_deflection_limit_mm']:.0f} mm at the tip\n= {g['tip_deflection_pct_semispan']:.1f} % of semispan")]
    for i, (ax, (t, v, lab)) in enumerate(zip(axs, panels)):
        ax.plot(y, v, color=style.EIDOLON, lw=2)
        ax.fill_between(y, v, color=style.EIDOLON, alpha=0.10, lw=0)
        ax.set_title(t, fontsize=12.5); ax.set_xlabel("Distance from centreline [m]")
        ax.set_xlim(0, 5.9); ax.set_ylim(0, max(v) * 1.18)
        ax.text(0.97 if i < 3 else 0.04, 0.93, lab, transform=ax.transAxes, ha="right" if i < 3 else "left",
                va="top", fontsize=11, color=style.INK)
    fig.tight_layout(w_pad=2.5)
    style.note(fig, "6.6 g ultimate (1.5 × 4.4 g) at 750 kg, no fuel bending relief. Lift shape from our lifting-line solution. "
                    "CFRP caps at 550 MPa allowable; deflection uses E = 125 GPa [assumed]. studies/17_structural_analysis.py")
    style.save(fig, OUT / "wing_loads.png")

    label = {"Wing spar caps (CFRP)": "Spar caps (CFRP)", "Wing shear webs": "Shear webs",
             "Wing skins (sandwich)": "Skins (glass sandwich)", "Wing ribs": "Ribs", "Wing rear spar": "Rear spar",
             "Flaps + ailerons": "Flaps + ailerons", "Wing root fittings": "Root fittings",
             "Tank sealing": "Tank sealing", "Wing paint": "Paint"}
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(15, 5.0), gridspec_kw=dict(width_ratios=[1.05, 1]))
    wi = sorted(g["wing_items"].items(), key=lambda kv: kv[1], reverse=True)
    vals = [v for _, v in wi]; tot = sum(vals)
    a1.barh([label[k] for k, _ in wi], vals, height=0.55, color=style.EIDOLON); a1.invert_yaxis()
    for i, v in enumerate(vals):
        a1.text(v + 0.8, i, f"{v:.1f} kg ({100*v/tot:.0f} %)", va="center", fontsize=10.5, color=style.INK2)
    a1.set_title(f"v1 wing: {tot:.1f} kg, and where it goes"); a1.set_xlabel("kg")
    a1.grid(axis="y", visible=False); a1.set_xlim(0, max(vals) * 1.35)
    grp = ["Powerplant", "Fuselage", "Wing", "Systems & furnishings", "Landing gear", "Tail"]
    gv = [g["groups"][k] for k in grp]
    a2.barh(grp, gv, height=0.55, color=style.EIDOLON); a2.invert_yaxis()
    for i, v in enumerate(gv):
        a2.text(v + 1, i, f"{v:.1f} kg", va="center", fontsize=10.5, color=style.INK2)
    a2.set_title(f"Counted items: {sum(gv):.0f} kg  (+ {g['groups']['Class allowance']:.0f} kg class allowance = {g['empty_kg']:.0f} kg)")
    a2.set_xlabel("kg"); a2.grid(axis="y", visible=False); a2.set_xlim(0, max(gv) * 1.25)
    fig.tight_layout(w_pad=3)
    style.note(fig, "First closure (glass skins). Spar caps and webs sized for 6.6 g; skins, ribs and control surfaces by area; "
                    "catalogue items for systems. studies/17_structural_analysis.py")
    style.save(fig, OUT / "structure_mass.png")

    write_json(OUT / "structures.json", {k: {kk: vv for kk, vv in v.items() if not kk.startswith("_")} for k, v in res.items()})
    for k, v in res.items():
        print(k, {kk: round(float(vv), 2) for kk, vv in v.items() if not kk.startswith("_") and not isinstance(vv, dict)})


if __name__ == "__main__":
    main()
