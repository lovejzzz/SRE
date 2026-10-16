import test from 'node:test';import assert from 'node:assert/strict';import {readFileSync,existsSync} from 'node:fs';
import * as THREE from 'three';
import {validateResidentHD,createResidentHDActor,syncResidentHD,residentHDMaterial,RESIDENT_HD_PARTS} from '../src/resident-hd-character.js';
import {showerPartVisible} from '../src/shower-presentation.js';
const dir=new URL('../assets/characters/resident-hd/',import.meta.url);
const manifest=JSON.parse(readFileSync(new URL('resident-hd.json',dir)));
const bin=readFileSync(new URL(manifest.binary,dir));
const arr=ref=>{const b=bin.buffer.slice(bin.byteOffset+ref.offset,bin.byteOffset+ref.offset+ref.length);return ref.type==='u32'?new Uint32Array(b):new Float32Array(b);};
const part=name=>manifest.parts.find(p=>p.name===name);
const bindWorld=bone=>new THREE.Matrix4().fromArray(manifest.inverseBind[bone]).invert();
const joint=bone=>new THREE.Vector3().setFromMatrixPosition(bindWorld(bone));

test('the high-detail resident is a complete, much denser replacement with every part present',()=>{
 validateResidentHD(manifest);
 for(const name of RESIDENT_HD_PARTS)assert.ok(part(name),name);
 assert.ok(manifest.triangles.body>=20000,'body is the 26k-triangle CC0 base mesh, not the 916-triangle original');
 assert.ok(Object.values(manifest.triangles).reduce((a,b)=>a+b)>=50000);
 for(const p of manifest.parts){assert.ok(p.material?.map,p.name+' has a texture');for(const file of [p.material.map,p.material.bumpMap].filter(Boolean))assert.ok(existsSync(new URL(file,dir)),file);}
 assert.match(manifest.sources.mesh,/CC0/);assert.match(manifest.sources.weights,/CC0/);
});

test('skin weights are normalised top-four influences on bones that exist in the bind pose',()=>{
 for(const p of manifest.parts)for(const m of p.meshes){
  const idx=arr(m.skinIndex),w=arr(m.skinWeight);assert.equal(idx.length,m.vertexCount*4);
  for(let v=0;v<m.vertexCount;v++){let s=0;for(let k=0;k<4;k++){s+=w[v*4+k];assert.ok(idx[v*4+k]<m.skinBones.length);}assert.ok(Math.abs(s-1)<1e-4,p.name+' vertex '+v);}
  assert.equal(arr(m.positions).length,m.vertexCount*3);assert.equal(arr(m.normals).length,m.vertexCount*3);assert.equal(arr(m.uvs).length,m.vertexCount*2);
  assert.equal(arr(m.indices).length%3,0);assert.ok(Math.max(...arr(m.indices))<m.vertexCount);
 }
});

test('bind matrices are the game skeleton\'s own, so existing animations drive the new body unchanged',{skip:!existsSync(new URL('../private-assets/characters/character.json',import.meta.url))},()=>{
 const source=JSON.parse(readFileSync(new URL('../private-assets/characters/character.json',import.meta.url)));
 const inverse=new Map();for(const p of source.parts)for(const m of p.meshes)for(const w of m.weights)if(!inverse.has(w.bone))inverse.set(w.bone,w.inverse); // body part first, as the build does
 for(const [bone,matrix] of Object.entries(manifest.inverseBind))assert.deepEqual(matrix,inverse.get(bone),bone);
 assert.deepEqual(manifest.bones.map(b=>b.name),source.parts[0].bones.map(b=>b.name));
});

test('the reposed body sits on the Bip01 joints: feet on the ground, hands at the wrists, head above the head joint',()=>{
 const m=part('body').meshes[0],P=arr(m.positions),idx=arr(m.skinIndex),w=arr(m.skinWeight);
 let minY=Infinity,maxY=-Infinity;for(let i=1;i<P.length;i+=3){minY=Math.min(minY,P[i]);maxY=Math.max(maxY,P[i]);}
 assert.ok(minY>-.01&&minY<.03,'soles at ground level: '+minY);
 assert.ok(maxY>joint('Bip01_Head').y+.05&&maxY<1.0,'crown above the head joint: '+maxY);
 for(const side of ['L','R']){
  const slot=m.skinBones.indexOf(`Bip01_${side}_Hand`),wrist=joint(`Bip01_${side}_Hand`);let far=0,n=0;
  for(let v=0;v<m.vertexCount;v++)for(let k=0;k<4;k++)if(idx[v*4+k]===slot&&w[v*4+k]>.9){n++;far=Math.max(far,new THREE.Vector3(P[v*3],P[v*3+1],P[v*3+2]).distanceTo(wrist));}
  assert.ok(n>50,'hand vertices weighted to the hand');assert.ok(far<.12,side+' hand stays at the wrist: '+far);
 }
});

test('clothing stays outside the skin it covers; shoes stand on the floor',()=>{
 const shoes=arr(part('shoes').meshes[0].positions);let min=Infinity;for(let i=1;i<shoes.length;i+=3)min=Math.min(min,shoes[i]);
 assert.ok(min>=-1e-6&&min<.01,'sole on the ground: '+min);
 // Both shoes wind outward (a mirrored foot once rendered inside-out and vanished).
 const sh=part('shoes').meshes[0],I=arr(sh.indices);for(const side of [1,-1]){let vol=0,n=0,c=[0,0,0];for(let v=0;v<sh.vertexCount;v++)if(Math.sign(shoes[v*3])===side){n++;for(let k=0;k<3;k++)c[k]+=shoes[v*3+k];}c=c.map(x=>x/n);
  for(let t=0;t<I.length;t+=3){const [a,b,d]=[I[t],I[t+1],I[t+2]].map(i=>[shoes[i*3],shoes[i*3+1],shoes[i*3+2]]);if(Math.sign(a[0])!==side)continue;const u=b.map((x,k)=>x-a[k]),w=d.map((x,k)=>x-a[k]),cr=[u[1]*w[2]-u[2]*w[1],u[2]*w[0]-u[0]*w[2],u[0]*w[1]-u[1]*w[0]];vol+=cr.reduce((s,x,k)=>s+x*(a[k]-c[k]),0);}
  assert.ok(vol>0,'shoe '+side+' winds outward');}
 // Each shirt vertex is further from the spine axis than the nearest body vertex at that height band.
 const body=arr(part('body').meshes[0].positions),shirt=arr(part('shirt').meshes[0].positions),neck=joint('Bip01_Neck'),pelvis=joint('Bip01_Pelvis');
 const radius=(P,y0,y1)=>{let r=0;for(let i=0;i<P.length;i+=3)if(P[i+1]>y0&&P[i+1]<y1&&Math.abs(P[i])<.12)r=Math.max(r,Math.hypot(P[i],P[i+2]-pelvis.z));return r;};
 const mid=(neck.y+pelvis.y)/2;assert.ok(radius(shirt,mid-.02,mid+.02)>radius(body,mid-.02,mid+.02),'shirt encloses the chest');
});

test('the actor shares one Bip01 skeleton and copies the sampled pose by bone name',()=>{
 const geometryFor=()=>{const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute([0,0,0,0,1,0,1,0,0],3));g.setIndex([0,1,2]);g.setAttribute('skinIndex',new THREE.Uint16BufferAttribute(new Uint16Array(12),4));g.setAttribute('skinWeight',new THREE.Float32BufferAttribute([1,0,0,0,1,0,0,0,1,0,0,0],4));return g;};
 const hd={manifest,parts:manifest.parts.map(p=>({part:p,maps:{},meshes:p.meshes.map(m=>({mesh:m,geometry:geometryFor()}))}))};
 const actor=createResidentHDActor(hd);
 assert.equal(actor.model.children.filter(c=>c.isSkinnedMesh).length,manifest.parts.length);
 const skeletons=new Set(actor.model.children.filter(c=>c.isSkinnedMesh).flatMap(c=>c.skeleton.bones));
 for(const b of skeletons)assert.equal(actor.bones.get(b.name),b,'one shared bone per name');
 const head=new THREE.Bone();head.name='Bip01_Head';head.position.set(1,2,3);head.quaternion.setFromEuler(new THREE.Euler(.3,0,0));
 const source={actor:new THREE.Group(),bodyBones:new Map([['Bip01_Head',head]])};source.actor.rotation.y=1;source.actor.scale.z=-1;
 syncResidentHD(actor,source,{showering:true,partVisible:showerPartVisible});
 assert.deepEqual(actor.bones.get('Bip01_Head').position.toArray(),[1,2,3]);
 assert.ok(actor.bones.get('Bip01_Head').quaternion.equals(head.quaternion));
 assert.equal(actor.model.scale.z,-1,'mirroring and facing come from the source actor');
 const visible=Object.fromEntries(actor.model.children.filter(c=>c.isSkinnedMesh).map(c=>[c.userData.characterPart,c.visible]));
 assert.deepEqual(visible,{body:true,eyes:true,shirt:false,trousers:false,shoes:false,hair:true,underwear:true});
});

test('materials: fabrics are double-sided with sheen, eyes glossy, hair alpha-tested',()=>{
 const mat=name=>residentHDMaterial(part(name).material,{});
 assert.equal(mat('shirt').side,THREE.DoubleSide);assert.ok(mat('shirt').sheen>0);
 assert.equal(mat('body').side,THREE.FrontSide);assert.ok(mat('eyes').clearcoat>0);assert.ok(mat('hair').alphaTest>0);
});
