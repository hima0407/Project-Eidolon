"""Study 21 - Presentation renders: each part on its own, exploded-view layers and an assembly animation.

Everything is rendered by eidolon/render.py from the same mesh as study 16 (eidolon/oml.py), so the
pictures are the analysed geometry, not drawings.
    part_*.png            each part alone on a transparent background (part-intro slides)
    crop_*.png + layers.json
                          the aircraft split into layers from one camera; overlaid at their 'assembled'
                          positions they rebuild the aircraft, at 'exploded' positions they form the
                          exploded view (the deck animates between the two)
    assembly.mp4          parts fly in along their assembly direction while the camera orbits, then the
                          propeller spins up. Slow (about 160 frames): run with --animate.
Wing, tail and gear halves are split into near and far layers so that flat layers still occlude
correctly; the parts of the wing and tailplane inside the fuselage are trimmed from the near layers.
"""
from _common import style, write_json
import math
import shutil
import subprocess
import sys

import numpy as np
from PIL import Image

from eidolon.design import eidolon_v1
from eidolon.oml import build_oml, to_mesh, COLORS, livery_stripe
from eidolon.render import render

OUT = style.out("21_renders")
EYE, TGT = np.array([-6.8, -9.6, 2.3]), np.array([4.1, 0.6, -0.55])
SPEC = {"canopy": (0.9, 140), "spinner": (0.6, 80), "propeller_blade": (0.2, 30), "main_gear_leg": (0.3, 40), "nose_gear_leg": (0.3, 40)}
GROUPS = {
    "fuselage": ["fuselage", "livery_stripe"],
    "canopy": ["canopy"],
    "wing": ["wing_inboard", "wing_outboard_cuffed", "wing_tip", "flap", "wing_te_filler", "aileron"],
    "tail": ["stabiliser", "stabiliser_tip", "elevator", "fin", "fin_tip", "rudder", "dorsal_fin", "ventral_strake"],
    "prop": ["spinner", "propeller_blade"],
    "gear": ["main_gear_leg", "main_wheel_fairing", "nose_gear_leg", "nose_wheel_fairing"],
}
# darker albedo for the part stills, which sit on dark slides
STILL = {k: ("#b4b8bd" if v.lower() in ("#f1f1ee", "#f4f4f1") else ("#a7abb0" if v.lower() == "#e8e8e4" else v)) for k, v in COLORS.items()}
STILL["propeller_blade"] = "#7c838c"


def mesh_of_v1():
    c = eidolon_v1(); ac = c.model.ac
    parts, meta = build_oml(ac, c.env)
    mesh = to_mesh(parts); mesh["livery_stripe"] = livery_stripe(ac)
    return mesh, meta["z_ground"]


def subset(mesh, names, side=None, ymin=0.0):
    out = {}
    for n in names:
        t = mesh[n]; cy = t[:, :, 1].mean(axis=1)
        keep = np.abs(cy) >= ymin
        if side is not None:
            keep &= (cy > 0) if side == "far" else (cy <= 0)
        if keep.any():
            out[n] = t[keep]
    return out


def still(mesh, zg, names, fn, W=1500, H=1000, fov=24, dirv=None, fill=0.98):
    m = subset(mesh, names)
    pts = np.concatenate([t.reshape(-1, 3) for t in m.values()])
    c = 0.5 * (pts.min(0) + pts.max(0)); r = 0.5 * np.linalg.norm(pts.max(0) - pts.min(0))
    d = np.array(dirv, float); d /= np.linalg.norm(d)
    dist = r / math.sin(math.radians(fov / 2)) * fill
    img = render(m, STILL, eye=c + d * dist, target=c, fov=fov, W=W, H=H, ss=2, z_ground=zg - 50, extra_specular=SPEC,
                 ground=False, alpha=True)
    Image.fromarray(img, "RGBA").save(OUT / fn)
    print(f"  wrote {fn}")


LAYERS = {  # name: (parts, side, trim |y| below, exploded offset on a 1920 x 1080 slide [px])
    "wing_far": (GROUPS["wing"], "far", 0.0, (0, 170)),
    "tail_far": (["stabiliser", "stabiliser_tip", "elevator"], "far", 0.0, (260, -50)),
    "gear": (GROUPS["gear"], None, 0.0, (0, 230)),
    "fuselage": (GROUPS["fuselage"], None, 0.0, (0, 0)),
    "canopy": (["canopy"], None, 0.0, (0, -190)),
    "fin": (["fin", "fin_tip", "rudder", "dorsal_fin", "ventral_strake"], None, 0.0, (260, -50)),
    "tail_near": (["stabiliser", "stabiliser_tip", "elevator"], "near", 0.10, (260, -50)),
    "wing_near": (GROUPS["wing"], "near", 0.56, (0, 170)),
    "prop": (GROUPS["prop"], None, 0.0, (-260, 0)),
}
SLIDE_SCALE, SLIDE_LEFT, SLIDE_TOP = 1.2, -89, 19   # layer pixels -> slide pixels


def layers(mesh, zg):
    pos = {}
    for k, (names, side, ymin, off) in LAYERS.items():
        img = render(subset(mesh, names, side, ymin), COLORS, eye=EYE, target=TGT, fov=27, W=1600, H=934, ss=2,
                     z_ground=zg - 50, extra_specular=SPEC, ground=False, alpha=True)
        im = Image.fromarray(img, "RGBA"); a = np.array(im)[..., 3]
        ys, xs = np.nonzero(a > 0)
        x0, x1, y0, y1 = xs.min() - 4, xs.max() + 5, ys.min() - 4, ys.max() + 5
        im.crop((x0, y0, x1, y1)).save(OUT / f"crop_{k}.png")
        w, h = round((x1 - x0) * SLIDE_SCALE), round((y1 - y0) * SLIDE_SCALE)
        ax, ay = round(SLIDE_LEFT + x0 * SLIDE_SCALE), round(SLIDE_TOP + y0 * SLIDE_SCALE)
        pos[k] = dict(width=w, height=h, assembled=(ax, ay), exploded=(ax + off[0], ay + off[1]))
        print(f"  wrote crop_{k}.png")
    write_json(OUT / "layers.json", {"paint_order": list(LAYERS), "layers": pos})


# ---- animation
OFF = {"fuselage": (0, 0, 0), "gear": (0, 0, -1.6), "wing": (0, 0, 2.6), "canopy": (0, 0, 1.7), "tail": (3.2, 0, 1.0), "prop": (-3.0, 0, 0)}
T0 = {"gear": 0.6, "wing": 1.1, "tail": 1.6, "canopy": 2.1, "prop": 2.5, "fuselage": 0}
DUR, FPS, TOTAL = 1.3, 24, 6.5
DARK = dict(bg_top="#1b1e22", bg_bot="#111316", ground_col="#24272c")


def ease(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * u * (u * (6 * u - 15) + 10)


def frame(mesh, zg, i):
    t = i / FPS
    spin = 0.0
    if t > 3.6:
        spin = 0.5 * 9.0 * (t - 3.6) ** 2 if t < 4.6 else 4.5 + 9.0 * (t - 4.6)
    R = np.array([[1, 0, 0], [0, math.cos(spin), -math.sin(spin)], [0, math.sin(spin), math.cos(spin)]])
    scene = {}
    for g, names in GROUPS.items():
        k = 0 if g == "fuselage" else 1 - ease((t - T0[g]) / DUR)
        d = np.array(OFF[g]) * k
        for n in names:
            m = mesh[n] @ R.T if g == "prop" and spin else mesh[n]
            scene[n] = m + d
    az = math.radians(-137 + 26 * t / TOTAL)
    dist = 19.5 - 4.5 * ease(min(t / 3.6, 1))
    tgt = np.array([3.6, 0.4, -0.25 + 0.4 * (1 - ease(min(t / 3.6, 1)))])
    eye = tgt + dist * np.array([math.cos(az) * 0.96, math.sin(az) * 0.96, 0.27])
    return render(scene, COLORS, eye=eye, target=tgt, fov=30, W=1280, H=720, ss=2, z_ground=zg,
                  extra_specular=SPEC, light_dir=(-0.35, -0.55, 0.76), **DARK)


def animate(mesh, zg):
    fdir = OUT / "frames"; fdir.mkdir(exist_ok=True)
    n = int(FPS * TOTAL)
    for i in range(n):
        Image.fromarray(frame(mesh, zg, i)).save(fdir / f"f{i:04d}.png")
    shutil.copy(fdir / f"f{n - 1:04d}.png", OUT / "assembly_still.png")
    if shutil.which("ffmpeg"):
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", str(fdir / "f%04d.png"), "-vf",
                        "tpad=stop_mode=clone:stop_duration=1.2,fade=t=in:st=0:d=0.4:color=0x16191d,"
                        "fade=t=out:st=7.1:d=0.6:color=0x16191d,format=yuv420p",
                        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-movflags", "+faststart",
                        str(OUT / "assembly.mp4")], check=True)
        shutil.rmtree(fdir)
        print("  wrote assembly.mp4")
    else:
        print("  ffmpeg not found: frames left in results/21_renders/frames")


def main():
    mesh, zg = mesh_of_v1()
    jobs = {"wing": (GROUPS["wing"], dict(W=2000, H=1000, dirv=(-0.40, -0.30, 0.86), fill=0.62)),
            "prop": (GROUPS["prop"], dict(fov=22, dirv=(-0.75, -0.55, 0.25))),
            "tail": (GROUPS["tail"], dict(dirv=(0.45, -0.8, 0.4))),
            "gear": (GROUPS["gear"], dict(dirv=(-0.6, -0.75, 0.2))),
            "fuselage": (GROUPS["fuselage"] + GROUPS["canopy"], dict(dirv=(-0.55, -0.8, 0.3)))}
    only = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not only or "stills" in only:
        for k, (names, kw) in jobs.items():
            still(mesh, zg, names, f"part_{k}.png", **kw)
    if not only or "layers" in only:
        layers(mesh, zg)
    if "--animate" in sys.argv:
        animate(mesh, zg)


if __name__ == "__main__":
    main()
