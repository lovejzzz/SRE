"""Build the high-detail resident body from the CC0 MakeHuman base mesh.

The body is shaped with MakeHuman macro targets, reposed onto the game's Bip01
bind pose with MakeHuman's own CC0 game-engine skin weights, and re-weighted to
the Bip01 bones so every existing animation drives it unchanged. Clothing, hair
and textures are generated here (original work). No network access: the base
mesh, targets and weights come from the locally installed MPFB extension.

Usage: python3 tools/build_resident_hd.py [--mpfb DIR] [--out DIR]
"""
import argparse, gzip, json, math, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DEFAULT_MPFB = os.path.expanduser('~/Library/Application Support/Blender/5.2/extensions/blender_org/mpfb/data')

# Shape: male, young adult (~25), slightly above average muscle, mixed Asian/European.
MACRO = [
    ('macrodetails/asian-male-young.target.gz', .6),
    ('macrodetails/caucasian-male-young.target.gz', .4),
    ('macrodetails/universal-male-young-maxmuscle-averageweight.target.gz', .3),
]

# MakeHuman game-engine bone -> Bip01 bone. Fingers collapse onto the two PZ finger bones.
BONE_MAP = {'Root': 'Bip01_Pelvis', 'pelvis': 'Bip01_Pelvis', 'spine_01': 'Bip01_Spine', 'spine_02': 'Bip01_Spine1',
            'spine_03': 'Bip01_Spine1', 'neck_01': 'Bip01_Neck', 'head': 'Bip01_Head'}
for side, S in (('l', 'L'), ('r', 'R')):
    BONE_MAP.update({f'clavicle_{side}': f'Bip01_{S}_Clavicle', f'upperarm_{side}': f'Bip01_{S}_UpperArm',
                     f'lowerarm_{side}': f'Bip01_{S}_Forearm', f'hand_{side}': f'Bip01_{S}_Hand',
                     f'thigh_{side}': f'Bip01_{S}_Thigh', f'calf_{side}': f'Bip01_{S}_Calf',
                     f'foot_{side}': f'Bip01_{S}_Foot', f'ball_{side}': f'Bip01_{S}_Foot'})
    for finger in ('thumb', 'index', 'middle', 'ring', 'pinky'):
        for k in (1, 2, 3):
            BONE_MAP[f'{finger}_0{k}_{side}'] = f'Bip01_{S}_Finger0' if finger == 'thumb' else f'Bip01_{S}_Finger1'


def read_obj(path):
    v, vt, faces = [], [], []
    group = None
    for line in open(path):
        if line.startswith('v '):
            v.append([float(x) for x in line.split()[1:4]])
        elif line.startswith('vt '):
            vt.append([float(x) for x in line.split()[1:3]])
        elif line.startswith('g '):
            group = line.split()[1]
        elif line.startswith('f '):
            corners = [c.split('/') for c in line.split()[1:]]
            faces.append((group, [int(c[0]) - 1 for c in corners], [int(c[1]) - 1 if len(c) > 1 and c[1] else -1 for c in corners]))
    return np.array(v), np.array(vt), faces


def apply_target(verts, path, weight):
    with gzip.open(path, 'rt') as f:
        for line in f:
            parts = line.split()
            if len(parts) == 4 and not line.startswith('#'):
                verts[int(parts[0])] += weight * np.array([float(x) for x in parts[1:]])


def pz_bind(character):
    """Bind-pose world matrices of the Bip01 bones, from the source skin's inverse bind matrices."""
    bind = {}
    for part in character['parts']:
        for mesh in part['meshes']:
            for w in mesh['weights']:
                bind.setdefault(w['bone'], {'inverse': w['inverse'], 'world': np.linalg.inv(np.array(w['inverse']).reshape(4, 4).T)})
    return bind


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--mpfb', default=DEFAULT_MPFB)
    ap.add_argument('--out', default=os.path.join(ROOT, 'assets', 'characters', 'resident-hd'))
    ap.add_argument('--stage', default='all')
    args = ap.parse_args()
    data = args.mpfb
    verts, uvs, faces = read_obj(os.path.join(data, '3dobjs', 'base.obj'))
    for rel, w in MACRO:
        apply_target(verts, os.path.join(data, 'targets', rel), w)
    groups = {}
    for g, vi, ti in faces:
        groups.setdefault(g, set()).update(vi)
    joint = {g: verts[sorted(ix)].mean(0) for g, ix in groups.items() if g.startswith('joint-')}
    character = json.load(open(os.path.join(ROOT, 'private-assets', 'characters', 'character.json')))
    bind = pz_bind(character)
    P = {n: b['world'][:3, 3] for n, b in bind.items()}
    if args.stage == 'joints':
        for n in ['joint-pelvis', 'joint-neck', 'joint-head', 'joint-l-shoulder', 'joint-l-elbow', 'joint-l-hand', 'joint-l-upper-leg', 'joint-l-knee', 'joint-l-ankle', 'joint-ground']:
            print(n, np.round(joint.get(n, [np.nan] * 3), 3))
        print('mesh min', verts.min(0).round(2), 'max', verts.max(0).round(2))
        for n in ['Bip01_Pelvis', 'Bip01_Neck', 'Bip01_Head', 'Bip01_L_UpperArm', 'Bip01_L_Forearm', 'Bip01_L_Hand', 'Bip01_L_Thigh', 'Bip01_L_Calf', 'Bip01_L_Foot']:
            print(n, np.round(P[n], 3))
        return
    from resident_hd_stages import build
    build(args, verts, uvs, faces, groups, joint, character, bind, BONE_MAP)


if __name__ == '__main__':
    sys.path.insert(0, HERE)
    main()
