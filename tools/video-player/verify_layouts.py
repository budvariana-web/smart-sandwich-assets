import json
from playwright.sync_api import sync_playwright
URL='http://127.0.0.1:8879/video-player.html'
checks=[]
with sync_playwright() as p:
 b=p.chromium.launch(headless=True)
 for width,height in ((1280,720),(1920,1080),(3840,2160)):
  page=b.new_page(viewport={'width':width,'height':height}); errors=[]
  page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
  page.goto(URL,wait_until='domcontentloaded'); page.wait_for_function("()=>document.querySelector('.player-layer.active')?.currentTime>0.5",timeout=45000)
  result=page.evaluate("""()=>{const h=document.querySelector('header').getBoundingClientRect(),v=document.querySelector('.player-layer.active'),t=document.querySelector('#hours-status').getBoundingClientRect();const videos=[...document.querySelectorAll('.player-layer')];return {header:[h.left,h.top,h.right,h.bottom],timer:[t.left,t.top,t.right,t.bottom],timerText:document.querySelector('#hours-countdown').textContent,timerLabel:document.querySelector('#hours-label').textContent,timerLabelFont:parseFloat(getComputedStyle(document.querySelector('#hours-label')).fontSize),timerFont:parseFloat(getComputedStyle(document.querySelector('#hours-countdown')).fontSize),timerDirection:getComputedStyle(document.querySelector('#hours-status')).flexDirection,scroll:[document.documentElement.scrollWidth,document.documentElement.scrollHeight,innerWidth,innerHeight],playing:!v.paused,time:v.currentTime,status:document.querySelector('#status').hidden,layers:videos.length,contained:videos.every(x=>getComputedStyle(x).objectFit==='contain')}}""")
  checks.append({'viewport':[width,height],**result,'errors':errors}); page.close()
 b.close()
print(json.dumps(checks,ensure_ascii=False))
for c in checks:
 assert c['playing'] and c['time']>0 and c['status'] and c['layers']==2 and c['contained'] and not c['errors']
 assert c['scroll'][0]==c['scroll'][2] and c['scroll'][1]==c['scroll'][3]
 assert 0<=c['header'][0]<c['header'][2]<=c['scroll'][2] and 0<=c['header'][1]<c['header'][3]<=c['scroll'][3]
 assert 0<=c['timer'][0]<c['timer'][2]<=c['scroll'][2] and 0<=c['timer'][1]<c['timer'][3]<=c['scroll'][3]
 assert c['timer'][2] > c['scroll'][2] / 2 and c['timer'][1] > c['scroll'][3] / 2
 assert c['timerDirection'] == 'row'
 assert c['timerLabel'] in ('До открытия осталось:', 'До перерыва осталось:', 'До закрытия осталось:') and len(c['timerText']) == 8
 assert c['timerFont'] >= 66
 assert c['timerLabelFont'] >= 33.75
