"""Study 01 - How heavy is Eidolon, and how sure are we?

Method (eidolon/structures.py):
  1. Bottom-up: every structural item is sized from its own load with Eidolon's own geometry and
     materials (CFRP spar caps from the 6.6 g bending moment, shear webs, sandwich skins by area,
     ribs, control surfaces, fittings, tank sealing, paint; tails from the tail load at V_A; fuselage
     shell by area; landing gear from the CS-23.473 energy), plus catalogue items for the engine,
     systems and furnishings.
  2. Class allowance: what every certified composite trainer carries that such a list misses.
     Measured as (published empty - bottom-up) on three certified 730-750 kg composite trainers:
     Hansa-NG, Aquila A210, Diamond DV20 Katana. Leave-one-out cross-validation gives the honest
     prediction error.
  3. Uncertainty: every item gets a 1-sigma spread by how it was obtained (data sheet 3 %, sized
     structure 10-12 %, areal estimates 15 %, allowances 20-30 %) and the allowance gets its
     leave-one-out scatter. 5,000 Monte-Carlo draws give the empty-mass distribution.
  4. Cross-check: Raymer's statistical equations, calibrated on Hansa-NG.
"""
from _common import ROOT, style, write_json, write_csv
import numpy as np
import matplotlib.pyplot as plt

from eidolon.aircraft import COMPARATORS, comparator, eidolon
from eidolon.design import BASELINE
from eidolon.structures import bottom_up, monte_carlo, wing_structure
from eidolon.weights import raymer_ga, calibrate_on
from eidolon.aircraft import hansa_ng

OUT = style.out("01_mass")
CERTIFIED = [n for n, v in COMPARATORS.items() if v[7] == "certified trainer"]


def main():
    rows, gaps = [], {}
    for n in COMPARATORS:
        ac = comparator(n)
        bu = bottom_up(ac).total
        pub = COMPARATORS[n][1]
        gaps[n] = pub - bu
        rows.append((n, COMPARATORS[n][7], pub, bu, pub - bu, COMPARATORS[n][8]))
    cert = np.array([gaps[n] for n in CERTIFIED])
    mean, sd = float(cert.mean()), float(cert.std(ddof=1))
    loo = {}
    for n in CERTIFIED:
        others = np.mean([gaps[m] for m in CERTIFIED if m != n])
        pred = COMPARATORS[n][1] - gaps[n] + others
        loo[n] = {"allowance_from_others_kg": float(others), "predicted_empty_kg": float(pred),
                  "published_empty_kg": COMPARATORS[n][1], "error_kg": float(pred - COMPARATORS[n][1]),
                  "error_pct": float(100 * (pred - COMPARATORS[n][1]) / COMPARATORS[n][1])}
    loo_rms = float(np.sqrt(np.mean([v["error_kg"] ** 2 for v in loo.values()])))
    write_json(OUT / "class_allowance.json", {"mean_kg": mean, "sd_kg": sd, "loo_rms_kg": loo_rms,
                                              "certified_trainers": CERTIFIED, "gaps_kg": gaps, "leave_one_out": loo})
    write_csv(OUT / "comparators.csv", ["aircraft", "category", "published_empty_kg", "bottom_up_kg", "gap_kg", "source"], rows)
    import eidolon.structures as st
    st.CLASS_ALLOWANCE_KG, st.CLASS_ALLOWANCE_SD = mean, loo_rms

    # ---------------- Eidolon: bottom-up breakdown + distribution
    from eidolon.design import eidolon_v1
    e_ac = eidolon_v1().model.ac          # the closed design (tail sized, wing positioned)
    mm = st.empty_mass_model(e_ac)
    draws = monte_carlo(mm, 5000)
    p5, p50, p95 = np.percentile(draws, [5, 50, 95])
    h_mm = st.empty_mass_model(hansa_ng())
    h_draws = monte_carlo(h_mm, 5000)
    rk = calibrate_on(hansa_ng(), 540.0)
    ray_e = raymer_ga(e_ac, calibration=rk).empty
    write_csv(OUT / "eidolon_mass_items.csv", ["item", "group", "mass_kg", "spread_1sigma", "basis"],
              [(i.name, i.group, i.mass, i.spread, i.basis) for i in mm.items])
    res = {"eidolon": {"nominal_kg": mm.total, "p05": p5, "p50": p50, "p95": p95, "groups": mm.groups()},
           "hansa_model": {"nominal_kg": h_mm.total, "published_kg": 540.0},
           "raymer_cross_check_eidolon_kg": ray_e, "class_allowance": {"mean": mean, "sd": sd, "loo_rms": loo_rms},
           "leave_one_out": loo}
    write_json(OUT / "mass_summary.json", res)

    # ---------------- figures
    fig, axs = plt.subplots(1, 2, figsize=(13, 4.8), gridspec_kw={"width_ratios": [1.1, 1]})
    ax = axs[0]
    names = [r[0] for r in rows]
    y = np.arange(len(rows))
    ax.barh(y, [r[3] for r in rows], color=style.EIDOLON, height=0.55, label="bottom-up (load-sized items)")
    ax.barh(y, [max(r[4], 0) for r in rows], left=[r[3] for r in rows], color=style.SERIES[3], height=0.55,
            label="gap = class allowance")
    ax.plot([r[2] for r in rows], y, "D", color=style.INK, ms=7, label="published empty mass")
    for yi, r in zip(y, rows):
        ax.text(max(r[2], r[3]) + 8, yi, f"{r[2]:.0f} kg  (gap {r[4]:+.0f})", va="center", fontsize=8.5, color=style.INK2)
    ax.set_yticks(y, [f"{r[0]}\n{r[1]}" for r in rows], fontsize=8.5); ax.invert_yaxis()
    ax.set_xlim(0, 700); ax.set_xlabel("Empty mass [kg]"); ax.grid(axis="y", visible=False)
    ax.set_title(f"Certified trainers carry {mean:.0f} ± {sd:.0f} kg the load-sized list misses")
    ax.legend(fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.13), ncol=3)
    ax = axs[1]
    bins = np.linspace(min(draws.min(), h_draws.min()), max(draws.max(), h_draws.max()), 50)
    ax.hist(h_draws, bins=bins, color=style.HANSA, alpha=0.55, label=f"Hansa-NG model (published 540 kg)")
    ax.hist(draws, bins=bins, color=style.EIDOLON, alpha=0.75, label="Eidolon v1")
    for v, ls in ((p5, ":"), (p50, "-"), (p95, ":")):
        ax.axvline(v, color=style.INK, ls=ls, lw=1.3)
    ax.axvline(540, color=style.HANSA, lw=1.5, ls="--")
    ax.text(0.98, 0.95, f"Eidolon P50 {p50:.0f} kg\n90 % in {p5:.0f}-{p95:.0f} kg", transform=ax.transAxes,
            ha="right", va="top", fontsize=9.5)
    ax.set_xlabel("Empty mass [kg]"); ax.set_ylabel("Monte-Carlo samples"); ax.legend(fontsize=8.5, loc="upper left")
    ax.set_title("Empty mass as a distribution, not a number")
    style.note(fig, f"Leave-one-out error of the method on the 3 certified trainers: RMS {loo_rms:.1f} kg. "
               f"Raymer cross-check for Eidolon: {ray_e:.0f} kg. Every item and its spread: results/01_mass/eidolon_mass_items.csv")
    style.save(fig, OUT / "mass_estimation.png")

    # breakdown bar by group
    fig, ax = plt.subplots(figsize=(8.5, 4))
    g = mm.groups()
    keys = sorted(g, key=lambda k: -g[k])
    ax.barh(range(len(keys)), [g[k] for k in keys], color=style.EIDOLON, height=0.55)
    for i, k in enumerate(keys):
        ax.text(g[k] + 2, i, f"{g[k]:.0f} kg", va="center", fontsize=9, color=style.INK2)
    ax.set_yticks(range(len(keys)), keys); ax.invert_yaxis(); ax.grid(axis="y", visible=False)
    ax.set_title(f"Eidolon v1 empty mass {mm.total:.0f} kg by group"); ax.set_xlim(0, max(g.values()) * 1.2)
    style.note(fig, "Wing, tail, fuselage and gear sized from their loads; powerplant from data sheets; systems from catalogue-class items.")
    style.save(fig, OUT / "eidolon_mass_breakdown.png")

    # wing mass vs span, both methods (this is what drives the wing-sizing optimum)
    spans = np.linspace(9.5, 12.5, 13)
    bu_w, ray_w = [], []
    for b in spans:
        a = eidolon("912iSc", BASELINE["wing_area"], b)
        bu_w.append(sum(wing_structure(a).masses.values()))
        ray_w.append(raymer_ga(a, calibration=rk).items["Wing"])
    fig, ax = plt.subplots(figsize=(7.5, 4))
    ax.plot(spans, bu_w, color=style.EIDOLON, marker="o", ms=5, label="bottom-up (sized spar + skins)")
    ax.plot(spans, ray_w, color=style.HANSA, marker="o", ms=5, label="Raymer statistics x calibration")
    ax.set_xlabel(f"Span [m] at S = {BASELINE['wing_area']} m²"); ax.set_ylabel("Wing mass [kg]")
    ax.set_title("Wing mass vs span: the two methods disagree on the slope"); ax.legend()
    style.note(fig, "Bottom-up: skins scale with area, only the spar caps grow with span. Raymer's AR^0.6 trend is much steeper.")
    style.save(fig, OUT / "wing_mass_vs_span.png")
    write_csv(OUT / "wing_mass_vs_span.csv", ["span_m", "bottom_up_kg", "raymer_kg"], list(zip(spans, bu_w, ray_w)))
    print(f"  class allowance {mean:.1f} +- {sd:.1f} kg (LOO RMS {loo_rms:.1f}); Eidolon {mm.total:.1f} kg "
          f"[P5 {p5:.0f}, P95 {p95:.0f}]; Raymer {ray_e:.1f}")
    for n, v in loo.items():
        print(f"  LOO {n:22s} predicted {v['predicted_empty_kg']:.0f} vs {v['published_empty_kg']:.0f} ({v['error_pct']:+.1f} %)")


if __name__ == "__main__":
    main()
