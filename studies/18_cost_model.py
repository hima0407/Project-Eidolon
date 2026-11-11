"""Study 18 - Unit cost: Eastlake / Gudmundsson GA cost model, calibrated on Hansa-NG's reported price.

One labour-rate factor is fitted so the model gives Hansa-NG about Rs 3 crore, then the same model
prices Eidolon with a glass airframe and with a carbon airframe built two ways (vacuum infusion,
prepreg + oven cure). Method and every assumption: eidolon/cost.py.
"""
from _common import style, write_json
import matplotlib.pyplot as plt

from eidolon import cost
from eidolon.design import eidolon_v1, hansa_closed

OUT = style.out("18_cost")


def bar(items_usd, title, note, path):
    kv = sorted(((k, v * cost.INR_PER_USD / 1e5) for k, v in items_usd.items() if v > 1), key=lambda kv: kv[1], reverse=True)
    vals = [v for _, v in kv]; tot = sum(vals)
    fig, ax = plt.subplots(figsize=(11, 5.6))
    ax.barh([k for k, _ in kv], vals, height=0.55, color=style.EIDOLON); ax.invert_yaxis()
    for i, v in enumerate(vals):
        ax.text(v + 1.5, i, f"₹{v:.0f} lakh ({100*v/tot:.0f} %)", va="center", fontsize=10.5, color=style.INK2)
    ax.set_xlim(0, max(vals) * 1.32); ax.grid(axis="y", visible=False); ax.set_xlabel("₹ lakh per aircraft")
    ax.set_title(title.format(tot=tot / 100))
    fig.tight_layout()
    style.note(fig, note)
    style.save(fig, path)


def main():
    h = hansa_closed(); e = eidolon_v1()
    vh_h = h.model.plane.v_max(h.model.W, 0.0) * 3.6
    vh_e = e.model.plane.v_max(e.model.W, 0.0) * 3.6
    k = cost.calibrate_labour(vh_h)
    _, hansa_usd = cost.eastlake(cost.HANSA_EMPTY_KG, vh_h, k)
    res = {p: cost.unit_cost(e.model.ac, vh_e, e.model.empty_kg, k, p) for p in ("glass", "infusion", "prepreg")}
    base = res["glass"]["total_usd"]
    note = ("Gudmundsson / Eastlake GA cost model, 180 aircraft in 5 years; labour rate fitted so the same model gives "
            "Hansa-NG ₹3.0 crore. ₹88 per US$ [assumed]. studies/18_cost_model.py")
    bar(res["glass"]["items"], "Eidolon, glass airframe: unit cost ≈ ₹{tot:.2f} crore (model)", note, OUT / "cost_glass.png")
    bar(res["infusion"]["items"], "Eidolon, carbon airframe: unit cost ≈ ₹{tot:.2f} crore (model)", note + " Carbon by vacuum infusion.",
        OUT / "cost_carbon.png")
    out = {"labour_factor": k, "hansa_vh_kmh": vh_h, "eidolon_vh_kmh": vh_e,
           "hansa_model_inr_crore": hansa_usd * cost.INR_PER_USD / 1e7,
           "cases": {p: dict(total_inr_crore=r["total_inr"] / 1e7, vs_glass_pct=100 * (r["total_usd"] / base - 1),
                             items_inr_lakh={kk: vv * cost.INR_PER_USD / 1e5 for kk, vv in r["items"].items()},
                             laminate_m2=r["laminate_m2"], fabric_usd=r["fabric_usd"]) for p, r in res.items()},
           "assumptions": dict(CPI=cost.CPI, INR_per_USD=cost.INR_PER_USD, built=cost.N_BUILT, prototypes=cost.N_PROTO,
                               airframe_fraction=cost.AIRFRAME_FRACTION, liability=cost.LIABILITY,
                               fabric_usd_m2=cost.FABRIC_USD_M2, process=cost.PROCESS)}
    write_json(OUT / "cost.json", out)
    print(f"labour factor {k:.3f}; Hansa-NG model ₹{out['hansa_model_inr_crore']:.2f} cr")
    for p, r in out["cases"].items():
        print(f"  {p:9s} ₹{r['total_inr_crore']:.2f} cr ({r['vs_glass_pct']:+.1f} % vs glass)")


if __name__ == "__main__":
    main()
