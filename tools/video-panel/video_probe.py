"""Probe: watch the FIRST fullscreen video page, log video state every 1s."""
import time, urllib.request
from playwright.sync_api import sync_playwright

DIRECT_URL = ("https://script.google.com/macros/s/"
              "AKfycbxlyDvP-_TbVVXGXG7_rxKdXvowJxPu8gn8BXpLKuGnfsCmpHL71CXIWSVUbbamwY4skg/exec")

def find_frame(page):
    for f in page.frames:
        try:
            if f.evaluate("() => !!document.querySelector('.layout')"):
                return f
        except Exception:
            pass
    return None

def snap(frame):
    return frame.evaluate("""() => {
        var v = document.getElementById('fullscreen-video-el');
        return {
            act: document.getElementById('fullscreen-video').classList.contains('active'),
            pc: document.getElementById('page-count').textContent,
            ct: v.currentTime.toFixed(2), dur: v.duration.toFixed(2),
            pau: v.paused, end: v.ended, loop: v.loop,
            rs: v.readyState, ns: v.networkState, err: v.error ? v.error.code : 0
        };
    }""")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
    ctx = browser.new_context(viewport={"width": 1920, "height": 1080})
    page = ctx.new_page()
    page.goto(DIRECT_URL + "?lang=both", wait_until="domcontentloaded", timeout=30000)
    frame = None
    for _ in range(6):
        page.wait_for_timeout(3000)
        frame = find_frame(page)
        if frame:
            break
    if not frame:
        print("no frame"); browser.close(); raise SystemExit(1)
    t0 = time.time()
    while time.time() - t0 < 70:
        s = snap(frame)
        if s['act']:
            print(f"[{time.time()-t0:6.1f}s] VIDEO {s}")
        else:
            print(f"[{time.time()-t0:6.1f}s] {s['pc']:>8} {s['ct']}/{s['dur']} rs={s['rs']} ns={s['ns']} err={s['err']} end={s['end']}")
        page.wait_for_timeout(1000)
    browser.close()
