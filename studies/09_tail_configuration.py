"""Study 09 - Which tail, at what height, with how much elevator?

Each configuration is a fully re-closed aircraft: the horizontal tail is re-sized by the same three
criteria (12 % static margin, landing flare, take-off rotation with propeller slipstream), the wing is
re-positioned, and mass, drag and performance are recomputed. Then two trainer-safety screens:
spin recovery (Bowman's tail damping power factor) and deep stall (wake crossing angle).

Part A: six configurations.  Part B: HT height offset swept from the tail cone to the fin tip.
Part C: elevator chord ratio swept 0.25-0.50 on the chosen configuration.
"""
from _common import ROOT, style, write_json, write_csv
import copy
import math
import numpy as np
import matplotlib.pyplot as plt

from eidolon.aircraft import eidolon
from eidolon.design import BASELINE, close
from eidolon.empennage import PRESETS, NOTES, apply, tdpf, wake_crossing_alpha, TDPF_REQUIRED
from eidolon.lifting_line import LiftingLine
from eidolon.model import V_CRUISE, CRUISE_ALT
from eidolon.stability import elevator_cl_h_max

OUT = style.out("09_tail")


def evaluate(ac):
    c = close(ac)
    M = c.model; P = M.plane; W = M.W; a = M.ac
    x_cg_aft = a.wing.x_le_mac + c.env.h_aft * a.wing.mac
    t = tdpf(a, x_cg_aft)
    ll = LiftingLine(a.wing)
    _, a_stall, _ = ll.stall(a.cl_max_2d_clean, a.cl_max_2d_clean - 0.08)
    a_wake = wake_crossing_alpha(a, c.stab.deps_dalpha)
    deep = (a_stall + 5) <= a_wake <= 45
    tail_mass = sum(v for k, v in M.mass.items.items() if k in ("Horizontal tail", "Vertical tail", "Ventral strake"))
    tail_cd = sum(v for k, v in M.drag.items.items() if "tail" in k.lower())
    return dict(Sh=a.htail.area, Vh=a.vh, Sv=a.vtail.area, tail_mass=tail_mass, tail_drag_counts=tail_cd * 1e4,
                empty=M.empty_kg, f100=P.fuel_per_100km(W, V_CRUISE, CRUISE_ALT)[0],
                range=P.range_km(W, M.fuel_kg, V_CRUISE, CRUISE_ALT)[0], roc=P.max_roc(W, 0, 0, "takeoff")[0],
                v_rot=c.rotation[0] * 3.6, v_lof=c.rotation[1] * 3.6, sm=100 * (c.stab.h_np - c.env.h_aft),
                deps=c.stab.deps_dalpha, alpha_wake=a_wake, alpha_stall=a_stall, deep_stall_risk=bool(deep),
                TDPF=t["TDPF"], URVC=t["URVC"], TDR=t["TDR"], unshielded_rudder=t["unshielded_rudder_m2"],
                cl_h_max=elevator_cl_h_max(a), closed=c)


def main():
    base = eidolon(**BASELINE)
    # ---------------- Part A: configurations
    res = {}
    for name in PRESETS:
        r = evaluate(apply(base, name))
        r.pop("closed")
        r["note"] = NOTES.get(name, "")
        spin_ok = (r["TDPF"] >= TDPF_REQUIRED) if not math.isnan(r["TDPF"]) else False
        r["spin_ok"] = spin_ok
        res[name] = r
        print(f"  {name:42s} Sh {r['Sh']:.2f} Vh {r['Vh']:.3f} tail {r['tail_mass']:.1f} kg {r['tail_drag_counts']:.0f} cts "
              f"L/100 {r['f100']:.3f} rng {r['range']:.0f} Vrot {r['v_rot']:.0f}/{r['v_lof']:.0f} TDPF {r['TDPF']*1e6:.0f}e-6 "
              f"wake {r['alpha_wake']:.1f} deep {r['deep_stall_risk']}")
    # score: 40 % efficiency (fuel burn, range), 35 % spin-recovery margin, 25 % no deep stall; a tail that
    # cannot rotate the aircraft before lift-off scores zero (a trainer must take off at forward CG)
    names = list(res)
    f = np.array([res[n]["f100"] for n in names]); rg = np.array([res[n]["range"] for n in names])
    for n in names:
        r = res[n]
        eff = 0.5 * (f.max() - r["f100"]) / max(np.ptp(f), 1e-9) + 0.5 * (r["range"] - rg.min()) / max(np.ptp(rg), 1e-9)
        spin = 0.0 if math.isnan(r["TDPF"]) else min(r["TDPF"] / (2 * TDPF_REQUIRED), 1.0)   # full marks at 2x required
        rotates = r["v_rot"] <= r["v_lof"] * 1.001
        r["score"] = (0.40 * eff + 0.35 * spin + 0.25 * (0.0 if r["deep_stall_risk"] else 1.0)) * (1.0 if rotates else 0.0)
    best = max(res, key=lambda n: res[n]["score"])
    write_json(OUT / "configurations.json", {"results": res, "chosen": best, "tdpf_required": TDPF_REQUIRED})
    write_csv(OUT / "configurations.csv", ["configuration"] + [k for k in res[names[0]] if k != "note"],
              [[n] + [v for k, v in res[n].items() if k != "note"] for n in names])

    fig, axs = plt.subplots(1, 4, figsize=(16, 4.6), sharey=True)
    order = sorted(names, key=lambda n: -res[n]["score"])
    lab = [n.replace(" (", "\n(") for n in order]
    cols = [style.EIDOLON if n == best else style.MUTED for n in order]
    panels = [("f100", "Fuel at 200 km/h [L/100 km]", None), ("Sh", "Horizontal tail needed [m²]", None),
              ("TDPF", "Spin: tail damping power factor (×10⁻⁶)", TDPF_REQUIRED), ("alpha_wake", "HT enters wing wake at α [deg]", None)]
    for ax, (k, title, req) in zip(axs, panels):
        vals = [res[n][k] * (1e6 if k == "TDPF" else 1) for n in order]
        vals = [0 if (isinstance(v, float) and math.isnan(v)) else v for v in vals]
        ax.barh(range(len(order)), vals, color=cols, height=0.6)
        for i, v in enumerate(vals):
            txt = "n/a" if (k == "TDPF" and v == 0) else f"{v:.3g}"
            if k == "Sh" and res[order[i]]["v_rot"] > res[order[i]]["v_lof"] * 1.001:
                txt += "  cannot rotate before lift-off"
            ax.text(v, i, " " + txt, va="center", fontsize=8.5, color=style.INK2)
        if req:
            ax.axvline(req * 1e6, color=style.BAD, ls="--", lw=1.4)
            ax.text(req * 1e6, len(order) - 0.4, " required", color=style.BAD, fontsize=8.5)
        if k == "alpha_wake":
            a_st = res[order[0]]["alpha_stall"]
            ax.axvspan(a_st + 5, 45, color=style.BAD, alpha=0.08)
            ax.text(a_st + 6, len(order) - 0.4, "deep-stall band", color=style.BAD, fontsize=8.5)
        if k == "f100":
            ax.set_xlim(min(vals) * 0.97, max(vals) * 1.01)
        ax.set_title(title, fontsize=10.5); ax.grid(axis="y", visible=False)
        ax.set_yticks(range(len(order)), lab, fontsize=8.5)
    axs[0].invert_yaxis()
    fig.suptitle(f"Tail configuration trade, each a re-closed aircraft - chosen: {best}", x=0.01, ha="left", fontsize=13, weight="semibold")
    fig.tight_layout()
    style.note(fig, "Tail re-sized by stability, flare and rotation (with slipstream). Spin: Bowman TDPF (NASA TN D-6575). Deep stall: wing-wake crossing.")
    style.save(fig, OUT / "tail_configurations.png")

    # ---------------- Part B: HT height offset sweep (cone -> fin tip), conventional-forward geometry
    rows = []
    for hf in np.linspace(0, 0.95, 9):
        a = apply(base, best)
        a.ht_height_frac = float(hf)
        a.eta_h = 0.90 + 0.10 * hf
        a.slipstream_immersion = max(0.0, min(1.0, a.prop.diameter / max(a.htail.span, 1e-3)) * (1 - hf / 0.5)) if hf < 0.5 else 0.0
        a.ht_endplate = 1.0 + 0.12 * hf
        a.vt_mass_factor = 1.0 + 0.22 * hf
        a.tail_config = "conventional" if hf == 0 else ("cruciform" if hf < 0.9 else "T-tail")
        r = evaluate(a); r.pop("closed")
        rows.append({"height_frac": hf, **r})
    write_csv(OUT / "ht_height_sweep.csv", list(rows[0].keys()), [list(r.values()) for r in rows])
    fig, axs = plt.subplots(1, 3, figsize=(14, 4.2))
    hfs = [r["height_frac"] for r in rows]
    axs[0].plot(hfs, [r["Sh"] for r in rows], color=style.EIDOLON, marker="o", ms=5, label="HT area needed")
    axs[0].set_ylabel("m²"); axs[0].set_title("Tail size needed (rotation governs)")
    ax2 = axs[0].twinx(); ax2.grid(False)
    axs[1].plot(hfs, [r["deps"] for r in rows], color=style.SERIES[2], marker="o", ms=5)
    axs[1].set_title("Downwash at the tail dε/dα"); axs[1].set_ylabel("dε/dα")
    axs[2].plot(hfs, [r["TDPF"] * 1e6 for r in rows], color=style.SERIES[6], marker="o", ms=5, label="spin TDPF ×10⁻⁶")
    axs[2].plot(hfs, [r["alpha_wake"] * 10 for r in rows], color=style.HANSA, marker="o", ms=5, label="wake-crossing α ×10 [deg]")
    axs[2].axhline(TDPF_REQUIRED * 1e6, color=style.BAD, ls="--", lw=1.2)
    axs[2].set_title("Spin and deep-stall screens"); axs[2].legend(fontsize=8.5)
    ax2.remove()
    for ax in axs:
        ax.set_xlabel("HT height / fin height  (0 = on the tail cone, 1 = T-tail)")
    style.note(fig, "Higher HT: less downwash and out of the wing wake at cruise, but out of the slipstream for rotation, heavier fin, deep-stall band near the top.")
    style.save(fig, OUT / "ht_height_sweep.png")

    # ---------------- Part C: elevator chord ratio on the chosen configuration
    erows = []
    for ce in (0.25, 0.30, 0.35, 0.40, 0.45, 0.50):
        a = apply(base, best); a.elevator_chord_ratio = ce
        r = evaluate(a); cl = r["closed"]; r.pop("closed")
        ch = cl.model.ac.htail
        hinge_index = ce**2 * ch.area * ch.mac            # elevator area x elevator chord ~ hinge moment scale
        erows.append({"chord_ratio": ce, "cl_h_max": r["cl_h_max"], "Sh": r["Sh"], "tail_mass": r["tail_mass"],
                      "f100": r["f100"], "hinge_index": hinge_index})
    h0 = next(e["hinge_index"] for e in erows if e["chord_ratio"] == 0.40)
    for e in erows:
        e["stick_force_rel"] = e["hinge_index"] / h0
    write_csv(OUT / "elevator_sweep.csv", list(erows[0].keys()), [list(e.values()) for e in erows])
    fig, ax = plt.subplots(figsize=(8, 4.2))
    ces = [e["chord_ratio"] for e in erows]
    ax.plot(ces, [e["Sh"] for e in erows], color=style.EIDOLON, marker="o", ms=6, label="HT area needed [m²]")
    ax.plot(ces, [e["stick_force_rel"] * 2 for e in erows], color=style.HANSA, marker="o", ms=6, label="hinge-moment / stick-force index (×2, 1 = 0.40)")
    ax.axvline(0.40, color=style.INK2, ls=":", lw=1)
    ax.set_xlabel("Elevator chord / tail chord"); ax.legend(fontsize=8.5)
    ax.set_title("Elevator size: smaller tail vs heavier stick")
    style.note(fig, "Thin-airfoil flap effectiveness with a 0.6 viscous factor; full-up 25 deg. Above ~0.40 the tail barely shrinks while stick force keeps rising.")
    style.save(fig, OUT / "elevator_sweep.png")
    write_json(OUT / "tail_summary.json", {"chosen": best, "chosen_result": res[best], "elevator": erows,
                                           "height_sweep": rows})
    print("  chosen:", best)


if __name__ == "__main__":
    main()
