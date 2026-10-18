import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import * as THREE from 'three';
import {createVolumeWalkthrough} from '../src/volume-walkthrough.js';
import {isTap,mountTouchStick,stickVector,twoFingerView} from '../src/touch-controls.js';

// Minimal DOM and frame clock: enough for the walkthrough loop and the touch stick.
function fakeDom(t){
 const names=['document','window','requestAnimationFrame','cancelAnimationFrame'],old=new Map(names.map(n=>[n,Object.getOwnPropertyDescriptor(globalThis,n)]));
 const doc=new EventTarget();doc.hidden=false;doc.activeElement=null;
 class Element extends EventTarget{
  children=[];disabled=false;hidden=false;className='';style={};textContent='';captured=null;
  append(...children){for(const c of children){c.parent=this;this.children.push(c);}}
  insertBefore(child,before){const i=this.children.indexOf(before);this.children.splice(i<0?this.children.length:i,0,child);}
  setAttribute(){} remove(){this.parent?.children.splice(this.parent.children.indexOf(this),1);this.parent=null;}
  get classList(){const el=this,list=()=>el.className.split(' ').filter(Boolean);return {add:c=>{el.className=[...new Set([...list(),c])].join(' ');},remove:c=>{el.className=list().filter(x=>x!==c).join(' ');},contains:c=>list().includes(c)};}
  getBoundingClientRect(){return {left:20,top:600,width:112,height:112};}
  setPointerCapture(id){this.captured=id;}
  focus(){if(doc.activeElement===this)return;const previous=doc.activeElement;doc.activeElement=this;previous?.dispatchEvent(new Event('blur'));this.dispatchEvent(new Event('focus'));}
 }
 doc.createElement=()=>new Element();let next=0;const frames=new Map();
 Object.assign(globalThis,{document:doc,window:new EventTarget(),requestAnimationFrame:fn=>{frames.set(++next,fn);return next;},cancelAnimationFrame:id=>frames.delete(id)});
 t.after(()=>{for(const [n,d]of old)if(d)Object.defineProperty(globalThis,n,d);else delete globalThis[n];});
 let now=0;const run=(ms=16)=>{const entry=frames.entries().next().value;if(!entry)return false;frames.delete(entry[0]);now+=ms;entry[1](now);return true;};
 return {doc,Element,frames,run};
}
const floor={polygon:[[0,0],[6,0],[6,3],[0,3]],minZ:-.2,maxZ:0},wall={polygon:[[3,0],[3.2,0],[3.2,3],[3,3]],minZ:0,maxZ:2.5};
function resident(t,collision=[floor]){
 const dom=fakeDom(t),scene=new THREE.Scene(),canvas=new dom.Element(),dialog=new dom.Element();dialog.append(canvas);const inputs=[];let draws=0;
 const walk=createVolumeWalkthrough({scene,canvas,dialog,draw(){draws++;},advance:(_dt,_p,input)=>inputs.push(input),focus(){},follow(){},spawnPosition:()=>[1,1.5,.900001]});
 walk.setVolumes([{roomId:'room',collision}]);walk.setRoom('room');walk.setResidentMode(true);walk.controls.children[0].onclick();
 return {...dom,scene,canvas,walk,inputs,draws:()=>draws};
}
const key=(type,k)=>{const e=new Event(type,{cancelable:true});Object.assign(e,{key:k});window.dispatchEvent(e);};

test('click-to-walk: the resident walks to the floor point through the physics, with a ring that clears on arrival',t=>{
 const {walk,run,scene,inputs}=resident(t);
 assert.equal(walk.walkTo([2.5,2,0]),true);assert.equal(walk.walkRing.visible,true);assert.equal(walk.walkRing.parent,scene);
 assert.deepEqual([walk.walkRing.position.x,walk.walkRing.position.y],[2.5,2]);
 for(let i=0;i<200&&walk.getWalkTarget();i++)run();
 const [x,y]=walk.getPosition();assert.ok(Math.hypot(x-2.5,y-2)<.12,`arrived at ${x},${y}`);
 assert.equal(walk.getWalkTarget(),null);assert.equal(walk.walkRing.visible,false);
 assert.ok(inputs.some(i=>i.x>0&&i.y>0),'the simulation sees walking input');
 assert.equal(walk.walkTo([NaN,0,0]),false);walk.dispose();
});

test('click-to-walk stops when blocked, and any WASD key cancels it',t=>{
 const {walk,run}=resident(t,[floor,wall]);
 walk.walkTo([5,1.5,0]);let frames=0;for(;frames<400&&walk.getWalkTarget();frames++)run();
 assert.equal(walk.getWalkTarget(),null,'gives up instead of pushing into the wall');assert.ok(frames<120,`stopped after ${frames} frames`);
 assert.ok(walk.getPosition()[0]<3,'still on this side of the wall');
 walk.walkTo([1,2.8,0]);run();assert.notEqual(walk.getWalkTarget(),null);
 key('keydown','s');assert.equal(walk.getWalkTarget(),null);assert.equal(walk.walkRing.visible,false);key('keyup','s');
 walk.walkTo([1,2.8,0]);key('keydown','Shift');assert.notEqual(walk.getWalkTarget(),null,'a modifier alone does not cancel');key('keyup','Shift');walk.dispose();
});

test('touch stick drives the resident like the keys and cancels a walk target',t=>{
 const {walk,run,canvas,Element,doc}=resident(t);
 run();const before=walk.getPosition();walk.walkTo([1,2.8,0]);
 walk.setStick([1,0]);assert.equal(walk.getWalkTarget(),null);
 for(let i=0;i<10;i++)run();const after=walk.getPosition();assert.ok(after[0]>before[0]+.2,'moves east (screen right, default direction mapping)');
 walk.setStick(null);run();const still=walk.getPosition();run();run();assert.deepEqual(walk.getPosition(),still);
 // The stick element: pointer offsets become a stick vector; release stops; focus stays on the scene.
 const parent=new Element(),moves=[];const stick=mountTouchStick({parent,canvas,onMove:v=>moves.push(v),radius:44});
 const pointer=(type,x,y)=>{const e=new Event(type,{cancelable:true});Object.assign(e,{pointerId:7,clientX:x,clientY:y});stick.element.dispatchEvent(e);return e;};
 new Element().focus();const down=pointer('pointerdown',76+44,656);assert.equal(down.defaultPrevented,true);assert.equal(doc.activeElement,canvas);
 assert.deepEqual(moves.at(-1),[1,0]);pointer('pointermove',76,656-200);const [ux,uy]=moves.at(-1);assert.ok(Math.abs(ux)<1e-9&&Math.abs(uy+1)<1e-9,'clamped to full up');
 pointer('pointerup',76,456);assert.equal(moves.at(-1),null);assert.equal(stick.element.parent,parent);stick.dispose();assert.equal(stick.element.parent,null);walk.dispose();
});

test('touch maths: stick dead zone, two-finger pinch and orbit, tap slop',()=>{
 assert.equal(stickVector(3,0,44),null);assert.deepEqual(stickVector(44,0,44),[1,0]);assert.ok(Math.abs(Math.hypot(...stickVector(22,22,44))-(Math.SQRT1_2-.18)/.82)<1e-9,'eased past the dead zone');
 const start={a:{x:100,y:300},b:{x:200,y:300},yaw:1,pitch:.6,radius:10};
 assert.equal(twoFingerView(start,{x:50,y:300},{x:250,y:300}).radius,5,'spread zooms in');
 assert.equal(twoFingerView(start,{x:125,y:300},{x:175,y:300}).radius,20,'pinch zooms out');
 const orbit=twoFingerView(start,{x:200,y:340},{x:300,y:340});assert.equal(orbit.radius,10);assert.ok(Math.abs(orbit.yaw-(1-100*.007))<1e-9);assert.ok(Math.abs(orbit.pitch-(.6+40*.005))<1e-9);
 assert.equal(twoFingerView(start,{x:0,y:300},{x:100000,y:300}).radius,2,'clamped');
 assert.equal(isTap({x:0,y:0},{x:3,y:0}),true);assert.equal(isTap({x:0,y:0},{x:5,y:0}),false,'a drag orbits');assert.equal(isTap({x:0,y:0},{x:8,y:0},'touch'),true);
});

test('index.html carries share metadata',()=>{
 const html=readFileSync(new URL('../index.html',import.meta.url),'utf8');
 for(const re of [/<meta name="description" content="[^"]{40,}">/,/<meta property="og:title" content="[^"]+">/,/<meta property="og:description" content="[^"]{40,}">/,/<meta name="theme-color" content="#[0-9a-f]{6}">/])assert.match(html,re);
});
