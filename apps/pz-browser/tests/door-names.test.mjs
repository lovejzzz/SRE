import test from 'node:test';import assert from 'node:assert/strict';import {doorName} from '../src/door-names.js';
const scene={rooms:[{id:'main',name:'Living studio',levelId:'g',rect:[0,0,10,6]},{id:'bath',name:'Bathroom',levelId:'g',rect:[7,6,10,8]}],walls:[{id:'entry',axis:'W',x:10,y:5,levelId:'g'},{id:'bathwall',axis:'N',x:8,y:6,levelId:'g'},{id:'lost',axis:'N',x:30,y:30,levelId:'g'}]};
test('doors are named from the rooms either side of their wall',()=>{
 assert.equal(doorName(scene,{hostWallId:'entry'}),'Entrance door');
 assert.equal(doorName(scene,{hostWallId:'bathwall'}),'Bathroom door');
 assert.equal(doorName(scene,{hostWallId:'lost'}),'Door');assert.equal(doorName(scene,{hostWallId:'missing'},'Gate'),'Gate');
});
