"""Live monitor: watch page transitions in both-mode to find the video bug.

Polls every 500ms for DURATION seconds and logs:
- page-count text (page X / Y)
- fullscreen video: active, paused, ended, currentTime, duration, src, loop
- menu cards count
Detects: double-advances, flips while video active, video repeating, wrong page after video.
"""
import json
import os
import sys
import time

DIRECT_URL = ("https://script.google.com/macros/s/"
              "AKfycbxlyDvP-_TbVVXGXG7_rxKdXvowJxPu8gn8BXpLKuGnfsCmpHL71CXIWSVUbbamwY4skg/exec")
DURATION = int(sys.argv[1]) if len(sys.argv) > 1 else 100

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(BASE_DIR, "last-build.txt")) as f:
    BUILD = f.read().strip()


def warm_up():
    import urllib.request
    for i in range(1, 8):
        url = DIRECT_URL + "?warm=" + str(int(time.time() * 1000))
        try:
            html = urllib.request.urlopen(urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0", "Cache-Control": "no-cache"}), timeout=20).read().decode("utf-8", "replace")
            if BUILD in html:
                print(f"[warm] fresh on attempt {i}")
                return True
        except Exception as e:
            print(f"[warm] {i}: {e}")
        time.sleep(2)
    print("[warm] FAILED")
    return False


def find_frame(page):
    for f in page.frames:
        try:
            if f.evaluate("() => !!document.querySelector('.layout')"):
                return f
        except Exception:
            pass
    return None


def main():
    from playwright.sync_api import sync_playwright
    warm_up()
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
            print("[monitor] FAIL: no app frame")
            browser.close()
            return 1
        print("[monitor] frame ok, build:", frame.evaluate("() => window.BUILD_ID || ''"))

        t0 = time.time()
        prev = None
        events = []
        while time.time() - t0 < DURATION:
            try:
                snap = frame.evaluate("""() => {
                    var v = document.getElementById('fullscreen-video-el');
                    var wrap = document.getElementById('fullscreen-video');
                    var pc = document.getElementById('page-count');
                    return {
                        page: window.__sb_state ? window.__sb_state.page : null,
                        pc: pc ? pc.textContent : '',
                        vActive: wrap ? wrap.classList.contains('active') : false,
                        vPaused: v ? v.paused : null,
                        vEnded: v ? v.ended : null,
                        vCT: v ? Math.round(v.currentTime * 10) / 10 : null,
                        vDur: v ? (isFinite(v.duration) ? Math.round(v.duration * 10) / 10 : 'NaN') : null,
                        vLoop: v ? v.loop : null,
                        vSrc: v ? (v.src || '').split('/').pop() : null,
                        cards: document.querySelectorAll('.card').length
                    };
                }""")
                # also try to expose state
                try:
                    sp = frame.evaluate("() => (window.state ? {page: state.page, n: state.pages.length, lastAdv: state._lastAdvance, vDurS: state._videoDurSec} : null)")
                except Exception:
                    sp = None
                line = f"[{time.time()-t0:6.1f}s] pc={snap['pc']!r} act={snap['vActive']} pau={snap['vPaused']} end={snap['vEnded']} ct={snap['vCT']} dur={snap['vDur']} loop={snap['vLoop']} src={snap['vSrc']} cards={snap['cards']} state={sp}"
                print(line)
                if prev and prev != (snap['pc'], snap['vActive']):
                    events.append(line)
                prev = (snap['pc'], snap['vActive'])
            except Exception as e:
                print(f"[{time.time()-t0:6.1f}s] poll error: {e}")
            page.wait_for_timeout(500)

        print("\n=== transitions (page-count / active changed) ===")
        for e in events:
            print(e)
        browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
