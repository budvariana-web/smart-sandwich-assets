"""Best-fit two-page A5 Russian booklet: retains every item, full description, price and photo."""
from __future__ import annotations
import json,re
from collections import defaultdict
from pathlib import Path
import requests
from fpdf import FPDF
ROOT=Path(r"C:/Users/Asus/AppData/Local/hermes/projects/smart-sandwich-bar")
OUT=ROOT/'smart-sandwich-bar-brochure-a5-full-2-pages.pdf'; CACHE=ROOT/'.brochure-image-cache'; FONT=Path(r'C:/Windows/Fonts')
NAVY=(21,48,70); BLUE=(30,136,229); PALE=(239,248,254); INK=(35,54,68); MUTED=(91,113,130); ORANGE=(239,137,55); WHITE=(255,255,255)

def images(items):
    CACHE.mkdir(exist_ok=True); result={}
    for n,it in enumerate(items):
        url=it.get('imageUrl','')
        if not url.startswith('http'):continue
        p=CACHE/f'full2-{n:02d}.jpg'
        try:
            if not p.exists():
                r=requests.get(url,timeout=20);r.raise_for_status();p.write_bytes(r.content)
            result[it['name']]=p
        except requests.RequestException:pass
    return result
class PDF(FPDF):
    def __init__(self):
        super().__init__('P','mm','A5');self.set_auto_page_break(False)
        self.add_font('Arial','',str(FONT/'arial.ttf'));self.add_font('Arial','B',str(FONT/'arialbd.ttf'))
    def band(self,num,caption):
        self.set_fill_color(*NAVY);self.rect(0,0,148,22,'F');self.set_fill_color(*BLUE);self.rect(0,21.2,148,.8,'F')
        self.set_font('Arial','B',10.8);self.set_text_color(*WHITE);self.set_xy(7,4);self.cell(102,4.5,'SMART SANDWICH BAR')
        self.set_font('Arial','',5.5);self.set_text_color(187,222,246);self.set_xy(7,11);self.cell(110,3,caption)
        self.set_font('Arial','B',6.5);self.set_xy(128,8);self.cell(12,3,f'{num}/2',align='R')
    def footer(self):
        self.set_font('Arial','',4.5);self.set_text_color(*MUTED);self.set_xy(7,203);self.cell(134,2.5,'Bar, Crna Gora   •   @smartsandwichbar   •   Цены указаны в евро',align='C')
    def section(self,x,y,w,title):
        self.set_font('Arial','B',6.8);self.set_text_color(*NAVY);self.set_xy(x,y);self.cell(w,3,title.upper())
        self.set_draw_color(*BLUE);self.line(x,y+4.8,x+w,y+4.8)
        return y+7
    def picture(self,p,x,y,w,h):
        self.set_fill_color(211,233,248);self.rect(x,y,w,h,'F')
        if p and p.exists():
            try:self.image(str(p),x=x,y=y,w=w,h=h,keep_aspect_ratio=True)
            except Exception:pass
    def item(self,it,p,x,y,w,h):
        self.set_fill_color(*PALE);self.set_draw_color(207,226,238);self.rect(x,y,w,h,'DF');self.set_fill_color(*ORANGE);self.rect(x,y,1.4,h,'F')
        # A narrower photo rail maximizes readable type while retaining a photo for every item.
        self.picture(p,x+2,y+2,12,h-4)
        tx=x+16;tw=w-18;name=it['name'];desc=re.sub(r'\s+',' ',it.get('description','')).strip()
        # Fixed price rail and adaptive text scale: retain full source description inside the card.
        self.set_font('Arial','B',7.4 if len(name)<31 else 6.3);self.set_text_color(*INK);self.set_xy(tx,y+2);self.multi_cell(tw-13,3.05,name,align='L')
        self.set_font('Arial','B',7.7);self.set_text_color(*ORANGE);self.set_xy(x+w-12,y+2);self.cell(10,3,it['price'],align='R')
        desc_font=5.5 if len(desc)<180 else 5.0
        self.set_font('Arial','',desc_font);self.set_text_color(*MUTED);self.set_xy(tx,y+9.4 if len(name)<31 else y+12.6);self.multi_cell(tw,2.45 if desc_font>5.2 else 2.25,desc,align='L')

def draw_col(pdf,items,img,x,y,title):
    y=pdf.section(x,y,64,title)
    for it in items:
        pdf.item(it,img.get(it['name']),x,y,64,25);y+=26.5

def main():
    raw=json.loads((ROOT/'menu-data.json').read_text(encoding='utf-8'))['items']; items=[i for i in raw if re.search(r'[А-Яа-яЁё]',i.get('category',''))]
    g=defaultdict(list)
    for i in items:g[i['category']].append(i)
    img=images(items);pdf=PDF()
    # Balance 11 / 12 items across pages, six rows maximum in a column.
    p1left=g['Бургеры']+g['Сэндвичи'][:2];p1right=g['Сэндвичи'][2:]+g['Брускеты']
    p2left=g['Фокачча']+g['Закуски'];p2right=g['Хлеб']+g['Десерты']+g['Соусы']
    pdf.add_page();pdf.band(1,'бургеры и сэндвичи — полное меню')
    draw_col(pdf,p1left,img,7,27,'Бургеры и сэндвичи');draw_col(pdf,p1right,img,77,27,'Сэндвичи и брускеты');pdf.footer()
    pdf.add_page();pdf.band(2,'брускеты, закуски и дополнения — полное меню')
    draw_col(pdf,p2left,img,7,27,'Брускеты и закуски');draw_col(pdf,p2right,img,77,27,'Дополнения и соусы');pdf.footer()
    pdf.set_title('Smart Sandwich Bar — полная брошюра A5, 2 страницы');pdf.set_author('Smart Sandwich Bar');pdf.output(str(OUT));print(f'Saved {OUT}; pages={pdf.pages_count}; items={len(items)}; bytes={OUT.stat().st_size}')
if __name__=='__main__':main()
