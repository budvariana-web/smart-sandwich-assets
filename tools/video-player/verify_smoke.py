import json, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright
URL=sys.argv[1] if len(sys.argv)>1 else 'http://127.0.0.1:8877/video-player.html'
shot=Path(r'C:\Users\Asus\AppData\Local\hermes\projects\smart-sandwich-bar\artifacts\video-player-1280x720.png')
with sync_playwright() as p:
 b=p.chromium.launch(headless=True); c=b.new_context(viewport={'width':1280,'height':720}); page=c.new_page(); errors=[]
 page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None); page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto(URL,wait_until='domcontentloaded'); page.wait_for_function("()=>{const v=document.querySelector('#player');return v&&v.currentSrc&&v.currentTime>1}",timeout=45000)
 a=page.evaluate("()=>{const v=document.querySelector('#player'),h=document.querySelector('header').getBoundingClientRect();return {src:v.currentSrc,time:v.currentTime,paused:v.paused,video:[v.videoWidth,v.videoHeight],header:[h.left,h.top,h.right,h.bottom],clock:document.querySelector('#clock').textContent,scroll:[document.documentElement.scrollWidth,document.documentElement.scrollHeight,innerWidth,innerHeight]}}")
 page.wait_for_timeout(1100); b2=page.evaluate("()=>document.querySelector('#player').currentTime"); page.screenshot(path=str(shot)); b.close()
print(json.dumps({'before':a,'afterTime':b2,'errors':errors,'screenshot':str(shot)},ensure_ascii=False))
