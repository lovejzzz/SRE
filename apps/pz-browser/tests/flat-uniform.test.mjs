import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import {flatUniform} from '../src/flat-uniform.js';
test('flat uniform: a Float32Array view of vector uniforms, refreshed once per render call',()=>{
 const renderer={info:{render:{frame:0}}},source={value:[new THREE.Vector3(1,2,3),new THREE.Vector3(4,5,6)]},u=flatUniform(source,3,renderer);
 const a=u.value;assert.ok(a instanceof Float32Array);assert.deepEqual([...a],[1,2,3,4,5,6]);
 source.value[0].set(7,8,9);assert.equal(u.value,a,'same array within a render call');assert.equal(u.value[0],1,'not re-copied mid-call');
 renderer.info.render.frame++;assert.deepEqual([...u.value],[7,8,9,4,5,6],'refreshed on the next render call');
 const v4={value:[new THREE.Vector4(1,2,3,4)]},w=flatUniform(v4,4,renderer);assert.deepEqual([...w.value],[1,2,3,4]);
});
