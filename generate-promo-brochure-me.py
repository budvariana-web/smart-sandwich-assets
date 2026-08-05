"""Create a print-ready 4-page A4 portrait promotional booklet for Smart Sandwich Bar."""
from __future__ import annotations

import json
import os
import re
import shutil
from pathlib import Path
from collections import defaultdict

import requests
from fpdf import FPDF

ROOT = Path(r"C:/Users/Asus/AppData/Local/hermes/projects/smart-sandwich-bar")
DATA_PATH = ROOT / "menu-data.json"
OUT = ROOT / "smart-sandwich-bar-brochure-a4-mne.pdf"
CACHE = ROOT / ".brochure-image-cache"
FONT_DIR = Path(r"C:/Windows/Fonts")

NAVY = (21, 48, 70)
BLUE = (30, 136, 229)
PALE = (233, 244, 253)
MIST = (246, 250, 253)
INK = (35, 54, 68)
MUTED = (103, 123, 138)
ORANGE = (239, 137, 55)
WHITE = (255, 255, 255)


def clean_text(text: str, limit: int = 145) -> str:
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    if len(text) > limit:
        text = text[:limit].rsplit(" ", 1)[0] + "…"
    return text


def download_images(items: list[dict]) -> dict[str, Path]:
    CACHE.mkdir(exist_ok=True)
    result = {}
    for i, item in enumerate(items):
        url = item.get("imageUrl", "")
        if not url.startswith("http"):
            continue
        suffix = ".png" if ".png" in url.lower() else ".jpg"
        path = CACHE / f"{i:02d}{suffix}"
        if not path.exists():
            try:
                response = requests.get(url, timeout=20)
                response.raise_for_status()
                path.write_bytes(response.content)
            except requests.RequestException:
                continue
        result[item["name"]] = path
    return result


class Brochure(FPDF):
    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.set_auto_page_break(auto=False)
        self.add_font("Arial", "", str(FONT_DIR / "arial.ttf"))
        self.add_font("Arial", "B", str(FONT_DIR / "arialbd.ttf"))
        self.add_font("Arial", "I", str(FONT_DIR / "ariali.ttf"))

    def header_band(self, title: str, subtitle: str, page_no: int) -> None:
        self.set_fill_color(*NAVY)
        self.rect(0, 0, 210, 27, "F")
        self.set_fill_color(*BLUE)
        self.rect(0, 25.8, 210, 1.2, "F")
        self.set_font("Arial", "B", 17)
        self.set_text_color(*WHITE)
        self.set_xy(12, 6)
        self.cell(140, 7, title)
        self.set_font("Arial", "", 8)
        self.set_text_color(200, 222, 238)
        self.set_xy(12, 15)
        self.cell(145, 5, subtitle)
        self.set_font("Arial", "B", 8)
        self.set_xy(180, 11)
        self.cell(18, 6, f"{page_no} / 4", align="R")

    def footer(self) -> None:
        self.set_draw_color(205, 222, 235)
        self.line(12, 284, 198, 284)
        self.set_font("Arial", "", 7)
        self.set_text_color(*MUTED)
        self.set_xy(12, 287)
        self.cell(186, 4, "SMART SANDWICH BAR  •  Bar, Crna Gora  •  @smartsandwichbar", align="C")

    def image_box(self, path: Path | None, x: float, y: float, w: float, h: float) -> None:
        self.set_fill_color(*PALE)
        self.rect(x, y, w, h, "F")
        if path and path.exists():
            try:
                # Keep image inside box without cropping product photos.
                self.image(str(path), x=x, y=y, w=w, h=h, keep_aspect_ratio=True)
                return
            except Exception:
                pass
        self.set_font("Arial", "B", 8)
        self.set_text_color(*BLUE)
        self.set_xy(x, y + h / 2 - 2)
        self.cell(w, 4, "SMART", align="C")

    def section_title(self, title: str, x: float, y: float, note: str = "") -> float:
        self.set_font("Arial", "B", 13)
        self.set_text_color(*NAVY)
        self.set_xy(x, y)
        self.cell(115, 6, title.upper())
        self.set_draw_color(*BLUE)
        self.set_line_width(.55)
        self.line(x, y + 8, x + 186, y + 8)
        if note:
            self.set_font("Arial", "", 7.5)
            self.set_text_color(*MUTED)
            self.set_xy(x, y + 1)
            self.cell(186, 5, note, align="R")
        return y + 12

    def product_card(self, item: dict, image: Path | None, x: float, y: float, w: float = 91, h: float = 37) -> None:
        self.set_fill_color(*MIST)
        self.set_draw_color(205, 222, 235)
        self.set_line_width(.25)
        self.rect(x, y, w, h, "DF")
        self.image_box(image, x + 1.3, y + 1.3, 27, h - 2.6)
        tx = x + 31
        price = item.get("price", "")
        name = item.get("name", "")
        desc = clean_text(item.get("description", ""), 145)
        self.set_font("Arial", "B", 9.2)
        self.set_text_color(*NAVY)
        self.set_xy(tx, y + 3)
        self.multi_cell(w - 49, 4.5, name)
        self.set_font("Arial", "B", 10)
        self.set_text_color(*ORANGE)
        self.set_xy(x + w - 18, y + 3)
        self.cell(15, 5, price, align="R")
        if desc:
            self.set_font("Arial", "", 6.5)
            self.set_text_color(*MUTED)
            self.set_xy(tx, y + 14)
            self.multi_cell(w - 34, 3.15, desc)

    def compact_row(self, item: dict, image: Path | None, x: float, y: float, w: float = 186, h: float = 19) -> None:
        self.set_fill_color(*MIST)
        self.set_draw_color(205, 222, 235)
        self.rect(x, y, w, h, "DF")
        self.image_box(image, x + 1, y + 1, 17, h - 2)
        self.set_font("Arial", "B", 8.2)
        self.set_text_color(*NAVY)
        self.set_xy(x + 21, y + 3)
        self.cell(w - 45, 4.4, item["name"])
        self.set_font("Arial", "B", 9)
        self.set_text_color(*ORANGE)
        self.set_xy(x + w - 20, y + 3)
        self.cell(16, 4.4, item.get("price", ""), align="R")
        desc = clean_text(item.get("description", ""), 165)
        if desc:
            self.set_font("Arial", "", 6.3)
            self.set_text_color(*MUTED)
            self.set_xy(x + 21, y + 8.5)
            self.multi_cell(w - 27, 2.85, desc)


def main() -> None:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    # Use the Latin-script Montenegrin duplicate of the live menu.
    items = [x for x in data["items"] if not re.search(r"[А-Яа-яЁё]", x.get("category", ""))]
    images = download_images(items)
    grouped = defaultdict(list)
    for item in items:
        grouped[item["category"]].append(item)

    pdf = Brochure()

    # --- PAGE 1: COVER ---
    pdf.add_page()
    pdf.set_fill_color(*NAVY)
    pdf.rect(0, 0, 210, 297, "F")
    pdf.set_fill_color(*BLUE)
    pdf.rect(0, 0, 210, 7, "F")
    pdf.set_fill_color(45, 98, 137)
    pdf.ellipse(128, 24, 118, 118, "F")
    pdf.ellipse(-44, 202, 148, 110, "F")
    # Three product photo windows.
    cover_items = [grouped["Burgeri"][0], grouped["Sendviči"][0], grouped["Predjela"][0]]
    for item, x, y, w, h in [(cover_items[0], 113, 42, 77, 55), (cover_items[1], 22, 166, 73, 51), (cover_items[2], 111, 195, 68, 47)]:
        pdf.set_fill_color(*WHITE)
        pdf.rect(x - 2, y - 2, w + 4, h + 4, "F")
        pdf.image_box(images.get(item["name"]), x, y, w, h)
    pdf.set_font("Arial", "B", 25)
    pdf.set_text_color(*WHITE)
    pdf.set_xy(17, 38)
    pdf.multi_cell(100, 12, "SMART\nSANDWICH\nBAR")
    pdf.set_font("Arial", "B", 11)
    pdf.set_text_color(183, 221, 248)
    pdf.set_xy(18, 81)
    pdf.cell(90, 6, "burgeri • sendviči • italijanska predjela")
    pdf.set_font("Arial", "", 10)
    pdf.set_text_color(*WHITE)
    pdf.set_xy(18, 107)
    pdf.multi_cell(83, 5.2, "Svježa peciva, autorski sosovi i bogati ukusi — pripremamo u srcu Bara.")
    pdf.set_fill_color(*ORANGE)
    pdf.rect(17, 130, 72, 12, "F")
    pdf.set_font("Arial", "B", 9)
    pdf.set_text_color(*WHITE)
    pdf.set_xy(20, 133.5)
    pdf.cell(66, 4, "MENI I CIJENE • 2026", align="C")
    pdf.set_font("Arial", "", 8)
    pdf.set_text_color(183, 221, 248)
    pdf.set_xy(17, 269)
    pdf.cell(160, 5, "Bar, Crna Gora   •   @smartsandwichbar")
    pdf.set_font("Arial", "B", 7)
    pdf.set_xy(17, 278)
    pdf.cell(176, 4, "PODIJELITE OVAJ MENI SA PRIJATELJIMA — UKUS JE BOLJI ZAJEDNO", align="C")

    # --- PAGE 2: BURGERS + first sandwiches ---
    pdf.add_page()
    pdf.header_band("Burgeri i sendviči", "Domaće brioche pecivo, svježi sastojci i autorski sosovi", 2)
    y = pdf.section_title("Burgeri", 12, 35, "topli • zasitni • pripremljeni s karakterom")
    for idx, item in enumerate(grouped["Burgeri"]):
        x = 12 + (idx % 2) * 95
        if idx and idx % 2 == 0:
            y += 40
        pdf.product_card(item, images.get(item["name"]), x, y)
    y += 45
    y = pdf.section_title("Sendviči", 12, y, "na ciabatti i fokači")
    for idx, item in enumerate(grouped["Sendviči"][:3]):
        x = 12 + (idx % 2) * 95
        yy = y + (idx // 2) * 40
        pdf.product_card(item, images.get(item["name"]), x, yy)
    pdf.footer()

    # --- PAGE 3: remaining sandwiches + Italian bites ---
    pdf.add_page()
    pdf.header_band("Sendviči i italijanski ukusi", "Topli, hrskavi, s obilnim punjenjem", 3)
    y = pdf.section_title("Sendviči", 12, 35, "nastavak")
    rest = grouped["Sendviči"][3:]
    for idx, item in enumerate(rest):
        x = 12 + (idx % 2) * 95
        yy = y + (idx // 2) * 40
        pdf.product_card(item, images.get(item["name"]), x, yy)
    y += 80
    y = pdf.section_title("Bruskete i fokača", 12, y, "idealno uz kafu ili kao lagani zalogaj")
    italian = grouped["Bruskete"] + grouped["Fokača"]
    for idx, item in enumerate(italian):
        x = 12 + (idx % 2) * 95
        yy = y + (idx // 2) * 40
        pdf.product_card(item, images.get(item["name"]), x, yy)
    pdf.footer()

    # --- PAGE 4: snacks, drinks, sauces ---
    pdf.add_page()
    pdf.header_band("Predjela, slatko i dodaci", "Dodajte porudžbini ono što je čini posebnom", 4)
    y = pdf.section_title("Predjela", 12, 35, "zlatna, hrskava, za svako raspoloženje")
    for item in grouped["Predjela"]:
        pdf.compact_row(item, images.get(item["name"]), 12, y)
        y += 21
    y += 3
    y = pdf.section_title("Hljeb i dezert", 12, y)
    for item in grouped["Hljeb"] + grouped["Dezerti"]:
        pdf.compact_row(item, images.get(item["name"]), 12, y)
        y += 21
    y += 3
    y = pdf.section_title("Sosovi", 12, y, "mali dodaci — velika razlika")
    # Condiments in a concise price grid so all products fit on the back page.
    sauces = grouped["Umaci"]
    for idx, item in enumerate(sauces):
        x = 12 + (idx % 2) * 95
        pdf.set_fill_color(*PALE)
        pdf.rect(x, y, 91, 12, "F")
        pdf.set_font("Arial", "B", 8)
        pdf.set_text_color(*NAVY)
        pdf.set_xy(x + 4, y + 3.5)
        pdf.cell(60, 4, item["name"])
        pdf.set_text_color(*ORANGE)
        pdf.cell(22, 4, item["price"], align="R")
        if idx % 2:
            y += 14
    y += 4
    pdf.set_fill_color(*NAVY)
    pdf.rect(12, 257, 186, 18, "F")
    pdf.set_font("Arial", "B", 10)
    pdf.set_text_color(*WHITE)
    pdf.set_xy(18, 261)
    pdf.cell(174, 5, "NARUČITE SVOJE OMILJENE UKUSE U SMART SANDWICH BARU", align="C")
    pdf.set_font("Arial", "", 7.5)
    pdf.set_text_color(183, 221, 248)
    pdf.set_xy(18, 267)
    pdf.cell(174, 4, "Burgeri • sendviči • predjela • kafa", align="C")
    pdf.footer()

    pdf.set_title("Smart Sandwich Bar — promotivna brošura")
    pdf.set_author("Smart Sandwich Bar")
    pdf.output(str(OUT))
    print(f"PDF saved: {OUT}")
    print(f"pages={pdf.pages_count}; bytes={OUT.stat().st_size}; source_items={len(items)}")


if __name__ == "__main__":
    main()
