import test from 'node:test';import assert from 'node:assert/strict';import {readFileSync} from 'node:fs';
import {setItemCatalog,Inventory,inventoryState} from '../src/inventory.js';
import {planBrushTeeth,completeBrushTeeth,useToiletPaper,planBandageWash,completeBandageWash,advanceHygiene,teethLabel,HYGIENE_LOSS_PER_HOUR} from '../src/daily-care.js';
import {isRubbish,rubbishStack} from '../src/rubbish.js';
import {presetFluid} from '../src/workshop-apply.js';
import {Simulation,newState} from '../src/simulation.js';
setItemCatalog(JSON.parse(readFileSync(new URL('../private-assets/items.json',import.meta.url))));
const basin={id:'basin',type:'water',name:'Sink',x:1,y:1,z:0,tile:'basin',props:{CustomName:'Sink',waterPiped:'',waterAmount:'20'}};
const toilet={id:'toilet',type:'water',name:'Toilet',x:2,y:1,z:0,tile:'toilet',props:{CustomName:'Toilet',waterPiped:'',waterAmount:'20'}};
function setup(objects=[basin]){const world={changes:{},revision:0,reindexBuilds(){},interactions:()=>objects,state(x,y,z,t){return this.changes[t]??{}},change(x,y,z,t,p){this.changes[t]={...this.changes[t],...p}},move:()=>false,lineClear:()=>true};
 const state=newState([1.5,1.5,0]);state.utilities={water:false};const sim=new Simulation(world,state,null,{spawnZombies:false});sim.spawnNearby=()=>{};return {world,state,sim,inv:sim.inventory};}
const run=(sim,seconds)=>{for(let i=0;i<seconds*10+5&&sim.action;i++)sim.tick(.1);};
test('brushing teeth needs a toothbrush, toothpaste and a washbasin, and uses a little reservoir water',()=>{
 const {world,state,inv}=setup();
 assert.match(planBrushTeeth(world,state,inv,basin).reason,/toothbrush and toothpaste/);
 inv.create('Base.Toothbrush');assert.match(planBrushTeeth(world,state,inv,basin).reason,/toothpaste/);
 inv.create('Base.Toothpaste');assert.equal(planBrushTeeth(world,state,inv,toilet).ok,false,'not at a toilet');
 assert.equal(completeBrushTeeth(world,state,inv,basin).ok,true);assert.equal(state.player.teethBrushedAt,state.time);
 assert.ok(world.changes.basin.waterAmount<20);assert.equal(inv.list('player').filter(i=>/Tooth/.test(i.type)).length,2,'brush and paste are kept');
 assert.equal(teethLabel(state.player,state.time+5*60),'Teeth brushed 5 h ago');
});
test('a carried roll of toilet paper is used once per visit; without it the hands come out dirtier',()=>{
 const without=setup([toilet]);assert.ok(without.sim.useToilet(toilet,'useToilet'));run(without.sim,25);assert.equal(without.state.player.handHygiene,10);
 const withPaper=setup([toilet]),roll=withPaper.inv.create('Base.ToiletPaper'),before=roll.currentUses;
 assert.ok(withPaper.sim.useToilet(toilet,'useToilet'));run(withPaper.sim,25);
 assert.equal(withPaper.state.player.handHygiene,25);assert.equal(withPaper.inv.state.items[roll.id].currentUses,before-1);
 assert.equal(useToiletPaper(new Inventory(inventoryState())).used,false);
});
test('washing hands with soap reaches fully clean and spends one use of soap; water alone stops at 80',()=>{
 const rinse=setup();assert.ok(rinse.sim.rinseHands(basin));run(rinse.sim,15);assert.equal(rinse.state.player.handHygiene,80);
 const wash=setup(),soap=wash.inv.create('Base.Soap2'),uses=soap.currentUses;wash.state.player.handHygiene=20;
 assert.ok(wash.sim.rinseHands(basin,soap.id));assert.equal(wash.sim.action.name,'Wash hands with soap');run(wash.sim,15);
 assert.equal(wash.state.player.handHygiene,100);assert.equal(wash.inv.state.items[soap.id].currentUses,uses-1);
});
test('dirty bandages are washed into clean ones at a sink, limited by reservoir water; favourites stay',()=>{
 const {world,state,inv,sim}=setup(),dirty=Array.from({length:4},()=>inv.create('Base.BandageDirty'));dirty[3].favorite=true;const cleanBefore=inv.list('player').filter(i=>i.type==='Base.Bandage').length;
 world.changes.basin={waterAmount:.6};const plan=planBandageWash(world,state,inv,basin);assert.equal(plan.ids.length,2,'0.6 L washes two');
 assert.equal(completeBandageWash(world,state,inv,basin,plan.ids).washed,2);
 const count=t=>inv.list('player').filter(i=>i.type===t).length;assert.equal(count('Base.BandageDirty'),2);assert.equal(count('Base.Bandage'),cleanBefore+2);
 assert.ok(world.changes.basin.waterAmount<.25);assert.match(planBandageWash(world,state,inv,basin).reason,/no water/);
 const mains=setup();for(let i=0;i<3;i++)mains.inv.create('Base.BandageDirty');mains.state.utilities={water:true};mains.world.changes={};
 assert.ok(mains.sim.washBandages(basin));run(mains.sim,20);assert.equal(mains.inv.list('player').filter(i=>i.type==='Base.BandageDirty').length,0);
});
test('body hygiene wears off with time but not while showering',()=>{
 const p={hygiene:100};advanceHygiene(p,120);assert.equal(p.hygiene,100-2*HYGIENE_LOSS_PER_HOUR);advanceHygiene(p,60,{showering:true});assert.equal(p.hygiene,100-2*HYGIENE_LOSS_PER_HOUR);
 advanceHygiene(p,100000);assert.equal(p.hygiene,0);const none={};advanceHygiene(none,60);assert.equal(none.hygiene,undefined);
});
test('spoiled food is rubbish, edible food and care items are not, and stacks never mix fresh with rotten',()=>{
 const inv=new Inventory(inventoryState()),burnt=inv.create('Base.Chicken',undefined,{burnt:true}),fresh=inv.create('Base.Apple'),rotten=inv.create('Base.Apple',undefined,{ageHours:24*40}),rotten2=inv.create('Base.Apple',undefined,{ageHours:24*40});
 assert.equal(isRubbish(burnt),true);assert.equal(isRubbish(rotten),true);assert.equal(isRubbish(fresh),false);
 for(const t of ['Base.Toothbrush','Base.Toothpaste','Base.ToiletPaper'])assert.equal(isRubbish(inv.create(t)),false,t);
 assert.deepEqual(rubbishStack(inv,rotten).sort(),[rotten.id,rotten2.id].sort());assert.deepEqual(rubbishStack(inv,fresh),[]);
});
test('stocked sealed goods arrive with their listed fluid; open vessels arrive empty',()=>{
 assert.equal(presetFluid('Base.Milk'),'CowMilk');assert.equal(presetFluid('Base.WaterBottle'),'Water');
 for(const t of ['Base.MugWhite','Base.Kettle','Base.Pot','Base.Bread'])assert.equal(presetFluid(t),null,t);
});
test('Hearth Studio stock covers the essentials found missing during the three-day stay',()=>{
 const supplies=JSON.parse(readFileSync(new URL('../tools/hearth-supplies.json',import.meta.url)));const has=t=>supplies.some(s=>s.type===t&&s.count>0);
 for(const t of ['Base.Soap2','Base.Toothbrush','Base.Toothpaste','Base.ToiletPaper','Base.BathTowel','Base.Bread','Base.Milk','Base.Bowl','Base.Plate','Base.MugWhite','Base.Trousers','Base.Underpants_White','Base.Socks_Ankle','Base.Book'])assert.ok(has(t),t);
 // Care items live in the bathroom (y ≥ entry row + 6), soap also at the kitchen sink.
 for(const t of ['Base.Toothbrush','Base.ToiletPaper','Base.BathTowel'])assert.ok(supplies.some(s=>s.type===t&&s.y>=11407),t);
 assert.equal(supplies.filter(s=>s.type==='Base.Soap2').length,2);
});
