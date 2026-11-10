"""Study 16 - The 3-D model: Fusion 360 solid, meshes, studio renders and a dimensioned three-view.

One geometry description (eidolon/oml.py: closed planar section rings for every body) feeds:
  cad/fusion/Eidolon/eidolon_geometry.json   -> Fusion 360 script builds lofted B-rep solids
  cad/generated/*.stl                         -> mesh per body (Fusion: Insert > Insert Mesh)
  docs/viewer/model.json + specs.json         -> interactive web viewer
  results/16_geometry/*.png                   -> studio renders (eidolon/render.py) and three-view
"""
from _common import ROOT, style, write_json
import base64
import json
import shutil
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection

from eidolon.design import eidolon_v1, hansa_closed, headline
from eidolon.geometry3d import write_stl
from eidolon.oml import build_oml, to_mesh, COLORS, livery_stripe
from eidolon.render import render

OUT = style.out("16_geometry")
CAD = ROOT / "cad" / "generated"; CAD.mkdir(parents=True, exist_ok=True)
FUS = ROOT / "cad" / "fusion" / "Eidolon"; FUS.mkdir(parents=True, exist_ok=True)
VIEW = ROOT / "docs" / "viewer"
SPEC = {"canopy": (0.9, 140), "spinner": (0.6, 80), "propeller_blade": (0.2, 30), "main_gear_leg": (0.3, 40), "nose_gear_leg": (0.3, 40)}


def _dedupe(ring, tol_cm=0.02):
    """Drop points closer than tol to the previous kept point: Fusion's fitted splines can loop on them."""
    out = [ring[0]]
    for q in ring[1:]:
        if sum((a - b) ** 2 for a, b in zip(q, out[-1])) ** 0.5 >= tol_cm:
            out.append(q)
    return out


def main():
    c = eidolon_v1(); ac = c.model.ac
    parts, meta = build_oml(ac, c.env)
    mesh = to_mesh(parts)
    mesh["livery_stripe"] = livery_stripe(ac)
    for old in CAD.glob("*.stl"):
        old.unlink()
    for k, t in mesh.items():
        write_stl(CAD / f"eidolon_v1_{k}.stl", t, k)
    write_stl(CAD / "eidolon_v1_complete.stl", np.concatenate(list(mesh.values())), "eidolon_v1")

    # ---- Fusion 360: aircraft (x, y, z) [m]  ->  Fusion (x, z_up=Y, -y) [cm]
    axis_map = {"x": "x", "y": "z", "z": "y"}
    fparts = []
    for k, p in parts.items():
        rings = [_dedupe([[round(100 * x, 4), round(100 * z, 4), round(-100 * y, 4)] for x, y, z in r]) for r in p["rings"]]
        hexc = COLORS.get(k, "#dddddd").lstrip("#")
        fparts.append({"name": k, "plane": axis_map[p["plane"]], "rings": rings, "mirror": bool(p.get("mirror")),
                       "pattern": int(p.get("pattern", 0)),
                       "closed_loop": k in ("fuselage", "spinner", "main_wheel_fairing", "nose_wheel_fairing"),
                       "color": "#" + hexc, "rgb": [int(hexc[i:i + 2], 16) for i in (0, 2, 4)]})
    summary = (f"Span {ac.wing.span:.2f} m, wing {ac.wing.area:.2f} m2, NACA 63-415 -> 63-412, "
               f"{ac.wing.twist_tip_deg:.0f} deg washout, drooped outboard LE, V_h {ac.vh:.2f}, ventral strake.")
    (FUS / "eidolon_geometry.json").write_text(json.dumps({"units": "cm, Fusion Y-up", "summary": summary, "parts": fparts}))
    print(f"  wrote cad/fusion/Eidolon/eidolon_geometry.json ({len(fparts)} parts)")

    # ---- web viewer bundle
    bundle = {"parts": {k: {"b64": base64.b64encode(np.round(t.reshape(-1, 3), 4).astype("<f4").tobytes()).decode(),
                            "color": COLORS.get(k, "#dddddd")} for k, t in mesh.items()},
              "z_ground": meta["z_ground"]}
    (VIEW / "model.json").write_text(json.dumps(bundle))
    pts = np.concatenate([t.reshape(-1, 3) for t in mesh.values()])
    dims = {"length_m": float(pts[:, 0].max() - pts[:, 0].min()), "span_m": float(pts[:, 1].max() - pts[:, 1].min()),
            "height_m": float(pts[:, 2].max() - meta["z_ground"]), **meta, "triangles": int(sum(len(t) for t in mesh.values()))}
    E, H = headline(c), headline(hansa_closed())
    pick = ["Fuel per 100 km @200 km/h [L]", "Range @200 km/h, design payload, 45 min reserve [km]",
            "Cruise speed @75% 1500 m [km/h]", "Max ROC SL [m/s]", "Take-off to 15 m [m]",
            "Stall, landing flap [km/h]", "Empty mass [kg]", "L/D max", "CD0"]
    write_json(VIEW / "specs.json", {
        "compare": [{"name": k, "eidolon": E[k], "hansa": H[k]} for k in pick],
        "geometry": {"Span": f"{ac.wing.span:.2f} m", "Wing area": f"{ac.wing.area:.2f} m²",
                     "Aspect ratio": f"{ac.wing.aspect_ratio:.2f}", "Length": f"{dims['length_m']:.2f} m",
                     "Height": f"{dims['height_m']:.2f} m", "Wing section": "NACA 63-415 → 63-412",
                     "Washout / LE": f"{ac.wing.twist_tip_deg:.0f}°, drooped outboard", "Tail": f"conventional, V_h {ac.vh:.2f}, ventral strake",
                     "Engine": "Rotax 912 iSc, 73.5 kW", "Propeller": f"{ac.prop.diameter:.2f} m, {ac.prop.blades}-blade CS",
                     "MTOW / empty": f"{ac.mtow:.0f} / {c.model.empty_kg:.0f} kg",
                     "Static margin": f"{100*(c.stab.h_np-c.env.h_aft):.0f} % MAC (aft CG)"}})
    write_json(OUT / "geometry.json", {"dimensions": dims, "parts": list(parts)})
    body = (VIEW / "viewer_body.html").read_text()
    (VIEW / "index.html").write_text(
        '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        '<style>html,body{margin:0}</style>\n</head>\n<body>\n' + body + '\n</body>\n</html>\n')
    print("  wrote docs/viewer/index.html (open with: python3 -m http.server -d docs/viewer)")

    # ---- studio renders
    from PIL import Image
    zg = meta["z_ground"]
    shots = {"render_hero.png": dict(eye=(-6.8, -9.6, 2.3), target=(4.1, 0.6, -0.55), fov=27, W=1800, H=1050),
             "render_rear.png": dict(eye=(11.5, 7.0, 4.2), target=(3.4, 0, -0.35), fov=29, W=1800, H=1050),
             "render_top.png": dict(eye=(3.6, -0.01, 17.0), target=(3.6, 0, 0), fov=40, W=1400, H=1400),
             "render_front.png": dict(eye=(-13.0, -0.6, 0.2), target=(3.0, 0, -0.25), fov=27, W=1600, H=900)}
    for fn, kw in shots.items():
        img = render(mesh, COLORS, z_ground=zg, ss=2, extra_specular=SPEC, **kw)
        Image.fromarray(img).save(OUT / fn)
        print(f"  wrote results/16_geometry/{fn}")
    shutil.copy(OUT / "render_hero.png", OUT / "render.png")

    # ---- dimensioned three-view (silhouettes, painter-sorted)
    fig = plt.figure(figsize=(13, 8.2))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.25, 1], height_ratios=[1, 0.62], hspace=0.08, wspace=0.05)
    views = [(fig.add_subplot(gs[0, 0]), (1, 0), 2, "Top"), (fig.add_subplot(gs[1, 0]), (0, 2), 1, "Side"),
             (fig.add_subplot(gs[:, 1]), (1, 2), 0, "Front")]
    for ax, (i, j), depth_axis, name in views:
        allp, allc, alld = [], [], []
        for k, t in mesh.items():
            P = t[:, :, [i, j]]
            if name == "Top":
                P = P.copy(); P[:, :, 1] = -P[:, :, 1]
            d = t[:, :, depth_axis].mean(1) * (-1 if name == "Front" else 1) * (1 if name == "Top" else 1)
            if name == "Side":
                d = t[:, :, 1].mean(1)
            allp.append(P); allc += [COLORS.get(k, "#dddddd")] * len(t); alld.append(d)
        P = np.concatenate(allp); D = np.concatenate(alld); C = np.array(allc)
        o = np.argsort(D)
        ax.add_collection(PolyCollection(P[o], facecolors=C[o], edgecolors=C[o], linewidths=0.2))
        ax.autoscale(); ax.set_aspect("equal"); ax.axis("off")
        ax.set_title(name, loc="left", fontsize=11, color=style.INK2)
    axT, axS, axF = views[0][0], views[1][0], views[2][0]
    axT.text(ac.wing.span * 0.28, -(ac.wing.x_le_root + ac.wing.c_root + 0.45), f"span {ac.wing.span:.2f} m",
             ha="center", fontsize=9, color=style.INK2)
    axS.axhline(zg, color=style.MUTED, lw=0.8); axF.axhline(zg, color=style.MUTED, lw=0.8)
    axS.text(dims["length_m"] / 2, zg - 0.35, f"length {dims['length_m']:.2f} m", ha="center", fontsize=9, color=style.INK2)
    axF.text(0, zg - 0.35, f"height {dims['height_m']:.2f} m   track {2*meta['y_track']:.2f} m", ha="center", fontsize=9, color=style.INK2)
    fig.suptitle(f"Eidolon v1 - generated from the design closure  (S {ac.wing.area:.2f} m², AR {ac.wing.aspect_ratio:.1f}, "
                 f"NACA 63-415 -> 63-412, {ac.wing.twist_tip_deg:.0f}° washout, drooped outboard LE, ventral strake)",
                 x=0.01, ha="left", fontsize=12, weight="semibold")
    style.save(fig, OUT / "three_view.png")
    print("  dims", {k: round(v, 3) if isinstance(v, float) else v for k, v in dims.items()})


if __name__ == "__main__":
    main()
