import test from 'node:test';import assert from 'node:assert/strict';import * as THREE from 'three';
import {createQualityGovernor,QUALITY_TIERS} from '../src/quality-governor.js';
import {scallopPixels,createWallLightWash} from '../src/wall-light-wash.js';
import {sceneExteriorDetails} from '../src/exterior-architecture.js';
import {installFacadeWeathering} from '../src/facade-weathering.js';
test('quality governor: steps down on sustained slow frames, back up only after long headroom, ignores idle gaps',()=>{
 let t=0;const applied=[];const g=createQualityGovernor({apply:(s,tier)=>applied.push(tier),now:()=>t});
 const run=(ms,seconds)=>{for(let e=0;e<seconds*1000;e+=ms){t+=ms;g.frame();}};
 run(16,5);assert.equal(g.tier,2);run(40,1);assert.equal(g.tier,2,'a brief hitch does not drop quality');
 run(40,4);assert.equal(g.tier,1);run(40,4);assert.equal(g.tier,0);run(40,4);assert.equal(g.tier,0,'floor');
 t+=5000;g.frame();assert.equal(g.tier,0,'idle gap is not a sample');
 run(10,6);assert.equal(g.tier,0,'needs sustained headroom');run(10,6);assert.equal(g.tier,1);
 assert.deepEqual(applied,[1,0,1]);assert.ok(QUALITY_TIERS[0].detail<QUALITY_TIERS[2].detail&&!QUALITY_TIERS[0].bloom);
 g.force(2);assert.equal(g.tier,2);run(40,6);assert.equal(g.tier,2,'forced tier is locked');
});
test('quality governor: request-to-frame latency catches very slow machines; idle redraws and hidden pages are not slow',()=>{
 let t=0,hidden=false;const g=createQualityGovernor({now:()=>t,hidden:()=>hidden});
 for(let i=0;i<12;i++){t+=1000;g.request();t+=400;g.frame();}assert.equal(g.tier,1,'400 ms frames step down although each is over the idle cut-off');
 const h=createQualityGovernor({now:()=>t,hidden:()=>hidden});for(let i=0;i<200;i++){t+=5000;h.request();t+=12;h.frame();}assert.equal(h.tier,2);assert.ok(h.frameMs<14,'sparse idle redraws read as fast');
 hidden=true;for(let i=0;i<40;i++){h.request();t+=900;h.frame();}assert.equal(h.tier,2,'nothing sampled while hidden');assert.ok(h.frameMs<14);
 hidden=false;const k=createQualityGovernor({now:()=>t});for(let i=0;i<3;i++){k.request();t+=2000;k.frame();for(let j=0;j<30;j++){k.request();t+=12;k.frame();}}assert.equal(k.tier,2,'a few compile hitches do not drop quality');
});
test('wall wash: scallop is bright under the fitting and spreads down; decals land on the wall behind outdoor fittings only',()=>{
 const p=scallopPixels(64),a=(x,y)=>p.data[(Math.round((y*.5+.5)*63)*64+Math.round((x*.5+.5)*63))*4+3];
 assert.ok(a(0,0)>200,'hot spot');assert.ok(a(0,-.5)>a(.5,-.5),'cone below');assert.ok(a(0,-.5)>a(0,.5),'more light below than above');assert.ok(a(.95,.95)<10);
 const scene=new THREE.Scene(),wall=new THREE.Mesh(new THREE.BoxGeometry(4,.2,3),new THREE.MeshBasicMaterial());wall.position.set(0,0,1.5);wall.updateMatrixWorld();
 const wash=createWallLightWash(scene),n=wash.rebuild([{position:[0,.2,2],target:[0,.6,1]},{position:[0,-.2,2],target:[0,-.6,1]}],[wall],p=>p.y>0);
 assert.equal(n,1,'indoor fitting skipped');const d=wash.root.children[0];assert.ok(Math.abs(d.position.y-.104)<1e-3,'on the outer face');
 wash.update(0);assert.equal(wash.root.visible,false);wash.update(1);assert.ok(d.material.opacity>.5);wash.dispose();
});
test('cladding wraps the smallest room in larch boards cut round openings; switchable',()=>{
 const wall=(id,a,b,extra={})=>({id,levelId:'g',materialId:'plaster',hostEndpoints:[a,b],height:3,thickness:.2,base:0,indices:[0,1,2],...extra});
 const scene={rooms:[{levelId:'g',rect:[0,0,6,4]},{levelId:'g',rect:[6,0,9,4]}],openings:[{id:'w',kind:'window'}],walls:[]};
 const walls=[wall('S1',[0,0],[6,0]),wall('S2',[6,0],[9,0],{openingId:'w',opening:[1,1,2,2.2]}),wall('E',[9,0],[9,4]),wall('N2',[9,4],[6,4]),wall('N1',[6,4],[0,4]),wall('W',[0,4],[0,0]),wall('I',[6,0],[6,4])];
 const clad=sceneExteriorDetails(scene,walls,[],{cellSize:1}).filter(m=>m.role==='cladding');
 assert.deepEqual(clad.map(m=>m.hostWallId).sort(),['E','N2','S2']);
 const s2=clad.find(m=>m.hostWallId==='S2');assert.ok(!s2.vertices.some(v=>v[0]>1.2&&v[0]<1.8&&v[2]>1.1&&v[2]<2.1&&v[1]<-.1),'window left open');assert.equal(s2.material.texture.kind,'walnut');
 assert.equal(sceneExteriorDetails({...scene,exterior:{version:1,envelope:{cladding:false}}},walls,[],{cellSize:1}).filter(m=>m.role==='cladding').length,0);
});
test('facade detail: scanned plaster drives tone and normal on outdoor faces only, through world-aligned axes',()=>{
 const m=installFacadeWeathering(new THREE.MeshStandardMaterial(),[[0,0,4,4,0,3]],{detail:{map:new THREE.Texture(),normalMap:new THREE.Texture()}});
 const sh={uniforms:{},vertexShader:THREE.ShaderLib.standard.vertexShader,fragmentShader:THREE.ShaderLib.standard.fragmentShader,defines:{}};m.onBeforeCompile(sh,{});
 assert.ok('TFW_DETAIL' in sh.defines);assert.match(sh.fragmentShader,/tfwDetailOn>0\.5/);assert.match(sh.fragmentShader,/viewMatrix\*vec4\(0\.0,0\.0,1\.0,0\.0\)/);
 const plain=installFacadeWeathering(new THREE.MeshStandardMaterial(),[]),sh2={uniforms:{},vertexShader:THREE.ShaderLib.standard.vertexShader,fragmentShader:THREE.ShaderLib.standard.fragmentShader};plain.onBeforeCompile(sh2,{});assert.ok(!sh2.defines?.TFW_DETAIL);
});
