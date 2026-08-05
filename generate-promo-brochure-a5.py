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
        self.set_font("Arial","B",6.5); self.set_xy(127,7); self.cell(13,4,"%d / 8"%page,align="R")
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
    def card(self,it,img,y,h=39):
        x=8; w=132; self.set_fill_color(*MIST); self.set_draw_color(205,222,235); self.rect(x,y,w,h,"DF")
        self.image_box(img,x+1.2,y+1.2,31,h-2.4)
        tx=x+35; name=it['name']; desc=short(it.get('description',''),138)
        fs=8.3 if len(name)<38 else 7.4; dy=y+(14 if len(name)<38 else 19)
        self.set_font("Arial","B",fs); self.set_text_color(*INK); self.set_xy(tx,y+3); self.multi_cell(73,4,name)
        self.set_font("Arial","B",8.6); self.set_text_color(*ORANGE); self.set_xy(x+w-19,y+3); self.cell(15,4,it['price'],align="R")
        if desc:
            self.set_font("Arial","",5.6); self.set_text_color(*MUTED); self.set_xy(tx,dy); self.multi_cell(92,2.75,desc)

def menu_pages(pdf, items, imgs, title, note, page, cards):
    pdf.add_page(); pdf.top(title,note,page); y=pdf.heading(title,note)
    for it in items:
        pdf.card(it,imgs.get(it['name']),y); y+=42
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
    # 2 burgers, 3-4 sandwiches
    menu_pages(pdf,g['Бургеры'],imgs,'Бургеры','горячие • сытные • приготовлены с характером',2,4)
    menu_pages(pdf,g['Сэндвичи'][:3],imgs,'Сэндвичи','на чиабатте и фокачче',3,3)
    menu_pages(pdf,g['Сэндвичи'][3:],imgs,'Сэндвичи','тёплые, хрустящие, с щедрой начинкой',4,3)
    # 5 Italian bites
    menu_pages(pdf,g['Брускеты']+g['Фокачча'],imgs,'Брускеты и фокачча','идеально к кофе или как лёгкая закуска',5,3)
    # 6 starters
    menu_pages(pdf,g['Закуски'],imgs,'Закуски','золотистые, хрустящие, к любому настроению',6,4)
    # 7 compact extras
    pdf.add_page();pdf.top('Хлеб, десерт и соусы','маленькие дополнения — большая разница',7); y=pdf.heading('Хлеб и десерт','')
    for it in g['Хлеб']+g['Десерты']:
        pdf.card(it,imgs.get(it['name']),y,35);y+=38
    y+=2;pdf.set_font('Arial','B',9);pdf.set_text_color(*NAVY);pdf.set_xy(8,y);pdf.cell(55,4,'СОУСЫ')
    y+=7
    for i,it in enumerate(g['Соусы']):
        x=8+(i%2)*67; yy=y+(i//2)*15;pdf.set_fill_color(*PALE);pdf.rect(x,yy,63,12,'F');pdf.set_font('Arial','B',6.7);pdf.set_text_color(*INK);pdf.set_xy(x+3,yy+3);pdf.cell(42,3,it['name']);pdf.set_text_color(*ORANGE);pdf.cell(15,3,it['price'],align='R')
    pdf.foot()
    # 8 back cover
    pdf.add_page();pdf.set_fill_color(*NAVY);pdf.rect(0,0,148,210,'F');pdf.set_fill_color(*BLUE);pdf.rect(0,0,148,5,'F')
    pdf.image_box(imgs.get(g['Бургеры'][1]['name']),20,24,108,74)
    pdf.set_font('Arial','B',13);pdf.set_text_color(*WHITE);pdf.set_xy(12,118);pdf.multi_cell(124,6,'ЗАКАЗЫВАЙТЕ ЛЮБИМЫЕ ВКУСЫ\nВ SMART SANDWICH BAR')
    pdf.set_font('Arial','',7);pdf.set_text_color(185,222,247);pdf.set_xy(12,137);pdf.multi_cell(122,4,'Бургеры • сэндвичи • брускеты • закуски\nГотовим с вниманием к каждому вкусу.')
    pdf.set_draw_color(*ORANGE);pdf.set_line_width(.8);pdf.line(12,160,136,160);pdf.set_font('Arial','B',7);pdf.set_text_color(*WHITE);pdf.set_xy(12,166);pdf.cell(124,4,'Bar, Crna Gora  •  @smartsandwichbar',align='C')
    pdf.set_title('Smart Sandwich Bar — брошюра A5');pdf.set_author('Smart Sandwich Bar');pdf.output(str(OUT));print(f'Saved {OUT}; pages={pdf.pages_count}; items={len(items)}; bytes={OUT.stat().st_size}')
if __name__=='__main__':main()
