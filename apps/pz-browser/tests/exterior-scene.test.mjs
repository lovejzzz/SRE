import test from 'node:test';import assert from 'node:assert/strict';import * as THREE from 'three';
import {skySunVector,toSkySpace,horizonColor,createExteriorSky} from '../src/exterior-sky.js';
import {plotLayout,gardenTree,distantTreeGeometry,leafCardPixels,createExteriorLandscape} from '../src/exterior-landscape.js';
import {gravelPixels,ALBEDO_SURFACES} from '../src/procedural-surfaces.js';

test('sky: Z-up world maps to the Y-up sky shader, sun rises east-ish at 6:00, sets 18:00, night below',()=>{
 assert.deepEqual(toSkySpace([1,2,3]),[1,3,-2]);
 assert.ok(Math.abs(skySunVector(360)[2])<1e-9&&Math.abs(skySunVector(1080)[2])<1e-9);
 assert.ok(skySunVector(720)[2]>1&&skySunVector(0)[2]<-1);
 assert.notDeepEqual(horizonColor(.6).toArray(),horizonColor(-.4).toArray());
 assert.ok(horizonColor(-.4).r<horizonColor(.6).r,'night horizon darker');
});
test('sky without a WebGL renderer still drives stars, fog and night fill (no environment capture)',()=>{
 const scene=new THREE.Scene(),sky=createExteriorSky(scene,{});
 sky.setSun(skySunVector(720));assert.equal(sky.state().night,0);assert.ok(scene.fog&&scene.environmentIntensity>.3);
 sky.setSun(skySunVector(0));assert.equal(sky.state().night,1);assert.ok(scene.environmentIntensity<.1);
 const stars=sky.root.children.find(o=>o.isPoints);assert.ok(stars.material.opacity>.9&&stars.userData.indirectCaptureExclude);
 const dome=sky.root.children.find(o=>o.isMesh);assert.equal(dome.material.uniforms.tianNight.value,1);assert.match(dome.material.fragmentShader,/tianSkyD\.z, -tianSkyD\.y/);
 sky.dispose();assert.equal(scene.fog,null);assert.equal(scene.children.length,0);
});
const squares=[];for(let x=0;x<20;x++)for(let y=0;y<16;y++)squares.push({x,y,z:0,tiles:[x>=7&&x<13&&y>=5&&y<10?'floor':y===0&&x===10?'path':'blends_natural_01_16']});
test('plot layout finds lawn, the built footprint and hedge gaps where a path leaves',()=>{
 const p=plotLayout(squares);assert.deepEqual(p.bounds,[0,0,20,16]);assert.equal(p.built.length,31);assert.deepEqual(p.gaps,[[10,0]]);
 assert.equal(p.distBuilt(7,5),0);assert.ok(p.distBuilt(0,0)>7);
});
test('garden tree has a broad crown on a flared trunk; distant trees are welded (soft) and dark',()=>{
 const t=gardenTree(31,7);t.wood.computeBoundingBox();const b=t.wood.boundingBox;
 assert.ok(b.max.x-b.min.x>4&&b.max.y-b.min.y>4,'crown spread');assert.ok(b.max.z>5.5&&b.max.z<9);assert.ok(t.leaves.length>500);
 const col=t.wood.attributes.color.array;assert.ok(Math.max(...col)<.1,'linear bark albedo stays dark');
 const d=distantTreeGeometry(false,4);assert.ok(d.index.count/3<1000,'cheap enough for hundreds of instances');assert.ok(d.attributes.position.count<d.index.count/2,'shared vertices give smooth normals');
 const leaf=leafCardPixels(64,3,{leaves:20,length:[.08,.05]});let opaque=0;for(let i=3;i<leaf.data.length;i+=4)opaque+=leaf.data[i]>0;assert.ok(opaque>64*64*.2&&opaque<64*64*.95,'cut-out leaves');
});
test('landscape builds meadow, tree line, garden trees, hedge with a gap, and grass near the house only',()=>{
 const scene=new THREE.Scene(),l=createExteriorLandscape(scene,{quality:.25}),r=l.rebuild(squares),names=l.root.children.map(c=>c.name);
 for(const n of ['meadow','tree-line','conifers','hedge','hedge-leaves','grass-blades'])assert.ok(names.includes(n),n);
 assert.ok(r.trees>=1&&r.blades>0);const hedge=l.root.children.find(c=>c.name==='hedge'),m=new THREE.Matrix4(),p=new THREE.Vector3();
 for(let i=0;i<hedge.count;i++){hedge.getMatrixAt(i,m);p.setFromMatrixPosition(m);assert.ok(!(Math.abs(p.x-10.5)<1&&p.y<0),'hedge open at the path');}
 l.dispose();assert.equal(scene.children.length,0);
});
test('gravel ballast: seamless, mostly stones with dark interstices, albedo kind',()=>{
 const g=gravelPixels({size:128,stones:12});let dark=0;for(let i=0;i<128*128;i++)if(g.color[i*4]<45)dark++;
 assert.ok(dark>128*128*.05&&dark<128*128*.45,'membrane shows between stones: '+dark);assert.ok(ALBEDO_SURFACES.has('gravel'));
 assert.deepEqual(gravelPixels({size:64,stones:8}).color,gravelPixels({size:64,stones:8}).color);assert.throws(()=>gravelPixels({stones:2}),/gravel/);
});
