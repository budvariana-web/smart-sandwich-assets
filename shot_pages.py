"""Screenshots of menu board pages for user verification.

Usage: python shot_pages.py [--page N]
Page 0 = first page (burgers), page 3 = salami sandwich + bruschettas (new descriptions).
"""
import json
import os
import sys
import time

from playwright.sync_api import sync_playwright

WRAPPER_URL = "https://budvariana-web.github.io/smart-sandwich-assets/menu.html"
OUT_DIR = os.path.join(os.path.expanduser("~"), "AppData", "Local", "hermes", "cache", "images")

pages_to_shot = [int(a) for a in sys.argv[1:] if a.isdigit()] or [0, 3]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
    ctx = browser.new_context(viewport={"width": 1920, "height": 1080})
    page = ctx.new_page()
    page.goto(WRAPPER_URL, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(8000)

    frame = None
    for _ in range(8):
        for f in page.frames:
            try:
                if f.evaluate("() => !!document.querySelector('.layout')"):
                    frame = f
                    break
            except Exception:
                pass
        if frame:
            break
        page.wait_for_timeout(3000)

    if frame is None:
        print("NO FRAME")
        sys.exit(1)

    for _ in range(15):
        try:
            if frame.evaluate("() => document.querySelectorAll('.card').length > 0"):
                break
        except Exception:
            pass
        page.wait_for_timeout(2000)

    for pi in pages_to_shot:
        try:
            frame.evaluate(f"() => {{ window.state.page = {pi}; window.renderPage(); }}")
        except Exception as e:
            print(f"jump page {pi} failed: {e}")
        page.wait_for_timeout(2500)
        shot = os.path.join(OUT_DIR, f"align-page{pi}-" + time.strftime("%H%M%S") + ".png")
        page.screenshot(path=shot, full_page=False)
        print(shot)
        # verify file exists
        print("exists:", os.path.exists(shot), "size:", os.path.getsize(shot) if os.path.exists(shot) else 0)

    # dump the page-4 card texts + descs to prove descriptions rendered
    frame.evaluate("() => { window.state.page = 3; window.renderPage(); }")
    page.wait_for_timeout(2000)
    info = frame.evaluate("""() => {
        return Array.from(document.querySelectorAll('.card')).map(function(c) {
            return {
                name: (c.querySelector('.card-name') || {}).textContent || '',
                desc: (c.querySelector('.card-desc') || {}).textContent || '',
                cat: (c.querySelector('.card-category') || {}).textContent || '',
                price: (c.querySelector('.card-price') || {}).textContent || ''
            };
        });
    }""")
    print(json.dumps(info, ensure_ascii=False, indent=1))
    browser.close()
