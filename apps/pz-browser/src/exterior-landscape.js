import * as THREE from 'three';
import {mergeVertices} from '../node_modules/three/examples/jsm/utils/BufferGeometryUtils.js';
import {lawnPixels} from './procedural-surfaces.js';
import {installSurfaceVariation} from './surface-variation.js';
// Runtime landscape around the authored plot (Z-up, metres = grid cells):
// meadow ground to the horizon, a varied distant tree line, a few detailed garden
// trees whose leaf cards cast dappled shadows, a clipped boundary hedge with a gap
// where a path leaves, and short instanced grass blades with a gentle sway near
// the house. Deterministic (seeded); dressing only — no collision or gameplay.

export function rng(seed){let s=(seed>>>0)||1;return ()=>{s^=s<<13;s>>>=0;s^=s>>17;s^=s<<5;s>>>=0;return s/4294967296;};}
const LAWN='blends_natural_01_16';

// Plot analysis from the house plan: bounds, lawn cells, path exits, built area.
export function plotLayout(squares){
 const cells=new Map(squares.filter(s=>s.z===0).map(s=>[`${s.x},${s.y}`,s]));
 const xs=[...cells.values()].map(s=>s.x),ys=[...cells.values()].map(s=>s.y);
 const bounds=[Math.min(...xs),Math.min(...ys),Math.max(...xs)+1,Math.max(...ys)+1];
 const lawn=[...cells.values()].filter(s=>s.tiles?.[0]===LAWN).map(s=>[s.x,s.y]);
 const built=[...cells.values()].filter(s=>s.tiles?.[0]!==LAWN).map(s=>[s.x,s.y]);
 const isLawn=(x,y)=>cells.get(`${x},${y}`)?.tiles?.[0]===LAWN;
 // Edge cells that are not lawn (a path reaching the boundary) open the hedge.
 const gaps=[...cells.values()].filter(s=>s.tiles?.[0]!==LAWN&&(s.x===bounds[0]||s.y===bounds[1]||s.x===bounds[2]-1||s.y===bounds[3]-1)).map(s=>[s.x,s.y]);
 const distBuilt=(x,y)=>built.reduce((m,[bx,by])=>Math.min(m,Math.hypot(x-bx,y-by)),Infinity);
 return {bounds,lawn,built,gaps,isLawn,distBuilt,centre:[(bounds[0]+bounds[2])/2,(bounds[1]+bounds[3])/2]};
}

// Leaf-cluster card: overlapping ovate leaves with midribs on transparency.
export function leafCardPixels(size=128,seed=5,{leaves=14,length=[.16,.12]}={}){
 const r=rng(seed),px=new Uint8Array(size*size*4);
 for(let k=0;k<leaves;k++){
  const cx=.12+.76*r(),cy=.12+.76*r(),a=r()*Math.PI*2,len=length[0]+length[1]*r(),wid=len*(.38+.12*r()),tone=.75+.35*r(),hue=r();
  for(let y=0;y<size;y++)for(let x=0;x<size;x++){const u=(x+.5)/size-cx,v=(y+.5)/size-cy,s=Math.cos(a),c=Math.sin(a),p=u*s+v*c,q=-u*c+v*s;
   const t=p/len;if(t<-1||t>1)continue;const half=wid*Math.sqrt(Math.max(0,1-t*t))*(1-.25*t);if(Math.abs(q)>half)continue;
   const rib=Math.abs(q)<half*.08?1.12:1,edge=1-.25*Math.pow(Math.abs(q)/half,4),i=(y*size+x)*4;
   const g=Math.min(1,(.28+.1*hue)*tone*rib*edge),R=g*(.42+.25*hue),B=g*.28;px.set([Math.round(R*255),Math.round(g*255),Math.round(B*255),255],i);}
 }
 return {width:size,height:size,data:px};
}

function dataTexture({width,height,data},color=true,repeat=false){const t=new THREE.DataTexture(data,width,height,THREE.RGBAFormat);t.colorSpace=color?THREE.SRGBColorSpace:THREE.NoColorSpace;t.magFilter=THREE.LinearFilter;t.minFilter=THREE.LinearMipmapLinearFilter;t.generateMipmaps=true;t.anisotropy=8;if(repeat)t.wrapS=t.wrapT=THREE.RepeatWrapping;t.needsUpdate=true;return t;}

// Tapered branch cylinder from a to b (radii ra, rb), appended to arrays.
function branch(pos,idx,col,a,b,ra,rb,seg,color){
 const d=new THREE.Vector3().subVectors(b,a),len=d.length();d.normalize();
 const ref=Math.abs(d.z)<.9?new THREE.Vector3(0,0,1):new THREE.Vector3(1,0,0),u=new THREE.Vector3().crossVectors(d,ref).normalize(),v=new THREE.Vector3().crossVectors(d,u);
 const base=pos.length/3;
 for(const [p,r] of [[a,ra],[b,rb]])for(let i=0;i<seg;i++){const t=i/seg*Math.PI*2,q=p.clone().addScaledVector(u,Math.cos(t)*r).addScaledVector(v,Math.sin(t)*r);pos.push(q.x,q.y,q.z);col.push(...color);}
 for(let i=0;i<seg;i++){const j=(i+1)%seg;idx.push(base+i,base+j,base+seg+j,base+i,base+seg+j,base+seg+i);}
 return len;
}

// Garden tree: leaning trunk, 5–6 scaffold limbs spreading out of the trunk, each
// forking (parent direction turned 22–42° about a random axis, mild upward pull)
// down to twigs; leaf-card clusters at twig ends fill a broad, open crown.
// Bark colours are linear (a dark grey-brown that reads correctly in sunlight).
export function gardenTree(seed,height=7){
 const r=rng(seed),pos=[],idx=[],col=[],leaves=[],k=height/7;
 const bark=[.045,.036,.027],up=new THREE.Vector3(0,0,1);
 const turn=(dir,angle)=>{const axis=new THREE.Vector3(r()-.5,r()-.5,r()-.5).cross(dir).normalize();return dir.clone().applyAxisAngle(axis,angle);};
 const grow=(a,dir,len,radius,depth)=>{
  const b=a.clone().addScaledVector(dir,len);branch(pos,idx,col,a,b,radius,radius*.72,depth>2?7:5,bark.map(c=>c*(.8+.4*r())));
  if(depth===0){for(let j=0;j<11;j++){const p=b.clone().add(new THREE.Vector3((r()-.5)*1.05,(r()-.5)*1.05,(r()-.35)*.7).multiplyScalar(k));leaves.push({p,rot:r()*Math.PI*2,tilt:(r()-.5)*1.3,s:(.42+.3*r())*k});}return;}
  for(let j=0;j<2;j++){const nd=turn(dir,.38+.35*r()).addScaledVector(up,.18).normalize();grow(b,nd,len*(.7+.12*r()),radius*.7,depth-1);}
 };
 const lean=new THREE.Vector3((r()-.5)*.12,(r()-.5)*.12,1).normalize(),trunkTop=lean.clone().multiplyScalar(height*.36);
 branch(pos,idx,col,new THREE.Vector3(0,0,-.1),trunkTop,.17*k,.13*k,10,bark);
 // Root flare: a short wide collar so the trunk meets the ground convincingly.
 branch(pos,idx,col,new THREE.Vector3(0,0,-.1),new THREE.Vector3(0,0,.35*k),.27*k,.17*k,10,bark);
 const scaffolds=5+Math.floor(r()*2);
 for(let j=0;j<scaffolds;j++){const yaw=j/scaffolds*Math.PI*2+r()*.6,tilt=.6+.45*r(),start=trunkTop.clone().addScaledVector(lean,-r()*height*.08);
  const dir=new THREE.Vector3(Math.cos(yaw)*Math.sin(tilt),Math.sin(yaw)*Math.sin(tilt),Math.cos(tilt));
  grow(start,dir,height*(.2+.06*r()),.085*k,4);}
 const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(pos,3));g.setAttribute('color',new THREE.Float32BufferAttribute(col,3));g.setIndex(idx);g.computeVertexNormals();
 return {wood:g,leaves};
}

// Distant tree (seen at 55–260 m through haze): smooth, lumpy crown blobs with
// welded vertices (soft normals, no facets) or a layered, drooping conifer; the
// crown underside is darkened in vertex colour as cheap self-occlusion.
export function distantTreeGeometry(conifer,seed=1){
 const r=rng(seed),parts=[];
 const trunk=new THREE.CylinderGeometry(.16,.3,conifer?3:3.6,8);trunk.rotateX(Math.PI/2);trunk.translate(0,0,conifer?1.5:1.8);parts.push([trunk,[.07,.055,.045],false]);
 if(conifer){for(let k=0;k<6;k++){const c=new THREE.ConeGeometry(2.3-k*.33,2.4-k*.12,16,2,true);c.rotateX(Math.PI/2);const p=c.attributes.position;
   for(let i=0;i<p.count;i++){const z=p.getZ(i),rad=Math.hypot(p.getX(i),p.getY(i));if(rad>.05){const a=Math.atan2(p.getY(i),p.getX(i)),f=1+.16*Math.sin(a*7+k*1.7)+.1*(r()-.5);p.setXYZ(i,p.getX(i)*f,p.getY(i)*f,z-.25*rad*rad/2.3);}}
   c.translate(0,0,2.6+k*1.45);parts.push([c,[.035,.075,.04],true]);}}
 else{for(let k=0;k<5;k++){let s=new THREE.IcosahedronGeometry(1.6+r()*1.1,2);s.deleteAttribute('normal');s.deleteAttribute('uv');s=mergeVertices(s);const p=s.attributes.position,ph=[r()*6,r()*6,r()*6];
   for(let i=0;i<p.count;i++){const x=p.getX(i),y=p.getY(i),z=p.getZ(i),l=Math.hypot(x,y,z),f=1+.13*Math.sin(x*2.1+ph[0])*Math.sin(y*2.3+ph[1])+.09*Math.sin(z*3.1+ph[2])+.05*(r()-.5);p.setXYZ(i,x*f,y*f,z*f*.82);}
   s.translate((r()-.5)*2.4,(r()-.5)*2.4,4.4+r()*2.4);parts.push([s,[.05,.085,.035],true]);}}
 const pos=[],col=[],idx=[];let off=0;
 for(const [g,c,crown] of parts){const p=g.attributes.position;let zmin=Infinity,zmax=-Infinity;for(let i=0;i<p.count;i++){zmin=Math.min(zmin,p.getZ(i));zmax=Math.max(zmax,p.getZ(i));}
  for(let i=0;i<p.count;i++){pos.push(p.getX(i),p.getY(i),p.getZ(i));const shade=(.85+.3*r())*(crown?.55+.45*(p.getZ(i)-zmin)/(zmax-zmin||1):1);col.push(c[0]*shade,c[1]*shade,c[2]*shade);}
  const ix=g.index?g.index.array:Array.from({length:p.count},(_,i)=>i);for(const i of ix)idx.push(i+off);off+=p.count;g.dispose();}
 const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(pos,3));g.setAttribute('color',new THREE.Float32BufferAttribute(col,3));g.setIndex(idx);g.computeVertexNormals();return g;
}

// One grass blade: 3 segments, tapering, curving forward; z up, base at origin.
function bladeGeometry(){
 const pos=[],idx=[],n=3;
 const col=[];for(let i=0;i<=n;i++){const t=i/n,w=.0032*(1-t*.85),bend=.012*t*t,shade=.38+.62*t;pos.push(-w,bend,t,w,bend,t);col.push(shade,shade,shade*.9,shade,shade,shade*.9);}
 for(let i=0;i<n;i++){const a=i*2;idx.push(a,a+1,a+3,a,a+3,a+2);}
 const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(pos,3));g.setAttribute('color',new THREE.Float32BufferAttribute(col,3));g.setIndex(idx);g.computeVertexNormals();
 // Base of the sward sits in its own shade (vertex gradient); normals mostly up so blades read like a lawn surface, not flat cards.
 const nrm=g.attributes.normal;for(let i=0;i<nrm.count;i++){nrm.setXYZ(i,nrm.getX(i)*.35,nrm.getY(i)*.35,.94);}nrm.needsUpdate=true;
 return g;
}

function swayMaterial(base,uniforms,amount){
 base.onBeforeCompile=shader=>{shader.uniforms.tianWind=uniforms.time;
  shader.vertexShader=shader.vertexShader.replace('#include <common>','#include <common>\nuniform float tianWind;').replace('#include <begin_vertex>',`#include <begin_vertex>
  #ifdef USE_INSTANCING
   vec3 tianRoot=instanceMatrix[3].xyz;
  #else
   vec3 tianRoot=vec3(0.);
  #endif
  float tianPhase=tianRoot.x*.7+tianRoot.y*.9;
  transformed.xy+=vec2(sin(tianWind*1.3+tianPhase),cos(tianWind*1.1+tianPhase*1.3))*${amount.toFixed(3)}*transformed.z*transformed.z;`);};
 base.customProgramCacheKey=()=>'tian-sway-'+amount;return base;
}

export function createExteriorLandscape(scene,{quality=1}={}){
 const root=new THREE.Group();root.name='exterior-landscape';scene.add(root);
 const uniforms={time:{value:0}};const disposables=[];let built=false;
 const track=(...items)=>{disposables.push(...items);return items[0];};
 function clear(){for(const c of [...root.children])root.remove(c);for(const d of disposables.splice(0))d.dispose();built=false;}
 function rebuild(squares){
  clear();if(!squares?.length)return;
  const plot=plotLayout(squares),[x0,y0,x1,y1]=plot.bounds,[cx,cy]=plot.centre,r=rng(97);
  // 1. Meadow to the horizon (plot surfaces sit above it).
  const lawnTex=track(dataTexture((()=>{const p=lawnPixels({size:1024,seed:23});const d=new Uint8Array(p.color.length);d.set(p.color);return {width:p.width,height:p.height,data:d};})(),true,true));
  const groundGeo=track(new THREE.PlaneGeometry(1600,1600,1,1));const uv=groundGeo.attributes.uv;for(let i=0;i<uv.count;i++)uv.setXY(i,uv.getX(i)*1600/1.3,uv.getY(i)*1600/1.3);
  const groundMat=track(installSurfaceVariation(new THREE.MeshStandardMaterial({map:lawnTex,roughness:.97,color:0xd8e0c8}),{tone:.22,roughness:.1,scale:.25}));
  const ground=new THREE.Mesh(groundGeo,groundMat);ground.position.set(cx,cy,-.03);ground.receiveShadow=true;ground.name='meadow';root.add(ground);
  // 2. Distant tree line: two species, ring 55–260 m, clumped, never inside the plot.
  for(const conifer of [false,true]){
   const geo=track(distantTreeGeometry(conifer,conifer?3:4)),mat=track(new THREE.MeshStandardMaterial({vertexColors:true,roughness:.92,side:conifer?THREE.DoubleSide:THREE.FrontSide}));
   const n=Math.round((conifer?170:330)*quality),mesh=new THREE.InstancedMesh(geo,mat,n),m=new THREE.Matrix4(),c=new THREE.Color();
   for(let i=0;i<n;i++){let a=r()*Math.PI*2,d=55+Math.pow(r(),.7)*205;const clump=Math.sin(a*5+1.3)*.5+.5;if(r()>.35+.6*clump){a+=.2;d+=20;}
    const s=(.7+.9*r())*(d>140?1.25:1);m.compose(new THREE.Vector3(cx+Math.cos(a)*d,cy+Math.sin(a)*d,-.05),new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0,0,1),r()*6.3),new THREE.Vector3(s,s,s*(.85+.4*r())));
    mesh.setMatrixAt(i,m);mesh.setColorAt(i,c.setRGB(.8+.4*r(),.85+.3*r(),.75+.35*r()));}
   mesh.castShadow=false;mesh.receiveShadow=false;mesh.userData.indirectCaptureExclude=true;mesh.name=conifer?'conifers':'tree-line';root.add(mesh);
  }
  // 3. Garden trees on lawn far from the house, with dappled leaf shadows.
  const leafTex=track(dataTexture(leafCardPixels(256,11,{leaves:46,length:[.075,.05]})));
  const leafMat=track(new THREE.MeshStandardMaterial({map:leafTex,alphaTest:.45,side:THREE.DoubleSide,roughness:.75,color:0xffffff}));
  const barkMat=track(installSurfaceVariation(new THREE.MeshStandardMaterial({vertexColors:true,roughness:.95}),{tone:.25,roughness:.1,scale:3}));
  const spots=plot.lawn.filter(([x,y])=>plot.distBuilt(x,y)>=5&&x>x0+1&&y>y0+1&&x<x1-2&&y<y1-2);
  const chosen=[];for(const pick of [[x0,y0],[x1,y0],[x0,y1],[x1,y1]]){const best=spots.filter(s=>chosen.every(c=>Math.hypot(c[0]-s[0],c[1]-s[1])>8)).sort((a,b)=>Math.hypot(a[0]-pick[0],a[1]-pick[1])-Math.hypot(b[0]-pick[0],b[1]-pick[1]))[0];if(best)chosen.push(best);}
  const card=track(new THREE.PlaneGeometry(1,1));
  // Cards face outward from the crown (normal ≈ radial + jitter): the canopy then
  // shades like one soft volume — lit crown top, darker underside — not loose paper.
  const Z=new THREE.Vector3(0,0,1),outward=(radial,jitter)=>{const n=radial.clone().normalize().add(new THREE.Vector3(r()-.5,r()-.5,r()-.5).multiplyScalar(jitter)).normalize();return new THREE.Quaternion().setFromUnitVectors(Z,n).multiply(new THREE.Quaternion().setFromAxisAngle(Z,r()*Math.PI*2));};
  chosen.forEach(([x,y],k)=>{const t=gardenTree(31+k*17,6.5+r()*2.5);track(t.wood);const wood=new THREE.Mesh(t.wood,barkMat);wood.position.set(x+.5,y+.5,0);wood.castShadow=true;wood.receiveShadow=true;wood.name='garden-tree';root.add(wood);
   const leaves=new THREE.InstancedMesh(card,leafMat,t.leaves.length),m=new THREE.Matrix4(),c=new THREE.Color();
   const centre=t.leaves.reduce((a,L)=>a.add(L.p),new THREE.Vector3()).multiplyScalar(1/t.leaves.length),reach=Math.max(...t.leaves.map(L=>L.p.distanceTo(centre)));
   t.leaves.forEach((L,i)=>{const radial=L.p.clone().sub(centre),depth=radial.length()/reach;radial.z+=.25*reach;m.compose(L.p.clone().add(new THREE.Vector3(x+.5,y+.5,0)),outward(radial,.9),new THREE.Vector3(L.s,L.s,L.s));leaves.setMatrixAt(i,m);
    // Inner leaves sit in the crown's own shade.
    leaves.setColorAt(i,c.setHSL(.24+.05*r(),.5,.2+.22*depth+.08*r()));});
   leaves.castShadow=true;leaves.receiveShadow=true;leaves.name='garden-tree-leaves';root.add(leaves);});
  // 4. Boundary hedge just outside the plot, open where a path leaves.
  const hedgeTex=track(dataTexture(leafCardPixels(256,29,{leaves:44,length:[.08,.05]})));
  const hedgeMat=track(new THREE.MeshStandardMaterial({map:hedgeTex,alphaTest:.4,side:THREE.DoubleSide,roughness:.8}));
  const hedgeCore=track(installSurfaceVariation(new THREE.MeshStandardMaterial({color:0x24331a,roughness:1}),{tone:.3,roughness:.1,scale:2}));
  const runs=[];const gapAt=(x,y)=>plot.gaps.some(([gx,gy])=>Math.abs(gx-x)<=1&&Math.abs(gy-y)<=1);
  for(let x=x0;x<x1;x++){if(!gapAt(x,y0))runs.push([x+.5,y0-.45,0]);if(!gapAt(x,y1-1))runs.push([x+.5,y1+.45,0]);}
  for(let y=y0;y<y1;y++){if(!gapAt(x0,y))runs.push([x0-.45,y+.5,1]);if(!gapAt(x1-1,y))runs.push([x1+.45,y+.5,1]);}
  const coreGeo=track(new THREE.BoxGeometry(1.02,.62,1.05));coreGeo.translate(0,0,.525);
  const cores=new THREE.InstancedMesh(coreGeo,hedgeCore,runs.length),m=new THREE.Matrix4();
  runs.forEach(([x,y,side],i)=>{m.compose(new THREE.Vector3(x,y,0),new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0,0,1),side?Math.PI/2:0),new THREE.Vector3(1,1,.95+.1*r()));cores.setMatrixAt(i,m);});
  cores.castShadow=true;cores.receiveShadow=true;cores.name='hedge';root.add(cores);
  const perRun=Math.round(72*quality),cards=new THREE.InstancedMesh(card,hedgeMat,runs.length*perRun),c=new THREE.Color();let ci=0;
  for(const [x,y,side] of runs)for(let k=0;k<perRun;k++){const along=r()-.5,face=r()<.5?-1:1,top=r()<.3;
   const lx=along*1.05,ly=top?(r()-.5)*.62:face*(.31+.04*r()),lz=top?1.02+.05*r():.08+r()*.95,px=side?x+ly:x+lx,py=side?y+lx:y+ly;
   const nx=top?0:(side?face:0),ny=top?0:(side?0:face);m.compose(new THREE.Vector3(px,py,lz),outward(new THREE.Vector3(nx,ny,top?1:.15),.8),new THREE.Vector3(.32,.32,.32));cards.setMatrixAt(ci,m);cards.setColorAt(ci++,c.setHSL(.24+.03*r(),.45,.2+.1*r()));}
  cards.castShadow=false;cards.receiveShadow=true;cards.name='hedge-leaves';root.add(cards);
  // 5. Grass blades on lawn cells near the house (mown, 5–11 cm).
  const near=plot.lawn.filter(([x,y])=>plot.distBuilt(x,y)<=7);
  const perCell=Math.round(110*quality),bladeGeo=track(bladeGeometry());
  const bladeMat=track(swayMaterial(new THREE.MeshStandardMaterial({color:0xffffff,vertexColors:true,roughness:1,envMapIntensity:.6,side:THREE.DoubleSide}),uniforms,.04));
  const blades=new THREE.InstancedMesh(bladeGeo,bladeMat,near.length*perCell);let bi=0;
  for(const [x,y] of near)for(let k=0;k<perCell;k++){const h=.05+.06*r();m.compose(new THREE.Vector3(x+r(),y+r(),0),new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0,0,1),r()*6.3),new THREE.Vector3(1,1,h));blades.setMatrixAt(bi,m);blades.setColorAt(bi++,c.setHSL(.22+.06*r(),.48+.15*r(),.2+.12*r()));}
  blades.castShadow=false;blades.receiveShadow=true;blades.userData.indirectCaptureExclude=true;blades.name='grass-blades';root.add(blades);
  built=true;
  return {trees:chosen.length,hedgeRuns:runs.length,blades:bi,lawnCells:plot.lawn.length};
 }
 return {root,rebuild,update(dt){uniforms.time.value+=dt;},stats:()=>({built,children:root.children.map(c=>[c.name,c.isInstancedMesh?c.count:1])}),dispose(){clear();scene.remove(root);}};
}
