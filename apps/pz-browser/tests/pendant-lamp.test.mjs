import test from 'node:test';import assert from 'node:assert/strict';
import {readVolume} from './helpers/volume-delivery.mjs';import {studioFurnitureVolume} from '../src/studio-furniture-volume.js';import {installStudioAssets} from '../src/studio-assets.js';
test('pendant hangs above head height over a worktop and lights it from under the shade',()=>{
 const a=readVolume('studio-pendant-lamp');assert.deepEqual(a.geometry,JSON.parse(JSON.stringify(studioFurnitureVolume(a.recipe))));
 const {parts,light}=a.geometry,zs=parts.flatMap(p=>p.vertices.map(v=>v[2]));
 assert.ok(Math.min(...zs)>1.55,'nothing hangs into walking height');assert.ok(Math.max(...zs)<=a.recipe.parameters.ceiling);
 assert.ok(parts.every(p=>p.collision.length===0),'visual only: no physical blocking');
 assert.ok(light.target[2]<light.position[2]&&light.position[2]<a.recipe.parameters.rimHeight,'down beam starts under the shade rim');
 assert.ok(parts.find(p=>p.id==='shade').doubleSided);
 const props={},atlas={regions:{}};installStudioAssets(props,atlas);const p=props.tian_studio_pendant_lamp_S_0;
 assert.equal(p.TianMount,'ceiling');assert.equal(p.TianLight,'true');assert.equal(p.BlocksPlacement,undefined);
});
