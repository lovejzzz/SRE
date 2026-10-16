"""Stages for tools/build_resident_hd.py: repose, re-weight, dress, texture, export."""
import json, os
import numpy as np


def rotation_between(a, b):
    a = a / np.linalg.norm(a); b = b / np.linalg.norm(b)
    v = np.cross(a, b); c = float(np.dot(a, b))
    if c < -0.999999:
        axis = np.cross(a, [1, 0, 0]);
        if np.linalg.norm(axis) < 1e-6: axis = np.cross(a, [0, 1, 0])
        axis /= np.linalg.norm(axis); return 2 * np.outer(axis, axis) - np.eye(3)
    k = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + k + k @ k / (1 + c)


def segment_transform(m_head, m_tail, p_head, p_tail, stretch=True):
    """Affine map taking the MakeHuman segment onto the Bip01 segment (rotation, axial stretch)."""
    a = m_tail - m_head; b = p_tail - p_head
    R = rotation_between(a, b)
    axis = a / np.linalg.norm(a)
    f = np.linalg.norm(b) / np.linalg.norm(a) if stretch else 1.0
    S = np.eye(3) + (f - 1) * np.outer(axis, axis)
    A = R @ S
    return A, p_head - A @ m_head


def load_rig(data):
    rig = json.load(open(os.path.join(data, 'rigs', 'standard', 'rig.game_engine.json')))
    weights = json.load(open(os.path.join(data, 'rigs', 'standard', 'weights.game_engine.json')))['weights']
    return rig, weights


def joint_point(spec, joint, verts):
    if spec.get('strategy') == 'CUBE':
        return joint[spec['cube_name']]
    if spec.get('strategy') == 'MEAN':
        return verts[spec['vertex_indices']].mean(0)
    return np.array(spec['default_position'])


def to_game_space(verts, ground, scale):
    """MakeHuman decimetres, Y up, front +Z -> Bip01 bind space (Y up, front -Z, ground 0)."""
    out = np.empty_like(verts)
    out[:, 0] = verts[:, 0] * scale
    out[:, 1] = (verts[:, 1] - ground) * scale
    out[:, 2] = -verts[:, 2] * scale
    return out


def repose(verts, joint, rig, mh_weights, P):
    ground = joint['joint-ground'][1]
    scale = (P['Bip01_Head'][1]) / (joint['joint-head'][1] - ground)
    V = to_game_space(verts, ground, scale)
    J = {k: to_game_space(v[None], ground, scale)[0] for k, v in joint.items()}
    heads = {b: to_game_space(joint_point(s['head'], joint, verts)[None], ground, scale)[0] for b, s in rig.items()}
    tails = {b: to_game_space(joint_point(s['tail'], joint, verts)[None], ground, scale)[0] for b, s in rig.items()}
    T = {}
    # Torso: vertical stretch so pelvis->neck matches, centred on the Bip01 spine.
    k = (P['Bip01_Neck'][1] - P['Bip01_Pelvis'][1]) / (J['joint-neck'][1] - J['joint-pelvis'][1])
    torso = np.diag([1.0, k, 1.0]); t_torso = P['Bip01_Pelvis'] - torso @ J['joint-pelvis']
    for b in ('Root', 'pelvis', 'spine_01', 'spine_02', 'spine_03'):
        T[b] = (torso, t_torso)
    # Neck and head: rigid shift so the head joint lands on Bip01_Head.
    shift = P['Bip01_Head'] - J['joint-head']
    for b in ('neck_01', 'head'):
        T[b] = (np.eye(3), shift)
    for side, S in (('l', 'L'), ('r', 'R')):
        T[f'clavicle_{side}'] = segment_transform(J[f'joint-{side}-clavicle'], J[f'joint-{side}-shoulder'], P[f'Bip01_{S}_Clavicle'], P[f'Bip01_{S}_UpperArm'], stretch=True)
        T[f'upperarm_{side}'] = segment_transform(J[f'joint-{side}-shoulder'], J[f'joint-{side}-elbow'], P[f'Bip01_{S}_UpperArm'], P[f'Bip01_{S}_Forearm'])
        T[f'lowerarm_{side}'] = segment_transform(J[f'joint-{side}-elbow'], J[f'joint-{side}-hand'], P[f'Bip01_{S}_Forearm'], P[f'Bip01_{S}_Hand'])
        # Hand keeps its own shape: rigid, oriented by the forearm, wrist on Bip01 hand.
        A, _ = segment_transform(J[f'joint-{side}-elbow'], J[f'joint-{side}-hand'], P[f'Bip01_{S}_Forearm'], P[f'Bip01_{S}_Hand'], stretch=False)
        hand = (A, P[f'Bip01_{S}_Hand'] - A @ J[f'joint-{side}-hand'])
        for b in rig:
            if b.endswith('_' + side) and b.split('_')[0] in ('hand', 'thumb', 'index', 'middle', 'ring', 'pinky'):
                T[b] = hand
        T[f'thigh_{side}'] = segment_transform(J[f'joint-{side}-upper-leg'], J[f'joint-{side}-knee'], P[f'Bip01_{S}_Thigh'], P[f'Bip01_{S}_Calf'])
        T[f'calf_{side}'] = segment_transform(J[f'joint-{side}-knee'], J[f'joint-{side}-ankle'], P[f'Bip01_{S}_Calf'], P[f'Bip01_{S}_Foot'])
        A, _ = segment_transform(J[f'joint-{side}-knee'], J[f'joint-{side}-ankle'], P[f'Bip01_{S}_Calf'], P[f'Bip01_{S}_Foot'], stretch=False)
        foot = (A, P[f'Bip01_{S}_Foot'] - A @ J[f'joint-{side}-ankle'])
        T[f'foot_{side}'] = foot; T[f'ball_{side}'] = foot
    missing = [b for b in mh_weights if b not in T]
    if missing:
        raise SystemExit('No repose transform for ' + ', '.join(missing))
    out = np.zeros_like(V); total = np.zeros(len(V))
    for b, pairs in mh_weights.items():
        A, t = T[b]
        if not pairs: continue
        ix = np.array([p[0] for p in pairs], dtype=int); w = np.array([p[1] for p in pairs])
        out[ix] += w[:, None] * (V[ix] @ A.T + t)
        total[ix] += w
    unweighted = total < 1e-6
    out[~unweighted] /= total[~unweighted, None]
    out[unweighted] = V[unweighted] @ torso.T + t_torso
    return out, scale


def bip_weights(mh_weights, bone_map, count):
    """Per-vertex Bip01 weights (top four, normalised) from the MakeHuman weights."""
    per = [dict() for _ in range(count)]
    for b, pairs in mh_weights.items():
        target = bone_map[b]
        for i, w in pairs:
            per[i][target] = per[i].get(target, 0) + w
    out = []
    for d in per:
        top = sorted(d.items(), key=lambda kv: -kv[1])[:4]
        s = sum(w for _, w in top) or 1
        out.append([(b, w / s) for b, w in top] if top else [('Bip01_Pelvis', 1.0)])
    return out


def build(args, verts, uvs, faces, groups, joint, character, bind, bone_map):
    rig, mh_weights = load_rig(args.mpfb)
    P = {n: b['world'][:3, 3] for n, b in bind.items()}
    posed, scale = repose(verts, joint, rig, mh_weights, P)
    weights = bip_weights(mh_weights, bone_map, len(verts))
    from resident_hd_dress import dress_and_export
    dress_and_export(args, verts, posed, uvs, faces, groups, joint, weights, character, bind, scale)
