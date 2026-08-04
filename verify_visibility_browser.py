import json,time
from playwright.sync_api import sync_playwright
url='https://budvariana-web.github.io/smart-sandwich-assets/assets/menu/index.html?lang=both&visibility-check='+str(int(time.time()))
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    page=b.new_page(viewport={'width':1280,'height':720})
    logs=[]; page.on('console',lambda m: logs.append({'type':m.type,'text':m.text}))
    page.goto(url,wait_until='domcontentloaded',timeout=90000)
    frame=None; end=time.time()+70
    while time.time()<end:
        for f in page.frames:
            try:
                if f.evaluate('() => typeof state !== "undefined" && state.data && state.data.items && state.data.items.length'):
                    frame=f; break
            except: pass
        if frame: break
        time.sleep(1)
    if not frame: raise RuntimeError('menu app data not loaded')
    out=frame.evaluate('''() => ({items:state.data.items.length,pages:state.pages.length,
      forbidden:state.data.items.filter(x=>['Лимонад','Американо','Limunada','Amerikano'].includes(x.name)).map(x=>x.name),
      count:document.getElementById('page-count').textContent,
      cardNames:[...document.querySelectorAll('.card-name')].map(x=>x.textContent.trim())})''')
    out['consoleErrors']=[x for x in logs if x['type']=='error']
    print(json.dumps(out,ensure_ascii=False))
    b.close()
