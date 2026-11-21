# 모락 NEXT — 한 덩어리 아바타 몸 (Blender 5.3)
# 좌표: three(x, y, z) = blender(x, -z, y). 얼굴은 three +z = blender -y.
# 치수는 v4.0 아바타와 같게 맞춤(머리 중심 높이 1.15·반지름 .27, 어깨 (±.34, .84), 골반 (±.12, .38), 무릎 .20)
#  → 기존 얼굴·머리카락·모자·액세서리를 그대로 얹을 수 있음.
# 결과: 뼈대(body, head, armL/R, legL/R, shinL/R) + 한 메시 + 구역 UV(u=(구역+.5)/8, 게임에서 8칸 팔레트로 색칠)
import bpy, bmesh, math, sys, os
from mathutils import Vector

OUT = sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else '/home/claude/out'
bpy.ops.wm.read_factory_settings(use_empty=True)
col = bpy.context.scene.collection
A = .8                                    # 묶는 자세의 팔 벌림(라디안). 게임 코드 NX_BIND 와 같아야 함
HEAD_C, HEAD_R = Vector((0, 0, 1.15)), .275
SH = {s: Vector((s*.34, 0, .84)) for s in (-1, 1)}
ADIR = {s: Vector((s*math.sin(A), 0, -math.cos(A))) for s in (-1, 1)}
HIP = {s: Vector((s*.12, 0, .38)) for s in (-1, 1)}
KNEE_Z = .20

# ---------- 모양: 단순 도형 거리장(SDF)을 부드럽게 합친 뒤 메시로 ----------
def sd_ell(p, c, r):            # 타원체 (근사)
    q = Vector(((p.x-c.x)/r[0], (p.y-c.y)/r[1], (p.z-c.z)/r[2]))
    return (q.length - 1) * min(r)
def sd_cap(p, a, b, ra, rb):    # 굵기가 변하는 캡슐
    pa, ba = p-a, b-a; h = max(0, min(1, pa.dot(ba)/ba.dot(ba)))
    return (pa - ba*h).length - (ra + (rb-ra)*h)
def smin(a, b, k):
    h = max(0, min(1, .5 + .5*(b-a)/k)); return b + (a-b)*h - k*h*(1-h)

PARTS = {}
def parts(p):
    d = {}
    d['head'] = sd_ell(p, HEAD_C, (HEAD_R, HEAD_R*.96, HEAD_R*.98))
    d['neck'] = sd_cap(p, Vector((0, 0, .88)), Vector((0, 0, 1.0)), .12, .11)
    d['torso'] = sd_ell(p, Vector((0, 0, .66)), (.32, .29, .35))
    d['belly'] = sd_ell(p, Vector((0, -.06, .55)), (.27, .25, .22))
    for s in (-1, 1):
        k = 'L' if s < 0 else 'R'
        d['leg'+k] = sd_cap(p, HIP[s] + Vector((0, 0, .04)), Vector((s*.12, 0, .085)), .105, .082)
        d['foot'+k] = sd_ell(p, Vector((s*.125, -.045, .05)), (.095, .14, .06))
        a0 = SH[s] - ADIR[s]*.04
        d['arm'+k] = sd_cap(p, a0, SH[s] + ADIR[s]*.30, .074, .06)
        d['hand'+k] = sd_ell(p, SH[s] + ADIR[s]*.345, (.075, .07, .082))
    return d
def field(p):
    d = parts(p)
    body = smin(smin(d['torso'], d['belly'], .08), d['neck'], .07)
    body = smin(body, d['head'], .05)
    for k in 'LR':
        leg = smin(d['leg'+k], d['foot'+k], .04)
        arm = smin(d['arm'+k], d['hand'+k], .03)
        body = smin(body, leg, .06); body = smin(body, arm, .025)
    return body

# 격자에서 거리장을 표본 → 메타볼 대신 Blender의 "Remesh 없이" 마칭 큐브: 간단히 bmesh 로 만든 뒤 Blender remesh 로 정리
import numpy as np
try:
    from skimage.measure import marching_cubes
except ImportError:
    marching_cubes = None
step = .012
xs = np.arange(-.58, .58+step, step); ys = np.arange(-.36, .36+step, step); zs = np.arange(-.02, 1.48+step, step)
vol = np.zeros((len(xs), len(ys), len(zs)), np.float32)
for i, x in enumerate(xs):
    for j, y in enumerate(ys):
        for k, z in enumerate(zs):
            vol[i, j, k] = field(Vector((x, y, z)))
verts, faces, _, _ = marching_cubes(vol, 0.0, spacing=(step, step, step))
verts = verts + np.array([xs[0], ys[0], zs[0]])
me = bpy.data.meshes.new('morak_body'); me.from_pydata(verts.tolist(), [], faces[:, ::-1].tolist()); me.update()
ob = bpy.data.objects.new('morak_body', me); col.objects.link(ob)
bpy.context.view_layer.objects.active = ob; ob.select_set(True)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.remove_doubles(threshold=.0005)
bpy.ops.mesh.normals_make_consistent(inside=False); bpy.ops.object.mode_set(mode='OBJECT')
dec = ob.modifiers.new('d', 'DECIMATE'); dec.ratio = 2000 / len(me.polygons)
bpy.ops.object.modifier_apply(modifier='d')
bm = bmesh.new(); bm.from_mesh(me)
def cut(co, no):
    geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
    bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-5, plane_co=co, plane_no=no)
for z in (.52, .20, .09, .93): cut((0, 0, z), (0, 0, 1))      # 밑단·무릎·발목·목
for s_ in (-1, 1):
    for t in (.13, .29, .325): cut(SH[s_] + ADIR[s_]*t, ADIR[s_])   # 반팔·긴팔·손목
bmesh.ops.triangulate(bm, faces=bm.faces[:]); bm.to_mesh(me); bm.free()
for p in me.polygons: p.use_smooth = True
print('tris', sum(len(p.vertices)-2 for p in me.polygons), 'verts', len(me.vertices))

# ---------- 구역(색칠 칸)과 뼈 무게 ----------
def sst(a, b, x):               # smoothstep (a→b)
    t = max(0, min(1, (x-a)/(b-a))); return t*t*(3-2*t)
def arm_t(p, s):                # 어깨에서 팔 방향으로 얼마나 왔나(0 어깨, .34 손목쯤)
    return (p - SH[s]).dot(ADIR[s])
ZONE = {}
def zone_at(p, wa_=None):
    d = parts(p); near = min(d, key=d.get); s = -1 if p.x < 0 else 1
    if near in ('head', 'neck') or (p.z > .93 and abs(p.x) < .17): return 0
    if near.startswith('hand'): return 0
    if near.startswith('foot') or p.z < .09: return 0
    if near.startswith('arm') or (wa_ is not None and wa_ > .5 and not near.startswith('hand')):
        t = arm_t(p, s); return 2 if t < .13 else (3 if t < .29 else (0 if t > .325 else 3))
    if near.startswith('leg'): return 5 if p.z > KNEE_Z else 6
    return 1 if p.z > .52 else 4                        # 0 피부(머리·목·손·발) 1 윗몸 2 위팔 3 아래팔 4 골반 5 허벅지 6 정강이
weights = []
ARMW = {}
for v in me.vertices:
    p = v.co; d = parts(p); near = min(d, key=d.get)
    s = -1 if p.x < 0 else 1; k = 'L' if s < 0 else 'R'
    if near in ('head', 'neck') or p.z > .93: z = 0
    elif near.startswith('hand'): z = 0
    elif near.startswith('foot') or p.z < .09: z = 0
    elif near.startswith('arm'):
        t = arm_t(p, s); z = 2 if t < .13 else (3 if t < .29 else 0)
    elif near.startswith('leg'): z = 5 if p.z > KNEE_Z else 6
    else: z = 1 if p.z > .52 else 4
    ZONE[v.index] = z
    # 무게
    w = {'body': 1.0}
    wh = sst(.95, 1.04, p.z)
    if wh > 0: w['head'] = wh
    t_ = arm_t(p, s)
    if near.startswith(('arm', 'hand')): wa = sst(-.04, .05, t_)
    elif (p - SH[s]).length < .13: wa = sst(-.02, .06, t_) * .6
    else: wa = 0
    if wa > 0: w['arm'+k] = wa
    ARMW[v.index] = wa
    if p.z < .5:
        wl = sst(.47, .33, p.z) * sst(.0, .05, abs(p.x))
        if wl > 0:
            ws = sst(.25, .15, p.z)
            if wl*(1-ws) > 0: w['leg'+k] = wl*(1-ws)
            if wl*ws > 0: w['shin'+k] = wl*ws
    rest = 1 - sum(x for n, x in w.items() if n != 'body')
    w['body'] = max(0, rest)
    tot = sum(w.values()); weights.append({n: x/tot for n, x in w.items() if x/tot > .002})

uv = me.uv_layers.new(name='UVMap')
for poly in me.polygons:
    z = zone_at(Vector(poly.center), sum(ARMW[vi] for vi in poly.vertices)/len(poly.vertices))
    for li in poly.loop_indices: uv.data[li].uv = ((z+.5)/8, .5)

# ---------- 뼈대 ----------
arm = bpy.data.armatures.new('rig'); rig = bpy.data.objects.new('rig', arm); col.objects.link(rig)
bpy.context.view_layer.objects.active = rig; bpy.ops.object.mode_set(mode='EDIT')
E = arm.edit_bones
def bone(name, head, tail, parent=None):
    b = E.new(name); b.head = head; b.tail = tail
    if parent: b.parent = E[parent]
    return b
bone('body', (0, 0, .0), (0, 0, .6))
bone('head', (0, 0, 1.0), (0, 0, 1.4), 'body')
for s in (-1, 1):
    k = 'L' if s < 0 else 'R'
    bone('arm'+k, SH[s], SH[s] + ADIR[s]*.34, 'body')
    bone('leg'+k, HIP[s], (s*.12, 0, KNEE_Z), 'body')
    bone('shin'+k, (s*.12, 0, KNEE_Z), (s*.12, 0, .03), 'leg'+k)
bpy.ops.object.mode_set(mode='OBJECT')
for n in ['body', 'head', 'armL', 'armR', 'legL', 'legR', 'shinL', 'shinR']: ob.vertex_groups.new(name=n)
for v, w in zip(me.vertices, weights):
    for n, x in w.items(): ob.vertex_groups[n].add([v.index], x, 'REPLACE')
ob.parent = rig; m = ob.modifiers.new('rig', 'ARMATURE'); m.object = rig
mat = bpy.data.materials.new('morak_body'); ob.data.materials.append(mat)

os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=OUT + '/avatar.blend')
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=OUT + '/avatar.glb', export_format='GLB', use_selection=True,
                          export_skins=True, export_animations=False, export_yup=True,
                          export_texcoords=True, export_normals=True, export_materials='PLACEHOLDER')
print('done')
