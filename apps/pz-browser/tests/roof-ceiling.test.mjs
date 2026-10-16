import test from 'node:test';import assert from 'node:assert/strict';import {roofCeilingCovers} from '../src/roof-ceiling.js';
const roof=[{slopes:[{vertices:[[0,6,1.04],[0,0,1.04],[10,0,1.07]]},{vertices:[[10,0,1.07],[10,6,1.07],[0,6,1.04]]}]}];
test('a low roof over a storey supports ceiling fixtures inside its footprint only',()=>{
 assert.equal(roofCeilingCovers(roof,7,2,0),true);assert.equal(roofCeilingCovers(roof,0,0,0),true);
 assert.equal(roofCeilingCovers(roof,12,2,0),false,'outside the footprint');
 assert.equal(roofCeilingCovers(roof,7,2,1),false,'a roof below cannot hang a fixture on the storey above');
 assert.equal(roofCeilingCovers([{slopes:[{vertices:[[0,6,3],[0,0,3],[10,0,3]]}]}],2,2,0),false,'a roof two storeys up is not this ceiling');
 assert.equal(roofCeilingCovers(undefined,1,1,0),false);
});
