import asyncio, sys
from playwright.async_api import async_playwright
# 아바타 시험: 서기 / 걷기 / 좋다~! / 탕에 앉기 + 예전 몸 비교
URL = sys.argv[1]; OUT = sys.argv[2]
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--use-gl=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist'])
        pg = await b.new_page(viewport={'width':900,'height':640})
        errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.on('console', lambda m: errs.append(m.text) if m.type=='error' or 'NEXT' in m.text else None)
        await pg.route('**/three.min.js', lambda r: r.fulfill(path='/tmp/three/package/build/three.min.js', content_type='application/javascript'))
        await pg.route('**/GLTFLoader.js', lambda r: r.fulfill(path='/tmp/three/package/examples/js/loaders/GLTFLoader.js', content_type='application/javascript'))
        async def patch(route):
            r = await route.fetch(); t = await r.text()
            i = t.rfind('})();'); t = t[:i] + '\nwindow.__dbg=c=>eval(c);\n' + t[i:]
            await route.fulfill(response=r, body=t)
        await pg.route('**/next/?*', patch)
        await pg.goto(URL); await pg.wait_for_timeout(3000)
        await pg.evaluate("()=>{document.getElementById('intro').style.display='none';document.getElementById('kiosk').style.display='none';}")
        dbg = lambda c: pg.evaluate("c=>__dbg(c)", c)
        await dbg("modeI=3;started=true;pos.set(-6,0,12);faceYaw=0;camYaw=0.6;camPitch=.22;camDist=3.6;camDistNow=3.6;")
        await pg.wait_for_timeout(1500); await pg.screenshot(path=f'{OUT}_1idle.png')
        await pg.keyboard.down('KeyW'); await pg.wait_for_timeout(700); await pg.screenshot(path=f'{OUT}_2walk.png'); await pg.keyboard.up('KeyW')
        await dbg("faceYaw=0;"); await pg.wait_for_timeout(900)
        await pg.click('#ahBtn'); await pg.wait_for_timeout(450); await pg.screenshot(path=f'{OUT}_3joy.png')
        for nm,cy in [('5joyF',0.0),('6joyS',1.5)]:
            await dbg(f"camYaw={cy};camPitch=.15;me.joy=1.4;"); await pg.wait_for_timeout(520); await pg.screenshot(path=f'{OUT}_{nm}.png'); await pg.wait_for_timeout(1200)
        await dbg("pos.set(0,0,-1.5);faceYaw=0;camYaw=0.5;camPitch=.3;camDist=4;camDistNow=4;")
        await pg.wait_for_timeout(2500); await pg.screenshot(path=f'{OUT}_4soak.png')
        info = await dbg("({loaded:NX.loaded, nx:!!me.nx, calls:renderer.info.render.calls})")
        print(info); print('errors:', errs[:6])
        await b.close()
asyncio.run(main())
