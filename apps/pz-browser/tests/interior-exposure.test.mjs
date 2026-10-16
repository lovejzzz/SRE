import test from 'node:test';import assert from 'node:assert/strict';
import {INTERIOR_EXPOSURE,probeKey,interiorGain,stepExposure} from '../src/interior-exposure.js';
// Measured505 probe DC terms at Day18 13:04 (main room low/high layers + bathroom).
const lampsOn=[[.1778,.0835,.032],[.1209,.0655,.0254],[.1861,.1122,.0467],[.1059,.0514,.0199],[.2,.0873,.0307],[.1435,.0776,.0292],[.2155,.1384,.0655],[.1574,.0838,.0346],[.6348,.3967,.1718],[.3695,.2267,.0924]];
const lampsOff=[[.0196,.0146,.0094],[.0375,.0264,.0134],[.0084,.0053,.0024],[.0161,.0129,.0085],[.0228,.0168,.0091],[.052,.0367,.0177],[.0073,.0054,.0029],[.0634,.0469,.0247],[.0107,.0074,.0035],[.0255,.0181,.0089]];
test('lamp-lit rooms keep unit gain; window-lit interiors adapt brighter but stay ordered',()=>{
 const on=interiorGain(probeKey(lampsOn)),off=interiorGain(probeKey(lampsOff));
 assert.ok(Math.abs(on-1)<.05,'lamps-on interior keeps the reviewed exposure');
 assert.ok(off>4,'window-lit interior gains more than two stops');
 assert.ok(probeKey(lampsOff)*off<probeKey(lampsOn)*on,'partial adaptation keeps lamp-lit rooms brighter');
});
test('night darkness and empty fields are clamped rather than amplified without bound',()=>{
 assert.equal(interiorGain(1e-6),INTERIOR_EXPOSURE.max);assert.equal(interiorGain(100),INTERIOR_EXPOSURE.min);
 assert.equal(probeKey([]),null);assert.equal(interiorGain(null),1);
});
test('gain eases toward its target independent of frame rate and settles exactly',()=>{
 let a=1,b=1;for(let i=0;i<60;i++)a=stepExposure(a,3,1/60);for(let i=0;i<30;i++)b=stepExposure(b,3,1/30);
 assert.ok(Math.abs(a-b)<1e-9);let c=1;for(let i=0;i<600;i++)c=stepExposure(c,3,1/60);assert.equal(c,3);assert.equal(stepExposure(2,3,0),2);
});
import {readFileSync} from 'node:fs';
test('probe capture renders physical radiance: interior gain is forced to 1 per cube face',()=>{
 // Regression505: capturing with the display gain active inflated each pass and fed
 // the next adaptation step (100x probe radiance, oscillating exposure).
 const source=readFileSync(new URL('../src/room-bounce-study.js',import.meta.url),'utf8');
 const draw=source.slice(source.indexOf('const drawFace='),source.indexOf('const drawFace=')+400);
 assert.match(draw,/gain=interiorGain\.value;interiorGain\.value=1;/);assert.match(draw,/finally\{interiorGain\.value=gain;/);
 assert.match(source,/if\(tianInside\)outgoingLight\*=tianInteriorGain;/);
});
