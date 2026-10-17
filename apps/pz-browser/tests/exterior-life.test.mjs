import test from 'node:test';import assert from 'node:assert/strict';import * as THREE from 'three';
import {plotLayout,terrainHeight,chunkInstances,normalFromCutout} from '../src/exterior-landscape.js';
import {buildExteriorProps} from '../src/exterior-props.js';
import {buildExteriorContext,asphaltPixels} from '../src/exterior-context.js';
import {ATMOSPHERE,installCloudShadow,installWetness,createWeather,weatherFor,createBirds,ShaftsShader} from '../src/atmosphere-effects.js';
const squares=[];for(let x=0;x<26;x++)for(let y=0;y<30;y++)squares.push({x,y,z:0,tiles:[x>=7&&x<17&&y>=8&&y<16?'floor':(y===0&&x===10)?'floors_exterior_tilesandstone_01_0':'blends_natural_01_16']});
const plot=plotLayout(squares),door={p:[12,16.1],out:[0,1],width:.9,top:2.1};
const bounds=o=>new THREE.Box3().setFromObject(o);
test('props: every exterior door gets canopy, step, mat, letterbox and number; garden life is placed on the lawn',()=>{
 const g=buildExteriorProps({plot,facades:[{a:[7,8],b:[17,8],length:10,t:[1,0],out:[0,-1],thickness:.2},{a:[7,16],b:[7,8],length:8,t:[0,-1],out:[-1,0],thickness:.2}],doors:[door]});
 assert.deepEqual(g.userData.placed,{doors:1,bike:true,clothesline:true,barrow:true});
 const canopy=bounds(g.getObjectByName('prop-steel'));assert.ok(canopy.max.z>2.3&&canopy.max.y>16.9,'canopy projects over the door');
 const step=bounds(g.getObjectByName('prop-concrete'));assert.ok(step.min.y>=16.1-1e-6&&step.max.z<=.13,'step outside, at ground');
 const lines=bounds(g.getObjectByName('prop-white'));assert.ok(lines.max.z>1.7&&lines.max.z<1.9,'washing line height');
 for(const m of g.children)assert.ok(m.geometry.attributes.position.count>0);
 assert.equal(buildExteriorProps({plot,facades:[{a:[7,8],b:[17,8],length:10,t:[1,0],out:[0,-1],thickness:.2}],doors:[],hoseReel:false}).getObjectByName('prop-hoseGreen'),undefined);
});
test('surroundings: lane on the gate side, drive into the gap, poles and cottages kept clear of the plot',()=>{
 const g=buildExteriorContext({plot,terrainHeight,doors:[door],paving:[[10,0]]});
 assert.equal(g.userData.side,'S');const road=bounds(g.getObjectByName('context-asphalt'));assert.ok(road.max.y<plot.bounds[1]-8&&road.min.y>plot.bounds[1]-16);
 assert.ok(g.userData.blocked(10,-12),'lane is blocked for planting');assert.ok(!g.userData.blocked(10,5),'the garden is not');
 const cot=bounds(g.getObjectByName('context-tile'));assert.ok(cot.max.y<plot.bounds[1]-15,'cottages across the lane');
 assert.ok(g.getObjectByName('worn-path').count>5);assert.ok(g.userData.weeds.length>=0);
 const a=asphaltPixels(64,1);let light=0;for(let i=0;i<a.data.length;i+=4)light+=a.data[i]>150;assert.ok(light>20,'painted lines');
});
test('chunking keeps every instance and gives each chunk a bound for culling; cut-out normals point out',()=>{
 const im=new THREE.InstancedMesh(new THREE.PlaneGeometry(),new THREE.MeshBasicMaterial(),200),m=new THREE.Matrix4();for(let i=0;i<200;i++){m.makeTranslation(i%20*3,Math.floor(i/20)*3,0);im.setMatrixAt(i,m);}
 const ch=chunkInstances(im,10,50);assert.equal(ch.reduce((s,c)=>s+c.count,0),200);assert.ok(ch.length>4&&ch.every(c=>c.boundingSphere&&c.userData.maxDist===50));
 const px=new Uint8Array(16*16*4);for(let y=4;y<12;y++)for(let x=4;x<12;x++)px.set([90,140,60,255],(y*16+x)*4);const n=normalFromCutout({width:16,height:16,data:px});const z=n.image.data[(8*16+8)*4+2];assert.ok(z>200);
});
test('atmosphere: cloud shadows and wetness patch shaders; weather states, rain and drying; birds fly; shafts shader',()=>{
 const compile=mt=>{const sh={uniforms:{},vertexShader:THREE.ShaderLib.physical.vertexShader,fragmentShader:THREE.ShaderLib.physical.fragmentShader};mt.onBeforeCompile(sh,{});return sh;};
 const s=compile(installWetness(installCloudShadow(new THREE.MeshStandardMaterial())));assert.equal(s.uniforms.tatCloud,ATMOSPHERE.cloudShadow);assert.match(s.fragmentShader,/reflectedLight\.directDiffuse\*=k/);assert.match(s.fragmentShader,/twtPuddle/);
 assert.ok(['clear','overcast','rain'].includes(weatherFor(15*60)));let rainy=0;for(let d=0;d<200;d++)rainy+=weatherFor(d*1440+15*60)==='rain';assert.ok(rainy>10&&rainy<100);
 const scene=new THREE.Scene(),w=createWeather(scene),cam=new THREE.PerspectiveCamera();w.set('rain');w.setTime(600);for(let i=0;i<300;i++)w.update(cam,.5);assert.ok(ATMOSPHERE.wetness.value>.5&&scene.getObjectByName('rain').visible);
 w.set('clear');w.setTime(600);for(let i=0;i<300;i++)w.update(cam,.5);assert.ok(ATMOSPHERE.wetness.value<.5&&!scene.getObjectByName('rain').visible);w.dispose();ATMOSPHERE.wetness.value=0;
 const b=createBirds(scene,[0,0]),p0=b.group.children[0].position.clone();b.update(1);assert.ok(b.group.children[0].position.distanceTo(p0)>.5);b.dispose();
 assert.match(ShaftsShader.fragmentShader,/sunUV/);
});
