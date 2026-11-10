"""Study 11 - Performance and the head-to-head with Hansa-NG.

Everything here comes from the same calibrated models for both aircraft.
Outputs: power-required/available curves, climb vs altitude (ISA and 45 C hot day),
payload-range diagram, and the comparison table used in the README and the deck.
"""
from _common import ROOT, style, write_json, write_csv
import numpy as np
import matplotlib.pyplot as plt

from eidolon.aircraft import G, OCCUPANT_KG
from eidolon.design import eidolon_v1, hansa_closed, headline
from eidolon.model import V_CRUISE, CRUISE_ALT
from eidolon import atmosphere as isa

OUT = style.out("11_performance")


def main():
    e, h = eidolon_v1(), hansa_closed()
    E, H = headline(e), headline(h)
    rows = [(k, H[k], E[k], 100 * (E[k] - H[k]) / H[k] if H[k] else 0.0) for k in H]
    write_csv(OUT / "head_to_head.csv", ["quantity", "Hansa-NG (model)", "Eidolon v1", "change_pct"], rows)
    write_json(OUT / "head_to_head.json", {"Hansa-NG": H, "Eidolon": E})

    # ---- power curves
    fig, axs = plt.subplots(1, 2, figsize=(12.5, 4.5))
    V = np.linspace(22, 75, 120)
    for c, col, name in ((h, style.HANSA, "Hansa-NG"), (e, style.EIDOLON, "Eidolon")):
        P, W = c.model.plane, c.model.W
        axs[0].plot(V * 3.6, P.p_req(V, W, CRUISE_ALT) / 1e3, color=col, label=f"{name}: power required")
        axs[0].plot(V * 3.6, P.p_av(V, CRUISE_ALT) / 1e3, color=col, ls="--", lw=1.4, label=f"{name}: power available (MCP)")
        hs = np.arange(0, 7001, 500.0)
        axs[1].plot([P.max_roc(W, x)[0] for x in hs], hs, color=col, label=f"{name}, ISA")
        dT = isa.isa_dT_for_oat(45, 0)
        axs[1].plot([P.max_roc(W, x, dT)[0] for x in hs], hs, color=col, ls=":", label=f"{name}, 45 °C day")
    axs[0].axvline(200, color=style.INK2, lw=0.8, ls=":")
    axs[0].set_xlabel("TAS [km/h]"); axs[0].set_ylabel("Power [kW]"); axs[0].set_ylim(0, 80)
    axs[0].set_title(f"Power at {CRUISE_ALT:.0f} m, MTOW")
    axs[0].legend(fontsize=8)
    axs[1].axvline(0.508, color=style.INK2, lw=0.8, ls=":")
    axs[1].text(0.55, 6600, "service-ceiling criterion 0.5 m/s", fontsize=8, color=style.INK2)
    axs[1].set_xlabel("Max rate of climb [m/s] (MCP)"); axs[1].set_ylabel("Altitude [m]")
    axs[1].set_title("Climb vs altitude"); axs[1].legend(fontsize=8); axs[1].set_xlim(0, 5)
    style.note(fig, "Same models, same calibration for both aircraft. Hot day = ISA + 30 K at sea level (45 °C).")
    style.save(fig, OUT / "power_and_climb.png")

    # ---- payload-range at 200 km/h, 1500 m, 45 min reserve
    fig, ax = plt.subplots(figsize=(8, 4.6))
    for c, col, name in ((h, style.HANSA, "Hansa-NG"), (e, style.EIDOLON, "Eidolon")):
        M = c.model; P = M.plane; ac = M.ac
        tank = ac.fuel_capacity_l * 0.72
        pts = []
        for payload in np.linspace(0, ac.mtow - M.empty_kg, 30):
            fuel = min(tank, ac.mtow - M.empty_kg - payload)
            W0 = (M.empty_kg + payload + fuel) * G
            r = P.range_km(W0, fuel, V_CRUISE, CRUISE_ALT)[0] if fuel > 0 else 0.0
            pts.append((r, payload))
        pts = np.array(sorted(pts))
        ax.plot(pts[:, 0], pts[:, 1], color=col, label=name)
    ax.axhline(2 * OCCUPANT_KG + 10, color=style.INK2, lw=0.8, ls=":")
    ax.text(10, 2 * OCCUPANT_KG + 14, "2 × 77 kg + 10 kg bag", fontsize=8.5, color=style.INK2)
    ax.set_xlabel("Range at 200 km/h, 1500 m, 45-min reserve [km]"); ax.set_ylabel("Payload [kg]")
    ax.set_title("Payload-range"); ax.legend(); ax.set_xlim(0); ax.set_ylim(0)
    style.note(fig, "Fuel limited by MTOW 750 kg or tank capacity (Hansa-NG 95 L published, Eidolon 100 L).")
    style.save(fig, OUT / "payload_range.png")

    # ---- head-to-head figure (percent change on the headline metrics)
    keys = [("Fuel per 100 km @200 km/h [L]", True), ("Range @200 km/h, design payload, 45 min reserve [km]", False),
            ("Cruise speed @75% 1500 m [km/h]", False), ("Max ROC SL [m/s]", False),
            ("Take-off to 15 m [m]", True), ("Stall, landing flap [km/h]", True), ("L/D max", False),
            ("Empty mass [kg]", True)]
    fig, ax = plt.subplots(figsize=(9, 4.6))
    for i, (k, lower) in enumerate(keys):
        d = 100 * (E[k] - H[k]) / H[k]
        better = (d < 0) if lower else (d > 0)
        ax.barh(i, d, color=style.GOOD if better else style.BAD, height=0.55)
        ax.text(d + (1.5 if d >= 0 else -1.5), i, f"{d:+.0f}%   {H[k]:.4g} → {E[k]:.4g}", va="center",
                ha="left" if d >= 0 else "right", fontsize=8.5, color=style.INK2)
    ax.set_yticks(range(len(keys)), [k.split(" [")[0].replace(" @200 km/h", "") for k, _ in keys])
    ax.invert_yaxis(); ax.axvline(0, color=style.INK2, lw=1)
    ax.set_xlim(-60, 75); ax.grid(axis="y", visible=False)
    ax.set_xlabel("Eidolon v1 vs Hansa-NG (same models) [%]")
    ax.set_title("Eidolon v1 against the Hansa-NG")
    style.note(fig, "Green = better. Hansa-NG run through the identical calibrated pipeline (studies/02).")
    style.save(fig, OUT / "head_to_head.png")
    for r in rows:
        print(f"  {r[0]:55s} {r[1]:9.4g} {r[2]:9.4g} {r[3]:+6.1f}%")


if __name__ == "__main__":
    main()
