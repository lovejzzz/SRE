import test from 'node:test';import assert from 'node:assert/strict';import * as THREE from 'three';
import {migrateHousePlan,exportSceneDocument,importSceneDocument,validateSceneDocument} from '../src/scene-document.js';
import {addRectangularRoom} from '../src/scene-structure.js';
import {applySceneOperation} from '../src/scene-session.js';
import {resolveExterior,validateExterior,EXTERIOR_DEFAULTS} from '../src/scene-exterior.js';
import {createExteriorLandscape} from '../src/exterior-landscape.js';
import {sceneExteriorDetails} from '../src/exterior-architecture.js';
import {exteriorWalls} from '../src/workshop-exterior-panel.js';
const blank=()=>{const s=migrateHousePlan({version:1,squares:[],items:[]},[0,0,20,20]);s.levels.push({id:'ground',index:0,height:null,elevation:null});return s;};
const house=()=>addRectangularRoom(blank(),{id:'a',name:'a',rect:[4,4,10,8],levelId:'ground',floorTile:'floor',wallN:'wall_1',wallW:'wall_0'});
test('old saves (no exterior) resolve to the automatic defaults and stay valid',()=>{
 const s=house();assert.equal(s.exterior,undefined);validateSceneDocument(s);assert.deepEqual(resolveExterior(s),JSON.parse(JSON.stringify(EXTERIOR_DEFAULTS)));
});
test('exterior commands edit a sparse override that survives export and import (a replicated house gets the same garden)',()=>{
 let s=house();const wall=exteriorWalls(s)[0];assert.ok(wall,'exterior walls listed for climbers');
 s=applySceneOperation(s,{type:'exterior.set',exterior:{hedge:{height:1.6},borders:{planting:'lavender'},life:{enabled:false},weathering:.4,envelope:{waterButt:false}}});
 s=applySceneOperation(s,{type:'exterior.tree.add',tree:{id:'oak',x:2,y:15,height:9,seed:7}});
 s=applySceneOperation(s,{type:'exterior.climber.set',wallId:wall.id,on:true});
 const copy=importSceneDocument(exportSceneDocument(s)),x=resolveExterior(copy);
 assert.equal(x.hedge.height,1.6);assert.equal(x.hedge.enabled,true,'unset fields keep defaults');assert.equal(x.borders.planting,'lavender');assert.equal(x.life.enabled,false);assert.equal(x.weathering,.4);assert.equal(x.envelope.waterButt,false);assert.equal(x.envelope.parapet,true);
 assert.deepEqual(x.gardenTrees,{mode:'listed',trees:[{id:'oak',x:2,y:15,height:9,seed:7}]});assert.deepEqual(x.climbers,{mode:'listed',walls:[wall.id]});
 s=applySceneOperation(s,{type:'exterior.tree.remove',id:'oak'});assert.equal(resolveExterior(s).gardenTrees.trees.length,0);
 assert.throws(()=>applySceneOperation(s,{type:'exterior.climber.set',wallId:'wall:nope',on:true}),/Wall not found/);
 s=applySceneOperation(s,{type:'exterior.reset'});assert.equal(s.exterior,undefined);
});
test('invalid exterior settings are rejected before they reach a save',()=>{
 for(const bad of [{version:2},{version:1,hedge:{height:9}},{version:1,borders:{planting:'roses'}},{version:1,gardenTrees:{mode:'some'}},{version:1,wat:{}},{version:1,weathering:2},{version:1,hedge:{enabled:'yes'}},{version:1,gardenTrees:{trees:[{id:'a',x:1,y:1,colour:'red'}]}}])
  assert.throws(()=>validateExterior(bad),/Invalid exterior/,JSON.stringify(bad));
 const s=house();s.exterior={version:1,hedge:{height:99}};assert.throws(()=>validateSceneDocument(s),/Invalid exterior/);
});
const squares=[];for(let x=0;x<26;x++)for(let y=0;y<30;y++)squares.push({x,y,z:0,tiles:[x>=7&&x<17&&y>=8&&y<16?'floor':'blends_natural_01_16']});
const facade={a:[7,8],b:[17,8],length:10,t:[1,0],out:[0,-1],thickness:.2,base:0,top:3,levelId:'g',wallIds:['wall:w1']};
test('the landscape follows the saved design: hedge, borders, listed trees, climbers, sections',()=>{
 const names=x=>{const sc=new THREE.Scene(),l=createExteriorLandscape(sc,{quality:.2,scanned:false});const st=l.rebuild(squares,{facades:[facade],exterior:x});const n=l.root.children.map(c=>c.name);const trees=l.root.children.filter(c=>c.name==='garden-tree').map(c=>[c.position.x,c.position.y]);l.dispose();return {n,st,trees};};
 const auto=names(resolveExterior(null));assert.ok(auto.n.includes('hedge')&&auto.n.includes('climber-leaves')&&auto.st.trees>0);
 const custom=resolveExterior({exterior:{version:1,hedge:{enabled:false},borders:{planting:'box'},gardenTrees:{mode:'listed',trees:[{id:'t',x:3,y:4,height:8,seed:2}]},climbers:{mode:'none'},treeLine:{enabled:false},meadow:{enabled:false},hills:{enabled:false}}});
 const c=names(custom);for(const gone of ['hedge','hedge-leaves','climber-leaves','tree-line','conifers','meadow-tufts','hills','perennials-lavender'])assert.ok(!c.n.includes(gone),gone);
 assert.deepEqual(c.trees,[[3,4]],'tree exactly where the design puts it');assert.ok(c.n.includes('shrubs'));
 const listed=names(resolveExterior({exterior:{version:1,climbers:{mode:'listed',walls:['wall:other']}}}));assert.ok(!listed.n.includes('climber-leaves'),'only listed walls grow climbers');
});
test('envelope details follow the saved design',()=>{
 const scene={rooms:[{levelId:'g',rect:[0,0,8,4]}],openings:[],walls:[],exterior:{version:1,envelope:{parapet:false,downpipes:false,waterButt:false},climbers:{mode:'none'}}};
 const wall=(id,a,b)=>({id,levelId:'g',materialId:'plaster',hostEndpoints:[a,b],height:3,thickness:.2,base:0,indices:[0,1,2]});
 const segs=[];for(let x=0;x<8;x++)segs.push(wall('S'+x,[x,0],[x+1,0]));segs.push(wall('E',[8,0],[8,4]),wall('N',[8,4],[0,4]),wall('W',[0,4],[0,0]));
 const roofs=[{role:'roof',roofId:'r',vertices:[[0,0,3.1],[8,0,3.1],[8,4,3.1],[0,4,3.1]]}],roles=new Set(sceneExteriorDetails(scene,segs,roofs,{cellSize:1}).map(m=>m.role));
 assert.deepEqual([...roles].sort(),['plinth']);
});
