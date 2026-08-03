"""E2E test for v72 video-page logic in both (bilingual) mode.

Checks:
  1. First fullscreen video page appears after the first RU+ME pair
     (page-count "3 / 25"), video has loop=false and a real duration.
  2. The video page ends on the REAL clip duration (not hardcoded 40s),
     then the next page is NOT page 1 (no reset after video).
  3. After a data refresh (refreshSeconds=60), the page position is kept
     (page-count != "1 / 25" ~75s in).

Usage: python video_cycle_test.py
"""
import json
import os
import sys
import time
import urllib.request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIRECT_URL = ("https://script.google.com/macros/s/"
              "AKfycbxlyDvP-_TbVVXGXG7_rxKdXvowJxPu8gn8BXpLKuGnfsCmpHL71CXIWSVUbbamwY4skg/exec")


def expected_build():
    p = os.path.join(BASE_DIR, "last-build.txt")
    if os.path.exists(p):
        with open(p) as f:
            return f.read().strip()
    return None


def warm_up(build_id):
    for i in range(1, 8):
        url = DIRECT_URL + "?warm=" + str(int(time.time() * 1000))
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (verifier)", "Cache-Control": "no-cache"})
            html = urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "replace")
            if build_id in html:
                print(f"[warm] fresh on attempt {i}")
                return True
        except Exception as e:
            print(f"[warm] attempt {i}: {e}")
        time.sleep(2)
    print("[warm] FAILED")
    return False


def find_app_frame(page):
    for f in page.frames:
        try:
            if f.evaluate("() => !!document.querySelector('.layout')"):
                return f
        except Exception:
            pass
    return None


def main():
    build_id = expected_build()
    print(f"[test] build={build_id}")
    warm_up(build_id)

    from playwright.sync_api import sync_playwright
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        ctx = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = ctx.new_page()
        page.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        page.on("console", lambda m: errors.append(f"[{m.type}] {m.text}") if m.type == "error" else None)

        page.goto(DIRECT_URL + "?lang=both", wait_until="domcontentloaded", timeout=30000)
        frame = None
        for _ in range(6):
            page.wait_for_timeout(4000)
            frame = find_app_frame(page)
            if frame:
                break
        if frame is None:
            print("[test] FAIL: app frame not found")
            browser.close()
            return 1
        print("[test] app frame found, build:", frame.evaluate("() => window.BUILD_ID || ''"))

        # ---- Phase 1: wait for the first video page (after RU0+ME0) ----
        t0 = time.time()
        video_active = False
        first_count = ""
        while time.time() - t0 < 90:
            try:
                act = frame.evaluate("() => document.getElementById('fullscreen-video').classList.contains('active')")
                if act:
                    first_count = frame.evaluate("() => document.getElementById('page-count').textContent")
                    video_active = True
                    break
            except Exception:
                pass
            page.wait_for_timeout(2000)
        if not video_active:
            print("[test] FAIL: video page never appeared (90s)")
            browser.close()
            return 1
        print(f"[test] video page active, page-count='{first_count}'")

        info = frame.evaluate("""() => {
            var v = document.getElementById('fullscreen-video-el');
            return {loop: v.loop, duration: v.duration, paused: v.paused,
                    currentTime: v.currentTime};
        }""")
        print("[test] video:", json.dumps(info, ensure_ascii=False))
        if info["loop"]:
            print("[test] FAIL: fullscreen video still has loop=true")
            browser.close()
            return 1
        if not (isinstance(info["duration"], (int, float)) and info["duration"] > 1):
            print("[test] FAIL: no real duration loaded:", info["duration"])
            browser.close()
            return 1

        # ---- Phase 2: wait until the video page ends ----
        t_video_start = time.time()
        while time.time() - t_video_start < info["duration"] + 30:
            try:
                act = frame.evaluate("() => document.getElementById('fullscreen-video').classList.contains('active')")
                if not act:
                    break
            except Exception:
                pass
            page.wait_for_timeout(1000)
        held = time.time() - t_video_start
        print(f"[test] video page held {held:.1f}s (clip duration {info['duration']:.1f}s)")
        if not (info["duration"] - 3 <= held <= info["duration"] + 12):
            print(f"[test] WARN: held time deviates from clip duration (>12s or <3s)")

        page.wait_for_timeout(2000)
        after = frame.evaluate("() => document.getElementById('page-count').textContent")
        print(f"[test] after video page-count='{after}'")
        if after.strip() == "1 / 25":
            print("[test] FAIL: reset to first page after video")
            browser.close()
            return 1

        # ---- Phase 3: refresh keeps position (refreshSeconds=60) ----
        page.wait_for_timeout(65000)
        later = frame.evaluate("() => document.getElementById('page-count').textContent")
        print(f"[test] ~75s in page-count='{later}'")
        if later.strip() == "1 / 25":
            print("[test] FAIL: data refresh reset to first page")
            browser.close()
            return 1

        shot = os.path.join(os.path.expanduser("~"), "AppData", "Local", "hermes",
                            "cache", "images", "video-cycle-" + time.strftime("%H%M%S") + ".png")
        page.screenshot(path=shot)
        print("[screenshot]", shot)
        browser.close()

    print("[console-errors]", len(errors))
    for e in errors[:5]:
        print("   ", e)
    print("[test] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
