import test from 'node:test';import assert from 'node:assert/strict';import * as THREE from 'three';
import {installFacadeWeathering,roomBoxes} from '../src/facade-weathering.js';
import {installLeafTranslucency,installLeafWind} from '../src/foliage-shading.js';
import {GradeShader} from '../src/cinematic-grade.js';
const RESERVED=/\b(patch|sample|input|output|filter|common|partition|active|resource|noise\d|subroutine|smooth|flat|varying|attribute|centroid|invariant|precise|buffer|shared)\s*=/;
const compile=m=>{const shader={uniforms:{},vertexShader:THREE.ShaderLib.physical.vertexShader,fragmentShader:THREE.ShaderLib.physical.fragmentShader};m.onBeforeCompile(shader,{});return shader;};
test('weathering: rooms become world boxes; uniform arrays are real vectors; only outdoor fragments are touched',()=>{
 const boxes=roomBoxes([{levelId:'g',rect:[10,20,14,23]}],{cellSize:1,storeyHeight:3},[{id:'g',index:0}]);assert.deepEqual(boxes,[[10,20,14,23,0,3]]);
 const s=compile(installFacadeWeathering(new THREE.MeshStandardMaterial(),boxes,{wallTop:3.5}));
 assert.ok(s.uniforms.tfwRects.value.every(v=>v.isVector4)&&s.uniforms.tfwHeights.value.every(v=>v.isVector2),'three uploads vec4[]/vec2[] via toArray');
 assert.equal(s.uniforms.tfwCount.value,1);assert.match(s.fragmentShader,/if\(tfwInside\(tfwProbe\)<0\.5\)/);assert.doesNotMatch(s.fragmentShader,RESERVED);
});
test('foliage translucency and wind inject into the light loop and vertex stage; grade shader has no reserved identifiers',()=>{
 const t={value:0},m=installLeafWind(installLeafTranslucency(new THREE.MeshPhysicalMaterial(),.5),t,.01),s=compile(m);
 assert.match(s.fragmentShader,/directionalLights\[ 0 \]\.direction/);assert.match(s.vertexShader,/leafWindTime/);assert.equal(s.uniforms.leafWindTime,t);
 assert.doesNotMatch(s.fragmentShader+s.vertexShader,RESERVED);assert.doesNotMatch(GradeShader.fragmentShader,RESERVED);
});
import {installGlassFresnel,installGroundVariation} from '../src/facade-weathering.js';
test('glass opacity follows Fresnel; ground variation adds dry and lush patches',()=>{
 const g=installGlassFresnel(new THREE.MeshStandardMaterial({transparent:true,opacity:.3,roughness:.15})),s=compile(g);
 assert.ok(g.envMapIntensity>1&&g.roughness<=.06);assert.match(s.fragmentShader,/diffuseColor\.a=mix\(tgfAlpha\.x,tgfAlpha\.y,tgfF\)/);assert.doesNotMatch(s.fragmentShader,RESERVED);
 const t=compile(installGroundVariation(new THREE.MeshStandardMaterial()));assert.match(t.fragmentShader,/tgvDry/);assert.doesNotMatch(t.fragmentShader,RESERVED);
});
import {SanitizeShader} from '../src/cinematic-grade.js';
test('a NaN/Inf pixel is replaced before bloom so it cannot black out the frame',()=>{assert.match(SanitizeShader.fragmentShader,/any\(isnan\(c\)\)\|\|any\(isinf\(c\)\)/);assert.doesNotMatch(SanitizeShader.fragmentShader,RESERVED);});
