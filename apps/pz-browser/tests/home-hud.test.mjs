import test from 'node:test';
import assert from 'node:assert/strict';
import {mountHomeHud,WELCOME_KEY} from '../src/home-hud.js';
import {sameHouse} from '../src/house-compare.js';

// Minimal DOM: enough element behaviour for the HUD (no layout).
function fakeDom(t){
 const names=['document','window','localStorage'],old=new Map(names.map(n=>[n,Object.getOwnPropertyDescriptor(globalThis,n)]));
 const doc=new EventTarget();doc.hidden=false;doc.activeElement=null;const store=new Map();
 class Element extends EventTarget{
  constructor(tag){super();this.tagName=tag.toUpperCase();this.children=[];this.parent=null;this.hidden=false;this.className='';this.textContent='';this.style={};this.dataset={};this.attrs={};this.open=false;this.clientWidth=1000;this.clientHeight=700;}
  get classList(){const el=this;const list=()=>el.className.split(' ').filter(Boolean);return {add:(...c)=>{el.className=[...new Set([...list(),...c])].join(' ');},remove:(...c)=>{el.className=list().filter(x=>!c.includes(x)).join(' ');},toggle:(c,on)=>{(on??!list().includes(c))?el.classList.add(c):el.classList.remove(c);},contains:c=>list().includes(c)};}
  append(...c){for(const x of c){x.parent?.children.splice(x.parent.children.indexOf(x),1);x.parent=this;this.children.push(x);}}
  prepend(...c){for(const x of c.reverse()){x.parent?.children.splice(x.parent.children.indexOf(x),1);x.parent=this;this.children.unshift(x);}}
  remove(){if(this.parent)this.parent.children.splice(this.parent.children.indexOf(this),1);this.parent=null;}
  setAttribute(k,v){this.attrs[k]=String(v);} getAttribute(k){return this.attrs[k]??null;}
  focus(){doc.activeElement=this;} click(){this.onclick?.();}
  *all(){for(const c of this.children){yield c;yield* c.all();}}
  querySelector(sel){for(const e of this.all()){if(sel==='.home-hud-items'&&e.classList.contains('home-hud-items'))return e;if(sel.includes('dialog[open]')&&(e.tagName==='DIALOG'&&e.open||e.attrs.role==='dialog'&&e.attrs['aria-modal']==='true'))return e;}return null;}
 }
 doc.createElement=tag=>new Element(tag);
 const win=new EventTarget();win.localStorage={getItem:k=>store.get(k)??null,setItem:(k,v)=>store.set(k,String(v))};Object.assign(globalThis,{document:doc,window:win});
 t.after(()=>{for(const [n,d]of old)if(d)Object.defineProperty(globalThis,n,d);else delete globalThis[n];});
 return {doc,Element,store};
}
const escape=()=>{const e=new Event('keydown',{cancelable:true});Object.defineProperty(e,'key',{value:'Escape'});window.dispatchEvent(e);return e;};

test('living HUD: one Workshop entry; Esc menu holds the controls and pauses; nested windows own Esc',t=>{
 const {doc,Element}=fakeDom(t);let clock=0,resumed=0,paused=0,workshops=0;
 const dialog=new Element('dialog');dialog.open=true;const canvas=new Element('canvas');dialog.append(canvas);
 const inventory=new Element('button'),help=new Element('p');dialog.append(help);
 const hud=mountHomeHud({dialog,canvas,name:'Hearth Studio',resume:()=>{resumed++;canvas.focus();},pause:()=>paused++,menuItems:[inventory],help,onWorkshop:()=>workshops++,now:()=>clock});
 // On screen while living: the Workshop button only (the hint shows only when the scene lost focus).
 canvas.focus();hud.update();assert.equal(hud.elements.workshop.hidden,false);assert.equal(hud.elements.hint.hidden,true);assert.equal(hud.elements.sheet.hidden,true);
 hud.elements.workshop.click();assert.equal(workshops,1);
 assert.equal(inventory.parent.classList.contains('home-hud-items'),true,'controls move into the menu, keeping their handlers');
 // Esc opens the menu (pausing), Esc again resumes; the default (dialog close) is prevented.
 const e1=escape();assert.equal(e1.defaultPrevented,true);assert.equal(hud.open,true);assert.equal(paused,1);assert.equal(hud.elements.sheet.hidden,false);assert.equal(hud.elements.workshop.hidden,true);
 escape();assert.equal(hud.open,false);assert.equal(resumed,1);assert.equal(doc.activeElement,canvas);
 // Lost focus -> "Click to continue"; clicking it resumes.
 doc.activeElement=null;hud.update();assert.equal(hud.elements.hint.hidden,false);hud.elements.hint.click();assert.equal(resumed,2);
 // A nested modal window (the desk computer) keeps Esc for itself and hides the hint.
 const computer=new Element('section');computer.setAttribute('role','dialog');computer.setAttribute('aria-modal','true');dialog.append(computer);doc.activeElement=null;
 const e2=escape();assert.equal(e2.defaultPrevented,false);assert.equal(hud.open,false);hud.update();assert.equal(hud.elements.hint.hidden,true);computer.remove();
 // First-visit help fades, and is not shown on the next visit.
 assert.equal(help.classList.contains('home-hud-help'),true);clock=10000;hud.update();assert.equal(help.classList.contains('home-hud-faded'),true);
 assert.equal(window.localStorage.getItem(WELCOME_KEY),'1');
 const help2=new Element('p'),again=mountHomeHud({dialog:new Element('dialog'),canvas,name:'x',resume(){},pause(){},help:help2,onWorkshop(){}});again.dispose();assert.equal(help2.hidden,true);
 hud.dispose();
});

test('desk computer marker: middle distance band, held at the screen edge when out of frame, opens the work',t=>{
 const {Element}=fakeDom(t);let opened=0;
 const dialog=new Element('dialog');dialog.open=true;const canvas=new Element('canvas');
 const hud=mountHomeHud({dialog,canvas,name:'x',resume(){},pause(){},onWorkshop(){},markers:[{position:[10,0,1.5],label:'My work',onClick:()=>opened++}]});
 const [pin]=hud.elements.markers,on={x:400,y:300,onScreen:true};
 hud.place(()=>on,()=>15);assert.equal(pin.hidden,true,'too far');
 hud.place(()=>on,()=>1);assert.equal(pin.hidden,true,'close enough for the E prompt');
 hud.place(()=>on,()=>6);assert.equal(pin.hidden,false);assert.equal(pin.style.left,'400px');assert.equal(pin.classList.contains('home-hud-marker-edge'),false);
 hud.place(()=>({x:-50,y:300,onScreen:false}),()=>6);assert.equal(pin.hidden,false);assert.equal(pin.style.left,'70px');assert.equal(pin.dataset.side,'left');
 hud.place(()=>({x:-50,y:900,onScreen:false}),()=>6);assert.equal(pin.style.top,'570px');hud.place(()=>({x:-50,y:900,onScreen:false}),()=>6,110);assert.equal(pin.style.top,'460px','held above the touch stick');
 hud.openMenu();hud.place(()=>on,()=>6);assert.equal(pin.hidden,true,'menu hides world labels');hud.closeMenu();
 pin.click();assert.equal(opened,1);hud.dispose();
});

test('sameHouse: the lived-in house matches its own draft regardless of key order or empty lists',()=>{
 const a={name:'A',sceneDocument:{walls:[{id:'w',x:1}],rooms:[]},squares:[{x:1,y:2,tiles:['t']}],items:[],vehicles:undefined};
 const b={name:'Renamed',vehicles:[],items:undefined,squares:[{tiles:['t'],y:2,x:1}],sceneDocument:{rooms:[],walls:[{x:1,id:'w'}]}};
 assert.equal(sameHouse(a,b),true);
 assert.equal(sameHouse(a,{...b,sceneDocument:{...b.sceneDocument,exterior:{version:1,hedge:{height:1.4}}}}),false,'an exterior edit is a different house');
 assert.equal(sameHouse(a,{...b,items:[{id:'i'}]}),false);
});
