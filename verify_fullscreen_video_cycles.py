import json
from playwright.sync_api import sync_playwright

errors = []
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1920, "height": 1080})
    page.on("console", lambda m: errors.append(f"{m.type}: {m.text}") if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
    page.goto("http://127.0.0.1:8766/assets/menu/index.html?lang=both", wait_until="networkidle", timeout=30000)
    page.wait_for_function("() => window.state && state.data && state.pages && state.pages.length", timeout=30000)

    def probe(label):
        return page.evaluate("""label => {
          const videos = state.pages.filter(p => p ? p.video : false).map(p => p.video);
          const types = state.pages.map(p => p ? (p.video ? 'V' : 'M') : 'M');
          const adjacent = types.some((t, i) => i > 0 && t === 'V' && types[i - 1] === 'V');
          return {label, total: types.length, menu: types.filter(t => t === 'M').length,
                  videos: videos.length, adjacent, vids: videos.map(x => x.split('/').pop())};
        }""", label)

    first = probe("cycle1")
    page.evaluate("() => { state.page = state.pages.length - 1; state._lastAdvance = 0; advancePage(); }")
    second = probe("cycle2")
    page.evaluate("() => { state.page = state.pages.length - 1; state._lastAdvance = 0; advancePage(); }")
    third = probe("cycle3")
    all_videos = first["vids"] + second["vids"] + third["vids"]
    overlap = sorted(set(first["vids"]).intersection(second["vids"]))
    result = {"cycles": [first, second, third], "overlap12": overlap,
              "allFirstPassUnique": len(set(all_videos)), "consoleErrors": errors}
    print(json.dumps(result, ensure_ascii=False))
    assert all(not item["adjacent"] for item in (first, second, third))
    assert (first["videos"], second["videos"], third["videos"]) == (8, 8, 1)
    assert not overlap
    assert len(set(all_videos)) == 17
    assert not errors
    browser.close()
