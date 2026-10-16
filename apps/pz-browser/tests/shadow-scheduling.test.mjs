import test from 'node:test';import assert from 'node:assert/strict';
import * as THREE from 'three';
import {spotTouches,createVolumeFixtureLights} from '../src/volume-fixture-lights.js';
const spot=(pos,target,angle=.6,distance=3)=>{const l=new THREE.SpotLight(0xffffff,1,distance,angle);l.position.set(...pos);l.target.position.set(...target);return l;};

test('a caster touches a spotlight only inside its cone and range',()=>{
 const l=spot([0,0,2],[0,0,0]);
 assert.ok(spotTouches(l,{center:[0,0,.9],radius:1}),'directly below');
 assert.ok(!spotTouches(l,{center:[5,0,.9],radius:1}),'beside, outside the cone');
 assert.ok(!spotTouches(l,{center:[0,0,-4],radius:.5}),'beyond range');
 assert.ok(spotTouches(l,{center:[1.6,0,.9],radius:1.15}),'sphere edge reaches into the cone');
 assert.ok(spotTouches(l,{center:[0,0,2.2],radius:.5}),'light inside the sphere');
});

test('character-driven refreshes are budgeted round-robin, so every touched light still updates',()=>{
 const scene=new THREE.Scene(),rig=createVolumeFixtureLights(scene,{shadowBudget:6});
 rig.rebuild([0,.5,1,1.5].map((x,i)=>({objectId:'f'+i,levelId:'g',light:{type:'spot',position:[x,0,2],target:[x,0,0],color:0xffffff,intensity:1,distance:3,angle:.6,penumbra:.5,decay:2}})),'g');
 const lights=[];scene.traverse(o=>{if(o.isSpotLight)lights.push(o);});const reset=()=>lights.forEach(l=>{l.shadow.needsUpdate=false;});
 reset();rig.scheduleShadows([]);const seen=new Set(),mover=[{center:[.75,0,.9],radius:1}];
 for(let f=0;f<2;f++){reset();assert.equal(rig.scheduleShadows(mover,{budget:2}),2,'never more than the budget');lights.forEach((l,i)=>{if(l.shadow.needsUpdate)seen.add(i);});}
 assert.equal(seen.size,4,'all four touched lights refreshed within two frames');
});

test('static rooms stop re-rendering shadow maps; movers and changes update only what they touch',()=>{
 const scene=new THREE.Scene(),rig=createVolumeFixtureLights(scene,{shadowBudget:4});
 const fixture=(x,id)=>({objectId:id,levelId:'g',light:{type:'spot',position:[x,0,2],target:[x,0,0],color:0xffffff,intensity:1,distance:3,angle:.6,penumbra:.5,decay:2}});
 rig.rebuild([fixture(0,'a'),fixture(10,'b')],'g');
 const lights=[];scene.traverse(o=>{if(o.isSpotLight)lights.push(o);});assert.equal(lights.length,2);
 for(const l of lights)assert.equal(l.shadow.autoUpdate,false,'never every frame');
 const reset=()=>lights.forEach(l=>{l.shadow.needsUpdate=false;});
 reset();assert.equal(rig.scheduleShadows([]),2,'first frame after rebuild renders all');
 reset();assert.equal(rig.scheduleShadows([]),0,'static room: nothing re-rendered');
 reset();assert.equal(rig.scheduleShadows([{center:[0,0,.9],radius:1}]),1,'only the light the character stands under');assert.ok(lights.find(l=>l.position.x===0).shadow.needsUpdate);
 reset();assert.equal(rig.scheduleShadows([{center:[5,0,.9],radius:1}]),1,'one more frame to clear the shadow it left');
 reset();assert.equal(rig.scheduleShadows([{center:[5,0,.9],radius:1}]),0);
 rig.invalidateShadows();reset();assert.equal(rig.scheduleShadows([]),2,'doors/drawers animating invalidate everything');
 rig.setEnabled(false);reset();assert.equal(rig.scheduleShadows([{center:[0,0,.9],radius:1}]),0,'lamps off: no shadow work');
 rig.setEnabled(true);reset();assert.equal(rig.scheduleShadows([]),2,'switching on re-renders once');
});
