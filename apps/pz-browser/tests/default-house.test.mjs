import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {validateHousePlan} from '../src/workshop-model.js';
import {validateSceneDocument} from '../src/scene-document.js';
import {RESIDENCE} from '../src/residence.js';
// The house every new visitor moves into (main.js DEFAULT_HOUSE). It must be the 3D
// Hearth Studio: without a scene structure the site falls back to the 2D title menu.
const plan=JSON.parse(fs.readFileSync(new URL('../assets/houses/hearth-studio/house.json',import.meta.url)));
test('default house: Hearth Studio, a valid plan in the residence bounds, with a 3D structure',()=>{
 assert.equal(plan.name,'Hearth Studio');
 validateHousePlan(plan,RESIDENCE.bounds);validateSceneDocument(plan.sceneDocument);
 assert.ok(plan.sceneDocument.walls.length>=30&&plan.sceneDocument.rooms.length>=2&&plan.sceneDocument.objects.length>=50);
 const [x0,y0,x1,y1]=RESIDENCE.bounds;assert.ok(plan.spawn.x>=x0&&plan.spawn.x<x1&&plan.spawn.y>=y0&&plan.spawn.y<y1,'spawn inside the residence');
 // The desk computer the portfolio lives on is part of the house.
 assert.ok(plan.sceneDocument.objects.some(o=>/tian_studio_workstation/.test(o.assetId)),'desk computer present');
});
