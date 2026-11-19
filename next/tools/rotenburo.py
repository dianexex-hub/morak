# 모락 NEXT — 노천탕 기본 모형 (Blender 5.3)
# 좌표: three(x, y, z) = blender(x, z, -y). 노천탕 중심 three(0,-7) -> blender(0, 7). 반지름 7.
# 결과: 한 덩어리 메시 + 구운 텍스처(질감·그림자만, 색조는 게임 실시간 조명) -> .glb
import bpy, bmesh, math, random, sys, os
from mathutils import Vector, noise

OUT = sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else '/home/claude/out'
TEX = 2048
random.seed(7)
CX, CY, R = 0.0, 7.0, 7.0
SPOUT_A = -2.2                      # three 기준 각도(x=cos, z=sin) -> blender y = -sin
def pol(a, r, z=0.0):               # three 각도 a 로 위치 (blender 좌표)
    return Vector((CX + math.cos(a)*r, CY - math.sin(a)*r, z))
def angdiff(a, b):
    d = (a-b) % (2*math.pi); return min(d, 2*math.pi-d)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
col = sc.collection

# ---------- 재질 (절차적, 굽기용) ----------
def mat_rock(name, base=(0.42,0.40,0.37), moss=True):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; N = nt.nodes; L = nt.links
    bsdf = N['Principled BSDF']; bsdf.inputs['Roughness'].default_value = .9
    tc = N.new('ShaderNodeTexCoord')
    nz = N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 3.0; nz.inputs['Detail'].default_value = 8
    L.new(tc.outputs['Object'], nz.inputs['Vector'])
    vor = N.new('ShaderNodeTexVoronoi'); vor.inputs['Scale'].default_value = 18
    L.new(tc.outputs['Object'], vor.inputs['Vector'])
    ramp = N.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = (base[0]*.62, base[1]*.62, base[2]*.62, 1)
    ramp.color_ramp.elements[1].color = (base[0]*1.25, base[1]*1.22, base[2]*1.18, 1)
    L.new(nz.outputs['Fac'], ramp.inputs['Fac'])
    speck = N.new('ShaderNodeMix'); speck.data_type = 'RGBA'; speck.blend_type = 'MULTIPLY'
    speck.inputs['Factor'].default_value = .25
    L.new(ramp.outputs['Color'], speck.inputs['A']); L.new(vor.outputs['Distance'], speck.inputs['B'])
    out = speck.outputs['Result']
    if moss:
        geo = N.new('ShaderNodeNewGeometry')
        sep = N.new('ShaderNodeSeparateXYZ'); L.new(geo.outputs['Normal'], sep.inputs['Vector'])
        nz2 = N.new('ShaderNodeTexNoise'); nz2.inputs['Scale'].default_value = 1.6
        L.new(tc.outputs['Object'], nz2.inputs['Vector'])
        add = N.new('ShaderNodeMath'); add.operation = 'ADD'
        L.new(sep.outputs['Z'], add.inputs[0]); L.new(nz2.outputs['Fac'], add.inputs[1])
        mr = N.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 1.38; mr.inputs['From Max'].default_value = 1.6
        L.new(add.outputs['Value'], mr.inputs['Value'])
        mix = N.new('ShaderNodeMix'); mix.data_type = 'RGBA'
        mix.inputs['B'].default_value = (0.26, 0.33, 0.15, 1)
        L.new(mr.outputs['Result'], mix.inputs['Factor']); L.new(out, mix.inputs['A']); out = mix.outputs['Result']
    L.new(out, bsdf.inputs['Base Color'])
    return m

def mat_flat(name, c, nscale=6, var=.25):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; bsdf = N['Principled BSDF']
    tc = N.new('ShaderNodeTexCoord'); nz = N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = nscale; nz.inputs['Detail'].default_value = 10
    L.new(tc.outputs['Object'], nz.inputs['Vector'])
    ramp = N.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = (c[0]*(1-var), c[1]*(1-var), c[2]*(1-var), 1)
    ramp.color_ramp.elements[1].color = (min(1,c[0]*(1+var)), min(1,c[1]*(1+var)), min(1,c[2]*(1+var)), 1)
    L.new(nz.outputs['Fac'], ramp.inputs['Fac']); L.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
    return m

M_ROCK  = mat_rock('rock', (0.50,0.48,0.45))
M_ROCK2 = mat_rock('rock_warm', (0.56,0.49,0.41))
M_WET   = mat_flat('wet_edge', (0.16,0.15,0.14), 9, .35)
M_STONE = mat_flat('flagstone', (0.40,0.38,0.35), 3, .3)
M_MOSS  = mat_flat('moss', (0.13,0.22,0.08), 8, .4)
M_PINE  = mat_flat('pine', (0.07,0.16,0.08), 5, .35)
M_BARK  = mat_flat('bark', (0.20,0.13,0.08), 12, .3)

objs = []
def link(o, m):
    o.data.materials.append(m); objs.append(o); return o

# ---------- 바위 ----------
def boulder(loc, size, rot, mat, seed):
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1)
    off = Vector((seed*3.1, seed*1.7, seed*2.3))
    for v in bm.verts:
        p = v.co
        d = 1 + .28*noise.noise(p*1.1+off) + .1*noise.noise(p*2.6+off)
        v.co = Vector((p.x*size[0], p.y*size[1], p.z*size[2]))*d
        if v.co.z < -size[2]*.35: v.co.z = -size[2]*.35        # 바닥 평평하게(땅에 박힘)
    me = bpy.data.meshes.new('b'); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new('boulder', me); col.objects.link(o)
    o.location = loc; o.rotation_euler = (0, 0, rot)
    dec = o.modifiers.new('d', 'DECIMATE'); dec.ratio = .42
    for p in me.polygons: p.use_smooth = True
    return link(o, mat)

gaps = [(math.pi/2, .32), (SPOUT_A, .22)]   # 건물 쪽 입구, 물대 자리
a = 0.0; i = 0
while a < 2*math.pi:
    s = random.uniform(.42, .78)
    if all(angdiff(a, g) > w for g, w in gaps):
        r = R + random.uniform(.15, .55)
        back = math.sin(a) < -.55                 # 북쪽(뒤) = 더 큰 바위
        k = 1.5 if back else 1.0
        sz = (s*1.25*k, s*1.0*k, s*.62*k*random.uniform(.9, 1.4))
        boulder(pol(a, r, sz[2]*.3), sz, -a+random.uniform(-.4,.4), M_ROCK2 if i % 3 == 0 else M_ROCK, i)
        if random.random() < .45:                 # 바깥쪽 둘째 줄 작은 돌
            s2 = s*.55; boulder(pol(a+.05, r+s*1.05, s2*.2), (s2*1.2, s2, s2*.6), random.uniform(0,6), M_ROCK, i+100)
    a += s*1.7/R + .02; i += 1
# 뒤쪽 큰 경관석 3개
for j, (aa, rr, sz) in enumerate([(-1.55, 8.4, (1.5,1.2,1.5)), (-1.2, 8.5, (1.1,1.0,1.05)), (-1.95, 8.3, (1.0,.9,.8))]):
    boulder(pol(aa, rr, sz[2]*.35), sz, aa, M_ROCK2, 300+j)

# ---------- 젖은 돌 테두리 (물가) ----------
bpy.ops.mesh.primitive_circle_add(vertices=96, radius=R+.28, fill_type='NOTHING', location=(CX, CY, .07))
ring = bpy.context.object; bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.extrude_region_shrink_fatten(TRANSFORM_OT_shrink_fatten={'value': .45})
bpy.ops.object.mode_set(mode='OBJECT'); ring.name = 'wet_edge'; link(ring, M_WET)

# ---------- 디딤돌 ----------
def flag(loc, rx, ry, rot):
    bpy.ops.mesh.primitive_cylinder_add(vertices=random.choice([6,7,8]), radius=1, depth=.07, location=(loc.x, loc.y, .04))
    o = bpy.context.object; o.scale = (rx, ry, 1); o.rotation_euler = (0, 0, rot)
    for v in o.data.vertices:
        v.co.x *= random.uniform(.85, 1.1); v.co.y *= random.uniform(.85, 1.1)
    return link(o, M_STONE)
for k in range(6):                       # 건물 쪽에서 물가로 오는 디딤돌 길
    rr = 8.4 + k*.95; aa = math.pi/2 + (.05 if k % 2 else -.05)
    flag(pol(aa, rr), random.uniform(.42, .52), random.uniform(.34, .42), random.uniform(0, 3))
# 입구 디딤돌 (건물 쪽에서 물로)
for k, rr in enumerate([7.75, 7.15]):
    flag(pol(math.pi/2 + (k-.5)*.05, rr), .45, .38, .3*k)

# ---------- 이끼 덩어리 + 작은 소나무 ----------
for k in range(16):
    aa = random.uniform(0, 2*math.pi)
    if angdiff(aa, math.pi/2) < .4: continue
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1, location=pol(aa, R + random.uniform(.9, 1.3), .05))
    o = bpy.context.object; s = random.uniform(.18, .35); o.scale = (s*1.4, s, s*.45)
    link(o, M_MOSS)
pine_at = pol(-1.55, 9.6)
bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=.09, depth=2.2, location=(pine_at.x, pine_at.y, 1.1)); link(bpy.context.object, M_BARK)
for k, (h, r) in enumerate([(1.3, .95), (1.85, .75), (2.35, .5)]):
    bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=r, depth=.75, location=(pine_at.x + (k-1)*.12, pine_at.y, h))
    o = bpy.context.object; o.scale = (1.25, .9, 1); link(o, M_PINE)

# ---------- 하나로 합치기 ----------
bpy.ops.object.select_all(action='DESELECT')
for o in objs:
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    for m in list(o.modifiers): bpy.ops.object.modifier_apply(modifier=m.name)
bpy.ops.object.convert(target='MESH')
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
bpy.ops.object.join()
ob = bpy.context.object; ob.name = 'rotenburo'; ob.data.name = 'rotenburo'
print('tris', sum(len(p.vertices)-2 for p in ob.data.polygons))

# ---------- UV + 굽기 ----------
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=.003)
bpy.ops.object.mode_set(mode='OBJECT')
# 평평하고 단순한 자갈·젖은 테두리는 텍스처 자리를 줄여 바위에 양보
small = {i for i, m in enumerate(ob.data.materials) if m.name.startswith('wet_edge')}
uvl = ob.data.uv_layers.active.data
for poly in ob.data.polygons:
    if poly.material_index in small:
        for li in poly.loop_indices: uvl[li].uv *= .28
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.uv.select_all(action='SELECT')
bpy.ops.uv.pack_islands(rotate=True, margin=.003)
bpy.ops.object.mode_set(mode='OBJECT')
img = bpy.data.images.new('rotenburo_bake', TEX, TEX, alpha=False)
for m in ob.data.materials:
    n = m.node_tree.nodes.new('ShaderNodeTexImage'); n.image = img; n.select = True; m.node_tree.nodes.active = n

w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (1, 1, 1, 1)
w.node_tree.nodes['Background'].inputs['Strength'].default_value = 1.0
# 바닥(그늘 받는 땅) — 굽기에만 쓰고 내보내지 않음
bpy.ops.mesh.primitive_plane_add(size=60, location=(CX, CY, 0)); gnd = bpy.context.object
gm = bpy.data.materials.new('g'); gm.use_nodes = True; gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.3,.3,.3,1); gnd.data.materials.append(gm)

sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 48
sc.render.bake.margin = 6
bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True); bpy.context.view_layer.objects.active = ob
bpy.ops.object.bake(type='COMBINED')
os.makedirs(OUT, exist_ok=True)
img.filepath_raw = OUT + '/rotenburo_bake.png'; img.file_format = 'PNG'; img.save()

# ---------- 내보내기용 재질: 구운 텍스처 하나 ----------
bpy.data.objects.remove(gnd)
fm = bpy.data.materials.new('rotenburo'); fm.use_nodes = True
tn = fm.node_tree.nodes.new('ShaderNodeTexImage'); tn.image = img
fm.node_tree.links.new(tn.outputs['Color'], fm.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
ob.data.materials.clear(); ob.data.materials.append(fm)
bpy.ops.wm.save_as_mainfile(filepath=OUT + '/rotenburo.blend')
bpy.ops.export_scene.gltf(filepath=OUT + '/rotenburo.glb', export_format='GLB', use_selection=True,
                          export_image_format='JPEG', export_jpeg_quality=85, export_normals=True,
                          export_texcoords=True, export_materials='EXPORT', export_yup=True)
print('done')
