import test from 'node:test';import assert from 'node:assert/strict';
import {sceneExteriorDetails,tube,EXTERIOR_DETAIL} from '../src/exterior-architecture.js';
// One 4×3 m room, window on the south wall, door on the north wall, flat roof on top.
const scene={rooms:[{levelId:'g',rect:[0,0,4,3]}],openings:[{id:'win',kind:'window'},{id:'door',kind:'door'}]};
const wall=(id,a,b,extra={})=>({id,levelId:'g',materialId:'plaster',hostEndpoints:[a,b],height:3,thickness:.2,base:0,indices:[0,1,2],...extra});
const walls=[wall('S',[0,0],[4,0],{openingId:'win',opening:[1,.9,2.2,2.2]}),wall('E',[4,0],[4,3]),wall('N',[4,3],[0,3],{openingId:'door',opening:[1.5,0,2.4,2.1]}),wall('W',[0,3],[0,0])];
const roofs=[{role:'roof',roofId:'r',vertices:[[0,0,3.12],[4,0,3.12],[4,3,3.21],[0,3,3.21]]}];
const bounds=m=>[0,1,2].map(i=>[Math.min(...m.vertices.map(v=>v[i])),Math.max(...m.vertices.map(v=>v[i]))]);
test('exterior envelope: parapet, coping, plinth broken at the door, sill and corner downpipes away from the door',()=>{
 const out=sceneExteriorDetails(scene,walls,roofs,{cellSize:1}),by=role=>out.filter(m=>m.role===role);
 assert.equal(by('parapet').length,4);assert.equal(by('coping').length,4);assert.equal(by('plinth').length,4);
 for(const m of [...by('parapet'),...by('coping')])assert.equal(m.roofId,'r','hides with the roof cutaway');
 for(const m of out)assert.deepEqual(m.collision,[],'render-only: navigation stays with the walls');
 const parapet=bounds(by('parapet')[0]);assert.ok(parapet[2][0]>=3-1e-9&&parapet[2][1]>3.21+.2,'rises above the roof skin');
 const coping=bounds(by('coping').find(m=>m.id==='S:coping'));assert.ok(coping[1][0]<-.1-EXTERIOR_DETAIL.copingOverhang+1e-6,'coping overhangs the outer face');
 // South plinth sits on the outside (y<0); north plinth leaves the doorway open.
 const south=bounds(by('plinth').find(m=>m.hostWallId==='S'));assert.ok(south[1][1]<=-.1+1e-6&&south[2][1]<.4);
 const north=by('plinth').find(m=>m.hostWallId==='N');assert.ok(!north.vertices.some(v=>v[0]>1.7&&v[0]<2.3&&v[1]>3),'threshold is clear');
 assert.ok(north.uv&&north.material.texture.kind==='wall-paint');
 const sill=by('sill');assert.equal(sill.length,1);assert.equal(sill[0].hostWallId,'S');const sb=bounds(sill[0]);assert.ok(Math.abs(sb[2][1]-.925)<1e-9&&sb[1][0]<-.1-.04,'sill (with end upstands) projects under the window');
 const pipes=by('downpipe');assert.equal(pipes.length,2);for(const p of pipes){const b=bounds(p);assert.ok(b[1][1]<0,'pipes on the south face, away from the north door');assert.ok(b[2][1]>2.8&&b[2][0]<.2);}
});
test('internal walls and walls without a roof get no envelope detail beyond the plinth',()=>{
 const internal=wall('I',[2,0],[2,3]);assert.equal(sceneExteriorDetails(scene,[internal],roofs,{cellSize:1}).length,0);
 const garden=sceneExteriorDetails(scene,walls,[],{cellSize:1});assert.deepEqual([...new Set(garden.map(m=>m.role))].sort(),['plinth','sill']);
});
test('tube is closed and sized',()=>{const t=tube([0,0,0],[0,0,2],.05);assert.equal(t.indices.length%3,0);const r=Math.max(...t.vertices.map(v=>Math.hypot(v[0],v[1])));assert.ok(Math.abs(r-.05)<1e-9);});
import {exteriorFacadeRuns,trellisSpan,wallExteriorSide} from '../src/exterior-architecture.js';
import {openingVolume} from '../src/opening-volume.js';
test('blank exterior runs merge collinear segments and carry a trellis; a water butt stands by the first downpipe',()=>{
 const big={rooms:[{levelId:'g',rect:[0,0,8,4]}],openings:[]},segs=[];for(let x=0;x<8;x++)segs.push(wall('S'+x,[x,0],[x+1,0]));
 segs.push(wall('E',[8,0],[8,4]),wall('N',[8,4],[0,4]),wall('W',[0,4],[0,0]));
 const runs=exteriorFacadeRuns(big,segs,{cellSize:1}),south=runs.find(r=>r.wallIds.includes('S0'));
 assert.equal(south.length,8);assert.equal(south.wallIds.length,8);assert.deepEqual(south.out.map(v=>Math.round(v)+0),[0,-1]);
 const span=trellisSpan(south);assert.ok(span&&span.u1-span.u0<=3.2&&span.z1<=3-.35);assert.equal(trellisSpan({...south,length:3}),null);
 const out=sceneExteriorDetails(big,segs,[{role:'roof',roofId:'r',vertices:[[0,0,3.1],[8,0,3.1],[8,4,3.1],[0,4,3.1]]}],{cellSize:1});
 const trellis=out.filter(m=>m.role==='trellis');assert.ok(trellis.length>=2);for(const t of trellis)assert.deepEqual(t.collision,[]);
 assert.equal(out.filter(m=>m.role==='water-butt').length,1);
 assert.equal(wallExteriorSide(big,segs[0],{cellSize:1}),-1);assert.equal(wallExteriorSide(big,wall('I',[4,0],[4,4]),{cellSize:1}),0);
});
test('a wall that is wholly glazing still gets parapet and coping',()=>{
 const glazed=wall('G',[0,0],[4,0],{indices:[],openingId:'win',opening:[0,0,4,3]});
 const out=sceneExteriorDetails(scene,[glazed,...walls.slice(1)],roofs,{cellSize:1});assert.ok(out.some(m=>m.id==='G:parapet'));assert.ok(out.some(m=>m.id==='G:coping'));
});
test('entrance doors: flush dark leaf, grooves and a pull bar outside, mouldings and lever inside',()=>{
 const args={id:'d',a:[0,0],b:[2,0],base:0,aperture:[.5,0,1.4,2.1],kind:'door',frameWidth:.05,frameDepth:.1,panelDepth:.035};
 const inner=openingVolume(args),entrance=openingVolume({...args,exteriorSide:-1});
 assert.ok(!inner.some(p=>/pull|groove/.test(p.id)));assert.equal(inner.find(p=>p.role==='leaf'&&p.id==='d:panel').material,undefined);
 const leaf=entrance.find(p=>p.id==='d:panel');assert.ok(leaf.material.color<0x404040,'dark composite leaf');
 const pull=entrance.filter(p=>/:pull/.test(p.id)),ys=pull.flatMap(p=>p.vertices.map(v=>v[1]));assert.ok(pull.length===3&&Math.max(...ys)<0,'pull bar on the outside (-y)');
 assert.equal(entrance.filter(p=>/groove/.test(p.id)).length,5);
 const mould=entrance.filter(p=>/moulding/.test(p.id)).flatMap(p=>p.vertices.map(v=>v[1]));assert.ok(Math.min(...mould)>0,'mouldings only inside (+y)');
});
