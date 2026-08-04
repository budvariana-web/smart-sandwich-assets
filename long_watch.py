# -*- coding: utf-8 -*-
"""Long watch (110s): track page transitions, mini-block video, and FULLSCREEN video page.
Catches the 60s data-refresh and the fullscreen video page moment."""
import json, sys, time
from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else 'https://budvariana-web.github.io/smart-sandwich-assets/menu.html'
DUR = int(sys.argv[2]) if len(sys.argv) > 2 else 110

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)  # no autoplay flag
    ctx = browser.new_context(viewport={'width': 1280, 'height': 720})
    page = ctx.new_page()
    console_log = []
    page.on('console', lambda m: console_log.append(f'[{m.type}] {m.text[:150]}'))
    page.on('pageerror', lambda e: console_log.append(f'[pageerror] {str(e)[:200]}'))
    page.goto(URL, wait_until='domcontentloaded', timeout=60000)

    frame = None
    deadline = time.time() + 35
    while time.time() < deadline:
        for f in page.frames:
            try:
                if f.evaluate('window.BUILD_ID'):
                    frame = f
                    break
            except Exception:
                pass
        if frame:
            break
        time.sleep(2)
    if not frame:
        print(json.dumps({'error': 'no app frame'}, ensure_ascii=False))
        browser.close()
        sys.exit(0)

    samples = []
    t0 = time.time()
    last_page = None
    while time.time() - t0 < DUR:
        try:
            s = frame.evaluate('''() => {
              const mini = document.querySelectorAll('#video-slot video');
              const miniActive = [...mini].find(v => v.classList.contains('active'));
              const fs = document.getElementById('fullscreen-video-el');
              const fsWrap = document.getElementById('fullscreen-video');
              return {
                page: (document.getElementById('page-count')||{}).textContent,
                fsActive: fsWrap.classList.contains('active'),
                fs: fs ? { paused: fs.paused, t: Math.round(fs.currentTime*10)/10, dur: Math.round(fs.duration*10)/10,
                           rs: fs.readyState, ns: fs.networkState, err: fs.error ? fs.error.code : null,
                           src: (fs.currentSrc||'').split('/').pop() } : null,
                mini: miniActive ? { paused: miniActive.paused, t: Math.round(miniActive.currentTime*10)/10, rs: miniActive.readyState } : null,
                miniCount: mini.length,
              };
            }''')
            if s['page'] != last_page:
                s['PAGE_CHANGED'] = True
                last_page = s['page']
            s['elapsed'] = round(time.time() - t0, 1)
            samples.append(s)
        except Exception as e:
            samples.append({'error': str(e)[:80], 'elapsed': round(time.time()-t0,1)})
        time.sleep(4)

    print(json.dumps({'samples': samples, 'console': console_log[-20:]}, ensure_ascii=False, indent=1))
    browser.close()
