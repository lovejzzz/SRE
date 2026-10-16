import test from 'node:test';import assert from 'node:assert/strict';import {readFileSync} from 'node:fs';
import {oakFloorPixels,lawnPixels,quartzPixels,fabricPixels,walnutPixels,isProceduralSurface,ALBEDO_SURFACES} from '../src/procedural-surfaces.js';
import {pillowVolume,quiltedDuvet} from '../src/textile-detail-volume.js';
import {lampVolume} from '../src/lamp-volume.js';
import {createVolumeFixtureLights} from '../src/volume-fixture-lights.js';
const lum=(img,i)=>(img.color[i*4]*.2126+img.color[i*4+1]*.7152+img.color[i*4+2]*.0722)/255;
// Seamless: the jump across the wrap edge is no larger than typical jumps inside the tile.
function seamless(img){const n=img.width,d=img.color,step=(a,b)=>Math.abs(d[a*4]-d[b*4]);let inner=0,edge=0;for(let y=0;y<n;y++){for(let x=1;x<n;x++)inner+=step(y*n+x,y*n+x-1);edge+=step(y*n,y*n+n-1);}return edge/n<=3*inner/(n*(n-1))+1;}

test('procedural surfaces are deterministic, valid size powers of two, and tile seamlessly',()=>{
 for(const [f,args] of [[oakFloorPixels,{size:256}],[quartzPixels,{size:128}],[fabricPixels,{size:128,threads:[32,32]}],[walnutPixels,{size:128}]]){
  const a=f(args),b=f(args);assert.deepEqual(a.color,b.color);assert.equal(a.color.length,args.size**2*4);assert.ok(seamless(a),f.name);
 }
 assert.throws(()=>oakFloorPixels({size:300}),/size/);assert.throws(()=>fabricPixels({size:128,weave:'velvet'}),/fabric/);
 assert.ok(isProceduralSurface('oak-floor')&&isProceduralSurface('fabric')&&!isProceduralSurface('source-floor'));
 assert.ok(ALBEDO_SURFACES.has('oak-floor')&&ALBEDO_SURFACES.has('lawn')&&!ALBEDO_SURFACES.has('fabric'));
});

test('oak boards have dark joints and warm wood between them; lawn is green',()=>{
 const oak=oakFloorPixels({size:256,boards:8});let joints=0,warm=0;
 for(let i=0;i<256*256;i++){const r=oak.color[i*4],g=oak.color[i*4+1],b=oak.color[i*4+2];if(lum(oak,i)<.2)joints++;if(r>g&&g>b)warm++;}
 assert.ok(joints>256*4&&joints<256*256*.12,'board joints present but thin: '+joints);assert.ok(warm>256*256*.9,'oak hue');
 const lawn=lawnPixels({size:256});let r=0,g=0;for(let i=0;i<256*256;i++){r+=lawn.color[i*4];g+=lawn.color[i*4+1];}assert.ok(g>r*1.3,'green overall');assert.ok(seamless(lawn),'lawn tiles');
});

test('quartz worktop is a quiet surface, not terrazzo speckle',()=>{
 const q=quartzPixels({size:256});let dark=0,sum=0,sq=0;for(let i=0;i<256*256;i++){const l=lum(q,i);sum+=l;sq+=l*l;if(l<.8)dark++;}
 const mean=sum/65536,sd=Math.sqrt(sq/65536-mean*mean);assert.equal(dark,0,'no dark flecks');assert.ok(sd<.03,'low contrast: '+sd);
});

test('pillows close at a seam all round and keep a soft loft; the duvet falls over the sides and foot',()=>{
 const p=pillowVolume({id:'pillow:0',origin:[0,0,1],size:[.6,.4,.15]}),zs=p.vertices.map(v=>v[2]);
 assert.ok(Math.max(...zs)-Math.min(...zs)>.12&&Math.max(...zs)<=1.15+.01&&Math.min(...zs)>=1-.005);
 assert.equal(p.collision.length,0);assert.ok(p.nonblocking);
 const d=quiltedDuvet({id:'duvet',x:0,y:0,z:1,width:1.4,length:1.6,sideDrop:.2,footDrop:.15}),xs=d.vertices.map(v=>v[0]),dz=d.vertices.map(v=>v[2]);
 assert.ok(Math.min(...xs)<-.04&&Math.max(...xs)>1.44,'overhangs both sides');assert.ok(Math.min(...dz)<1-.2,'drops below the mattress top');
 assert.ok(Math.max(...dz)>1.02,'quilted loft above the top');
});

test('lamp shade: pleated shell, glowing lining, hems and a spider that never block or self-shadow',()=>{
 const recipe=JSON.parse(readFileSync(new URL('../assets/recipes/volume/lamp.json',import.meta.url)));
 const {parts}=lampVolume(recipe),byId=Object.fromEntries(parts.map(p=>[p.id,p]));
 for(const id of ['shade','shade-lining','hem-top','hem-bottom','spider:0','spider:1','spider:2'])assert.ok(byId[id],id);
 assert.equal(byId['shade-lining'].materialId,'lining');assert.ok(recipe.materials.lining.fixtureEmission.intensity>recipe.materials.linen.fixtureEmission.intensity);
 const radii=byId.shade.vertices.slice(0,48).map(v=>Math.hypot(v[0]-.5,v[1]-.5));assert.ok(Math.max(...radii)-Math.min(...radii)>.003,'box pleats in the shell');
 for(const id of ['socket','finial','spider:0','shade-lining'])assert.equal(byId[id].castShadow,false,id);
 for(const p of parts.filter(p=>/^(shade|hem|spider)/.test(p.id)))assert.equal(p.collision?.length??0,0,p.id);
});

test('lit fabric glows through its own weave (the colour map drives emission)',()=>{
 const map={isTexture:true},material={emissive:{set(){}},map,needsUpdate:false};
 const rig=createVolumeFixtureLights({add(){},remove(){}});rig.bindMaterial(material,{color:0xffffff,intensity:.6});
 assert.equal(material.emissiveMap,map);
});
