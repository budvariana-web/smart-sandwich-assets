"""Regression: never replace the visible <video> while a following clip buffers."""
from playwright.sync_api import sync_playwright

URL = 'http://127.0.0.1:8878/video-player.html'
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1280, 'height': 720})
    page.goto(URL, wait_until='domcontentloaded')
    page.wait_for_function("() => document.querySelectorAll('.player-layer').length === 2", timeout=15000)
    page.wait_for_function("() => document.querySelector('.player-layer.active')?.currentTime > .25", timeout=45000)
    state = page.evaluate("""() => {
      const layers = [...document.querySelectorAll('.player-layer')];
      const active = document.querySelector('.player-layer.active');
      return {
        layers: layers.length,
        active: !!active,
        allContained: layers.every(v => getComputedStyle(v).objectFit === 'contain'),
        allBlack: layers.every(v => getComputedStyle(v).backgroundColor === 'rgb(0, 0, 0)'),
        loadingHidden: document.querySelector('#status').hidden,
      };
    }""")
    browser.close()
assert state == {'layers': 2, 'active': True, 'allContained': True, 'allBlack': True, 'loadingHidden': True}, state
print('buffered-layer regression: PASS')
