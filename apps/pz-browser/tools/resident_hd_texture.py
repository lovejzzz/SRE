"""Procedural textures for the high-detail resident, painted per texel.

Every garment reuses the body's UV layout, so one rasterised "position map"
(rest-pose position and normal behind each texel, MakeHuman decimetres, front
+Z) lets features be placed anatomically: lips, brows and stubble on the skin,
outseams, pockets, waistband and hems on the jeans, collar rib and hems on the
shirt, rubber sole and lacing on the shoes, strands radiating from the crown in
the hair. Fine fabric structure (jersey knit, denim twill) comes from the UVs.
"""
import os
import numpy as np
from PIL import Image

SKIN, GARMENT = 2048, 1024


def rasterize(uv_tris, attr_tris, size):
    """Barycentric fill of triangles in UV space; returns attributes image and coverage."""
    k = attr_tris.shape[2]
    img = np.zeros((size, size, k), np.float32); cover = np.zeros((size, size), bool)
    P = uv_tris * size
    for tri, attr in zip(P, attr_tris):
        x0, y0 = np.floor(tri.min(0)).astype(int); x1, y1 = np.ceil(tri.max(0)).astype(int)
        x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, size - 1), min(y1, size - 1)
        if x1 < x0 or y1 < y0:
            continue
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + .5, np.arange(y0, y1 + 1) + .5)
        (ax, ay), (bx, by), (cx, cy) = tri
        d = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
        if abs(d) < 1e-12:
            continue
        l1 = ((by - cy) * (xs - cx) + (cx - bx) * (ys - cy)) / d
        l2 = ((cy - ay) * (xs - cx) + (ax - cx) * (ys - cy)) / d
        l3 = 1 - l1 - l2
        inside = (l1 >= -.02) & (l2 >= -.02) & (l3 >= -.02)
        if not inside.any():
            continue
        vals = l1[..., None] * attr[0] + l2[..., None] * attr[1] + l3[..., None] * attr[2]
        sub = img[y0:y1 + 1, x0:x1 + 1]; sub[inside] = vals[inside]
        cover[y0:y1 + 1, x0:x1 + 1] |= inside
    return img, cover


def dilate(img, cover, steps=6):
    """Bleed edge texels outward so mip-mapping never pulls in black."""
    img = img.copy(); cover = cover.copy()
    for _ in range(steps):
        acc = np.zeros_like(img); n = np.zeros(cover.shape, np.float32)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            c = np.roll(cover, (dy, dx), (0, 1)); v = np.roll(img, (dy, dx), (0, 1))
            acc += v * c[..., None]; n += c
        grow = (~cover) & (n > 0)
        img[grow] = acc[grow] / n[grow, None]; cover |= grow
    return img


def hash3(ix, iy, iz, seed):
    h = (ix * 374761393 + iy * 668265263 + iz * 2147483647 + seed * 144269504) & 0xffffffff
    h = ((h ^ (h >> 13)) * 1274126177) & 0xffffffff
    return (h & 0xffff) / 65535.0


def noise3(p, freq, seed=1):
    q = p * freq; i = np.floor(q).astype(np.int64); f = q - i; f = f * f * (3 - 2 * f)
    out = 0
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                w = (f[..., 0] if dx else 1 - f[..., 0]) * (f[..., 1] if dy else 1 - f[..., 1]) * (f[..., 2] if dz else 1 - f[..., 2])
                out = out + w * hash3(i[..., 0] + dx, i[..., 1] + dy, i[..., 2] + dz, seed)
    return out


def fbm(p, freq, octaves=4, seed=1):
    s = 0; a = .5; t = 0
    for o in range(octaves):
        s += a * noise3(p, freq * 2 ** o, seed + o); t += a; a *= .5
    return s / t


def noise2(u, v, freq, seed=1):
    p = np.stack([u, v, np.zeros_like(u)], -1)
    return noise3(p, freq, seed)


def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)


def ellipsoid(p, c, r):
    return np.sqrt((((p - c) / r) ** 2).sum(-1))


def save(path, rgb, quality=90):
    Image.fromarray(np.clip(rgb * 255 + .5, 0, 255).astype(np.uint8)).save(path, quality=quality, optimize=True)


def position_map(rest, uvs, tris, uvt, size, normals):
    uv_tris = uvs[uvt].copy(); uv_tris[..., 1] = 1 - uv_tris[..., 1]
    attr = np.concatenate([rest[tris], normals[tris]], -1)
    img, cover = rasterize(uv_tris, attr, size)
    return img[..., :3], img[..., 3:], cover


def paint_all(out_dir, rest, uvs, tris, uvt, J):
    from resident_hd_dress import vertex_normals
    Nr = vertex_normals(rest, tris[:, [0, 2, 1]])
    pos, nrm, cover = position_map(rest, uvs, tris, uvt, SKIN, Nr)
    textures = {}
    textures['body'] = paint_skin(out_dir, pos, nrm, cover, J, rest)
    # Garments share the layout at lower resolution.
    small = lambda a: a[::SKIN // GARMENT, ::SKIN // GARMENT]
    gp, gn, gc = small(pos), small(nrm), small(cover)
    uu, vv = np.meshgrid((np.arange(GARMENT) + .5) / GARMENT, (np.arange(GARMENT) + .5) / GARMENT)
    textures['shirt'] = paint_shirt(out_dir, gp, gn, gc, uu, vv, J)
    textures['trousers'] = paint_jeans(out_dir, gp, gn, gc, uu, vv, J)
    textures['shoes'] = paint_shoes(out_dir, gp, gn, gc, uu, vv, J)
    textures['hair'] = paint_hair(out_dir, gp, gn, gc, uu, vv, J)
    textures['underwear'] = paint_briefs(out_dir, gp, gn, gc, uu, vv, J)
    textures['eyes'] = paint_eyes(out_dir)
    return textures


def paint_skin(out_dir, p, n, cover, J, rest):
    # Light-medium skin; low-frequency mottling, warmer ears/nose/cheeks/knuckles.
    base = np.array([.86, .69, .58])
    mott = fbm(p, .9, 4, 3) - .5; fine = noise3(p, 18, 9) - .5
    col = base * (1 + .07 * mott[..., None] + .025 * fine[..., None])
    red = np.array([.88, .55, .5])
    le, re, mouth = J['joint-l-eye'], J['joint-r-eye'], J['joint-mouth']
    nose_tip = rest[(np.abs(rest[:, 0]) < .1) & (rest[:, 1] > mouth[1]) & (rest[:, 1] < le[1])][:, 2].max()
    warm = np.zeros(p.shape[:2])
    for e in (le, re):
        warm = np.maximum(warm, 1 - smooth(.25, .75, ellipsoid(p, e + np.array([0, -.38, .1]), np.array([.45, .35, .5]))))
    warm = np.maximum(warm, 1 - smooth(.3, 1, ellipsoid(p, np.array([0, (le[1] + mouth[1]) / 2, nose_tip]), np.array([.22, .3, .3]))))
    ears = (np.abs(p[..., 0]) > .62) & (np.abs(p[..., 1] - le[1]) < .45) & (p[..., 2] < le[2])
    warm = np.maximum(warm, ears * .7)
    col = col * (1 - .25 * warm[..., None]) + red * .25 * warm[..., None]
    # Lips: band around the mouth joint, front facing.
    lip = (1 - smooth(.7, 1.0, ellipsoid(p, mouth + np.array([0, 0, .12]), np.array([.32, .12, .25])))) * (n[..., 2] > .2)
    col = col * (1 - .6 * lip[..., None]) + np.array([.7, .38, .37]) * .6 * lip[..., None]
    # Eyebrows: arched bands above each eye, slightly sparse at the tails.
    brow_col = np.array([.13, .1, .085]); brow = np.zeros(p.shape[:2])
    for e, s in ((le, 1), (re, -1)):
        dx = (p[..., 0] - e[0]) * s  # + towards the temple
        # Brow: from just inside the inner eye corner to past the outer corner; arched,
        # thicker at the head, thinning to the tail; ~2.3 cm above the eye centre.
        t = np.clip((dx + .17) / .5, 0, 1)
        arch = e[1] + .2 + .07 * np.sin(np.pi * np.clip(t * 1.1, 0, 1)) - .03 * t
        half = .032 * (1 - .5 * t)
        span = smooth(-.2, -.15, dx) * (1 - smooth(.3, .36, dx))
        band = (1 - smooth(half * .6, half, np.abs(p[..., 1] - arch))) * span * (n[..., 2] > .15)
        hairs = .35 + .65 * smooth(.35, .7, noise3(np.stack([p[..., 0] * 9 + p[..., 1] * 6, p[..., 1] * 90, p[..., 2] * 2], -1), 1.0, 7))
        brow = np.maximum(brow, band * hairs)
    col = col * (1 - .7 * brow[..., None]) + brow_col * .7 * brow[..., None]
    # Short stubble shadow on the upper lip, chin and jaw.
    jaw = (p[..., 1] < le[1] - .55) & (p[..., 1] > J['joint-neck'][1] + .25) & (p[..., 2] > J['joint-head'][2] - .25) & (lip < .2)
    stub = jaw * (1 - smooth(.6, .95, ellipsoid(p, mouth + np.array([0, -.15, -.2]), np.array([.75, .55, .9])))) * (.6 + .4 * noise3(p, 60, 4))
    col = col * (1 - .16 * stub[..., None]) + np.array([.3, .25, .22]) * .16 * stub[..., None]
    # Nails: pale, glossier tips on fingers and toes (dorsal, distal).
    bump = .5 + .18 * (noise3(p, 55, 11) - .5) + .1 * (noise3(p, 9, 12) - .5) - .25 * brow - .12 * stub * noise3(p, 120, 5)
    save(os.path.join(out_dir, 'skin.jpg'), dilate(col, cover))
    save(os.path.join(out_dir, 'skin-bump.jpg'), dilate(np.repeat(bump[..., None], 3, -1), cover))
    return {'map': 'skin.jpg', 'bumpMap': 'skin-bump.jpg', 'bumpScale': .6, 'roughness': .52, 'sheen': .25, 'sheenColor': [.9, .6, .5], 'kind': 'skin'}


def leg_angle(p, J):
    """Angle around each leg; 0 = outer side, pi = inner side."""
    side = np.sign(p[..., 0]); hip = np.where(side[..., None] > 0, J['joint-l-upper-leg'], J['joint-r-upper-leg'])
    dx = (p[..., 0] - hip[..., 0]) * side; dz = p[..., 2] - hip[..., 2]
    return np.arctan2(dz, dx)


def paint_jeans(out_dir, p, n, cover, u, v, J):
    pelvis_y = J['joint-pelvis'][1]; ankle = (J['joint-l-ankle'][1] + J['joint-r-ankle'][1]) / 2
    # 3/1 twill: diagonal ribs, white weft showing between indigo warp.
    # 3/1 twill at ~4 texels per rib (below that it aliases into moire).
    tw = .5 + .5 * np.sin((u + v) * 1600)
    slub = noise2(u, v * 9, 140, 2)
    indigo = np.array([.13, .19, .33]); weft = np.array([.62, .64, .68])
    col = indigo * (.85 + .3 * slub[..., None]) * tw[..., None] + (indigo * .55 + weft * .45) * (1 - tw[..., None])
    # Wear: lighter on thigh fronts, knees and seat; whiskers at the hips.
    fade = smooth(-.2, .8, n[..., 2]) * (1 - smooth(.6, 2.4, np.abs(p[..., 1] - (J['joint-l-knee'][1] + 1.6)))) * .22
    fade += (1 - smooth(.2, .7, np.abs(p[..., 1] - J['joint-l-knee'][1]))) * .2 * smooth(0, .8, n[..., 2])
    whisk = 0
    col = col + (np.array([.55, .62, .74]) - col) * np.clip(fade + whisk, 0, .6)[..., None]
    thread = np.array([.78, .55, .25]); stitch = np.zeros(u.shape)
    ang = leg_angle(p, J)
    leg = p[..., 1] < pelvis_y - .15
    dash = (np.sin(p[..., 1] * 260) > -.2)
    for target in (0.0, np.pi):  # outseam, inseam
        d = np.abs(np.angle(np.exp(1j * (ang - target))))
        stitch = np.maximum(stitch, leg * dash * ((np.abs(d - .06) < .018) | (np.abs(d + .06) < .018) | (np.abs(d - .1) < .015)))
    # Waistband with belt loops, hem band.
    top = pelvis_y + .6; band = (p[..., 1] > top - .42)
    stitch = np.maximum(stitch, dash * ((np.abs(p[..., 1] - (top - .42)) < .012) | (np.abs(p[..., 1] - (top - .06)) < .012)))
    loops = band * (np.abs(np.sin(np.arctan2(p[..., 2], p[..., 0]) * 3.5)) > .985)
    hem = p[..., 1] < ankle + .35 + .3
    stitch = np.maximum(stitch, dash * (np.abs(p[..., 1] - (ankle + .35 + .25)) < .012))
    # Back pockets (seat) and front pocket curves.
    for s in (1, -1):
        cx = s * .85; back = (n[..., 2] < -.2)
        box = back * (np.abs(p[..., 0] - cx) < .55) * (p[..., 1] < pelvis_y + .1) * (p[..., 1] > pelvis_y - .9)
        edge = box * ((np.abs(np.abs(p[..., 0] - cx) - .55) < .02) | (np.abs(p[..., 1] - (pelvis_y + .1)) < .02) | (np.abs(p[..., 1] - (pelvis_y - .9 + .35 * (1 - np.abs(p[..., 0] - cx) / .55))) < .02))
        stitch = np.maximum(stitch, edge * dash)
        front_curve = (n[..., 2] > .2) * (np.abs(np.hypot((p[..., 0] - s * 1.65) / .7, (p[..., 1] - top) / .75) - 1) < .03) * (p[..., 1] > pelvis_y - .3)
        stitch = np.maximum(stitch, front_curve)
    col = col * (1 - .9 * stitch[..., None]) + thread * .9 * stitch[..., None]
    col = col * (1 - .08 * band[..., None] - .06 * hem[..., None] - .25 * loops[..., None] * 0)
    bump = .5 + .25 * (tw - .5) + .15 * stitch - .1 * ((np.abs(p[..., 1] - (top - .42)) < .02) | loops)
    save(os.path.join(out_dir, 'jeans.jpg'), dilate(col, cover))
    save(os.path.join(out_dir, 'jeans-bump.jpg'), dilate(np.repeat(bump[..., None], 3, -1), cover))
    return {'map': 'jeans.jpg', 'bumpMap': 'jeans-bump.jpg', 'bumpScale': 1.2, 'roughness': .86, 'sheen': .3, 'sheenColor': [.35, .45, .65], 'kind': 'cloth'}


def paint_shirt(out_dir, p, n, cover, u, v, J):
    # Plain cotton jersey: knit columns of small V loops, heathered navy-grey.
    knit = .5 + .5 * np.sin(u * 1500) * np.sin(v * 2000 + np.sign(np.sin(u * 1500)) * 1.2)
    heather = noise2(u * 40, v * 6, 90, 3)
    base = np.array([.33, .39, .45])
    col = base * (.88 + .16 * heather[..., None] + .05 * knit[..., None])
    neck = J['joint-neck']; pelvis_y = J['joint-pelvis'][1]
    # Ribbed collar band and twin-needle hems at waist and sleeves.
    collar_d = p[..., 1] - (neck[1] - .25 - .45 * np.clip((p[..., 2] - neck[2]) / 1.0, 0, 1))
    collar = (collar_d > -.18)
    rib = (np.sin(np.arctan2(p[..., 2] - neck[2], p[..., 0]) * 160) > 0)
    col = col * (1 - .1 * collar[..., None]) + .03 * (collar * rib)[..., None]
    hem = (p[..., 1] < pelvis_y - .35 + .22)
    seam = (np.abs(p[..., 1] - (pelvis_y - .35 + .2)) < .012) | (np.abs(collar_d + .18) < .012)
    arm = np.abs(p[..., 0]) > 1.55
    for side in 'lr':
        s, e = J[f'joint-{side}-shoulder'], J[f'joint-{side}-elbow']
        ax = (e - s) / np.linalg.norm(e - s); t = ((p - s) @ ax) / np.linalg.norm(e - s)
        mine = np.sign(p[..., 0]) == (1 if side == 'l' else -1)
        seam |= mine & arm & (np.abs(t - .4) < .012)
        hem |= mine & arm & (t > .32)
        seam |= mine & (np.abs(t - .02) < .01) & (np.abs(p[..., 0]) > 1.3)  # set-in sleeve seam
    col = col * (1 - .06 * hem[..., None]) * (1 - .25 * seam[..., None])
    bump = .5 + .18 * (knit - .5) - .2 * seam + .08 * (collar * rib)
    save(os.path.join(out_dir, 'shirt.jpg'), dilate(col, cover))
    save(os.path.join(out_dir, 'shirt-bump.jpg'), dilate(np.repeat(bump[..., None], 3, -1), cover))
    return {'map': 'shirt.jpg', 'bumpMap': 'shirt-bump.jpg', 'bumpScale': .9, 'roughness': .92, 'sheen': .5, 'sheenColor': [.45, .55, .6], 'kind': 'cloth'}


def paint_shoes(out_dir, p, n, cover, u, v, J, size=512):
    """Shoe UVs are (length, angle from the bottom centre): sole band, welt, lacing, heel tab."""
    uu, vv = np.meshgrid((np.arange(size) + .5) / size, (np.arange(size) + .5) / size)
    ang = vv * 2 * np.pi  # 0 = bottom centre
    low = np.cos(ang)  # 1 at the bottom
    sole = low > .62
    tread = sole & (np.sin(uu * 180) > .2) & (low > .9)
    pos3 = np.stack([uu * 4, vv * 4, np.zeros_like(uu)], -1)
    leather = np.array([.19, .17, .155]) * (.9 + .2 * noise3(pos3, 40, 5)[..., None])
    col = np.where(sole[..., None], np.array([.84, .82, .78]) * (1 - .3 * tread[..., None]), leather)
    welt = np.abs(low - .62) < .03
    stitch = (np.abs(low - .5) < .012) & (np.sin(uu * 900) > 0)
    top = np.abs(vv - .5) < .09
    lace_zone = top & (uu > .42) & (uu < .8)
    laces = lace_zone & (np.sin(uu * 110) > .45)
    eyelets = lace_zone & (np.abs(np.abs(vv - .5) - .075) < .012) & (np.sin(uu * 110 + 1.4) > .9)
    col = np.where(lace_zone[..., None], np.array([.13, .12, .11]), col)
    col = np.where(laces[..., None], np.array([.86, .85, .82]), col)
    col = np.where(eyelets[..., None], np.array([.55, .55, .55]), col)
    heel = (uu < .1) & (low < 0)
    col = col * (1 - .35 * welt[..., None]) * (1 - .3 * stitch[..., None]) * (1 - .15 * heel[..., None])
    bump = .5 + .15 * (noise3(pos3, 80, 2) - .5) - .3 * welt + .3 * laces - .25 * tread - .15 * stitch
    save(os.path.join(out_dir, 'shoes.jpg'), col)
    save(os.path.join(out_dir, 'shoes-bump.jpg'), np.repeat(bump[..., None], 3, -1))
    return {'map': 'shoes.jpg', 'bumpMap': 'shoes-bump.jpg', 'bumpScale': .8, 'roughness': .62, 'kind': 'leather'}


def paint_hair(out_dir, p, n, cover, u, v, J):
    from resident_hd_dress import hairline
    crown = J['joint-head'] + np.array([0, 1.35, -.45])
    d = p - crown; az = np.arctan2(d[..., 2], d[..., 0]); el = np.linalg.norm(d, axis=-1)
    strands = noise3(np.stack([np.cos(az) * 40, np.sin(az) * 40, el * 2], -1), 1.0, 8)
    fine = noise3(np.stack([np.cos(az) * 220, np.sin(az) * 220, el * 6], -1), 1.0, 9)
    base = np.array([.075, .06, .05])
    col = base * (.7 + .5 * strands[..., None] + .35 * fine[..., None])
    col += np.array([.05, .04, .03]) * smooth(.55, .9, fine)[..., None]
    # Soft, irregular hairline: alpha from the distance above the hairline, broken by strands.
    above = p[..., 1] - hairline(p, J)
    edge = above + .09 * (fine - .5) + .05 * (strands - .5)
    alpha = smooth(-.02, .05, edge)
    bump = .5 + .35 * (fine - .5) + .2 * (strands - .5)
    rgba = np.concatenate([dilate(col, cover), dilate(alpha[..., None], cover)], -1)
    Image.fromarray(np.clip(rgba * 255 + .5, 0, 255).astype(np.uint8), 'RGBA').save(os.path.join(out_dir, 'hair.png'), optimize=True)
    save(os.path.join(out_dir, 'hair-bump.jpg'), dilate(np.repeat(bump[..., None], 3, -1), cover))
    return {'map': 'hair.png', 'bumpMap': 'hair-bump.jpg', 'bumpScale': 1.5, 'roughness': .48, 'sheen': .6, 'sheenColor': [.3, .25, .2], 'alphaTest': .5, 'kind': 'hair'}


def paint_eyes(out_dir, size=256):
    y, x = np.mgrid[0:size, 0:size] / size - .5
    r = np.hypot(x, y) * 2; a = np.arctan2(y, x)
    sclera = np.array([.93, .9, .86]) * (1 - .15 * smooth(.6, 1, r))[..., None]
    fibres = .5 + .5 * np.sin(a * 60 + 4 * noise2(x * 3, y * 3, 6, 2))
    iris = np.array([.24, .15, .09]) * (.7 + .5 * fibres[..., None]) * (1 - .4 * smooth(.2, .32, r))[..., None]
    col = np.where((r < .33)[..., None], iris, sclera)
    col = np.where((r < .13)[..., None], np.array([.02, .02, .02]), col)
    limbal = (np.abs(r - .33) < .025)
    col = col * (1 - .5 * limbal[..., None])
    save(os.path.join(out_dir, 'eye.jpg'), col)
    return {'map': 'eye.jpg', 'roughness': .08, 'clearcoat': 1, 'kind': 'eye'}


def paint_briefs(out_dir, p, n, cover, u, v, J):
    knit = .5 + .5 * np.sin(u * 1500) * np.sin(v * 2000)
    col = np.array([.16, .16, .17]) * (.9 + .1 * knit[..., None])
    band = p[..., 1] > J['joint-pelvis'][1] + .05
    col = np.where(band[..., None], np.array([.32, .32, .34]), col)
    save(os.path.join(out_dir, 'briefs.jpg'), dilate(col, cover))
    return {'map': 'briefs.jpg', 'roughness': .9, 'sheen': .4, 'sheenColor': [.4, .4, .45], 'kind': 'cloth'}
