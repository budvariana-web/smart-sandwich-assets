import json, time
from pathlib import Path
from playwright.sync_api import sync_playwright

errors = []
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 720}, device_scale_factor=1)
    page.on("console", lambda msg: errors.append(f"console:{msg.type}:{msg.text}") if msg.type == "error" else None)
    page.on("pageerror", lambda err: errors.append(f"pageerror:{err}"))
    page.goto("http://127.0.0.1:8765/assets/menu/index.html?lang=both&weather-check=1", wait_until="networkidle", timeout=60000)
    page.wait_for_function("() => window.state && state.data && state.weather && state.weather.current", timeout=45000)
    result = page.evaluate("""() => {
      const anns = (state.data && state.data.announcements) || [];
      window.annIndex = anns.length; renderAnnouncements();
      const card = document.querySelector('.weather-card');
      const host = document.getElementById('ann-top');
      const r = card.getBoundingClientRect(), h = host.getBoundingClientRect();
      const text = card.innerText.replace(/\\s+/g, ' ').trim();
      return {weather: state.weather.current, card: {left:r.left, top:r.top, right:r.right, bottom:r.bottom, width:r.width, height:r.height}, host: {left:h.left, top:h.top, right:h.right, bottom:h.bottom, width:h.width, height:h.height}, fits: r.left >= h.left && r.right <= h.right + 1 && r.top >= h.top && r.bottom <= h.bottom + 1, text, pageCount: state.pages.length};
    }""")
    page.screenshot(path="weather-widget-1280x720.png", full_page=True)
    browser.close()
print(json.dumps({"result": result, "errors": errors}, ensure_ascii=False))
if errors or not result["fits"] or "БАР" not in result["text"]:
    raise SystemExit(1)
