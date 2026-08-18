# -*- coding: utf-8 -*-
"""Measure full JS fetch-to-Blob time under CDP network throttling.
Usage (from project root): python tools/video-panel/blob_fetch_probe.py [kbps] [filename]
"""
import json, sys, time
from playwright.sync_api import sync_playwright
kbps=int(sys.argv[1]) if len(sys.argv)>1 else 1000
name=sys.argv[2] if len(sys.argv)>2 else 'video_2c3483f72f6c.mp4'
base='https://budvariana-web.github.io/smart-sandwich-assets/assets/'
url=base+'videos/'+name+'?blobprobe='+str(int(time.time()*1000))
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    page=b.new_page()
    cdp=page.context.new_cdp_session(page); cdp.send('Network.enable')
    cdp.send('Network.emulateNetworkConditions',{'offline':False,'latency':150,'downloadThroughput':kbps*1024/8,'uploadThroughput':kbps*1024/8,'connectionType':'cellular3g'})
    page.goto(base+'menu/index.html?blobprobe='+str(int(time.time()*1000)),wait_until='domcontentloaded',timeout=90000)
    t=time.time()
    r=page.evaluate('''async url => { const r=await fetch(url,{cache:'no-store'}); const b=await r.blob(); return {ok:r.ok,status:r.status,size:b.size,type:b.type}; }''',url)
    r['elapsed']=round(time.time()-t,2); r['kbps']=kbps; r['url']=name
    print(json.dumps(r,ensure_ascii=False))
    b.close()
