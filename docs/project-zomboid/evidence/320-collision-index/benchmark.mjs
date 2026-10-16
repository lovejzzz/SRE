// Synthetic Node CPU evidence only; not browser rendering/latency acceptance.
import {createSolidIndex} from '../../../../apps/pz-browser/src/solid-index.js';
import {prismSolid} from '../../../../apps/pz-browser/src/prism-solid.js';
import {movePhysicalBody} from '../../../../apps/pz-browser/src/physical-body.js';
import assert from 'node:assert/strict';
const results=[];
for(const count of [2000,10000,50000]){
 const solids=Array.from({length:count},(_,i)=>{const x=(i%250)*3,y=Math.floor(i/250)*3;return prismSolid({polygon:[[x,y],[x+1,y],[x+1,y+1],[x,y+1]],minZ:0,maxZ:3});});
 const t=performance.now(),index=createSolidIndex(solids),buildMs=performance.now()-t;
 const p=[1.5,1.5,1],d=[-1,-1,0],half=[.25,.25,.9];
 assert.deepEqual(movePhysicalBody(solids,p,d,half),movePhysicalBody(index,p,d,half));
 const run=s=>{const t=performance.now();for(let i=0;i<100;i++)movePhysicalBody(s,p,d,half);return (performance.now()-t)/100;};
 results.push({count,buildMs,candidates:index.query(p,p.map((v,i)=>v+d[i]),half).length,fullScanMs:run(solids),indexedMs:run(index)});
}
console.log(JSON.stringify({environment:'Node synthetic CPU benchmark; 100 repeated local sweeps per size, no rendering; timings not browser budgets',results},null,2));
