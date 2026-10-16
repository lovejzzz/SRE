import test from 'node:test';import assert from 'node:assert/strict';import * as THREE from 'three';import {withContactVisibility,installScreenOcclusion,SCREEN_OCCLUSION_GLSL} from '../src/contact-shading.js';
test('contact depth excludes faded/glass surfaces and restores visibility/shadow state after failure',()=>{
 const scene=new THREE.Scene(),opaque=new THREE.Mesh(),glass=new THREE.Mesh(undefined,new THREE.MeshBasicMaterial({opacity:.2,transparent:true})),hidden=new THREE.Mesh();hidden.visible=false;scene.add(opaque,glass,hidden);
 const renderer={shadowMap:{autoUpdate:true,needsUpdate:true}};
 assert.throws(()=>withContactVisibility(scene,renderer,()=>{assert.equal(opaque.visible,true);assert.equal(glass.visible,false);assert.equal(hidden.visible,false);assert.equal(renderer.shadowMap.autoUpdate,false);throw Error('capture failed');}),/capture failed/);
 assert.equal(glass.visible,true);assert.equal(hidden.visible,false);assert.deepEqual(renderer.shadowMap,{autoUpdate:true,needsUpdate:true});
});
test('screen occlusion attenuates only indirect light on opaque lit materials and keys the program',()=>{
 const uniforms={map:{value:null},enabled:{value:0},strength:{value:1}};
 const standard=new THREE.MeshStandardMaterial(),glass=new THREE.MeshStandardMaterial({transparent:true,opacity:.3}),basic=new THREE.MeshBasicMaterial();
 const key=standard.customProgramCacheKey();
 assert.equal(installScreenOcclusion(standard,uniforms),true);assert.equal(installScreenOcclusion(standard,uniforms),false,'installs once');
 assert.equal(installScreenOcclusion(glass,uniforms),false);assert.equal(installScreenOcclusion(basic,uniforms),false);
 assert.notEqual(standard.customProgramCacheKey(),key);
 const shader={uniforms:{},fragmentShader:'void main(){\n#include <lights_fragment_end>\n#include <aomap_fragment>\n}'};standard.onBeforeCompile(shader);
 assert.equal(shader.uniforms.tianScreenOcclusion,uniforms.map);assert.equal(shader.uniforms.tianScreenOcclusionEnabled,uniforms.enabled);
 const body=shader.fragmentShader.slice(shader.fragmentShader.indexOf('#include <aomap_fragment>'));
 assert.match(body,/reflectedLight\.indirectDiffuse\*=tianAO/);assert.match(body,/reflectedLight\.indirectSpecular\*=computeSpecularOcclusion/);
 assert.doesNotMatch(SCREEN_OCCLUSION_GLSL,/\.directDiffuse|\.directSpecular|totalEmissive/,'direct light and emission keep their own shadows');
});
