"""Study 02 - Calibrate the models on the Hansa-NG, then check what they predict.

Why: any conceptual-design model has bias. Fitting three factors on a real aircraft of the
same class (same MTOW, same engine, same mission) and then running Eidolon through the
*same* models makes the comparison like-for-like: whatever bias is left cancels to first order.

Fitted (3 numbers, 3 published targets):
    mass_cal   (cross-check only) Raymer statistical items -> empty mass 540 kg
The primary mass model (study 01) is NOT fitted here: its Hansa-NG empty mass is a leave-one-out
prediction (class allowance measured on Aquila A210 and DV20 only).
    drag_cal   additive unmodelled CD0 -> 200 km/h at 75 % of rated power, 1500 m   [assumed setting]
    climb_cal  excess power in climb   -> max ROC 3.3 m/s at sea level

Then predicted (not fitted) and compared with the brochure: stall speed, take-off and
landing distance, endurance, range.
"""
from _common import ROOT, style, write_json, write_csv
import numpy as np
import matplotlib.pyplot as plt

from eidolon.aircraft import hansa_ng, HANSA_PUBLISHED, G
from eidolon.model import build, CRUISE_ALT
from eidolon.weights import calibrate_on

OUT = style.out("02_calibration")
H = HANSA_PUBLISHED


def bisect(f, lo, hi, target, n=40, increasing=True):
    for _ in range(n):
        mid = 0.5 * (lo + hi)
        if (f(mid) < target) == increasing:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def fit(power_fraction=0.75):
    ac = hansa_ng()
    mass_cal = calibrate_on(ac, H["empty_mass_kg"])
    spd = lambda dc: build(ac, drag_cal=dc, mass_cal=mass_cal, climb_factor=1.0).plane.speed_at_power(
        ac.weight, CRUISE_ALT, power_fraction) * 3.6
    drag_cal = bisect(spd, -0.01, 0.04, H["max_cruise_kmh"], increasing=False)
    roc = lambda cf: build(ac, drag_cal=drag_cal, mass_cal=mass_cal, climb_factor=cf).plane.max_roc(
        ac.weight, 0.0, 0.0, "takeoff")[0]
    climb_cal = bisect(roc, 0.5, 1.2, H["roc_ms"], increasing=True)
    return mass_cal, drag_cal, climb_cal


def main():
    mass_cal, drag_cal, climb_cal = fit(0.75)
    import eidolon.model as em          # later studies in the same process use the fresh values
    em.MASS_CAL, em.DRAG_CAL, em.CLIMB_CAL = mass_cal, drag_cal, climb_cal
    write_json(OUT / "calibration.json", {
        "mass_cal": mass_cal, "drag_cal": drag_cal, "climb_cal": climb_cal,
        "fitted_on": "Hansa-NG: empty 540 kg, 200 km/h @75% power 1500 m, ROC 3.3 m/s",
        "source": H["source"]})

    # sensitivity of the drag calibration to the assumed 'max cruise' power setting
    sens = []
    for pf in (0.65, 0.70, 0.75, 0.80, 0.85):
        m, d, c = fit(pf)
        sens.append((pf, m, d, c))
    write_csv(OUT / "calibration_vs_cruise_power_assumption.csv",
              ["cruise_power_fraction", "mass_cal", "drag_cal", "climb_cal"], sens)

    # ---- independent predictions with the fitted model
    ac = hansa_ng()
    import json as _j
    loo = _j.loads((ROOT / "results" / "01_mass" / "class_allowance.json").read_text())["leave_one_out"]["Hansa-NG"]
    M = build(ac, drag_cal=drag_cal, mass_cal=mass_cal, climb_factor=climb_cal,
              allowance_kg=loo["allowance_from_others_kg"])
    P, W = M.plane, ac.weight
    fuel_full = H["fuel_l"] * 0.72
    vs0 = float(P.v_stall(W, M.polar.cl_max_land)) * 3.6
    to = P.takeoff_distance(W)[1]
    ld = P.landing_distance(W)[0]
    v65 = P.speed_at_power(W, CRUISE_ALT, 0.65)
    p65, fr = P.cruise_power(v65, W, CRUISE_ALT)
    endur = fuel_full / (P.bsfc(fr) * p65 / 1e6)
    rng75, v75 = P.range_at_power(W, fuel_full, CRUISE_ALT, 0.75)
    ceil = P.ceiling(W)
    rows = [
        ("Empty mass [kg] (leave-one-out)", H["empty_mass_kg"], M.empty_kg, "predicted"),
        ("Max cruise @75% [km/h]", H["max_cruise_kmh"], P.speed_at_power(W, CRUISE_ALT, 0.75) * 3.6, "fitted"),
        ("Max rate of climb [m/s]", H["roc_ms"], P.max_roc(W, 0, 0, "takeoff")[0], "fitted"),
        ("Stall speed, flap 20 [km/h]", H["stall_kmh_flaps20"], vs0, "predicted"),
        ("Take-off distance [m]", H["takeoff_m"], to, "predicted"),
        ("Landing distance [m]", H["landing_m"], ld, "predicted"),
        ("Endurance @65%, full fuel [h]", H["endurance_h"], endur, "predicted"),
        ("Range @75%, full fuel, 45 min res. [km]", H["range_km"], rng75, "predicted"),
    ]
    write_csv(OUT / "hansa_validation.csv", ["quantity", "published", "model", "role"],
              [(a, b, c, d) for a, b, c, d in rows])
    write_json(OUT / "hansa_validation.json", {
        r[0]: {"published": r[1], "model": r[2], "error_pct": 100 * (r[2] - r[1]) / r[1], "role": r[3]} for r in rows}
        | {"Service ceiling [m]": {"published": ">= 3048 (max operating altitude)", "model": ceil}})

    # ---- figure: predicted vs published
    fig, ax = plt.subplots(figsize=(8.6, 4.4))
    labels = [r[0] for r in rows][::-1]
    err = [100 * (r[2] - r[1]) / r[1] for r in rows][::-1]
    roles = [r[3] for r in rows][::-1]
    colors = [style.MUTED if ro == "fitted" else (style.EIDOLON) for ro in roles]
    y = np.arange(len(rows))
    ax.barh(y, err, color=colors, height=0.55, zorder=3)
    ax.axvline(0, color=style.INK2, lw=1)
    ax.axvspan(-15, 15, color=style.GRID, alpha=0.45, zorder=0)
    for yi, e, r in zip(y, err, rows[::-1]):
        ax.text(e + (1 if e >= 0 else -1), yi, f"{e:+.0f}%  ({r[2]:.4g} vs {r[1]:.4g})",
                va="center", ha="left" if e >= 0 else "right", fontsize=8.5, color=style.INK2)
    ax.set_yticks(y, labels)
    ax.set_xlim(-45, 45)
    ax.set_xlabel("Model error vs. published Hansa-NG figure [%]")
    ax.set_title("Model check on a real aircraft: Hansa-NG")
    ax.grid(axis="y", visible=False)
    ax.text(0.99, 0.02, "grey = fitted (3 factors)   blue = predicted   band = ±15 %",
            transform=ax.transAxes, ha="right", fontsize=8.5, color=style.INK2)
    style.note(fig, "Published values: CSIR-NAL Hansa-NG brochure (2020). Model: eidolon/ package, studies/02.")
    style.save(fig, OUT / "hansa_validation.png")
    for r in rows:
        print(f"  {r[0]:42s} published {r[1]:8.4g}  model {r[2]:8.4g}  ({r[3]})")
    print(f"  calibration: mass {mass_cal:.3f}  dCD0 {drag_cal:.5f}  climb {climb_cal:.3f}; ceiling {ceil:.0f} m")


if __name__ == "__main__":
    main()
