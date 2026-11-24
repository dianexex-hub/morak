// ===== 모락 NEXT: 한 덩어리 아바타 =====
// assets/avatar.glb(Blender) 의 몸 하나를 기존 legs/arms 묶음에 그대로 입힌다(묶음이 곧 뼈).
// 그래서 걷기·앉기·헤엄·탁구 같은 기존 동작 코드가 새 몸도 그대로 움직인다. 색은 8칸 팔레트(구역별) → 몸 그리기 1번.
// 구역: 0 피부(머리·목·손·발) 1 윗몸 2 위팔 3 아래팔 4 골반 5 허벅지 6 정강이. ?v4 면 예전 몸.
// 대상: 나·다른 손님(온라인)·키오스크 미리보기. 합쳐지는 가상 손님(guests)·걷는 NPC(walkers)는 예전 몸 그대로.
NX.avs=[];NX.avGeo=null;NX.avBones=null;const NX_BIND=.8;
const NX_SLEEVE=[1,2,0,2,2,1,0,2,2,2],NX_LONGB=[1,0,1,1,1,1,1,0,1,0];  // 상의: 0 민소매 1 반팔 2 긴팔 / 하의: 1 긴 0 짧은
const NX_OK={clothes:1,towel:1,jjim:1,kid:1};
function nxZones(av){const sk=av.skin.color.getHex(),L=av.look||defLook(),o=av.outfit;
 if(o==='clothes'){const sl=NX_SLEEVE[L.tp]??1,lb=NX_LONGB[L.bt]??1;return [sk,L.tc,sl>=1?L.tc:sk,sl>=2?L.tc:sk,L.bc,L.bc,lb?L.bc:sk,sk];}
 if(o==='towel')return [sk,sk,sk,sk,0xfbf9f3,0xfbf9f3,sk,sk];
 if(o==='jjim')return [sk,0xf08a4b,0xf08a4b,sk,0xe07a3b,0xe07a3b,sk,sk];
 return [sk,sk,sk,sk,0x3a8ae0,0x3a8ae0,sk,sk];}
function nxPaint(av){if(!av.nx)return;const on=!!NX_OK[av.outfit];
 av.nx.mesh.visible=on;av.nx.old.forEach(m=>m.visible=!on);av.extra.forEach(m=>m.visible=!on);
 if(!on)return;const d=av.nx.pal.image.data;nxZones(av).forEach((c,i)=>{d[i*4]=c>>16&255;d[i*4+1]=c>>8&255;d[i*4+2]=c&255;d[i*4+3]=255;});av.nx.pal.needsUpdate=true;}
function nxUpgrade(av){if(av.nx||!NX.avGeo||guests.some(G=>G.a===av)||walkers.some(w=>w.a===av))return;
 const old=av.body.children.filter(m=>m.isMesh&&m.material===av.skin);av.legs.concat(av.arms).forEach(p=>{if(p.children[0]&&p.children[0].isMesh)old.push(p.children[0]);});
 // 머리 뼈: 얼굴·머리카락·모자·액세서리를 목(높이 1.0) 기준으로 돌 수 있게 옮김
 const hb=new THREE.Group();hb.position.y=1.0;const hin=new THREE.Group();hin.position.y=-1.0;hb.add(hin);av.body.add(hb);[av.headG,av.faceG,av.hairG,av.accG].forEach(g=>hin.add(g));
 const shins=av.legs.map(l=>{const k=new THREE.Group();k.position.y=-.18;l.add(k);return k;});
 const map={body:av.body,head:hb,armL:av.arms[0],armR:av.arms[1],legL:av.legs[0],legR:av.legs[1],shinL:shins[0],shinR:shins[1]};
 const bones=NX.avBones.map(n=>map[n]);
 const pal=new THREE.DataTexture(new Uint8Array(32),8,1,THREE.RGBAFormat);pal.magFilter=pal.minFilter=THREE.NearestFilter;
 const mat=new THREE.MeshLambertMaterial({map:pal,emissiveMap:pal,emissive:0x404040,skinning:true});
 const mesh=new THREE.SkinnedMesh(NX.avGeo,mat);mesh.frustumCulled=false;mesh.userData.dyn=1;av.g.add(mesh);
 // 묶는 자세: 팔을 NX_BIND만큼 벌린 모양으로 만든 몸(avatar.py 의 A 와 같아야 함)
 const keep=bones.map(b=>[b.position.clone(),b.rotation.clone()]);
 bones.forEach(b=>b.rotation.set(0,0,0));av.body.position.set(0,0,0);av.arms.forEach((a,i)=>a.rotation.z=(i?1:-1)*NX_BIND);
 av.g.updateMatrixWorld(true);mesh.bind(new THREE.Skeleton(bones));
 bones.forEach((b,i)=>{b.position.copy(keep[i][0]);b.rotation.copy(keep[i][1]);});
 av.nx={mesh,pal,old,hb,shins,soak:0,joy:0};nxPaint(av);}
{const _ba=buildAvatar,_al=applyLook,_so=setOutfit;
 buildAvatar=function(...a){const av=_ba(...a);NX.avs.push(av);nxUpgrade(av);return av;};
 applyLook=function(av,L){_al(av,L);nxPaint(av);};
 setOutfit=function(av,o){_so(av,o);nxPaint(av);};}
if(!NX.old)new THREE.GLTFLoader().load('assets/avatar.glb',gl=>{let sm=null;gl.scene.traverse(o=>{if(o.isSkinnedMesh)sm=o;});if(!sm)return;
 NX.avGeo=sm.geometry;NX.avBones=sm.skeleton.bones.map(b=>b.name);NX.loaded.push('avatar.glb');NX.avs.forEach(nxUpgrade);},undefined,e=>console.warn('NEXT 아바타 불러오기 실패',e));
// 동작: 걷기(무릎·골반), 서 있기(살랑), 탕에 앉기(a.soak), 「좋다~!」 만세(a.joy 초)
function nxAnim(a,moving,dt){const X=a.nx;if(!X||!X.mesh.visible)return;const k=Math.min(1,dt*6),up=a.body.rotation.x>-.5;
 X.soak+=((a.soak&&!moving?1:0)-X.soak)*k;const j=a.joy>0?(a.joy-=dt,Math.min(1,(1.4-a.joy)*7)*Math.min(1,a.joy*4)):0;
 if(moving){const ph=a.phase;X.shins.forEach((s,i)=>s.rotation.x=Math.max(0,Math.sin(ph+(i?Math.PI:0)-.9))*.85);if(up){a.body.rotation.z=Math.sin(ph)*.05;a.body.rotation.y=Math.sin(ph)*.07;}}
 else{X.shins.forEach(s=>s.rotation.x+=(X.soak*1.25-s.rotation.x)*k);a.body.rotation.z*=.85;a.body.rotation.y*=.85;
  if(X.soak>.01)a.legs.forEach(l=>l.rotation.x=l.rotation.x*(1-X.soak)-1.15*X.soak);}
 a.arms.forEach((ar,i)=>{const s=i?1:-1;ar.rotation.z=s*(.3+(moving?0:.03*Math.sin(TT*1.6+i))+X.soak*.45+j*.3);if(j>0)ar.rotation.x=ar.rotation.x*(1-j)-2.75*j;});
 X.hb.rotation.x=-.28*j-.05*X.soak;X.hb.rotation.z=moving?0:Math.sin(TT*.7)*.04;
 if(j>0&&!moving)a.body.position.y=Math.abs(Math.sin((1.4-a.joy)*9))*.05*j;}
{const _aw=animWalk;animWalk=function(a,moving,dt,speed){_aw(a,moving,dt,speed);nxAnim(a,moving,dt);};}
