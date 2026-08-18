"""Generate A4 PDF menu for Smart Sandwich Bar — 2 columns, 1 page."""
import json, os, requests, tempfile
from pathlib import Path
from fpdf import FPDF

ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS = ROOT / 'artifacts' / 'brochures'
ARTIFACTS.mkdir(parents=True, exist_ok=True)

WHITE = (255, 255, 255)
LIGHT_BLUE = (220, 235, 245)
ACCENT_BLUE = (100, 160, 200)
DARK_BLUE = (40, 70, 100)
SOFT_GRAY = (120, 130, 140)
WARM_BROWN = (80, 60, 50)

with open(ROOT / "menu-data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

items = data["items"]
categories = {}
for item in items:
    cat = item.get("category", "Другое")
    categories.setdefault(cat, []).append(item)


class MenuPDF(FPDF):
    def __init__(self):
        super().__init__(orientation='P', unit='mm', format='A4')
        fd = "C:/Windows/Fonts/"
        self.add_font("Arial", "", fd + "arial.ttf")
        self.add_font("Arial", "B", fd + "arialbd.ttf")
        self.add_font("Arial", "I", fd + "ariali.ttf")

    def draw_cat_mascot(self, x, y, s=1.0):
        """Sketch cat reaching for a burger."""
        self.set_draw_color(*WARM_BROWN)
        self.set_line_width(0.4*s)
        self.set_fill_color(255, 248, 240)
        # Body
        self.ellipse(x - 12*s, y - 5*s, 24*s, 18*s, 'DF')
        # Head
        self.ellipse(x - 8*s, y - 16*s, 16*s, 14*s, 'DF')
        # Ears
        self.set_fill_color(255, 248, 240)
        self.polygon([(x-7*s,y-15*s),(x-5*s,y-24*s),(x-1*s,y-15*s)], 'DF')
        self.polygon([(x+1*s,y-15*s),(x+5*s,y-24*s),(x+7*s,y-15*s)], 'DF')
        self.set_fill_color(255, 200, 200)
        self.polygon([(x-5.5*s,y-15.5*s),(x-4.5*s,y-21*s),(x-2*s,y-15.5*s)], 'F')
        self.polygon([(x+2*s,y-15.5*s),(x+4.5*s,y-21*s),(x+5.5*s,y-15.5*s)], 'F')
        # Eyes
        self.set_fill_color(60, 60, 60)
        self.ellipse(x-4*s, y-12*s, 2.5*s, 2.5*s, 'F')
        self.ellipse(x+1.5*s, y-12*s, 2.5*s, 2.5*s, 'F')
        self.set_fill_color(255, 255, 255)
        self.ellipse(x-3.2*s, y-12.5*s, 0.8*s, 0.8*s, 'F')
        self.ellipse(x+2.3*s, y-12.5*s, 0.8*s, 0.8*s, 'F')
        # Nose
        self.set_fill_color(255, 150, 150)
        self.polygon([(x,y-9*s),(x-1.2*s,y-7.5*s),(x+1.2*s,y-7.5*s)], 'DF')
        # Mouth + whiskers
        self.set_line_width(0.3*s)
        self.line(x, y-7.5*s, x-2*s, y-6*s)
        self.line(x, y-7.5*s, x+2*s, y-6*s)
        self.set_line_width(0.2*s)
        for dy in [-1, 0, 1]:
            self.line(x-5*s, y-8*s+dy*1.5*s, x-12*s, y-9*s+dy*2*s)
            self.line(x+5*s, y-8*s+dy*1.5*s, x+12*s, y-9*s+dy*2*s)
        # Arm reaching up
        self.set_line_width(0.5*s)
        self.line(x+10*s, y-2*s, x+18*s, y-12*s)
        self.ellipse(x+17*s, y-14*s, 4*s, 3*s, 'DF')
        # Tail
        self.line(x-12*s, y+3*s, x-16*s, y)
        self.line(x-16*s, y, x-20*s, y-5*s)
        self.line(x-20*s, y-5*s, x-21*s, y-9*s)
        # Burger
        bx, by = x+22*s, y-16*s
        self.set_fill_color(210, 160, 80)
        self.ellipse(bx-3*s, by-2*s, 6*s, 3*s, 'DF')
        self.set_fill_color(80, 140, 60)
        self.ellipse(bx-3.5*s, by+0.5*s, 7*s, 1.5*s, 'DF')
        self.set_fill_color(180, 80, 60)
        self.ellipse(bx-3*s, by+1.5*s, 6*s, 1.5*s, 'DF')
        self.set_fill_color(220, 180, 100)
        self.ellipse(bx-3*s, by+2.8*s, 6*s, 2*s, 'DF')
        self.set_fill_color(255, 250, 230)
        self.ellipse(bx-1*s, by-1.5*s, 0.8*s, 0.5*s, 'F')
        self.ellipse(bx+1*s, by-1*s, 0.8*s, 0.5*s, 'F')

    def draw_cat_small(self, x, y, s=0.5, variant=0):
        self.set_draw_color(*WARM_BROWN)
        self.set_line_width(0.3*s)
        self.set_fill_color(255, 248, 240)
        self.ellipse(x-8*s, y-3*s, 16*s, 12*s, 'DF')
        self.ellipse(x-6*s, y-12*s, 12*s, 10*s, 'DF')
        self.polygon([(x-5*s,y-11*s),(x-3*s,y-18*s),(x-1*s,y-11*s)], 'DF')
        self.polygon([(x+1*s,y-11*s),(x+3*s,y-18*s),(x+5*s,y-11*s)], 'DF')
        self.set_fill_color(255, 200, 200)
        self.polygon([(x-4*s,y-11.5*s),(x-3*s,y-16*s),(x-2*s,y-11.5*s)], 'F')
        self.polygon([(x+2*s,y-11.5*s),(x+3*s,y-16*s),(x+4*s,y-11.5*s)], 'F')
        self.set_fill_color(60, 60, 60)
        if variant == 1:
            self.set_line_width(0.4*s)
            self.arc(x-3*s, y-10*s, 2*s, 2*s, 200, 340)
            self.arc(x+1*s, y-10*s, 2*s, 2*s, 200, 340)
        else:
            self.ellipse(x-3*s, y-9*s, 2*s, 2*s, 'F')
            if variant == 0:
                self.ellipse(x+1*s, y-9*s, 2*s, 2*s, 'F')
            else:
                self.set_line_width(0.4*s)
                self.arc(x+1*s, y-10*s, 2*s, 2*s, 200, 340)
        if variant != 1:
            self.set_fill_color(255, 255, 255)
            self.ellipse(x-2.3*s, y-9.5*s, 0.6*s, 0.6*s, 'F')
        self.set_fill_color(255, 150, 150)
        self.polygon([(x,y-7*s),(x-0.8*s,y-5.8*s),(x+0.8*s,y-5.8*s)], 'DF')
        self.set_line_width(0.25*s)
        self.line(x, y-5.8*s, x-1.5*s, y-4.5*s)
        self.line(x, y-5.8*s, x+1.5*s, y-4.5*s)
        self.set_line_width(0.4*s)
        self.line(x+8*s, y+1*s, x+13*s, y-4*s)
        self.line(x+13*s, y-4*s, x+14*s, y-7*s)

    def draw_paw(self, x, y, size=2.5):
        self.set_fill_color(*ACCENT_BLUE)
        self.ellipse(x-size*0.5, y-size*0.3, size, size*0.8, 'F')
        for dx in [-size*0.4, 0, size*0.4]:
            self.ellipse(x+dx-size*0.18, y-size*0.8, size*0.35, size*0.35, 'F')


pdf = MenuPDF()
pdf.set_auto_page_break(auto=False)
pdf.add_page()

# --- HEADER ---
pdf.set_fill_color(*LIGHT_BLUE)
pdf.rect(0, 0, 210, 32, 'F')
pdf.set_draw_color(*ACCENT_BLUE)
pdf.set_line_width(0.8)
pdf.line(10, 32, 200, 32)
pdf.set_font("Arial", "B", 20)
pdf.set_text_color(*DARK_BLUE)
pdf.set_xy(10, 5)
pdf.cell(130, 10, "SMART SANDWICH BAR")
pdf.set_font("Arial", "I", 9)
pdf.set_text_color(*SOFT_GRAY)
pdf.set_xy(10, 16)
pdf.cell(130, 7, "Меню  •  Bar, Crna Gora")

# Mascot top-right
pdf.draw_cat_mascot(175, 42, s=0.9)

# Paw prints
pdf.draw_paw(15, 7, 2)
pdf.draw_paw(192, 7, 2)

# --- Download images ---
tmpdir = tempfile.mkdtemp()
img_files = {}
for item in items:
    url = item.get("imageUrl", "")
    if url.startswith("http"):
        fname = url.split("/")[-1]
        fpath = os.path.join(tmpdir, fname)
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                with open(fpath, "wb") as f:
                    f.write(r.content)
                img_files[item["name"]] = fpath
        except:
            pass

# --- 2-COLUMN LAYOUT ---
col_w = 90
col_gap = 10
col_x = [10, 10 + col_w + col_gap]
col_y = [36, 36]
row_h = 30  # height per item card

cat_colors = {
    "Сэндвичи": ACCENT_BLUE,
    "Бургеры": (180, 100, 50),
    "Закуски": (120, 160, 80),
    "Напитки": (100, 150, 180),
}

col = 0  # which column we're writing in

for cat_name, cat_items in categories.items():
    # Category header in current column
    cx = col_x[col]
    cy = col_y[col]

    if cy > 250:
        col += 1
        if col >= 2:
            break  # won't fit
        cx = col_x[col]
        cy = col_y[col]

    # Category bar
    cc = cat_colors.get(cat_name, ACCENT_BLUE)
    pdf.set_fill_color(*cc)
    pdf.rect(cx, cy, col_w, 7, 'F')
    pdf.set_font("Arial", "B", 9)
    pdf.set_text_color(255, 255, 255)
    pdf.set_xy(cx + 2, cy + 1)
    pdf.cell(col_w - 4, 5, cat_name.upper())
    pdf.draw_paw(cx + col_w - 8, cy + 3.5, 1.8)
    col_y[col] += 10

    for item in cat_items:
        cy = col_y[col]
        if cy > 268:
            col += 1
            if col >= 2:
                break
            cx = col_x[col]
            cy = col_y[col]

        name = item.get("name", "")
        price = item.get("price", "")
        desc = item.get("description", "")
        badge = item.get("badge", "")
        img_path = img_files.get(name)

        # Card background
        pdf.set_fill_color(248, 252, 255)
        pdf.set_draw_color(210, 225, 240)
        pdf.set_line_width(0.25)
        pdf.rect(cx, cy, col_w, row_h, 'DF')

        # Photo (left side)
        if img_path and os.path.exists(img_path):
            try:
                pdf.image(img_path, x=cx+1.5, y=cy+1.5, w=16, h=row_h-3)
            except:
                pdf.set_fill_color(*LIGHT_BLUE)
                pdf.ellipse(cx+1.5, cy+5, 16, 16, 'F')
        else:
            pdf.set_fill_color(*LIGHT_BLUE)
            pdf.ellipse(cx+1.5, cy+5, 16, 16, 'F')

        tx = cx + 20  # text start x

        # Badge
        if badge:
            pdf.set_fill_color(*cc)
            pdf.set_font("Arial", "B", 5.5)
            pdf.set_text_color(255, 255, 255)
            bw = pdf.get_string_width(badge) + 4
            pdf.set_xy(tx, cy + 2)
            pdf.cell(bw, 4, badge, align="C", fill=True)
            nx = tx + bw + 2
        else:
            nx = tx

        # Name
        pdf.set_font("Arial", "B", 8.5)
        pdf.set_text_color(*DARK_BLUE)
        pdf.set_xy(nx, cy + 2)
        pdf.cell(col_w - nx + cx - 22, 5, name)

        # Price (right aligned)
        pdf.set_font("Arial", "B", 10)
        pdf.set_text_color(*ACCENT_BLUE)
        pdf.set_xy(cx + col_w - 30, cy + 2)
        pdf.cell(28, 5, price, align="R")

        # Description
        if desc:
            pdf.set_font("Arial", "", 6.5)
            pdf.set_text_color(*SOFT_GRAY)
            pdf.set_xy(tx, cy + 8)
            pdf.multi_cell(col_w - 24, 3.2, desc)

        col_y[col] += row_h + 2

    col_y[col] += 3

# --- DECORATIVE CATS on empty space ---
if col_y[0] < 200:
    pdf.draw_cat_small(55, col_y[0] + 10, 0.5, 0)
if col_y[1] < 200:
    pdf.draw_cat_small(145, col_y[1] + 10, 0.5, 1)

# --- FOOTER ---
pdf.set_y(-12)
pdf.set_font("Arial", "", 6.5)
pdf.set_text_color(*SOFT_GRAY)
pdf.cell(0, 8, "smart-sandwich-bar.me  •  @smartsandwichbar", align="C")
# Paw trail footer
for i in range(10):
    pdf.draw_paw(20 + i * 17, 289, 1.2)

output = ARTIFACTS / "smart-sandwich-menu.pdf"
pdf.output(str(output))
print(f"PDF saved: {output}  ({pdf.pages_count} page)")
