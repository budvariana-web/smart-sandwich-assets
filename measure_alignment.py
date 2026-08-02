"""Measure card alignment geometry on the live menu board.

Reports:
  - menu cards bottom vs right-zone announcement bottoms (footer gap)
  - category top positions across cards (should be identical)
  - price-row bottom positions vs card bottom (should be identical offset)

Usage: python measure_alignment.py [--url URL]
"""
import json
import sys
import time

BASE_DIR = r"C:\Users\Asus\AppData\Local\hermes\projects\smart-sandwich-bar"
WRAPPER_URL = "https://budvariana-web.github.io/smart-sandwich-assets/menu.html"
DIRECT_URL = ("https://script.google.com/macros/s/"
              "AKfycbxlyDvP-_TbVVXGXG7_rxKdXvowJxPu8gn8BXpLKuGnfsCmpHL71CXIWSVUbbamwY4skg/exec")

JS = """() => {
  var rect = function(el) {
    if (!el) return null;
    var r = el.getBoundingClientRect();
    return {top: Math.round(r.top), bottom: Math.round(r.bottom), h: Math.round(r.height)};
  };
  var cards = Array.from(document.querySelectorAll('.card'));
  var cardData = cards.map(function(c) {
    var cat = c.querySelector('.card-category');
    var price = c.querySelector('.card-price-row');
    var img = c.querySelector('.card-img, .card-no-img');
    return {
      name: (c.querySelector('.card-name') || {}).textContent || '',
      cardTop: rect(c).top, cardBottom: rect(c).bottom, cardH: rect(c).h,
      imgBottom: rect(img) ? rect(img).bottom : null,
      catTop: rect(cat) ? rect(cat).top : null,
      catBottom: rect(cat) ? rect(cat).bottom : null,
      priceBottom: rect(price) ? rect(price).bottom : null
    };
  });
  var menuRect = rect(document.querySelector('#menu'));
  var footerRect = rect(document.querySelector('footer'));
  var zoneRect = rect(document.querySelector('#video-zone'));
  var annTop = rect(document.querySelector('#ann-top'));
  var annBottom = rect(document.querySelector('#ann-bottom'));
  var videoSlot = rect(document.querySelector('#video-slot'));
  return {
    viewport: {w: window.innerWidth, h: window.innerHeight},
    menuRect: menuRect, footerRect: footerRect, zoneRect: zoneRect,
    annTop: annTop, annBottom: annBottom, videoSlot: videoSlot,
    cardCount: cards.length,
    cards: cardData,
    diffs: {
      menuBottom_vs_annBottom: menuRect && annBottom ? annBottom.bottom - menuRect.bottom : null,
      menuBottom_vs_zoneBottom: menuRect && zoneRect ? zoneRect.bottom - menuRect.bottom : null,
      annBottomOffset: annBottom ? (annBottom.bottom - (zoneRect ? zoneRect.bottom : 0)) : null
    }
  };
}"""


def main():
    url = WRAPPER_URL
    if "--url" in sys.argv:
        url = sys.argv[sys.argv.index("--url") + 1]

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        ctx = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = ctx.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
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
            print("APP FRAME NOT FOUND")
            return

        # wait for cards
        for _ in range(15):
            try:
                if frame.evaluate("() => document.querySelectorAll('.card').length > 0"):
                    break
            except Exception:
                pass
            page.wait_for_timeout(2000)

        data = frame.evaluate(JS)
        print(json.dumps(data, ensure_ascii=False, indent=1))
        browser.close()


if __name__ == "__main__":
    main()
