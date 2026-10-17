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
import {tuftPixels,flowerPixels,mulchPixels,barkPixels,crossGeometry} from '../src/exterior-landscape.js';
import {withContactVisibility} from '../src/contact-shading.js';
test('planting textures: cut-out tufts and flowers grow upward on cards; mulch is opaque; bark tiles',()=>{
 const alphaRows=p=>{const n=p.width,top=[...Array(n*n/4).keys()].filter(i=>p.data[i*4+3]).length,bottom=[...Array(n*n/4).keys()].filter(i=>p.data[(n*n*3/4+i)*4+3]).length;return [top,bottom];};
 for(const p of [tuftPixels(64,1),flowerPixels('daisy',64,2)]){const [top,bottom]=alphaRows(p);assert.ok(bottom>top,'rows are written top-down: dense base at the image bottom');}
 assert.throws(()=>flowerPixels('rose'),/Unknown flower/);
 const g=crossGeometry(3),uv=g.attributes.uv,pos=g.attributes.position;for(let i=0;i<uv.count;i++)assert.equal(uv.getY(i),1-pos.getZ(i),'v is flipped so the image bottom sits on the ground');
 const m=mulchPixels(64,1);for(let i=3;i<m.data.length;i+=4)assert.equal(m.data[i],255);
 const b=barkPixels(64,3);assert.equal(b.relief.length,b.data.length);const col=x=>b.data[(10*64+x)*4];assert.ok(Math.abs(col(0)-col(63))<60,'wraps around the trunk');
});
test('the contact-occlusion pass hides cut-out foliage, whose override material would ignore alphaTest',()=>{
 const scene=new THREE.Scene(),leaf=new THREE.Mesh(new THREE.PlaneGeometry(),new THREE.MeshStandardMaterial({alphaTest:.4})),wall=new THREE.Mesh(new THREE.BoxGeometry(),new THREE.MeshStandardMaterial());scene.add(leaf,wall);
 withContactVisibility(scene,{shadowMap:{}},()=>{assert.equal(leaf.visible,false);assert.equal(wall.visible,true);});assert.equal(leaf.visible,true);
});
import {needlePixels} from '../src/exterior-landscape.js';
test('tree line carries crown cards; climbers grow on long blank facades only; lawn blades cover the whole lawn',()=>{
 const d=distantTreeGeometry(false,4),c=distantTreeGeometry(true,3);assert.ok(d.userData.cards.length>=80&&c.userData.cards.length>=30);
 for(const k of c.userData.cards)assert.ok(k.n[2]<0,'conifer sprays droop');
 const nd=needlePixels(64,2);let a=0;for(let i=3;i<nd.data.length;i+=4)a+=nd.data[i]>0;assert.ok(a>100&&a<64*64*.6);
 const scene=new THREE.Scene(),l=createExteriorLandscape(scene,{quality:.3}),facade={a:[7,5],b:[13,5],length:6,t:[1,0],out:[0,-1],thickness:.2,base:0,top:3,levelId:'g',wallIds:['w']};
 const r=l.rebuild(squares,{facades:[facade]});assert.ok(r.climberLeaves>50);
 const leaves=l.root.children.find(o=>o.name==='climber-leaves'),m=new THREE.Matrix4(),p=new THREE.Vector3();for(let i=0;i<leaves.count;i++){leaves.getMatrixAt(i,m);p.setFromMatrixPosition(m);assert.ok(p.y<5-.1+.01&&p.y>4.6,'on the outer face');}
 assert.equal(l.rebuild(squares,{facades:[{...facade,length:3,b:[10,5]}]}).climberLeaves,0);
 const lawn=plotLayout(squares).lawn.length;assert.ok(r.blades>lawn*100*.3*.5,'blades beyond 8 m too');l.dispose();
});
