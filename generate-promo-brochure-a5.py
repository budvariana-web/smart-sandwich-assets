"""Reflow the Russian Smart Sandwich Bar menu into a print-friendly 8-page A5 booklet."""
from __future__ import annotations
import json, os, re
from pathlib import Path
from collections import defaultdict
import requests
from fpdf import FPDF

ROOT = Path(r"C:/Users/Asus/AppData/Local/hermes/projects/smart-sandwich-bar")
OUT = ROOT / "smart-sandwich-bar-brochure-a5.pdf"
CACHE = ROOT / ".brochure-image-cache"
FONT = Path(r"C:/Windows/Fonts")
NAVY=(21,48,70); BLUE=(30,136,229); PALE=(233,244,253); MIST=(247,251,254); INK=(35,54,68); MUTED=(103,123,138); ORANGE=(239,137,55); WHITE=(255,255,255)


def short(txt, limit=135):
    txt = re.sub(r"\s+", " ", str(txt or "")).strip()
    return txt if len(txt)<=limit else txt[:limit].rsplit(" ",1)[0]+"…"

def get_images(items):
    CACHE.mkdir(exist_ok=True); out={}
    for i,it in enumerate(items):
        url=it.get("imageUrl","")
        if not url.startswith("http"): continue
        ext=".png" if ".png" in url.lower() else ".jpg"; p=CACHE/f"a5-{i:02d}{ext}"
        try:
            if not p.exists():
                r=requests.get(url,timeout=20); r.raise_for_status(); p.write_bytes(r.content)
            out[it['name']]=p
        except requests.RequestException: pass
    return out

class A5(FPDF):
    def __init__(self):
        super().__init__(orientation="P",unit="mm",format="A5")
        self.set_auto_page_break(False)
        self.add_font("Arial","",str(FONT/"arial.ttf")); self.add_font("Arial","B",str(FONT/"arialbd.ttf")); self.add_font("Arial","I",str(FONT/"ariali.ttf"))
    def top(self,title,sub,page):
        self.set_fill_color(*NAVY); self.rect(0,0,148,18,"F"); self.set_fill_color(*BLUE); self.rect(0,17.2,148,.8,"F")
        self.set_font("Arial","B",10.5); self.set_text_color(*WHITE); self.set_xy(8,4); self.cell(100,4.7,title)
        self.set_font("Arial","",5.9); self.set_text_color(195,222,240); self.set_xy(8,10); self.cell(110,3.5,sub)
        self.set_font("Arial","B",6.5); self.set_xy(127,7); self.cell(13,4,"%d / 14"%page,align="R")
    def foot(self):
        self.set_draw_color(205,222,235); self.line(8,199,140,199)
        self.set_font("Arial","",5.2); self.set_text_color(*MUTED); self.set_xy(8,201); self.cell(132,3,"SMART SANDWICH BAR  •  Bar, Crna Gora  •  @smartsandwichbar",align="C")
    def image_box(self,p,x,y,w,h):
        self.set_fill_color(*PALE); self.rect(x,y,w,h,"F")
        if p and p.exists():
            try: self.image(str(p),x=x,y=y,w=w,h=h,keep_aspect_ratio=True); return
            except Exception: pass
        self.set_font("Arial","B",5); self.set_text_color(*BLUE); self.set_xy(x,y+h/2-1.5); self.cell(w,3,"SMART",align="C")
    def heading(self,title,note,y=25):
        self.set_font("Arial","B",10); self.set_text_color(*NAVY); self.set_xy(8,y); self.cell(75,4.5,title.upper())
        self.set_font("Arial","",5.8); self.set_text_color(*MUTED); self.set_xy(8,y+5); self.cell(132,3,note,align="R")
        self.set_draw_color(*BLUE); self.line(8,y+9,140,y+9); return y+12
    def card(self,it,img,y,h=70):
        x=8; w=132; self.set_fill_color(*MIST); self.set_draw_color(205,222,235); self.rect(x,y,w,h,"DF")
        image_w = 48 if h >= 60 else 35
        self.image_box(img,x+1.5,y+1.5,image_w,h-3)
        tx=x+image_w+4; name=it['name']; desc=short(it.get('description',''),190)
        large = h >= 60
        long_title = len(name) > 27
        fs=(10.5 if not long_title else 9.0) if large else (8.8 if not long_title else 7.7)
        dy=y+(18 if not long_title else 29) if large else y+(15 if not long_title else 22)
        self.set_font("Arial","B",fs); self.set_text_color(*INK); self.set_xy(tx,y+4); self.multi_cell(57 if large else 56,5.1 if large else 4.3,name)
        self.set_font("Arial","B",10.2 if large else 8.8); self.set_text_color(*ORANGE); self.set_xy(x+w-22,y+4); self.cell(18,5,it['price'],align="R")
        if desc:
            self.set_font("Arial","",7.2 if large else 6.2); self.set_text_color(*MUTED); self.set_xy(tx,dy); self.multi_cell(78 if large else 90,3.6 if large else 3.0,desc)

def menu_pages(pdf, items, imgs, title, note, page, cards):
    pdf.add_page(); pdf.top(title,note,page); y=pdf.heading(title,note)
    h = 70 if len(items) <= 2 else 48
    gap = 4
    for it in items:
        pdf.card(it,imgs.get(it['name']),y,h); y+=h+gap
    pdf.foot()

def main():
    raw=json.loads((ROOT/"menu-data.json").read_text(encoding="utf-8"))['items']
    items=[x for x in raw if re.search(r"[А-Яа-яЁё]",x.get('category',''))]
    g=defaultdict(list)
    for x in items:g[x['category']].append(x)
    imgs=get_images(items); pdf=A5()
    # 1 cover
    pdf.add_page(); pdf.set_fill_color(*NAVY); pdf.rect(0,0,148,210,"F"); pdf.set_fill_color(*BLUE); pdf.rect(0,0,148,5,"F"); pdf.set_fill_color(46,97,137); pdf.ellipse(79,12,92,92,"F"); pdf.ellipse(-55,148,110,91,"F")
    hero=[g['Бургеры'][0],g['Сэндвичи'][0],g['Закуски'][0]]
    for it,x,y,w,h in [(hero[0],79,32,55,38),(hero[1],14,122,55,37),(hero[2],78,154,50,34)]:
        pdf.set_fill_color(*WHITE);pdf.rect(x-1.5,y-1.5,w+3,h+3,"F");pdf.image_box(imgs.get(it['name']),x,y,w,h)
    pdf.set_font('Arial','B',18);pdf.set_text_color(*WHITE);pdf.set_xy(12,29);pdf.multi_cell(65,9,'SMART\nSANDWICH\nBAR')
    pdf.set_font('Arial','B',7.5);pdf.set_text_color(185,222,247);pdf.set_xy(12,61);pdf.cell(64,4,'бургеры • сэндвичи • закуски')
    pdf.set_font('Arial','',7.2);pdf.set_text_color(*WHITE);pdf.set_xy(12,78);pdf.multi_cell(57,4,'Свежая выпечка, авторские соусы и яркие вкусы — в самом сердце Бара.')
    pdf.set_fill_color(*ORANGE);pdf.rect(12,97,52,9,'F');pdf.set_font('Arial','B',6.5);pdf.set_xy(14,100);pdf.cell(48,3,'МЕНЮ И ЦЕНЫ • 2026',align='C')
    pdf.set_font('Arial','',6);pdf.set_text_color(185,222,247);pdf.set_xy(12,196);pdf.cell(120,3,'Bar, Crna Gora   •   @smartsandwichbar')
    # Exactly two menu items per A5 page for comfortable print readability.
    menu_pages(pdf,g['Бургеры'][:2],imgs,'Бургеры','горячие • сытные • приготовлены с характером',2,2)
    menu_pages(pdf,g['Бургеры'][2:],imgs,'Бургеры','горячие • сытные • приготовлены с характером',3,2)
    menu_pages(pdf,g['Сэндвичи'][:2],imgs,'Сэндвичи','на чиабатте и фокачче',4,2)
    menu_pages(pdf,g['Сэндвичи'][2:4],imgs,'Сэндвичи','на чиабатте и фокачче',5,2)
    menu_pages(pdf,g['Сэндвичи'][4:],imgs,'Сэндвичи','на чиабатте и фокачче',6,2)
    italian=g['Брускеты']+g['Фокачча']
    menu_pages(pdf,italian[:2],imgs,'Брускеты и фокачча','идеально к кофе или как лёгкая закуска',7,2)
    menu_pages(pdf,italian[2:],imgs,'Брускеты и фокачча','идеально к кофе или как лёгкая закуска',8,1)
    menu_pages(pdf,g['Закуски'][:2],imgs,'Закуски','золотистые, хрустящие, к любому настроению',9,2)
    menu_pages(pdf,g['Закуски'][2:],imgs,'Закуски','золотистые, хрустящие, к любому настроению',10,2)
    menu_pages(pdf,g['Хлеб']+g['Десерты'],imgs,'Хлеб и десерт','небольшое дополнение к вашему заказу',11,2)
    menu_pages(pdf,g['Соусы'][:2],imgs,'Соусы','маленькие дополнения — большая разница',12,2)
    menu_pages(pdf,g['Соусы'][2:],imgs,'Соусы','маленькие дополнения — большая разница',13,2)
    # 14 back cover
    pdf.add_page();pdf.set_fill_color(*NAVY);pdf.rect(0,0,148,210,'F');pdf.set_fill_color(*BLUE);pdf.rect(0,0,148,5,'F')
    pdf.image_box(imgs.get(g['Бургеры'][1]['name']),20,24,108,74)
    pdf.set_font('Arial','B',13);pdf.set_text_color(*WHITE);pdf.set_xy(12,118);pdf.multi_cell(124,6,'ЗАКАЗЫВАЙТЕ ЛЮБИМЫЕ ВКУСЫ\nВ SMART SANDWICH BAR')
    pdf.set_font('Arial','',7);pdf.set_text_color(185,222,247);pdf.set_xy(12,137);pdf.multi_cell(122,4,'Бургеры • сэндвичи • брускеты • закуски\nГотовим с вниманием к каждому вкусу.')
    pdf.set_draw_color(*ORANGE);pdf.set_line_width(.8);pdf.line(12,160,136,160);pdf.set_font('Arial','B',7);pdf.set_text_color(*WHITE);pdf.set_xy(12,166);pdf.cell(124,4,'Bar, Crna Gora  •  @smartsandwichbar',align='C')
    pdf.set_title('Smart Sandwich Bar — брошюра A5');pdf.set_author('Smart Sandwich Bar');pdf.output(str(OUT));print(f'Saved {OUT}; pages={pdf.pages_count}; items={len(items)}; bytes={OUT.stat().st_size}')
if __name__=='__main__':main()
