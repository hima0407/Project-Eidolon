"""Study 07 - Propeller: BEMT efficiency, momentum-theory bound, 2 vs 3 blades.

Replaces the earlier archive/first_iteration/scripts/propulsion_bemt.py result (89.2 % at 230 km/h / 3000 m, no stall model).
Checks shown on the figure:
  * BEMT efficiency always below the actuator-disk ideal (a hard physical bound)
  * installed efficiency = BEMT x 0.92 (spinner/nacelle blockage, scrubbing, blade Re) [A]
"""
from _common import ROOT, style, write_json
import numpy as np
import matplotlib.pyplot as plt

from eidolon.propeller import BEMTPropeller
from eidolon.engines import ENGINES

OUT = style.out("07_propeller")


def main():
    eng = ENGINES["912iSc"]
    V = np.linspace(15, 75, 25)
    fig, axs = plt.subplots(1, 2, figsize=(12, 4.3))
    res = {}
    for B, col in ((2, style.HANSA), (3, style.EIDOLON)):
        p = BEMTPropeller(1.75, B)
        for P_kw, ls, h in ((0.75 * 73.5, "-", 1500.0),):
            rs = [p.at_power(v, eng.prop_rpm_cruise * 1.08, P_kw * 1e3, h) for v in V]
            eta = np.array([r.eta for r in rs]); ideal = np.array([r.eta_ideal for r in rs])
            axs[0].plot(V * 3.6, eta, color=col, label=f"{B}-blade BEMT")
            axs[0].plot(V * 3.6, eta * 0.92, color=col, ls="--", lw=1.4, label=f"{B}-blade installed (x0.92)")
            if B == 3:
                axs[0].plot(V * 3.6, ideal, color=style.INK2, lw=1.2, ls=":", label="actuator-disk ideal (upper bound)")
            assert np.all(eta <= ideal + 1e-9), "BEMT exceeded the momentum-theory bound"
            r200 = p.at_power(200 / 3.6, eng.prop_rpm_cruise * 1.08, 0.6 * 73.5e3, 1500.0)
            res[f"{B}_blade"] = {"eta_bemt_200kmh": r200.eta, "eta_ideal_200kmh": r200.eta_ideal,
                                 "eta_installed_200kmh": r200.eta * 0.92, "beta75_deg": r200.beta75_deg,
                                 "tip_mach": r200.tip_mach,
                                 "static_thrust_N": p.at_power(0.5, eng.prop_rpm_max, 73.5e3, 0.0).thrust}
    axs[0].set_xlabel("True airspeed [km/h]"); axs[0].set_ylabel("Propeller efficiency")
    axs[0].set_ylim(0.3, 1.0); axs[0].legend(fontsize=8, loc="lower right")
    axs[0].set_title("Constant-speed 1.75 m prop, 55 kW, 1500 m")

    # spanwise loading at cruise for the 3-blade
    p = BEMTPropeller(1.75, 3)
    axs[1].plot(p.rR, p.c / p.R, color=style.EIDOLON, label="chord c/R")
    axs[1].plot(p.rR, np.rad2deg(p.beta_shape) / 100 + 0.3, color=style.SERIES[2], label="twist (deg/100, offset)")
    axs[1].set_xlabel("r/R"); axs[1].set_title("Blade geometry used (MTV-21-A class estimate)")
    axs[1].legend(fontsize=8.5)
    style.note(fig, "BEMT with Prandtl tip+hub loss, stall and drag rise; ideal-pitch twist. eta never exceeds the momentum bound (asserted in code).")
    style.save(fig, OUT / "propeller_efficiency.png")
    write_json(OUT / "propeller_summary.json", res)
    print(res)


if __name__ == "__main__":
    main()
