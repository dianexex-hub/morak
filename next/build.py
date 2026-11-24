# 모락 NEXT: src/*.js 를 index.html 의 표시 자리(// >>> src/이름.js ~ // <<< src/이름.js)에 끼워 넣는다.
# 사용: python3 next/build.py   (어느 폴더에서 돌려도 됨) → 문법 검사까지
import re, os, subprocess, sys
D = os.path.dirname(os.path.abspath(__file__)); P = os.path.join(D, 'index.html')
s = open(P, encoding='utf8').read()
def put(m):
    name = m.group(1); body = open(os.path.join(D, 'src', name), encoding='utf8').read().rstrip('\n')
    return m.group(0).split('\n', 1)[0] + '\n' + body + f'\n// <<< src/{name}'
s2, n = re.subn(r'// >>> src/(\S+)[^\n]*\n.*?\n// <<< src/\1', put, s, flags=re.S)
open(P, 'w', encoding='utf8').write(s2)
chk = "const s=require('fs').readFileSync(process.argv[1],'utf8');for(const m of s.matchAll(/<script>([\\s\\S]*?)<\\/script>/g))new Function(m[1]);console.log('OK')"
r = subprocess.run(['node', '-e', chk, P], capture_output=True, text=True)
print(f'{n}개 끼움,', 'changed' if s2 != s else 'unchanged', '·', (r.stdout or r.stderr).strip()[:300]); sys.exit(r.returncode)
