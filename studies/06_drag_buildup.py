"""Study 06 - Where the drag goes: Hansa-NG -> Eidolon waterfall.

Both aircraft use the identical component build-up (Raymer 12.5) and the identical additive
'unmodelled' increment fitted on Hansa-NG, so every bar in the waterfall is a design difference,
not a modelling difference. Assumption-driven bars are labelled.
"""
from _common import ROOT, style, write_json
import numpy as np
import matplotlib.pyplot as plt

from eidolon.design import eidolon_v1, hansa_closed

OUT = style.out("06_drag")


def main():
    h, e = hansa_closed().model, eidolon_v1().model
    # reference both breakdowns to the same area so the bars are comparable drag areas (CD*S, m^2)
    Dh = {k: v * h.ac.wing.area for k, v in h.drag.items.items()}
    De = {k: v * e.ac.wing.area for k, v in e.drag.items.items()}
    keys = list(Dh.keys())
    deltas = [(k, De.get(k, 0) - Dh[k]) for k in keys]
    small = sum(d for k, d in deltas if abs(d) < 0.002)
    deltas = [d for d in deltas if abs(d[1]) >= 0.002] + [("Tails", small)]
    tot_h, tot_e = sum(Dh.values()), sum(De.values())
    write_json(OUT / "drag_areas_m2.json", {"Hansa-NG": Dh, "Eidolon": De,
                                             "CD0": {"Hansa-NG": h.polar.cd0, "Eidolon": e.polar.cd0},
                                             "total_drag_area_m2": {"Hansa-NG": tot_h, "Eidolon": tot_e}})
    why = {"Landing gear": "Landing gear\n(faired legs)", "Wing": "Wing\n(laminar)", "Fuselage": "Fuselage\n(7.1 m body)",
           "Leakage & protuberances": "Leakage &\nprotuberances", "Tails": "Tails",
           "Unmodelled (fitted on Hansa-NG)": "Unmodelled\n(same ΔCD0)"}

    fig, ax = plt.subplots(figsize=(10, 4.8))
    x = 0
    ax.bar(x, tot_h * 1e4 / 1e4, color=style.HANSA, width=0.6)
    ax.text(x, tot_h + 0.01, f"Hansa-NG\n{tot_h:.3f} m²", ha="center", va="bottom", fontsize=9)
    run = tot_h
    labels = ["Hansa-NG"]
    for k, d in sorted(deltas, key=lambda t: t[1]):
        x += 1
        col = style.GOOD if d < 0 else style.BAD
        ax.bar(x, d, bottom=run, color=col, width=0.6)
        ax.text(x, max(run, run + d) + 0.006, f"{d:+.3f}", ha="center", va="bottom", fontsize=8.5, color=style.INK2)
        run += d
        labels.append(why.get(k, k))
    x += 1
    ax.bar(x, tot_e, color=style.EIDOLON, width=0.6)
    ax.text(x, tot_e + 0.01, f"Eidolon\n{tot_e:.3f} m²", ha="center", va="bottom", fontsize=9)
    labels.append("Eidolon v1")
    ax.set_xticks(range(len(labels)), labels, fontsize=8.5)
    ax.set_ylabel("Parasite drag area  CD0·S  [m²]")
    ax.set_ylim(0, tot_h * 1.25)
    ax.grid(axis="x", visible=False)
    ax.set_title(f"Parasite drag area: {100*(tot_e/tot_h-1):+.0f} % vs Hansa-NG")
    style.note(fig, "Raymer component build-up; same fitted unmodelled increment on both (cancels). "
               "Hansa-NG gear/airfoil details are not published: generic assumptions, see docs/DESIGN_DECISIONS.md (D5).")
    style.save(fig, OUT / "drag_waterfall.png")

    # pie-free breakdown of Eidolon: horizontal bars
    fig, ax = plt.subplots(figsize=(7.5, 3.8))
    items = sorted(e.drag.items.items(), key=lambda t: t[1])
    ax.barh([k for k, _ in items], [v * 1e4 for _, v in items], color=style.EIDOLON, height=0.55)
    for i, (k, v) in enumerate(items):
        ax.text(v * 1e4 + 1, i, f"{v*1e4:.0f}", va="center", fontsize=8.5, color=style.INK2)
    ax.set_xlabel("drag counts (1 count = 0.0001 CD0)")
    ax.set_title(f"Eidolon CD0 = {e.polar.cd0:.4f} by component")
    ax.grid(axis="y", visible=False)
    style.note(fig, "Referenced to Eidolon wing area. 'Unmodelled' is the Hansa-NG-fitted increment (cooling inlets, gaps, steps, antennas...).")
    style.save(fig, OUT / "eidolon_cd0_breakdown.png")
    print(f"  CD0 Hansa {h.polar.cd0:.4f}  Eidolon {e.polar.cd0:.4f};  drag area {tot_h:.3f} -> {tot_e:.3f} m2")


if __name__ == "__main__":
    main()
