"""Mesh assembly, clothing shells and export for the high-detail resident.

Clothes are shells of the body surface (so they carry the body's exact skin
weights and never drift away from it under animation): offset along normals,
relaxed with Laplacian smoothing so anatomy reads through as fabric rather than
skin, and kept a minimum distance outside the body. Textures are painted per
texel from the rest-pose 3D position behind each texel (resident_hd_texture.py).
"""
import json, os, struct
import numpy as np
from resident_hd_texture import paint_all

UNITS_PER_METRE = 0.98 / 1.8  # Bip01 bind height 0.98 units renders as 1.8 m in the 3D view
EYES = ('helper-l-eye', 'helper-r-eye')


def body_tris(faces, group):
    tris, uvt = [], []
    for g, vi, ti in faces:
        if g != group:
            continue
        for k in range(1, len(vi) - 1):
            tris.append((vi[0], vi[k + 1], vi[k])); uvt.append((ti[0], ti[k + 1], ti[k]))
    return np.array(tris), np.array(uvt)


def vertex_normals(P, tris):
    n = np.zeros_like(P)
    fn = np.cross(P[tris[:, 1]] - P[tris[:, 0]], P[tris[:, 2]] - P[tris[:, 0]])
    for k in range(3):
        np.add.at(n, tris[:, k], fn)
    l = np.linalg.norm(n, axis=1); l[l == 0] = 1
    return n / l[:, None]


def neighbours(tris, count):
    nb = [set() for _ in range(count)]
    for a, b, c in tris:
        nb[a].update((b, c)); nb[b].update((a, c)); nb[c].update((a, b))
    return nb


def boundary_vertices(tris):
    edges = {}
    for t in tris:
        for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
            k = (min(a, b), max(a, b)); edges[k] = edges.get(k, 0) + 1
    return {v for k, n in edges.items() if n == 1 for v in k}


def local_mesh(select, tris, uvt, P, weights, uvs):
    """Region of the body as its own mesh: positions, per-vertex weights, per-corner UVs."""
    keep = select[tris].all(1)
    t, u = tris[keep], uvt[keep]
    ids = np.unique(t); remap = {int(v): k for k, v in enumerate(ids)}
    T = np.vectorize(remap.get)(t)
    return {'P': P[ids].copy(), 'W': [dict(weights[i]) for i in ids], 'src': ids, 'T': T, 'UV': uvs[u].astype(float)}


def subdivide(m):
    """One 1->4 midpoint split; weights and UVs interpolate, positions get one smoothing pass later."""
    P = list(m['P']); W = list(m['W']); src = list(m['src']); mid = {}; T = []; UV = []
    def edge(a, b):
        k = (min(a, b), max(a, b))
        if k not in mid:
            mid[k] = len(P); P.append((m['P'][a] + m['P'][b]) / 2)
            w = {}
            for d in (W[a], W[b]):
                for bone, x in d.items(): w[bone] = w.get(bone, 0) + x / 2
            W.append(w); src.append(-1)
        return mid[k]
    for (a, b, c), (ua, ub, uc) in zip(m['T'], m['UV']):
        ab, bc, ca = edge(a, b), edge(b, c), edge(c, a)
        uab, ubc, uca = (ua + ub) / 2, (ub + uc) / 2, (uc + ua) / 2
        T += [(a, ab, ca), (ab, b, bc), (ca, bc, c), (ab, bc, ca)]
        UV += [(ua, uab, uca), (uab, ub, ubc), (uca, ubc, uc), (uab, ubc, uca)]
    return {'P': np.array(P), 'W': W, 'src': np.array(src), 'T': np.array(T), 'UV': np.array(UV)}


def laplacian(P, T, iters, lam=.5, border_scale=.5):
    nb = neighbours(T, len(P)); lists = [np.array(sorted(x), dtype=int) for x in nb]
    border = boundary_vertices(T); l = np.array([lam * border_scale if i in border else lam for i in range(len(P))])
    Q = P.copy()
    for _ in range(iters):
        mean = np.array([Q[k].mean(0) if len(k) else Q[i] for i, k in enumerate(lists)])
        Q = Q + l[:, None] * (mean - Q)
    return Q, lists, l


def relax_shell(m, base_n, offset, iters, minimum, push=None, base_iters=20, skin_clearance=.0025 * 0.98 / 1.8, border_scale=.5):
    """Offset from a smoothed copy of the body (so nipples, toes and muscle grooves vanish under
    the fabric), relax, and keep clear of both the smoothed surface and the real skin."""
    T = m['T']; P = m['P']
    NP = vertex_normals(P, T)
    B, lists, lam = laplacian(P, T, base_iters, border_scale=border_scale)
    NB = vertex_normals(B, T)
    off = offset(m) if callable(offset) else np.full(len(P), offset)
    Q = B + NB * off[:, None]
    if push is not None:
        push(Q, m)
    for _ in range(iters):
        mean = np.array([Q[k].mean(0) if len(k) else Q[i] for i, k in enumerate(lists)])
        Q = Q + lam[:, None] * (mean - Q)
        d = ((Q - B) * NB).sum(1); low = d < minimum
        Q[low] += (minimum - d[low])[:, None] * NB[low]
        d = ((Q - P) * NP).sum(1); low = d < skin_clearance
        Q[low] += (skin_clearance - d[low])[:, None] * NP[low]
    Q = smooth_boundaries(Q, T, iters=25)
    m = dict(m); m['P'] = Q
    return m


def smooth_boundaries(Q, T, iters=25):
    """Clean hem/neck/cuff lines: relax each open boundary loop along itself."""
    edges = {}
    for t in T:
        for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
            k = (min(a, b), max(a, b)); edges[k] = edges.get(k, 0) + 1
    nb = {}
    for (a, b), n in edges.items():
        if n == 1:
            nb.setdefault(a, []).append(b); nb.setdefault(b, []).append(a)
    ring = np.array([v for v, l in nb.items() if len(l) == 2], dtype=int)
    if not len(ring):
        return Q
    left = np.array([nb[v][0] for v in ring]); right = np.array([nb[v][1] for v in ring])
    Q = Q.copy()
    for _ in range(iters):
        Q[ring] += .5 * ((Q[left] + Q[right]) / 2 - Q[ring])
    return Q


def weights_payload(weights, src, bind):
    by_bone = {}
    for gpu, v in enumerate(src):
        for bone, w in weights[v]:
            by_bone.setdefault(bone, ([], []))
            by_bone[bone][0].append(gpu); by_bone[bone][1].append(w)
    return [{'bone': b, 'indices': ix, 'weights': ws, 'inverse': bind[b]['inverse']} for b, (ix, ws) in sorted(by_bone.items())]


def unweld_local(m):
    VN = vertex_normals(m['P'], m['T'])
    key = {}; pos = []; uv = []; W = []; index = []; nrm = []
    for vs, uvs3 in zip(m['T'], m['UV']):
        for v, t in zip(vs, uvs3):
            k = (int(v), round(float(t[0]), 6), round(float(t[1]), 6))
            if k not in key:
                key[k] = len(pos); pos.append(m['P'][v]); uv.append(t); W.append(m['W'][v]); nrm.append(VN[v])
            index.append(key[k])
    return np.array(pos, dtype=np.float32), np.array(uv, dtype=np.float32), W, np.array(index, dtype=np.uint32), np.array(nrm, dtype=np.float32)


def skin_arrays(W, bone_names):
    """Top four influences per vertex as (u32 bone slots, f32 weights), normalised."""
    slot = {b: i for i, b in enumerate(bone_names)}
    index = np.zeros((len(W), 4), np.uint32); weight = np.zeros((len(W), 4), np.float32)
    for v, d in enumerate(W):
        top = sorted(d.items(), key=lambda kv: -kv[1])[:4]; s = sum(x for _, x in top) or 1
        for k, (bone, x) in enumerate(top):
            index[v, k] = slot[bone]; weight[v, k] = x / s
        if not top: weight[v, 0] = 1
    return index, weight


class Bin:
    def __init__(self):
        self.chunks = []; self.size = 0

    def add(self, array):
        data = np.ascontiguousarray(array).tobytes()
        pad = (-len(data)) % 4
        ref = {'offset': self.size, 'length': len(data), 'type': {np.dtype('float32'): 'f32', np.dtype('uint32'): 'u32'}[array.dtype]}
        self.chunks.append(data + b'\0' * pad); self.size += len(data) + pad
        return ref


def shoe_mesh(P, side_x, s, foot_bone, calf_bone, m, ankle_y, slices=40, ring=48):
    """A lofted sneaker for one foot: superellipse sections sized from the foot's own extent
    in each slice (+ upper allowance), flat sole, rounded heel and toe, open collar."""
    ix = np.nonzero(np.sign(side_x) == s)[0]; F = P[ix]
    c = F.mean(0); d = F[:, [0, 2]] - c[[0, 2]]
    w, V = np.linalg.eigh(d.T @ d); ax2 = V[:, np.argmax(w)]
    axis = np.array([ax2[0], 0, ax2[1]]); axis /= np.linalg.norm(axis)
    if axis[2] > 0: axis = -axis
    lat = np.cross([0, 1, 0], axis); lat /= np.linalg.norm(lat)
    t = (F - c) @ axis; a = (F - c) @ lat; h = F[:, 1]
    t0, t1 = t.min() - .01 * m, t.max() + .02 * m
    floor = 0.0; allowance = .007 * m
    ts = np.linspace(t0, t1, slices)
    prof = []
    for k, tk in enumerate(ts):
        sel = np.abs(t - tk) < (t1 - t0) / slices * 1.6
        if sel.sum() < 3:
            sel = np.argsort(np.abs(t - tk))[:6]
        lo, hi = a[sel].min() - allowance, a[sel].max() + allowance
        low = sel & (h < ankle_y + .004) if sel.dtype == bool else sel
        top = (h[low].max() if np.any(low) else h[sel].min() + .02) + allowance
        prof.append([(lo + hi) / 2, (hi - lo) / 2, top])
    prof = np.array(prof)
    for _ in range(4):  # smooth the profile along the length
        prof[1:-1] = .25 * prof[:-2] + .5 * prof[1:-1] + .25 * prof[2:]
    u = (ts - t0) / (t1 - t0)
    # Never taller than the collar (just above the ankle joint); toe box stays low.
    prof[:, 2] = np.minimum(prof[:, 2], ankle_y + .012)
    # Round heel and toe in plan: circular ends.
    toe = np.clip((u - .84) / .16, 0, 1); heel = np.clip((.08 - u) / .08, 0, 1)
    prof[:, 1] *= np.sqrt(1 - toe ** 2 * .55) * np.sqrt(1 - heel ** 2 * .45)
    prof[:, 2] = floor + (prof[:, 2] - floor) * (.35 + .65 * np.sqrt(1 - toe ** 2)) * (.6 + .4 * np.sqrt(1 - heel ** 2))
    collar_t = t.min() + .4 * (t.max() - t.min()); collar_top = ankle_y + .012
    verts = []; uvs = []; W = []
    for k, tk in enumerate(ts):
        cx, hw, top = prof[k]; centre = c + axis * tk + lat * cx
        hh = (top - floor) / 2; cy = floor + hh
        for j in range(ring + 1):
            th = -np.pi / 2 + 2 * np.pi * j / ring  # start at the bottom centre
            co, si = np.cos(th), np.sin(th)
            ex = 2 / 3.2
            px = np.sign(co) * abs(co) ** ex * hw; py = np.sign(si) * abs(si) ** (ex if si > 0 else .35) * hh
            p = np.array([centre[0], cy + py, centre[2]]) + lat * px
            p[1] = max(p[1], floor)
            if tk < collar_t:
                p[1] = min(p[1], max(collar_top, floor + .02 * m))
            verts.append(p); uvs.append((u[k], j / ring))
            wc = .35 * np.clip((p[1] - (collar_top - .03 * m)) / (.03 * m), 0, 1) if tk < collar_t + .02 * m else 0
            W.append({foot_bone: 1 - wc, calf_bone: wc} if wc > 0 else {foot_bone: 1.0})
    T = []; UVT = []
    R = ring + 1
    for k in range(slices - 1):
        for j in range(ring):
            a0, a1, b0, b1 = k * R + j, k * R + j + 1, (k + 1) * R + j, (k + 1) * R + j + 1
            # Collar opening: skip the upper sections behind the collar line.
            vv = j / ring
            if ts[k] < collar_t and .35 < vv < .65:
                continue
            for tri in ((a0, b0, a1), (a1, b0, b1)) if s > 0 else ((a0, a1, b0), (a1, b1, b0)):
                T.append(tri); UVT.append([uvs[i] for i in tri])
    # Close the toe and heel with fans.
    verts = np.array(verts)
    for k, flip in ((0, s > 0), (slices - 1, s < 0)):
        cidx = len(verts); centre = verts[k * R:k * R + ring].mean(0) + axis * (1 if k else -1) * prof[k, 1] * .55
        verts = np.vstack([verts, centre]); W.append(W[k * R]); uvs.append((u[k], .5))
        for j in range(ring):
            tri = (cidx, k * R + j, k * R + j + 1) if (flip ^ (k == 0)) else (cidx, k * R + j + 1, k * R + j)
            T.append(tri); UVT.append([uvs[i] for i in tri])
    T = np.array(T); UVT = np.array(UVT, dtype=float)
    # Outward winding for either foot: a closed-ish shell must have positive signed volume.
    a_, b_, c_ = verts[T[:, 0]], verts[T[:, 1]], verts[T[:, 2]]
    if np.einsum('ij,ij->i', a_ - verts.mean(0), np.cross(b_ - a_, c_ - a_)).sum() < 0:
        T = T[:, [0, 2, 1]]; UVT = UVT[:, [0, 2, 1]]
    return {'P': verts, 'W': W, 'T': T, 'UV': UVT}


def hairline(p, J):
    """Rest-pose hairline height for each point (MakeHuman dm): forehead, temples, nape."""
    eye_y = (J['joint-l-eye'][1] + J['joint-r-eye'][1]) / 2
    front = np.clip((p[..., 2] - J['joint-head'][2]) / 1.0, -1, 1)
    side = np.clip(np.abs(p[..., 0]) / .7, 0, 1)
    return np.where(front > 0, eye_y + .62 - .1 * side ** 2 + .04 * front, eye_y + .55 - 1.05 * np.clip(-front, 0, 1) - .08 * side)


def dress_and_export(args, rest, posed, uvs, faces, groups, joint, weights, character, bind, scale):
    os.makedirs(args.out, exist_ok=True)
    tris, uvt = body_tris(faces, 'body')
    count = len(posed)
    J = joint
    m = UNITS_PER_METRE
    wsum = lambda v, names: sum(dict(weights[v]).get(n, 0) for n in names)
    arm_bones = [f'Bip01_{s}_{b}' for s in 'LR' for b in ('UpperArm', 'Forearm', 'Hand', 'Finger0', 'Finger1')]
    leg_bones = [f'Bip01_{s}_{b}' for s in 'LR' for b in ('Thigh', 'Calf', 'Foot')]
    head_w = np.array([wsum(v, ['Bip01_Head', 'Bip01_Neck']) for v in range(count)])
    arm_w = np.array([wsum(v, arm_bones) for v in range(count)])
    leg_w = np.array([wsum(v, leg_bones) for v in range(count)])
    x, y, z = rest[:, 0], rest[:, 1], rest[:, 2]
    pelvis_y, neck_y = J['joint-pelvis'][1], J['joint-neck'][1]
    ankle_y = (J['joint-l-ankle'][1] + J['joint-r-ankle'][1]) / 2
    knee_y = (J['joint-l-knee'][1] + J['joint-r-knee'][1]) / 2
    sleeve = np.zeros(count, bool)
    for side in 'lr':
        s0, e0 = J[f'joint-{side}-shoulder'], J[f'joint-{side}-elbow']
        axis = (e0 - s0) / np.linalg.norm(e0 - s0)
        t = (rest - s0) @ axis / np.linalg.norm(e0 - s0)
        sleeve |= (np.sign(x) == (1 if side == 'l' else -1)) & (t < .45)
    neck_line = neck_y - .25 - .45 * np.clip((z - J['joint-neck'][2]) / 1.0, 0, 1)
    in_body = np.zeros(count, bool); in_body[np.unique(tris)] = True
    hem_y = pelvis_y - .45; waist_y = pelvis_y + .55
    shirt_sel = in_body & (y >= hem_y) & (y < neck_line) & (head_w < .5) & ((arm_w < .5) | sleeve) & ((leg_w < .5) | (y > hem_y))
    brief_sel = in_body & (y <= pelvis_y + .25) & (y >= pelvis_y - 1.15) & (arm_w < .5) & ~((leg_w > .5) & (y < pelvis_y - .55 - .5 * (np.abs(x) > .2)))
    jeans_sel = in_body & (y <= waist_y) & (y >= ankle_y + .35) & (arm_w < .5)
    shoe_sel = in_body & (y <= ankle_y + .45) & (arm_w < .5)
    eye_y = (J['joint-l-eye'][1] + J['joint-r-eye'][1]) / 2
    front = np.clip((z - J['joint-head'][2]) / 1.0, -1, 1)
    hair_line = hairline(rest, J) - .22
    ear = (np.abs(x) > .64) & (y < eye_y + .12) & (front > -.75)
    hair_sel = in_body & (head_w > .5) & (y > hair_line) & ~ear
    in_overlap = lambda P_rest_y: (P_rest_y >= hem_y - .1) & (P_rest_y <= waist_y + .1)

    # Rest-pose y of each local vertex (for bands), carried through subdivision by averaging.
    def build(select, levels, offset, iters, minimum, push=None, base_iters=20, clearance=.0025, border_scale=.5):
        lm = local_mesh(select, tris, uvt, posed, weights, uvs)
        lm['ry'] = rest[lm['src'], 1]; lm['rx'] = rest[lm['src'], 0]
        for _ in range(levels):
            parent = lm; lm = subdivide(lm)
            ry = list(parent['ry']); rx = list(parent['rx'])
            # midpoints: recompute from position order (subdivide appends edges after originals)
            extra = len(lm['P']) - len(parent['P'])
            mids = {}
            for (a, b, c), _uv in zip(parent['T'], parent['UV']):
                pass
            lm['ry'] = np.concatenate([parent['ry'], np.zeros(extra)]); lm['rx'] = np.concatenate([parent['rx'], np.zeros(extra)])
            # fill midpoint rest coords from the 4-way split topology
            for (a, ab, ca), (ab2, b, bc), (ca2, bc2, c), _ in zip(*[iter(lm['T'])] * 4):
                for mid, p, q in ((ab, a, b), (bc, b, c), (ca, c, a)):
                    lm['ry'][mid] = (lm['ry'][p] + lm['ry'][q]) / 2; lm['rx'][mid] = (lm['rx'][p] + lm['rx'][q]) / 2
        return relax_shell(lm, None, offset, iters, minimum, push=push, base_iters=base_iters, skin_clearance=clearance * m, border_scale=border_scale)

    def straight_legs(Q, lm):
        for S in 'LR':
            a, b = bind[f'Bip01_{S}_Calf']['world'][:3, 3], bind[f'Bip01_{S}_Foot']['world'][:3, 3]
            ax = (b - a) / np.linalg.norm(b - a)
            side = np.nonzero((np.sign(lm['rx']) == (1 if S == 'L' else -1)) & (lm['ry'] < knee_y + .3))[0]
            rel = Q[side] - a; along = rel @ ax; radial = rel - along[:, None] * ax
            r = np.linalg.norm(radial, axis=1); r[r == 0] = 1
            k = np.clip((knee_y + .3 - lm['ry'][side]) / 1.2, 0, 1)
            grow = np.maximum(r, .064 * m * k + r * (1 - k))
            Q[side] = a + along[:, None] * ax + radial / r[:, None] * grow[:, None]

    shells = {
        'shirt': build(shirt_sel, 1, lambda lm: np.where(in_overlap(lm['ry']), .022, .011) * m, 30, .007 * m, clearance=.004),
        'trousers': build(jeans_sel, 1, .012 * m, 20, .007 * m, push=straight_legs, clearance=.0065),
        'underwear': build(brief_sel, 1, .002 * m, 4, .0015 * m, base_iters=4, clearance=.0015),
        'hair': build(hair_sel, 1, lambda lm: (.012 + .006 * np.clip((lm['ry'] - eye_y - .6) / .8, 0, 1)) * m, 8, .007 * m, border_scale=0),
    }
    foot = local_mesh(shoe_sel, tris, uvt, posed, weights, uvs)
    pair = [shoe_mesh(foot['P'], rest[foot['src'], 0], sgn, f'Bip01_{S}_Foot', f'Bip01_{S}_Calf', m, bind[f'Bip01_{S}_Foot']['world'][1, 3]) for sgn, S in ((1, 'L'), (-1, 'R'))]
    shells['shoes'] = {'P': np.vstack([pair[0]['P'], pair[1]['P']]), 'W': pair[0]['W'] + pair[1]['W'],
                       'T': np.vstack([pair[0]['T'], pair[1]['T'] + len(pair[0]['P'])]), 'UV': np.vstack([pair[0]['UV'], pair[1]['UV']])}
    # Eyes: own spherical UVs, iris at (0.5, 0.5) facing forward.
    eye_parts = []
    for g in EYES:
        et, eu = body_tris(faces, g)
        ids = np.unique(et); c = rest[ids].mean(0); r = np.linalg.norm(rest[ids] - c, axis=1).max()
        lm = local_mesh(np.isin(np.arange(count), ids), et, eu, posed, weights, uvs)
        rr = rest[lm['src']]
        uvv = np.stack([.5 + (rr[:, 0] - c[0]) / (2.2 * r), .5 + (rr[:, 1] - c[1]) / (2.2 * r)], 1)
        lm['UV'] = uvv[lm['T']]
        eye_parts.append(lm)
    eyes = {'P': np.concatenate([e['P'] for e in eye_parts]), 'W': sum((e['W'] for e in eye_parts), []),
            'T': np.concatenate([eye_parts[0]['T'], eye_parts[1]['T'] + len(eye_parts[0]['P'])]), 'UV': np.concatenate([e['UV'] for e in eye_parts])}
    body = local_mesh(in_body, tris, uvt, posed, weights, uvs)

    textures = paint_all(args.out, rest, uvs, tris, uvt, J)
    out = Bin(); parts = []
    bones = character['parts'][0]['bones']
    stats = {}
    for name, mesh, tex in (('body', body, 'body'), ('eyes', eyes, 'eyes'), ('shirt', shells['shirt'], 'shirt'), ('trousers', shells['trousers'], 'trousers'), ('shoes', shells['shoes'], 'shoes'), ('hair', shells['hair'], 'hair'), ('underwear', shells['underwear'], 'underwear')):
        pos, uv, W, index, nrm = unweld_local(mesh)
        used = sorted({b for d in W for b in d})
        sk_i, sk_w = skin_arrays(W, used)
        parts.append({'name': name, 'material': textures[tex], 'meshes': [{
            'name': name, 'vertexCount': len(pos), 'positions': out.add(pos.reshape(-1)), 'normals': out.add(nrm.reshape(-1)), 'uvs': out.add(uv.reshape(-1)),
            'indices': out.add(index), 'skinBones': used, 'skinIndex': out.add(sk_i.reshape(-1)), 'skinWeight': out.add(sk_w.reshape(-1))}]})
        stats[name] = len(index) // 3
        if args.stage == 'preview':
            with open(os.path.join(args.out, f'preview-{name}.obj'), 'w') as f:
                for p in pos: f.write('v %.5f %.5f %.5f\n' % tuple(p))
                for k in range(0, len(index), 3): f.write('f %d %d %d\n' % (index[k] + 1, index[k + 1] + 1, index[k + 2] + 1))
    from build_resident_hd import MACRO
    manifest = {'schemaVersion': 1, 'id': 'resident-hd', 'binary': 'resident-hd.bin', 'units': 'Bip01 bind space (0.98 units = 1.8 m)',
                'sources': {'mesh': 'MakeHuman base mesh (CC0), from the locally installed MPFB 2.0.17 extension',
                            'weights': 'MakeHuman game_engine skin weights (CC0), remapped to Bip01',
                            'targets': [t for t, _ in MACRO],
                            'clothing': 'body-surface shells generated by tools/resident_hd_dress.py',
                            'textures': 'procedural, painted per texel by tools/resident_hd_texture.py'},
                'triangles': stats, 'bones': bones,
                'inverseBind': {b: bind[b]['inverse'] for b in sorted({n for p in parts for m in p['meshes'] for n in m['skinBones']})}, 'parts': parts}
    with open(os.path.join(args.out, 'resident-hd.bin'), 'wb') as f:
        for c in out.chunks:
            f.write(c)
    with open(os.path.join(args.out, 'resident-hd.json'), 'w') as f:
        json.dump(manifest, f, separators=(',', ':'))
    print(json.dumps(stats), 'binary', out.size)
