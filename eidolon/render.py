"""Small deferred software renderer (numpy only) for studio images of the OML mesh.

Z-buffered triangle rasterisation with smooth (crease-aware) normals, a shadow map from the key
light onto the aircraft and a ground plane, Blinn-Phong key + fill + sky lighting, a soft contact
shadow and 2x supersampling. Enough for README/deck images without Blender.
"""
from __future__ import annotations

import math

import numpy as np


def _hex(c):
    c = c.lstrip("#")
    return np.array([int(c[i:i + 2], 16) / 255 for i in (0, 2, 4)])


def smooth_normals(tris, crease_deg=42.0):
    """Per-corner normals averaged over faces sharing the vertex within the crease angle."""
    v = tris.reshape(-1, 3)
    fn = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    area = np.linalg.norm(fn, axis=1, keepdims=True)
    fnu = fn / np.maximum(area, 1e-12)
    corner_fn = np.repeat(fnu, 3, axis=0)
    corner_fw = np.repeat(fn, 3, axis=0)
    keys = np.round(v / 2e-4).astype(np.int64)
    _, inv = np.unique(keys, axis=0, return_inverse=True)
    inv = inv.ravel()
    order = np.argsort(inv)
    bounds = np.flatnonzero(np.diff(inv[order])) + 1
    groups = np.split(order, bounds)
    out = corner_fn.copy()
    cth = math.cos(math.radians(crease_deg))
    for g in groups:
        if len(g) < 2:
            continue
        n = corner_fn[g]
        sim = n @ n.T > cth
        acc = sim.astype(float) @ corner_fw[g]
        out[g] = acc / np.maximum(np.linalg.norm(acc, axis=1, keepdims=True), 1e-12)
    return out.reshape(-1, 3, 3), fnu


def look_at(eye, target, up=(0, 0, 1)):
    eye, target, up = map(np.asarray, (eye, target, up))
    f = target - eye; f = f / np.linalg.norm(f)
    r = np.cross(f, up); r /= np.linalg.norm(r)
    u = np.cross(r, f)
    return np.stack([r, u, -f]), eye


def rasterise(tris, view, eye, W, H, fov_deg=None, ortho_halfh=None, attrs=None):
    """Returns depth buffer and, per pixel, the triangle id and barycentrics."""
    cam = (tris - eye) @ view.T                       # camera space, -z forward
    if ortho_halfh is None:
        f = 1 / math.tan(math.radians(fov_deg) / 2)
        z = -cam[..., 2]
        sx = (cam[..., 0] * f / z) * (H / 2) + W / 2
        sy = -(cam[..., 1] * f / z) * (H / 2) + H / 2
    else:
        z = -cam[..., 2]
        sx = cam[..., 0] / ortho_halfh * (H / 2) + W / 2
        sy = -cam[..., 1] / ortho_halfh * (H / 2) + H / 2
    depth = np.full((H, W), np.inf); tid = np.full((H, W), -1, np.int64)
    b0 = np.zeros((H, W)); b1 = np.zeros((H, W))
    xmin = np.clip(np.floor(sx.min(1)), 0, W - 1).astype(int); xmax = np.clip(np.ceil(sx.max(1)), 0, W - 1).astype(int)
    ymin = np.clip(np.floor(sy.min(1)), 0, H - 1).astype(int); ymax = np.clip(np.ceil(sy.max(1)), 0, H - 1).astype(int)
    for i in np.flatnonzero((z.min(1) > 0.05) & (xmax >= xmin) & (ymax >= ymin)):
        x0, x1, y0, y1 = xmin[i], xmax[i], ymin[i], ymax[i]
        px, py = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        ax, ay, bx, by, cx, cy = sx[i, 0], sy[i, 0], sx[i, 1], sy[i, 1], sx[i, 2], sy[i, 2]
        den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
        if abs(den) < 1e-12:
            continue
        l0 = ((by - cy) * (px - cx) + (cx - bx) * (py - cy)) / den
        l1 = ((cy - ay) * (px - cx) + (ax - cx) * (py - cy)) / den
        l2 = 1 - l0 - l1
        m = (l0 >= -1e-6) & (l1 >= -1e-6) & (l2 >= -1e-6)
        if not m.any():
            continue
        if ortho_halfh is None:   # perspective-correct depth
            zz = 1 / (l0 / z[i, 0] + l1 / z[i, 1] + l2 / z[i, 2])
        else:
            zz = l0 * z[i, 0] + l1 * z[i, 1] + l2 * z[i, 2]
        sub = depth[y0:y1 + 1, x0:x1 + 1]
        upd = m & (zz < sub)
        if upd.any():
            sub[upd] = zz[upd]
            tid[y0:y1 + 1, x0:x1 + 1][upd] = i
            b0[y0:y1 + 1, x0:x1 + 1][upd] = l0[upd]
            b1[y0:y1 + 1, x0:x1 + 1][upd] = l1[upd]
    return depth, tid, b0, b1


def render(parts: dict, colors: dict, eye, target, W=1600, H=1000, fov=26.0, ss=2, z_ground=-1.3,
           bg_top="#f6f7f8", bg_bot="#e3e7ea", light_dir=(-0.35, -0.55, 0.76), extra_specular=None,
           ground=True, ground_col="#d9dde0", alpha=False):
    names = list(parts)
    tris = np.concatenate([parts[k] for k in names])
    pid = np.concatenate([np.full(len(parts[k]), i) for i, k in enumerate(names)])
    # ground plane
    g = 30.0
    gq = np.array([[[-g, -g, z_ground], [g, -g, z_ground], [g, g, z_ground]],
                   [[-g, -g, z_ground], [g, g, z_ground], [-g, g, z_ground]]])
    tris_all = tris; pid_all = pid
    cn, fn = smooth_normals(tris)
    w, h = W * ss, H * ss
    view, e = look_at(eye, target)
    depth, tid, b0, b1 = rasterise(tris_all, view, e, w, h, fov)
    hit_ac = tid >= 0
    t = np.where(hit_ac, tid, 0)
    l2 = 1 - b0 - b1
    # world position & normal (affine barycentrics are adequate at this scale)
    P = tris_all[t, 0] * b0[..., None] + tris_all[t, 1] * b1[..., None] + tris_all[t, 2] * l2[..., None]
    N = cn[t, 0] * b0[..., None] + cn[t, 1] * b1[..., None] + cn[t, 2] * l2[..., None]
    # analytic ground plane for the pixels that missed the aircraft
    f_ = 1 / math.tan(math.radians(fov) / 2)
    px, py = np.meshgrid((np.arange(w) + 0.5 - w / 2) / (h / 2) / f_, -(np.arange(h) + 0.5 - h / 2) / (h / 2) / f_)
    dirs = np.stack([px, py, -np.ones_like(px)], -1) @ view            # camera -> world
    tg = (z_ground - e[2]) / np.where(np.abs(dirs[..., 2]) > 1e-9, dirs[..., 2], -1e-9)
    gm = (~hit_ac) & (tg > 0) & ground
    Pg = e + dirs * tg[..., None]
    P = np.where(gm[..., None], Pg, P)
    N = np.where(gm[..., None], np.array([0, 0, 1.0]), N)
    hit = hit_ac | gm
    pid_all = np.concatenate([pid_all, [-2]])
    t = np.where(gm, len(pid_all) - 1, t)
    N /= np.maximum(np.linalg.norm(N, axis=-1, keepdims=True), 1e-9)
    V = e - P; V /= np.maximum(np.linalg.norm(V, axis=-1, keepdims=True), 1e-9)
    flip = (N * V).sum(-1) < 0
    N[flip] *= -1
    # shadow map (orthographic, from the light)
    L = np.asarray(light_dir, float); L /= np.linalg.norm(L)
    sview, seye = look_at(target + L * 20, target, up=(1, 0, 0) if abs(L[2]) > 0.95 else (0, 0, 1))
    S = 2048
    sdepth, _, _, _ = rasterise(tris, sview, seye, S, S, ortho_halfh=7.0)
    cam = (P - seye) @ sview.T
    sx = np.clip((cam[..., 0] / 7.0 * (S / 2) + S / 2).astype(int), 0, S - 1)
    sy = np.clip((-cam[..., 1] / 7.0 * (S / 2) + S / 2).astype(int), 0, S - 1)
    dz = -cam[..., 2]
    shadow = np.zeros((h, w))
    for ox, oy in ((0, 0), (3, 0), (-3, 0), (0, 3), (0, -3), (3, 3), (-3, -3), (3, -3), (-3, 3)):   # PCF
        ref = sdepth[np.clip(sy + oy, 0, S - 1), np.clip(sx + ox, 0, S - 1)]
        shadow += (dz > ref + 0.02)
    lit = 1 - shadow / 9
    # albedo
    pal = np.array([_hex(colors.get(k, "#dddddd")) for k in names] + [_hex(ground_col)])
    pidp = np.where(gm, -2, pid_all[np.where(hit_ac, tid, 0)])
    A = np.where((pidp == -2)[..., None], pal[-1], pal[np.clip(pidp, 0, len(names) - 1)])
    spec_k = np.full((h, w), 0.35); shin = np.full((h, w), 60.0)
    for k, (ks, sh) in (extra_specular or {}).items():
        if k in names:
            m = pidp == names.index(k); spec_k[m] = ks; shin[m] = sh
    ndl = np.clip((N * L).sum(-1), 0, 1)
    Hh = L + V; Hh /= np.linalg.norm(Hh, axis=-1, keepdims=True)
    spec = spec_k * np.clip((N * Hh).sum(-1), 0, 1) ** shin
    fill_d = np.array([0.6, 0.7, 0.25]); fill_d /= np.linalg.norm(fill_d)
    fill = 0.22 * np.clip((N * fill_d).sum(-1), 0, 1)
    sky = 0.30 + 0.18 * N[..., 2]
    fres = (1 - np.clip((N * V).sum(-1), 0, 1)) ** 4 * 0.25
    col = A * (sky[..., None] + fill[..., None] + 0.78 * (ndl * lit)[..., None]) + (spec * lit)[..., None] + fres[..., None]
    col[gm] = (A * (0.97 - 0.30 * (1 - lit)[..., None]))[gm]
    # background gradient, ground fades into it with distance
    yy = np.linspace(0, 1, h)[:, None, None]
    bg = _hex(bg_top) * (1 - yy) + _hex(bg_bot) * yy
    bg = np.broadcast_to(bg, (h, w, 3))
    dist = np.linalg.norm(P[..., :2] - np.asarray(target)[:2], axis=-1)
    fade = np.clip((dist - 5.0) / 9.0, 0, 1)[..., None]
    out = np.where(hit[..., None], col, bg)
    out = np.where(gm[..., None], out * (1 - fade) + bg * fade, out)
    out = np.clip(out, 0, 1) ** (1 / 1.12)
    if alpha:
        # transparent background: premultiplied average over the super-samples (study 21)
        a = hit_ac.astype(float)
        rgb = (out * a[..., None]).reshape(H, ss, W, ss, 3).sum(axis=(1, 3))
        A = a.reshape(H, ss, W, ss).sum(axis=(1, 3))
        rgb = rgb / np.maximum(A, 1e-9)[..., None]
        return (np.dstack([rgb, A / (ss * ss)]) * 255).astype(np.uint8)
    out = out.reshape(H, ss, W, ss, 3).mean(axis=(1, 3))
    return (out * 255).astype(np.uint8)
