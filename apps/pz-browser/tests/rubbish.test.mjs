import test from 'node:test';import assert from 'node:assert/strict';import {readFileSync} from 'node:fs';
import {setItemCatalog,Inventory,inventoryState} from '../src/inventory.js';
import {rubbishStack,planDiscard,completeDiscard,planBagging,completeBagging,isRubbishBin,BIN_BAG,BIN_BAG_BOX} from '../src/rubbish.js';
import {Simulation,newState} from '../src/simulation.js';
setItemCatalog(JSON.parse(readFileSync(new URL('../private-assets/items.json',import.meta.url))));
const cans=(inv,n)=>Array.from({length:n},()=>inv.create('Base.TinCanEmpty'));
test('a carried stack goes into the bin together; favourites, equipped items and containers stay',()=>{
 const inv=new Inventory(inventoryState()),bin=inv.container('world:bin','Kitchen bin',10).id,c=cans(inv,5);c[4].favorite=true;inv.equip(c[3].id,'primary');inv.create('Base.Garbagebag');
 const ids=rubbishStack(inv,c[0]);assert.deepEqual(ids,[c[0].id,c[1].id,c[2].id]);
 const plan=planDiscard(inv,bin,ids);assert.equal(plan.ok,true);assert.equal(completeDiscard(inv,bin,plan.ids).moved,3);
 assert.equal(inv.list(bin).length,3);assert.equal(inv.list('player').filter(i=>i.type==='Base.TinCanEmpty').length,2);
});
test('a full bin refuses rubbish instead of overfilling; partial stacks fit what they can',()=>{
 const inv=new Inventory(inventoryState()),bin=inv.container('world:bin','Kitchen bin',.5).id,c=cans(inv,4);
 const plan=planDiscard(inv,bin,rubbishStack(inv,c[0]));assert.equal(plan.ids.length,2);assert.equal(plan.left,2);completeDiscard(inv,bin,plan.ids);
 assert.match(planDiscard(inv,bin,rubbishStack(inv,c[2])).reason,/full/);
});
test('tying a bag uses one bag from the box and moves the bin contents into a carried bin bag',()=>{
 const inv=new Inventory(inventoryState()),bin=inv.container('world:bin','Kitchen bin',10).id;for(const c of cans(inv,3))inv.transfer(c.id,bin);
 assert.match(planBagging(inv,bin).reason,/Carry a bin bag/);
 const box=inv.create(BIN_BAG_BOX),before=box.currentUses??20;const result=completeBagging(inv,bin);assert.equal(result.ok,true);assert.equal(result.moved,3);
 assert.equal(inv.list(bin).length,0);const bag=inv.state.items[result.bagId];assert.equal(bag.type,BIN_BAG);assert.equal(bag.container,'player');assert.equal(inv.list(bag.id).length,3);
 assert.ok((inv.state.items[box.id].currentUses)<before,'one bag was taken from the box');
 assert.match(planBagging(inv,bin).reason,/empty/);
});
test('simulation requires reach to a real bin and charges the summed transfer time',()=>{
 const bin={id:'bin',type:'container',distance:.4,x:1,y:1,z:0,tile:'tian_studio_pedal_bin_S_0',name:'Pedal bin',props:{container:'bin',ContainerCapacity:'10',CustomName:'Pedal bin',TianEmptyContainer:'true'}};
 let near=true;const world={changes:{},revision:0,reindexBuilds(){},interactions:()=>near?[bin]:[],state:()=>({}),move:()=>false,lineClear:()=>true};
 const sim=new Simulation(world,newState([1.5,1.5,0]),null,{spawnZombies:false}),c=cans(sim.inventory,3);
 assert.equal(isRubbishBin(bin),true);assert.equal(sim.throwAway({...bin,props:{container:'shelves'}},c[0].id),false);
 near=false;assert.equal(sim.throwAway(bin,c[0].id),false);near=true;
 assert.equal(sim.throwAway(bin,c[0].id),true);assert.equal(sim.action.name,'Throw away rubbish');assert.ok(sim.action.duration>0);
 sim.action.complete();sim.action=null;assert.equal(sim.inventory.list(sim.container(bin)).length,3);
 assert.equal(sim.tieBinBag(bin),false,'no bag carried');sim.inventory.create(BIN_BAG);assert.equal(sim.tieBinBag(bin),true);sim.action.complete();
 assert.equal(sim.inventory.list(sim.container(bin)).length,0);
});
test('only genuine rubbish is offered; full bottles, tools and washable bandages stay',()=>{
 const inv=new Inventory(inventoryState()),can=inv.create('Base.TinCanEmpty'),opener=inv.create('Base.TinOpener'),bandage=inv.create('Base.BandageDirty'),full=inv.create('Base.WaterBottle'),empty=inv.create('Base.WaterBottle');
 full.fluid.amount=full.fluid.capacity;empty.fluid.amount=0;
 assert.deepEqual(rubbishStack(inv,can),[can.id]);for(const item of [opener,bandage,full])assert.deepEqual(rubbishStack(inv,item),[],item.type);
 assert.ok(!rubbishStack(inv,empty).includes(full.id),'a full bottle never joins an empty stack');
});
test('a tied full bin bag can go into the outdoor bin; an empty bag is kept',()=>{
 const inv=new Inventory(inventoryState()),kitchen=inv.container('world:kitchen','Pedal bin',10).id,outdoor=inv.container('world:out','Wheelie bin',50).id;
 const spare=inv.create(BIN_BAG);assert.deepEqual(rubbishStack(inv,spare),[]);
 for(const c of cans(inv,4))inv.transfer(c.id,kitchen);const tied=completeBagging(inv,kitchen);const bag=inv.state.items[tied.bagId];
 assert.equal(bag.id,spare.id,'an empty carried bag is used before opening the box');
 assert.deepEqual(rubbishStack(inv,bag,{outdoor:false}),[],'a kitchen bin does not take a full bag');
 const plan=planDiscard(inv,outdoor,rubbishStack(inv,bag,{outdoor:true}));assert.equal(plan.ok,true);completeDiscard(inv,outdoor,plan.ids);
 assert.equal(inv.state.items[bag.id].container,outdoor);assert.equal(inv.list(bag.id).length,4,'the rubbish stays inside the tied bag');
});
