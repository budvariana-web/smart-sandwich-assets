"""Live browser regression for buffered transitions: no source replacement on visible layer."""
import json, time
from playwright.sync_api import sync_playwright

URL = 'http://127.0.0.1:8878/video-player.html'
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1280, 'height': 720})
    errors = []
    page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
    page.goto(URL, wait_until='domcontentloaded')
    page.wait_for_function("() => document.querySelector('.player-layer.active')?.currentTime > .25", timeout=45000)
    page.evaluate("() => document.querySelectorAll('.player-layer').forEach(v => v.playbackRate = 16)")
    events, last = [], ''
    deadline = time.monotonic() + 30
    while len(events) < 3 and time.monotonic() < deadline:
        item = page.evaluate("""() => {
          document.querySelectorAll('.player-layer').forEach(v => v.playbackRate = 16);
          const active = document.querySelector('.player-layer.active');
          const layers = [...document.querySelectorAll('.player-layer')];
          return {url:active?.dataset.url || '', activeCount:layers.filter(v=>v.classList.contains('active')).length,
                  allContained:layers.every(v=>getComputedStyle(v).objectFit === 'contain'),
                  activeTime:active?.currentTime || 0};
        }""")
        if item['url'] and item['url'] != last:
            events.append(item); last = item['url']
        time.sleep(.08)
    final = page.evaluate("""() => [...document.querySelectorAll('.player-layer')].map(v=>({url:v.dataset.url,ready:v.dataset.ready,active:v.classList.contains('active'),time:v.currentTime,duration:v.duration,rate:v.playbackRate,paused:v.paused,network:v.networkState}))""")
    browser.close()
print(json.dumps({'events': events, 'final': final, 'errors': errors}, ensure_ascii=False))
assert len(events) == 3, events
assert len({x['url'] for x in events}) == 3, events
assert all(x['activeCount'] == 1 and x['allContained'] for x in events), events
assert not errors, errors
print('buffered transitions: PASS')
