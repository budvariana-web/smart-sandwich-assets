from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1920, "height": 1080})
    # Background weather/video requests intentionally keep the network active.
    page.goto("http://127.0.0.1:8766/assets/menu/index.html?lang=both", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_function("() => window.state && state.pages && state.pages.some(p => p && p.video)", timeout=30000)
    page.evaluate("""() => {
      state.page = state.pages.findIndex(p => p && p.video);
      renderPage();
    }""")
    page.wait_for_function("""() => {
      const v = document.getElementById('fullscreen-video-el');
      return v.readyState >= 2 && !v.paused && v.currentTime > 0;
    }""", timeout=30000)
    result = page.evaluate("""() => { const v = document.getElementById('fullscreen-video-el'); return {
      overlay: document.getElementById('fullscreen-video').classList.contains('active'),
      duration: v.duration, currentTime: v.currentTime, paused: v.paused, readyState: v.readyState
    }; }""")
    print(result)
    assert result["overlay"] and not result["paused"] and result["duration"] > 1 and result["currentTime"] > 0
    browser.close()
