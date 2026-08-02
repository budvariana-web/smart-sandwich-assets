"""Verify ALL menu items' names and descriptions fully fit inside cards.

Walks every page (3 cards each), measures:
  - desc: clientHeight vs natural height (line-clamp cut?) and vs available space
  - name: does it overflow the info zone?
  - card-info: any content overflow (clipped at card bottom)?

Usage: python measure_fit.py
"""
import json
import time

from playwright.sync_api import sync_playwright

WRAPPER_URL = "https://budvariana-web.github.io/smart-sandwich-assets/menu.html"
LAST_BUILD = r"C:\Users\Asus\AppData\Local\hermes\projects\smart-sandwich-bar\last-build.txt"

# Per-card measurement, runs in the app iframe
PER_CARD_JS = """(c) => {
  var info = c.querySelector('.card-info');
  var name = info.querySelector('.card-name');
  var desc = info.querySelector('.card-desc');
  var priceRow = info.querySelector('.card-price-row');
  var cat = info.querySelector('.card-category');

  var infoH = info.clientHeight;
  var infoScroll = info.scrollHeight;

  // Natural (unclamped) description height via hidden clone
  var naturalH = 0;
  if (desc) {
    var clone = desc.cloneNode(true);
    clone.style.position = 'absolute';
    clone.style.visibility = 'hidden';
    clone.style.display = 'block';
    clone.style.webkitLineClamp = 'none';
    clone.style.height = 'auto';
    clone.style.flex = 'none';
    clone.style.overflow = 'visible';
    clone.style.width = desc.getBoundingClientRect().width + 'px';
    document.body.appendChild(clone);
    naturalH = Math.round(clone.getBoundingClientRect().height);
    document.body.removeChild(clone);
  }

  var descClipped = desc ? (desc.scrollHeight - desc.clientHeight) : 0;

  // Available vertical room for desc = info height minus fixed elements (cat, name, price, gaps, padding)
  var infoStyle = getComputedStyle(info);
  var padTop = parseFloat(infoStyle.paddingTop), padBot = parseFloat(infoStyle.paddingBottom);
  var gap = parseFloat(infoStyle.gap) || 0;
  var fixed = padTop + padBot + gap * 3;
  if (cat) fixed += cat.getBoundingClientRect().height;
  if (priceRow) fixed += priceRow.getBoundingClientRect().height;
  var nameH = name ? name.getBoundingClientRect().height : 0;
  fixed += nameH;
  var roomForDesc = infoH - fixed;

  return {
    name: (name || {}).textContent || '',
    nameLines: name ? Math.round(nameH / (parseFloat(getComputedStyle(name).lineHeight) || 1)) : 0,
    nameH: Math.round(nameH),
    descLen: desc ? (desc.textContent || '').length : 0,
    descClientH: desc ? desc.clientHeight : 0,
    descNaturalH: naturalH,
    descClipped: descClipped,
    roomForDesc: Math.round(roomForDesc),
    descFitsNatural: roomForDesc >= naturalH - 1,
    infoOverflow: infoScroll - infoH,
    catH: cat ? Math.round(cat.getBoundingClientRect().height) : 0,
    priceH: priceRow ? Math.round(priceRow.getBoundingClientRect().height) : 0
  };
}"""


def main():
    with open(LAST_BUILD) as f:
        expected = f.read().strip()

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
            return

        # BUILD_ID guard (proxy stale pitfall)
        for attempt in range(4):
            actual = frame.evaluate("() => window.BUILD_ID || ''")
            if actual == expected:
                print("[fit] BUILD_ID fresh: " + actual)
                break
            print("[fit] stale " + repr(actual) + ", reloading")
            page.reload(wait_until="domcontentloaded")
            page.wait_for_timeout(8000)
            for _ in range(6):
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

        # wait for data-driven cards
        for _ in range(15):
            try:
                if frame.evaluate("() => document.querySelectorAll('.card').length > 0"):
                    break
            except Exception:
                pass
            page.wait_for_timeout(2000)

        n_pages = frame.evaluate("() => (window.state.pages || []).length")
        print("[fit] pages: " + str(n_pages))

        problems = []
        for pi in range(n_pages):
            frame.evaluate("() => { window.state.page = " + str(pi) + "; window.renderPage(); }")
            page.wait_for_timeout(1200)
            data = frame.evaluate(
                "() => Array.from(document.querySelectorAll('.card')).map(" + PER_CARD_JS + ")")
            for c in data:
                flag = []
                if c["descClipped"] > 1:
                    flag.append("DESC-CLIPPED(%.0fpx)" % c["descClipped"])
                if not c["descFitsNatural"]:
                    flag.append("DESC-NO-ROOM(need %d, have %d)" % (c["descNaturalH"], c["roomForDesc"]))
                if c["infoOverflow"] > 1:
                    flag.append("INFO-OVERFLOW(%dpx)" % c["infoOverflow"])
                if c["nameLines"] > 3:
                    flag.append("NAME-%dLINES" % c["nameLines"])
                status = "OK " if not flag else "!!!"
                line = "  p%d [%s] %-46s name %dL desc %dch nat %dpx room %dpx" % (
                    pi, status, c["name"][:44], c["nameLines"], c["descLen"],
                    c["descNaturalH"], c["roomForDesc"])
                if flag:
                    line += " | " + ", ".join(flag)
                print(line)
                if flag:
                    problems.append({"page": pi, "name": c["name"], "flags": flag})

        print("\n[fit] problems: " + str(len(problems)))
        for p_ in problems:
            print("  ", p_)
        browser.close()


if __name__ == "__main__":
    main()
