import asyncio, sys
from playwright.async_api import async_playwright
# 사용: shot2.py URL OUT_PREFIX  -> 낮/밤 노천탕 캡처 + fps 정보
URL = sys.argv[1]; OUT = sys.argv[2]
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--use-gl=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist'])
        pg = await b.new_page(viewport={'width':1100,'height':650})
        errs=[]; logs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.on('console', lambda m: logs.append(m.text) if m.type in ('warning','error') and 'flatShading' not in m.text else None)
        await pg.route('**/three.min.js', lambda r: r.fulfill(path='/tmp/three/package/build/three.min.js', content_type='application/javascript'))
        await pg.route('**/GLTFLoader.js', lambda r: r.fulfill(path='/tmp/three/package/examples/js/loaders/GLTFLoader.js', content_type='application/javascript'))
        async def patch(route):
            r = await route.fetch(); t = await r.text()
            i = t.rfind('})();'); t = t[:i] + '\nwindow.__dbg=c=>eval(c);\n' + t[i:]
            await route.fulfill(response=r, body=t)
        await pg.route('**/next/?*', patch)
        await pg.goto(URL); await pg.wait_for_timeout(2500)
        await pg.evaluate("()=>{document.getElementById('intro').style.display='none';document.getElementById('kiosk').style.display='none';}")
        for name, mi in [('day',3),('night',2)]:
            await pg.evaluate(f"()=>__dbg('modeI={mi};pos.set(0,0,4.5);faceYaw=Math.PI;camYaw=0.25;camPitch=.5;camDist=9;camDistNow=9;')")
            await pg.wait_for_timeout(2500)
            await pg.screenshot(path=f'{OUT}_{name}.png')
        info = await pg.evaluate("()=>__dbg('({nx:NX, calls:renderer.info.render.calls, tris:renderer.info.render.triangles})')")
        print(info); print('errors:', errs[:5]); print('warn:', logs[:5])
        await b.close()
asyncio.run(main())
