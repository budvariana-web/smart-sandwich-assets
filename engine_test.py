# -*- coding: utf-8 -*-
"""Test live surfaces on multiple engines (firefox, webkit) — real user conditions."""
import json, sys, time
from playwright.sync_api import sync_playwright

URLS = {
    'static': 'https://budvariana-web.github.io/smart-sandwich-assets/assets/menu/index.html',
    'wrapper': 'https://budvariana-web.github.io/smart-sandwich-assets/menu.html',
    'exec': 'https://script.google.com/macros/s/AKfycbxlyDvP-_TbVVXGXG7_rxKdXvowJxPu8gn8BXpLKuGnfsCmpHL71CXIWSVUbbamwY4skg/exec',
}

def find_app_frame(page, timeout=35):
    deadline = time.time() + timeout
    while time.time() < deadline:
        for f in page.frames:
            try:
                if f.evaluate('window.BUILD_ID') or f.evaluate('document.getElementById("page-count")'):
                    return f
            except Exception:
                pass
        time.sleep(2)
    return None

results = {}
with sync_playwright() as p:
    for engine in ['firefox', 'webkit']:
        for name, url in URLS.items():
            key = f'{engine}-{name}'
            try:
                browser = p[engine].launch(headless=True)
                ctx = browser.new_context(viewport={'width': 1280, 'height': 720})
                page = ctx.new_page()
                console_log = []
                page.on('console', lambda m: console_log.append(f'[{m.type}] {m.text[:100]}'))
                page.on('pageerror', lambda e: console_log.append(f'[pageerror] {str(e)[:150]}'))
                try:
                    page.goto(url, wait_until='domcontentloaded', timeout=60000)
                except Exception as e:
                    results[key] = {'load_error': str(e)[:100]}
                    browser.close()
                    continue
                frame = find_app_frame(page)
                if not frame:
                    results[key] = {'error': 'app frame not found', 'console': console_log[-8:]}
                    browser.close()
                    continue
                time.sleep(8)
                vids = frame.evaluate('''() => {
                  return [...document.querySelectorAll('video')].map(v => ({
                    paused: v.paused, t: Math.round(v.currentTime*10)/10, rs: v.readyState,
                    err: v.error ? v.error.code : null,
                    src: (v.currentSrc||'').split('/').pop(),
                    active: v.classList.contains('active'),
                  }))
                }''')
                pc = frame.evaluate('(document.getElementById("page-count")||{textContent:""}).textContent')
                playing = [v for v in vids if not v['paused'] and v['t'] > 0.5]
                results[key] = {
                    'pageCount': pc,
                    'total_videos': len(vids),
                    'playing_videos': len(playing),
                    'videos': vids[:4],
                    'console': console_log[-8:],
                }
                browser.close()
            except Exception as e:
                results[key] = {'engine_error': str(e)[:150]}

print(json.dumps(results, ensure_ascii=False, indent=1))
