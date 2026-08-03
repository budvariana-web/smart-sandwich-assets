"""Rebuild the static GH Pages copy (assets/menu/index.html) from the GAS Index.html.

Transforms:
  1. <html lang="<?= lang ?>">              -> <html lang="ru">
  2. window.MENU_LANG = '<?= lang ?>'       -> URL ?lang= param parser (default 'both')
  3. var BUILD_ID = '%%BUILD_ID%%'          -> 'gh-pages-YYYYMMDD-HHMMSS'
"""
import re, time
from pathlib import Path

SRC = Path(__file__).parent / "delivery" / "smart-sandwich-menu-display" / "Index.html"
DST = Path(__file__).parent / "assets" / "menu" / "index.html"

html = SRC.read_text(encoding="utf-8")
ts = time.strftime("%Y%m%d-%H%M%S")

html = html.replace('<html lang="<?= lang ?>">', '<html lang="ru">')
html = html.replace(
    "window.MENU_LANG = '<?= lang ?>';",
    "window.MENU_LANG = (function(){var m=(location.search.match(/[?&]lang=([a-z-]+)/)||[])[1];"
    "return (m==='ru'||m==='me'||m==='both')?m:'both';})();",
)
html, n = re.subn(r"var BUILD_ID\s*=\s*'[^']*';", f"var BUILD_ID  = 'gh-pages-{ts}';", html)
assert n == 1, f"BUILD_ID replace count = {n}"

DST.write_text(html, encoding="utf-8")
print(f"static copy -> {DST}  (build gh-pages-{ts})")
