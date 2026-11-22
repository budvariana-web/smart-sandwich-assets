from pathlib import Path
from playwright.sync_api import sync_playwright
URL='http://127.0.0.1:8878/video-player.html'
PORTRAIT='https://budvariana-web.github.io/smart-sandwich-assets/assets/videos/video_858202d50429.mp4'
out=Path(r'C:\Users\Asus\AppData\Local\hermes\projects\smart-sandwich-bar\artifacts\video-player-portrait-1280x720.png')
with sync_playwright() as p:
    b=p.chromium.launch(headless=True); page=b.new_page(viewport={'width':1280,'height':720})
    page.goto(URL,wait_until='domcontentloaded')
    page.wait_for_function("()=>document.querySelector('.player-layer.active')?.currentTime>.2",timeout=45000)
    page.evaluate("""url=>{const active=document.querySelector('.player-layer.active');active.src=url;active.load();active.play()}""",PORTRAIT)
    page.wait_for_function("()=>{const v=document.querySelector('.player-layer.active');return v.videoWidth===720&&v.videoHeight===1280&&v.currentTime>.2}",timeout=45000)
    state=page.evaluate("""()=>{const v=document.querySelector('.player-layer.active'), s=getComputedStyle(v);return {video:[v.videoWidth,v.videoHeight],box:[v.clientWidth,v.clientHeight],fit:s.objectFit,background:s.backgroundColor}}""")
    page.screenshot(path=str(out)); b.close()
print(state); assert state['video']==[720,1280] and state['fit']=='contain' and state['background']=='rgb(0, 0, 0)'