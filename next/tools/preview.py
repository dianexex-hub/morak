# 모락 NEXT 미리보기(Claude 아티팩트)용 폴더를 만든다: /home/claude/preview
# - 아티팩트 페이지는 주소의 ?쿼리를 못 받고 #이름만 받으므로 location.search 에 #뒤를 덧붙임 → #fps, #v4 로 쓰기
# - trystero 경로를 같은 폴더로(아티팩트에선 외부 연결이 막혀 어차피 혼자 모드)
# 사용: python3 next/tools/preview.py  → 이어서 publish_files(slug는 개발노트 10번 NEXT 메모)
import os, shutil
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); O = '/home/claude/preview'
shutil.rmtree(O, ignore_errors=True); os.makedirs(O + '/assets')
s = open(R + '/next/index.html', encoding='utf8').read()
n = s.count('location.search'); s = s.replace('location.search', "(location.search+'&'+location.hash.slice(1))")
s = s.replace("import('../trystero.mjs')", "import('./trystero.mjs')")
s = s.replace('<title>가상온천 모락 NEXT</title>', '<title>모락 NEXT 미리보기</title>')
open(O + '/index.html', 'w', encoding='utf8').write(s)
shutil.copy(R + '/trystero.mjs', O)
# 아티팩트는 .glb를 못 올림 → 같은 내용을 JSON glTF(버퍼 base64 내장)로 바꿔 .json으로
import json, struct, base64
for f in os.listdir(R + '/next/assets'):
    if not f.endswith('.glb'): shutil.copy(R + '/next/assets/' + f, O + '/assets/'); continue
    b = open(R + '/next/assets/' + f, 'rb').read(); jl = struct.unpack('<I', b[12:16])[0]
    j = json.loads(b[20:20+jl]); bl = struct.unpack('<I', b[20+jl:24+jl])[0]; binc = b[28+jl:28+jl+bl]
    j['buffers'][0]['uri'] = 'data:application/octet-stream;base64,' + base64.b64encode(binc).decode()
    open(O + '/assets/' + f[:-4] + '.json', 'w').write(json.dumps(j, separators=(',', ':')))
    s = s.replace(f, f[:-4] + '.json')
open(O + '/index.html', 'w', encoding='utf8').write(s)
print('search 치환', n, '·', sorted(os.listdir(O)), sorted(os.listdir(O + '/assets')))
