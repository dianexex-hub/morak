import asyncio, sys
from playwright.async_api import async_playwright
async def run(url):
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--use-gl=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist'])
        pg = await b.new_page(viewport={'width':900,'height':640})
        await pg.route('**/three.min.js', lambda r: r.fulfill(path='/tmp/three/package/build/three.min.js', content_type='application/javascript'))
        await pg.route('**/GLTFLoader.js', lambda r: r.fulfill(path='/tmp/three/package/examples/js/loaders/GLTFLoader.js', content_type='application/javascript'))
        async def patch(route):
            r = await route.fetch(); t = await r.text(); i = t.rfind('})();'); t = t[:i] + '\nwindow.__dbg=c=>eval(c);\n' + t[i:]
            await route.fulfill(response=r, body=t)
        await pg.route('**/next/?*', patch)
        await pg.goto(url); await pg.wait_for_timeout(3000)
        await pg.evaluate("()=>{document.getElementById('intro').style.display='none';document.getElementById('kiosk').style.display='none';}")
        r = await pg.evaluate("""()=>__dbg(`modeI=3;pos.set(-6,0,12);faceYaw=0;camYaw=0.6;camPitch=.22;camDist=3.6;camDistNow=3.6;
          const R=()=>{renderer.render(scene,camera);const i=renderer.info.render;return [i.calls,i.triangles]};
          me.g.updateMatrixWorld(true);const a=R();me.g.visible=false;const b=R();me.g.visible=true;
          ({calls:a[0]-b[0],tris:a[1]-b[1]})`)""")
        print(url.split('?')[1], r); await b.close()
async def main():
    for u in ['http://localhost:8123/next/?local&v4','http://localhost:8123/next/?local']: await run(u)
asyncio.run(main())
