# -*- coding: utf-8 -*-
"""Reproduce fullscreen-video buffering under a constrained connection.
Usage: python throttled_video_probe.py [kbps=1000] [seconds=55] [prewarm_seconds=0] [target_filename_part]
Uses CDP throttling; optional prewarm keeps menu pages visible so v79's one
look-ahead video element can fill its buffer before the fullscreen page.
"""
import json, sys, time
from playwright.sync_api import sync_playwright

KBPS = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
DUR = int(sys.argv[2]) if len(sys.argv) > 2 else 55
PREWARM = int(sys.argv[3]) if len(sys.argv) > 3 else 0
TARGET = sys.argv[4] if len(sys.argv) > 4 else ''
URL = 'https://budvariana-web.github.io/smart-sandwich-assets/assets/menu/index.html?slow=' + str(int(time.time()*1000))

def media(frame):
    return frame.evaluate('''() => {
      const v = document.getElementById('fullscreen-video-el');
      const r=[]; for(let i=0;i<v.buffered.length;i++) r.push([+v.buffered.start(i).toFixed(2),+v.buffered.end(i).toFixed(2)]);
      return {t:+v.currentTime.toFixed(2), dur:+(v.duration||0).toFixed(2), paused:v.paused,
              ended:v.ended, rs:v.readyState, ns:v.networkState, buffered:r,
              page:(document.getElementById('page-count')||{}).textContent,
              active:document.getElementById('fullscreen-video').classList.contains('active'),
              blobSource:(v.currentSrc||'').indexOf('blob:') === 0,
              cache:window.fullscreenPreload ? {url:window.fullscreenPreload.url.split('/').pop(),
                loading:window.fullscreenPreload.loading, blob:!!window.fullscreenPreload.blobUrl,
                failed:window.fullscreenPreload.failed} : null};
    }''')

with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    page=b.new_page(viewport={'width':1280,'height':720})
    cdp=page.context.new_cdp_session(page)
    cdp.send('Network.enable')
    cdp.send('Network.emulateNetworkConditions', {
        'offline':False, 'latency':150,
        'downloadThroughput': KBPS*1024/8, 'uploadThroughput':KBPS*1024/8,
        'connectionType':'cellular3g'})
    events=[]
    page.goto(URL,wait_until='domcontentloaded',timeout=90000)
    deadline=time.time()+70; frame=None
    while time.time()<deadline:
        for f in page.frames:
            try:
                if f.evaluate('document.getElementById("page-count")'):
                    frame=f; break
            except: pass
        if frame: break
        time.sleep(1)
    if not frame: raise RuntimeError('app frame not found')
    deadline=time.time()+70
    while time.time()<deadline and frame.evaluate('() => state.pages.length')==0: time.sleep(1)
    vp=frame.evaluate('''target => {
      var pages = state.pages;
      if (target) {
        var hit = pages.findIndex(p => p && p.video && p.video.indexOf(target) !== -1);
        if (hit >= 0) return hit;
      }
      return pages.findIndex(p => p && p.video);
    }''', TARGET)
    if (vp < 0): raise RuntimeError('video page not found: ' + TARGET)
    # For a selected later clip, render the first of its two preceding menu
    # pages. That executes v79's look-ahead assignment for exactly this URL.
    if (TARGET):
        frame.evaluate('''idx => { state.page = (idx - 2 + state.pages.length) % state.pages.length; renderPage(); }''', vp)
    if PREWARM:
        # Hold menu page 1: v79 has already assigned the first upcoming clip to
        # the single hidden fullscreen element; do not let the normal 15s page
        # timer enter the video page before its buffer is sampled.
        frame.evaluate('() => clearTimeout(state.pageTimer)')
        print('PREWARM', PREWARM, 'before=', json.dumps(media(frame), ensure_ascii=False))
        time.sleep(PREWARM)
        print('PREWARM_DONE', json.dumps(media(frame), ensure_ascii=False))
    frame.evaluate('''() => {
      const v=document.getElementById('fullscreen-video-el');
      ['playing','waiting','stalled','progress','canplay','ended','error'].forEach(e =>
        v.addEventListener(e, () => window.__videoEvents.push({e:e,t:+v.currentTime.toFixed(2),at:Date.now()})));
      window.__videoEvents=[];
    }''')
    frame.evaluate('() => { state.page=%d; renderPage(); armPageTimer(document.getElementById("timer-bar")); }' % vp)
    started=time.time()
    while time.time()-started < DUR:
        s=media(frame); s['elapsed']=round(time.time()-started,1); print(json.dumps(s,ensure_ascii=False))
        if not s['active']: break
        time.sleep(2)
    events=frame.evaluate('() => window.__videoEvents')
    print('EVENTS',json.dumps(events,ensure_ascii=False))
    b.close()
