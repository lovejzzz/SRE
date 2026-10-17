import test from 'node:test';import assert from 'node:assert/strict';import * as THREE from 'three';
import {leafTexture,clusterCard,leafGeometry,leafQuaternion,growClimber,LEAF_SPECIES} from '../src/vegetation-leaves.js';
const coverage=t=>{let a=0;for(let i=3;i<t.color.length;i+=4)a+=t.color[i]>127;return a/(t.width*t.height);};
test('leaf textures: species outlines, sRGB-encoded mid greens (not near-black), unit normals facing out',()=>{
 for(const kind of Object.keys(LEAF_SPECIES)){const t=leafTexture(kind,64,3),c=coverage(t);assert.ok(c>.2&&c<.8,kind+' coverage '+c);
  let g=0,n=0;for(let i=0;i<t.color.length;i+=4)if(t.color[i+3]>200){g+=t.color[i+1];n++;}assert.ok(g/n>60,kind+' green channel is sRGB-encoded: '+g/n);
  for(let i=0;i<t.normal.length;i+=4){const v=[0,1,2].map(k=>t.normal[i+k]/127.5-1);assert.ok(v[2]>0&&Math.abs(Math.hypot(...v)-1)<.03);}}
 const ivy=leafTexture('ivy',128,1),at=(u,v)=>ivy.color[(Math.round((1-u)*127)*128+Math.round((v*.5+.5)*127))*4+3];
 assert.ok(at(.85,0)>127,'terminal lobe');assert.ok(at(.5,.45)>127,'side lobe');assert.ok(at(.95,.6)<127,'sinus between lobes');
 assert.throws(()=>leafTexture('fern'),/Unknown leaf/);
 assert.deepEqual(leafTexture('box',32,5).color,leafTexture('box',32,5).color);
});
test('cluster cards: wrapped cards tile across their edges; normals rotate with each leaf',()=>{
 const w=clusterCard('box',{size:64,leaves:200,leafScale:[.1,.16],seed:4,sourceSize:32,wrap:true});let edge=0;for(let y=0;y<64;y++)edge+=(w.color[(y*64)*4+3]>0)+(w.color[(y*64+63)*4+3]>0);assert.ok(edge>60,'leaves continue over the seam');
 const c=clusterCard('ovate',{size:64,leaves:20,seed:2,sourceSize:32});let tilted=0;for(let i=0;i<c.normal.length;i+=4)if(Math.abs(c.normal[i]-128)>20)tilted++;assert.ok(tilted>50);
});
test('leaf mesh is a folded, curled blade; orientation maps blade axis and face normal',()=>{
 const g=leafGeometry();g.computeBoundingBox();const b=g.boundingBox;assert.ok(b.max.y>.99&&b.min.y<.01&&b.max.x>.49);assert.ok(b.min.z<-.1,'tip curls');
 const q=leafQuaternion(new THREE.Vector3(1,0,0),new THREE.Vector3(0,0,1));assert.ok(new THREE.Vector3(0,1,0).applyQuaternion(q).distanceTo(new THREE.Vector3(1,0,0))<1e-6);assert.ok(new THREE.Vector3(0,0,1).applyQuaternion(q).distanceTo(new THREE.Vector3(0,0,1))<1e-6);
});
test('climber: stems from the root rise and run along the wires; leaves stay on the span and are larger on old wood',()=>{
 const g=growClimber({u0:0,u1:3,z0:.5,z1:2.6,base:0,wires:[.5,.85,1.2,1.55,1.9,2.25,2.6],seed:9});
 assert.ok(g.stems.length>100&&g.leaves.length>300);assert.ok(g.stems.some(([a,b])=>a[1]<.1),'rooted at the base');
 const along=g.stems.filter(([a,b])=>Math.abs(b[1]-a[1])<.02&&Math.abs(b[0]-a[0])>.05).length;assert.ok(along>40,'shoots trained along wires');
 for(const L of g.leaves){assert.ok(L.u>-.5&&L.u<3.5&&L.z>0&&L.z<3.1);}
 const old=g.leaves.filter(L=>L.age>.8),young=g.leaves.filter(L=>L.age<.35),mean=a=>a.reduce((s,L)=>s+L.size,0)/a.length;assert.ok(mean(old)>mean(young));
 assert.deepEqual(growClimber({u0:0,u1:3,z0:.5,z1:2.6,base:0,wires:[1],seed:9}).leaves.length,growClimber({u0:0,u1:3,z0:.5,z1:2.6,base:0,wires:[1],seed:9}).leaves.length);
});
