import test from 'node:test';import assert from 'node:assert/strict';import {readFileSync,existsSync,statSync} from 'node:fs';import {createHash} from 'node:crypto';
import {SCANNED_TEXTURES,SCANNED_MODELS,isScannedTexture} from '../src/scanned-assets.js';
const root=new URL('../',import.meta.url),man=JSON.parse(readFileSync(new URL('assets/scanned/manifest.json',root))),recipe=JSON.parse(readFileSync(new URL('assets/recipes/scanned/polyhaven.json',root)));
test('scanned deliveries carry provenance: CC0, source page, authors, source and delivery hashes',()=>{
 assert.equal(man.license,'CC0 1.0');assert.deepEqual(Object.keys(man.assets).sort(),Object.keys(recipe.assets).sort());
 for(const [id,a] of Object.entries(man.assets)){assert.match(a.page,/^https:\/\/polyhaven\.com\/a\//);assert.ok(Object.keys(a.authors||{}).length,id+' authors');assert.ok(Object.values(a.sourceFiles).every(h=>/^[0-9a-f]{64}$/.test(h)));
  for(const [rel,h] of Object.entries(a.deliveryFiles)){const p=new URL(`assets/scanned/${id}/${rel}`,root);assert.ok(existsSync(p),rel);assert.equal(createHash('sha256').update(readFileSync(p)).digest('hex'),h,rel);}}
});
test('runtime lists match the import and deliveries stay small',()=>{
 for(const id of SCANNED_TEXTURES){assert.equal(man.assets[id]?.type,'texture',id);for(const s of ['color','normal','orm'])assert.ok(man.assets[id].deliveryFiles[`${id}_${s}.jpg`],id+' '+s);}
 for(const id of Object.keys(SCANNED_MODELS)){assert.equal(man.assets[id]?.type,'model',id);assert.ok(Object.keys(man.assets[id].deliveryFiles).some(f=>f.endsWith('.gltf')));}
 assert.ok(isScannedTexture('gravel_floor_02')&&!isScannedTexture('square_concrete_pavers'));
 let total=0;for(const [id,a] of Object.entries(man.assets))for(const rel of Object.keys(a.deliveryFiles))total+=statSync(new URL(`assets/scanned/${id}/${rel}`,root)).size;assert.ok(total<25e6,'deliveries '+total);
});
test('the roof surface recipe uses the scanned gravel by id',()=>{
 const s=JSON.parse(readFileSync(new URL('assets/recipes/volume/surface-materials.json',root))),roof=s.surfaces.find(e=>e.tiles.includes('roofs_01_22'));assert.deepEqual([roof.material.texture.kind,roof.material.texture.id],['scanned','gravel_floor_02']);
});
