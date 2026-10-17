import test from 'node:test';import assert from 'node:assert/strict';
import {readVolume} from './helpers/volume-delivery.mjs';
import {sceneFurnitureVolumes} from '../src/scene-furniture-volumes.js';
import {createScenePlacementValidator} from '../src/scene-placement-validator.js';
// 505j: fixtures_bathroom_01_2 (Facing W, attachedE) rendered with its seat to the east wall.
// PZ Facing names the side the front faces; the attached wall is behind it.
const facingVector={S:[0,1],N:[0,-1],E:[1,0],W:[-1,0]},behind={S:'N',N:'S',E:'W',W:'E'};
const centroid=meshes=>{const v=meshes.flatMap(m=>m.vertices);return [0,1].map(i=>v.reduce((s,p)=>s+p[i],0)/v.length);};
const near=(a,b,label)=>a.forEach((v,i)=>assert.ok(Math.abs(v-b[i])<1e-9,`${label}: ${a} ≠ ${b}`));
const X=5,Y=5;
// Only the wall the fixture is attached to: PZ walls are N/W-axis segments on cell
// edges, so the east wall of cell X is the W-axis wall at X+1 (0.2 m thick, centred).
// N/S run too: the toilet cistern used to sit 6 cm inside that wall in every direction.
const attachedWall={E:{axis:'W',x:X,y:Y},W:{axis:'W',x:X+1,y:Y},S:{axis:'N',x:X,y:Y},N:{axis:'N',x:X,y:Y+1}};
function room(facing,objects=[]){return {id:'bath',levels:[{id:'g',index:0}],rooms:[],openings:[],verticalLinks:[],roofVolumes:[],objects,walls:[{id:'wall',levelId:'g',tile:'walls',...attachedWall[facing]}]};}
function place(name,facing){
 const asset=readVolume(name),parts=asset.recipe.sourceLayout[facing],object={id:name,levelId:'g',x:X,y:Y,parts};
 assert.equal(asset.recipe.migration[facing][0],parts[0].tile);
 return {asset,object,meshes:sceneFurnitureVolumes(room(facing,[object]),{squares:[]},{},[asset],{cellSize:1,storeyHeight:3})};
}
for(const [name,front,back] of [['toilet','seat','cistern'],['sink','basin','tap-riser'],['counter','drawer-pull:bar','carcass']])for(const facing of ['E','W','S','N']){
 test(`${name} ${facing}: front faces ${facing}, back sits on the attached ${behind[facing]} wall`,()=>{
  const {asset,object,meshes}=place(name,facing),[fx,fy]=facingVector[facing];
  const part=id=>meshes.filter(m=>m.id===`furniture:${name}:${id}`),f=centroid(part(front)),b=centroid(part(back));
  // The functional front lies further along Facing than the wall-side body.
  assert.ok((f[0]-b[0])*fx+(f[1]-b[1])*fy>.05,`${front} is not in front of ${back}`);
  assert.ok(Math.abs((f[0]-b[0])*fy-(f[1]-b[1])*fx)<.05,'front/back axis is not aligned with Facing');
  const use=meshes.find(m=>m.fixtureUse)?.fixtureUse;
  if(name==='counter')assert.equal(use,undefined);
  else{
   near(use.forward,[fx,fy,0],'fixtureUse.forward');if(use.seat)near(use.seat.forward,[fx,fy,0],'seat.forward');
   // The approach point is on the open side, at the front face, not behind the fixture.
   const v=meshes.flatMap(m=>m.vertices),frontmost=Math.max(...v.map(p=>p[0]*fx+p[1]*fy));
   const reach=use.point[0]*fx+use.point[1]*fy-frontmost;assert.ok(reach>=-.02&&reach<.15,`approach point is ${reach} m from the front face`);
   assert.ok(Math.abs(use.point[0]*fy-use.point[1]*fx-((X+.5)*fy-(Y+.5)*fx))<.15,'approach point is off the fixture centreline');
   if(use.handTarget)assert.ok(use.handTarget[0]*fx+use.handTarget[1]*fy<use.point[0]*fx+use.point[1]*fy,'hand target is outside the basin');
  }
  // The back stands just off the attached wall's inner face, on the open side of it.
  const v=meshes.flatMap(m=>m.vertices),rear=Math.min(...v.map(p=>p[0]*fx+p[1]*fy)),wallFace={E:X,S:Y,W:-(X+1),N:-(Y+1)}[facing]+.1;
  assert.ok(rear>=wallFace-1e-9&&rear<wallFace+.05,`${name} ${facing} rear ${rear} vs wall face ${wallFace}`);
  const before={sceneDocument:room(facing),squares:[]},after={sceneDocument:room(facing,[object]),squares:[]};
  assert.deepEqual(createScenePlacementValidator([asset])(before,after,{}),{ok:true,coverage:'mapped-furniture',unmapped:[]});
 });
}
test('studio pieces keep the E/W turn their catalogue sprites and saves were authored with',()=>{
 // tools/make_studio_assets.py draws the Facing:'E' studio sprite with its front to the west.
 for(const [name,read] of [['studio-upright-piano',m=>m.pianoKeyboard.forward]]){
  const asset=readVolume(name);
  for(const [facing,expected] of [['S',[0,1,0]],['N',[0,-1,0]],['E',[-1,0,0]],['W',[1,0,0]]]){
   const meshes=sceneFurnitureVolumes({levels:[{id:'g',index:0}],objects:[{id:name,levelId:'g',x:X,y:Y,parts:asset.recipe.sourceLayout[facing]}]},{squares:[]},{},[asset],{cellSize:1,storeyHeight:3});
   near(read(meshes.find(m=>m.pianoKeyboard)),expected,`${name} ${facing}`);
  }
 }
});
test('one rotation turns studio and PZ pieces the same physical way',async()=>{
 const {readFileSync}=await import('node:fs'),{StructuredWorkshopModel}=await import('../src/structured-workshop-model.js'),{workshopCatalog}=await import('../src/workshop-model.js'),{installStudioAssets}=await import('../src/studio-assets.js');
 const properties={...JSON.parse(readFileSync(new URL('../private-assets/world/properties.json',import.meta.url))),floor:{solidfloor:''},wall_0:{WallW:''},wall_1:{WallN:''}},atlas=JSON.parse(readFileSync(new URL('../private-assets/atlas.json',import.meta.url)));installStudioAssets(properties,atlas);
 const catalog=workshopCatalog(properties,atlas,{}).entries,assets=['toilet','studio-upright-piano','studio-sectional-sofa'].map(readVolume);
 const m=new StructuredWorkshopModel({version:1,squares:[],items:[]},[0,0,20,20],properties,catalog);m.begin('Room');m.structure({type:'room.add',room:{id:'room',name:'Room',levelId:'level:0',z:0,rect:[1,1,18,18],floorTile:'floor',wallN:'wall_1',wallW:'wall_0'}});m.commit();
 m.begin('Furnish');for(const [id,x,y] of [['tile:fixtures_bathroom_01_0',3,3],['tile:tian_studio_upright_piano_S_0',5,3],['tile:tian_studio_sectional_sofa_S_0',3,8]])assert.equal(m.place(catalog.find(e=>e.id===id),x,y,0).ok,true);m.commit();
 const forward=()=>sceneFurnitureVolumes({levels:m.scene.levels,objects:m.scene.objects},{squares:[]},{},assets,{cellSize:1,storeyHeight:3}).flatMap(v=>v.fixtureUse?[v.fixtureUse.forward]:v.pianoKeyboard?[v.pianoKeyboard.forward]:[]).map(f=>f.map(n=>Math.round(n)+0));
 const ids=m.scene.objects.map(o=>o.id);
 // turn() maps +x to +y: S-facing fronts end up facing west, and the L-shaped sofa footprint rotates with them.
 for(const expected of [[-1,0,0],[0,-1,0],[1,0,0],[0,1,0]]){m.begin('Rotate');assert.equal(m.structure({type:'objects.rotate',ids,turns:1}).ok,true);m.commit();assert.deepEqual(forward(),[expected,expected]);}
});
