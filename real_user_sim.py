# -*- coding: utf-8 -*-
"""Real-user simulation: NO autoplay-policy flag. Test surfaces: static copy, wrapper->/exec, /exec direct.
Report whether any video actually plays (paused=false, t>0.5)."""
import json, sys, time
from playwright.sync_api import sync_playwright

URLS = {
    'static': 'https://budvariana-web.github.io/smart-sandwich-assets/assets/menu/index.html',
    'wrapper': 'https://budvariana-web.github.io/smart-sandwich-assets/menu.html',
    'exec': 'https://script.google.com/macros/s/AKfycbxlyDvP-_TbVVXGXG7_rxKdXvowJxPu8gn8BXpLKuGnfsCmpHL71CXIWSVUbbamwY4skg/exec',
}

def find_app_frame(page):
    deadline = time.time() + 35
    while time.time() < deadline:
        for f in page.frames:
            try:
                bid = f.evaluate('window.BUILD_ID || ""')
                if bid:
                    return f
            except Exception:
                pass
        time.sleep(2)
    return None

results = {}
with sync_playwright() as p:
    for name, url in URLS.items():
        for viewport_name, viewport in [('desktop', {'width': 1280, 'height': 720}), ('mobile', {'width': 390, 'height': 844})]:
            key = f'{name}-{viewport_name}'
            browser = p.chromium.launch(headless=True)  # NO autoplay flag
            ctx = browser.new_context(viewport=viewport)
            page = ctx.new_page()
            console_log = []
            page.on('console', lambda m: console_log.append(f'[{m.type}] {m.text[:120]}'))
            try:
                page.goto(url, wait_until='domcontentloaded', timeout=60000)
            except Exception as e:
                results[key] = {'load_error': str(e)[:100]}
                browser.close()
                continue
            time.sleep(8)
            frame = find_app_frame(page)
            if not frame:
                results[key] = {'error': 'app frame not found', 'console': console_log[-8:]}
                browser.close()
                continue
            # wait for videos
            time.sleep(6)
            vids = frame.evaluate('''() => {
              return [...document.querySelectorAll('video')].map(v => ({
                paused: v.paused, t: Math.round(v.currentTime*10)/10, rs: v.readyState,
                ns: v.networkState, err: v.error ? v.error.code : null,
                src: (v.currentSrc||'').split('/').pop(),
                active: v.classList.contains('active'),
                muted: v.muted,
                playsinline: v.playsInline,
                preload: v.preload,
              }))
            }''')
            pc = frame.evaluate('(document.getElementById("page-count")||{textContent:""}).textContent')
            playing = [v for v in vids if not v['paused'] and v['t'] > 0.5]
            results[key] = {
                'pageCount': pc,
                'total_videos': len(vids),
                'playing_videos': len(playing),
                'videos': vids[:3],
                'console': console_log[-10:],
            }
            browser.close()

print(json.dumps(results, ensure_ascii=False, indent=1))
