import test from 'node:test';import assert from 'node:assert/strict';
import * as THREE from 'three';
import {surfaceVariationProfile,installSurfaceVariation,SURFACE_VARIATION_DEFAULTS} from '../src/surface-variation.js';
import {createVolumeSurfaceMaterial} from '../src/volume-surface-material.js';
import {PROCEDURAL_SURFACES} from '../src/procedural-surfaces.js';

test('every opaque, non-emissive surface gets world-space variation; glass and lamps opt out',()=>{
 assert.deepEqual(surfaceVariationProfile({}),SURFACE_VARIATION_DEFAULTS);
 assert.ok(surfaceVariationProfile({},{metalness:.8}).tone<SURFACE_VARIATION_DEFAULTS.tone,'metals vary less in tone');
 assert.equal(surfaceVariationProfile({},{opacity:.3}),null);
 assert.equal(surfaceVariationProfile({fixtureEmission:{intensity:1}},{emissive:true}),null);
 assert.equal(surfaceVariationProfile({variation:false}),null);
 assert.throws(()=>surfaceVariationProfile({variation:{tone:3}}),/variation/);
 const m=createVolumeSurfaceMaterial({color:0xffffff},{});assert.deepEqual(m.userData.tianSurfaceVariation,SURFACE_VARIATION_DEFAULTS);
 const glass=createVolumeSurfaceMaterial({color:0xffffff,transparent:true,opacity:.3},{});assert.equal(glass.userData.tianSurfaceVariation,undefined);
});

test('the shader patch modulates albedo and roughness with uniquely named symbols',()=>{
 const m=installSurfaceVariation(new THREE.MeshStandardMaterial(),SURFACE_VARIATION_DEFAULTS);
 const shader={uniforms:{},vertexShader:THREE.ShaderLib.standard.vertexShader,fragmentShader:THREE.ShaderLib.standard.fragmentShader};
 m.onBeforeCompile(shader);
 assert.match(shader.vertexShader,/vTsvWorld=\(modelMatrix\*tsvWP\)\.xyz/);
 assert.match(shader.fragmentShader,/diffuseColor\.rgb\*=1\.\+tsvVariation\.x/);assert.match(shader.fragmentShader,/roughnessFactor=clamp\(roughnessFactor\*/);
 // Other patches already use vTianWorld/tianP; redefining them broke every surface once.
 assert.doesNotMatch(shader.fragmentShader+shader.vertexShader,/\bvTianWorld\b|\btianP\b/);
 assert.match(m.customProgramCacheKey(),/tian-surface-variation/);
});

test('material-class textures are deterministic tiles in range',()=>{
 for(const kind of ['ceramic','paint','plastic','paper','terracotta','leaf','cast-iron','wall-paint']){
  const a=PROCEDURAL_SURFACES[kind]({size:64}),b=PROCEDURAL_SURFACES[kind]({size:64});assert.deepEqual(a.color,b.color,kind);
  let min=255,max=0;for(let i=0;i<64*64;i++){min=Math.min(min,a.color[i*4]);max=Math.max(max,a.color[i*4]);}
  assert.ok(max-min>3,kind+' is not a flat colour');assert.ok(min>150,kind+' stays a tint, not a dark stain');
 }
});
