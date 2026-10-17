#!/usr/bin/env python3
"""Scanned CC0 assets (Poly Haven) -> runtime deliveries with provenance.

Sources live in private-assets/polyhaven/<id>/ (downloaded once, not committed) and
are listed with their SHA-256 in private-assets/polyhaven/source-manifest.json.
This import is a raster/mesh conversion of photographic scans; it does not claim to
reconstruct them procedurally.

Textures: 2K colour / normal / roughness / AO -> 1K JPEG colour, 1K JPEG normal and
a packed 1K JPEG "orm" (R = ambient occlusion, G = roughness, B = 0, three.js layout).
Models: glTF + bin copied byte-for-byte; their textures re-encoded at the recorded
size (1K for large plants, 512 px for small ones) under the same file names.

  python3 tools/build_scanned_assets.py          # build assets/scanned + manifest
  python3 tools/build_scanned_assets.py --check  # verify deliveries against manifest
"""
import hashlib, io, json, os, shutil, sys
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'private-assets', 'polyhaven')
OUT = os.path.join(ROOT, 'assets', 'scanned')
RECIPE = os.path.join(ROOT, 'assets', 'recipes', 'scanned', 'polyhaven.json')

def sha(b): return hashlib.sha256(b).hexdigest()

def jpeg(img, quality):
    buf = io.BytesIO(); img.save(buf, 'JPEG', quality=quality, subsampling=0 if quality >= 90 else 2); return buf.getvalue()

def build():
    recipe = json.load(open(RECIPE))
    src = json.load(open(os.path.join(SRC, 'source-manifest.json')))
    shutil.rmtree(OUT, ignore_errors=True); os.makedirs(OUT)
    out = {'recipe': os.path.relpath(RECIPE, ROOT), 'license': src['license'], 'source': src['source'], 'assets': {}}
    for aid, spec in recipe['assets'].items():
        meta = src['assets'][aid]
        for f in meta['files'].values():
            data = open(os.path.join(SRC, aid, f['file']), 'rb').read()
            if sha(data) != f['sha256']: raise SystemExit(f'source hash mismatch: {aid}/{f["file"]}')
        files = {}
        if meta['type'] == 'texture':
            size = spec['size']
            load = lambda m: Image.open(os.path.join(SRC, aid, meta['files'][m]['file']))
            diff = load('Diffuse').convert('RGB').resize((size, size), Image.LANCZOS)
            nor = load('nor_gl').convert('RGB').resize((size, size), Image.LANCZOS)
            ao = load('AO').convert('L').resize((size, size), Image.LANCZOS)
            rough = load('Rough').convert('L').resize((size, size), Image.LANCZOS)
            orm = Image.merge('RGB', (ao, rough, Image.new('L', (size, size), 0)))
            for name, b in ((f'{aid}_color.jpg', jpeg(diff, 88)), (f'{aid}_normal.jpg', jpeg(nor, 92)), (f'{aid}_orm.jpg', jpeg(orm, 90))):
                os.makedirs(os.path.join(OUT, aid), exist_ok=True); open(os.path.join(OUT, aid, name), 'wb').write(b); files[name] = sha(b)
        else:
            for f in meta['files'].values():
                rel = f['file']; data = open(os.path.join(SRC, aid, rel), 'rb').read(); dst = os.path.join(OUT, aid, rel)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                if rel.endswith('.jpg') and spec.get('textureSize'):
                    img = Image.open(io.BytesIO(data)).convert('RGB'); s = spec['textureSize']
                    if img.width > s: img = img.resize((s, s), Image.LANCZOS)
                    data = jpeg(img, 90 if 'nor' in rel else 86)
                open(dst, 'wb').write(data); files[rel] = sha(data)
        out['assets'][aid] = {'type': meta['type'], 'authors': meta['authors'], 'page': meta['page'],
                              'sourceFiles': {k: v['sha256'] for k, v in meta['files'].items()}, 'use': spec['use'],
                              **({k: spec[k] for k in ('repeatMetres', 'size', 'textureSize', 'upAxis', 'scale') if k in spec}),
                              'deliveryFiles': files}
    json.dump(out, open(os.path.join(OUT, 'manifest.json'), 'w'), indent=1, sort_keys=True)
    total = sum(os.path.getsize(os.path.join(d, f)) for d, _, fs in os.walk(OUT) for f in fs)
    print(f'scanned deliveries: {len(out["assets"])} assets, {total/1e6:.1f} MB')

def check():
    man = json.load(open(os.path.join(OUT, 'manifest.json')))
    recipe = json.load(open(RECIPE))
    if set(man['assets']) != set(recipe['assets']): raise SystemExit('manifest does not match recipe')
    for aid, a in man['assets'].items():
        for rel, h in a['deliveryFiles'].items():
            p = os.path.join(OUT, aid, rel)
            if not os.path.exists(p) or sha(open(p, 'rb').read()) != h: raise SystemExit(f'delivery mismatch: {aid}/{rel}')
        if a['type'] == 'model' and not any(r.endswith('.gltf') for r in a['deliveryFiles']): raise SystemExit(f'model without gltf: {aid}')
    print(f'scanned deliveries ok: {len(man["assets"])} assets')

if __name__ == '__main__':
    check() if '--check' in sys.argv else build()
