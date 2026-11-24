// ===== 모락 NEXT: Blender 모형 =====
// ?v4 를 붙이면 예전(코드) 모습으로 비교. 불러오기에 실패하면 예전 모습으로 돌아감.
const NX={old:/[?&]v4\b/.test(location.search)||!THREE.GLTFLoader,loaded:[]};
function nxLoad(file,onFail){
 if(NX.old)return;
 new THREE.GLTFLoader().load('assets/'+file,gl=>{
  const g=new THREE.Group();g.name='nx:'+file;const aniso=renderer.capabilities.getMaxAnisotropy();
  gl.scene.traverse(o=>{if(!o.isMesh)return;const map=o.material.map;
   if(map){map.anisotropy=Math.min(8,aniso);map.encoding=THREE.sRGBEncoding;}
   o.material=new THREE.MeshLambertMaterial({map,color:0xffffff});});
  g.add(gl.scene);scene.add(g);NX.loaded.push(file);
 },undefined,e=>{console.warn('NEXT 모형 불러오기 실패',file,e);onFail&&onFail();});
}
