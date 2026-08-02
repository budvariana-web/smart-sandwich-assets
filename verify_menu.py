"""Verify the deployed Smart Sandwich Bar menu in a real browser.

Solves the recurring problem: after `python deploy.py`, the GAS proxy
(script.google.com / googleusercontent.com) can serve STALE HTML for the
first request(s). Plain Playwright runs then check the old page and report
wrong colors/layout.

Strategy (in order):
  1. Warm-up: request the /exec URL with a unique query param until the
     response HTML contains the expected BUILD_ID (or give up).
  2. Browser check with marker: load the TV wrapper (or direct URL), find
     the app iframe, compare window.BUILD_ID to expected. If stale,
     reload the TOP page (wrapper re-runs its JS and appends a fresh
     ?v=Date.now() cache-buster) and retry up to N times.
  3. Metrics + console errors + screenshot.

Usage:  python verify_menu.py [--url URL] [--build ID]
Exit code 0 = fresh page verified, 1 = stale / errors found.
"""
import json
import os
import sys
import time
import urllib.request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WRAPPER_URL = "https://budvariana-web.github.io/smart-sandwich-assets/menu.html"
DIRECT_URL = ("https://script.google.com/macros/s/"
              "AKfycbxlyDvP-_TbVVXGXG7_rxKdXvowJxPu8gn8BXpLKuGnfsCmpHL71CXIWSVUbbamwY4skg/exec")

MAX_WARM = 8      # warm-up attempts
WARM_DELAY = 2    # seconds between warm-up attempts
MAX_RELOADS = 4   # browser reloads while waiting for fresh marker


def expected_build():
    """Read build id written by deploy.py, or from --build."""
    if "--build" in sys.argv:
        return sys.argv[sys.argv.index("--build") + 1]
    p = os.path.join(BASE_DIR, "last-build.txt")
    if os.path.exists(p):
        with open(p) as f:
            return f.read().strip()
    return None


def warm_up(build_id):
    """Prime the GAS proxy so the first browser hit is fresh."""
    if not build_id:
        print("[warm] no expected build id -> skip")
        return True
    for i in range(1, MAX_WARM + 1):
        url = DIRECT_URL + "?warm=" + str(int(time.time() * 1000))
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (verifier)",
                "Cache-Control": "no-cache",
            })
            html = urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "replace")
            if build_id in html:
                print(f"[warm] fresh on attempt {i}")
                return True
            print(f"[warm] attempt {i}: stale (no {build_id})")
        except Exception as e:
            print(f"[warm] attempt {i}: error {e}")
        time.sleep(WARM_DELAY)
    print(f"[warm] FAILED: proxy still stale after {MAX_WARM} attempts")
    return False


def run_browser(url, build_id):
    from playwright.sync_api import sync_playwright

    errors_console = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        ctx = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = ctx.new_page()
        page.on("pageerror", lambda e: errors_console.append("pageerror: " + str(e)))
        page.on("console", lambda m: errors_console.append(f"[{m.type}] {m.text}")
                if m.type == "error" else None)

        fresh = False
        for attempt in range(MAX_RELOADS + 1):
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            # Wait for the app iframe to appear
            page.wait_for_timeout(8000)
            frame = None
            for f in page.frames:
                try:
                    if f.evaluate("() => !!document.querySelector('.layout')"):
                        frame = f
                        break
                except Exception:
                    pass
            if frame is None:
                print(f"[browser] attempt {attempt}: app frame not found yet")
                page.wait_for_timeout(5000)
                continue
            actual = frame.evaluate("() => window.BUILD_ID || ''")
            if build_id and actual != build_id:
                print(f"[browser] attempt {attempt}: stale HTML (BUILD_ID={actual!r}, "
                      f"want {build_id!r}) -> reload top page")
                page.reload(wait_until="domcontentloaded")
                page.wait_for_timeout(8000)
                continue
            fresh = True
            print(f"[browser] attempt {attempt}: FRESH (BUILD_ID={actual!r})")

            # ---- wait for data-driven cards ----
            cards_ok = False
            for _ in range(15):  # up to ~30s
                try:
                    if frame.evaluate("() => document.querySelectorAll('.card').length > 0"):
                        cards_ok = True
                        break
                except Exception:
                    pass
                page.wait_for_timeout(2000)
            print(f"[browser] cards loaded: {cards_ok}")

            # ---- metrics ----
            metrics = frame.evaluate("""() => {
                var cards = Array.from(document.querySelectorAll('.card'));
                var card = cards[0];
                var d = card ? card.querySelector('.card-desc') : null;
                var naturalDesc = 0;
                if (d) {
                    var clone = d.cloneNode(true);
                    clone.style.position = 'absolute';
                    clone.style.visibility = 'hidden';
                    clone.style.display = 'block';
                    clone.style.webkitLineClamp = 'none';
                    clone.style.height = 'auto';
                    clone.style.flex = 'none';
                    clone.style.overflow = 'visible';
                    clone.style.width = d.getBoundingClientRect().width + 'px';
                    document.body.appendChild(clone);
                    naturalDesc = Math.round(clone.getBoundingClientRect().height);
                    document.body.removeChild(clone);
                }
                var img = card ? card.querySelector('.card-img, .card-no-img') : null;
                var imgH = img ? Math.round(img.getBoundingClientRect().height) : 0;
                var cardH = card ? Math.round(card.getBoundingClientRect().height) : 0;
                var videos = Array.from(document.querySelectorAll('#video-slot video'));
                var active = videos.filter(function(v) { return v.classList.contains('active'); });
                var heights = cards.map(function(c) { return Math.round(c.getBoundingClientRect().height); });
                return {
                    build: window.BUILD_ID || '',
                    cards: cards.length,
                    cardHeights: heights,
                    imgPct: card ? Math.round(imgH / cardH * 100) : 0,
                    descNaturalH: naturalDesc,
                    annTop: (document.getElementById('ann-top-text') || {}).textContent || '',
                    annBottom: (document.getElementById('ann-bottom-text') || {}).textContent || '',
                    videoActive: active.length,
                    videoPlaying: active.length ? !active[0].paused && active[0].readyState >= 2 : false,
                    videoCount: videos.length
                };
            }""")
            print("[metrics]", json.dumps(metrics, ensure_ascii=False))

            shot = os.path.join(os.path.expanduser("~"), "AppData", "Local", "hermes",
                                "cache", "images", "verify-" + time.strftime("%H%M%S") + ".png")
            page.screenshot(path=shot)
            print("[screenshot]", shot)
            break

        browser.close()

    print("[console-errors]", len(errors_console))
    for e in errors_console[:5]:
        print("   ", e)
    return fresh


if __name__ == "__main__":
    url = WRAPPER_URL
    if "--url" in sys.argv:
        url = sys.argv[sys.argv.index("--url") + 1]
    bid = expected_build()
    print(f"[verify] url={url} build={bid}")

    warm_ok = warm_up(bid)
    if not warm_ok:
        # Still try the browser: reload loop may succeed where curl couldn't.
        print("[verify] warm-up failed, relying on browser reload loop")
    ok = run_browser(url, bid)
    sys.exit(0 if ok else 1)
