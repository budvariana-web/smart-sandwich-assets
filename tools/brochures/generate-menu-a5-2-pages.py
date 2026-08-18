"""Two-page A5 Russian menu: all current products and prices, no small descriptions."""
from __future__ import annotations
import json, re
from collections import defaultdict
from pathlib import Path
from fpdf import FPDF

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'artifacts' / 'brochures' / 'smart-sandwich-bar-menu-a5-2-pages.pdf'
FONT = Path(r"C:/Windows/Fonts")
NAVY=(21,48,70); BLUE=(30,136,229); PALE=(234,245,253); INK=(35,54,68); MUTED=(104,124,139); ORANGE=(239,137,55); WHITE=(255,255,255)

class MenuA5(FPDF):
    def __init__(self):
        super().__init__(orientation='P',unit='mm',format='A5');self.set_auto_page_break(False)
        self.add_font('Arial','',str(FONT/'arial.ttf'));self.add_font('Arial','B',str(FONT/'arialbd.ttf'))
    def banner(self, page, kicker):
        self.set_fill_color(*NAVY);self.rect(0,0,148,29,'F');self.set_fill_color(*BLUE);self.rect(0,28,148,1,'F')
        self.set_font('Arial','B',14);self.set_text_color(*WHITE);self.set_xy(8,6);self.cell(104,6,'SMART SANDWICH BAR')
        self.set_font('Arial','',6.7);self.set_text_color(188,222,245);self.set_xy(8,15);self.cell(112,3,kicker)
        self.set_font('Arial','B',7);self.set_xy(126,10);self.cell(14,4,f'{page} / 2',align='R')
    def footer(self):
        self.set_draw_color(200,222,237);self.line(8,199,140,199)
        self.set_font('Arial','',5.5);self.set_text_color(*MUTED);self.set_xy(8,201);self.cell(132,3,'Bar, Crna Gora   •   @smartsandwichbar   •   МЕНЮ И ЦЕНЫ',align='C')
    def section(self, x,y,w,title,caption):
        self.set_font('Arial','B',9.5);self.set_text_color(*NAVY);self.set_xy(x,y);self.cell(w,4,title.upper())
        self.set_font('Arial','',5.6);self.set_text_color(*MUTED);self.set_xy(x,y+5);self.cell(w,3,caption)
        self.set_draw_color(*BLUE);self.line(x,y+10,x+w,y+10)
        return y+14
    def item(self,x,y,w,h,item):
        self.set_fill_color(*PALE);self.set_draw_color(215,231,241);self.rect(x,y,w,h,'DF')
        self.set_fill_color(*ORANGE);self.rect(x,y,2,h,'F')
        name=item['name']; fs=9.2 if len(name)<32 else 8.2
        self.set_font('Arial','B',fs);self.set_text_color(*INK);self.set_xy(x+4,y+3);self.multi_cell(w-22,4.05,name,align='L')
        self.set_font('Arial','B',9.8);self.set_text_color(*ORANGE);self.set_xy(x+w-18,y+3);self.cell(14,4,item['price'],align='R')

def place(pdf, x, y, w, its, base_h):
    for it in its:
        h=base_h + (4 if len(it['name'])>38 else 0)
        pdf.item(x,y,w,h,it);y+=h+3

def main():
    raw=json.loads((ROOT/'menu-data.json').read_text(encoding='utf-8'))['items']
    its=[x for x in raw if re.search(r'[А-Яа-яЁё]',x.get('category',''))]
    g=defaultdict(list)
    for x in its:g[x['category']].append(x)
    pdf=MenuA5()
    # Page 1: Burgers and Sandwiches
    pdf.add_page();pdf.banner(1,'бургеры • сэндвичи • свежее приготовление')
    left,right=8,76;col=64
    y1=pdf.section(left,38,col,'Бургеры','горячие и сытные')
    place(pdf,left,y1,col,g['Бургеры'],25)
    y2=pdf.section(right,38,col,'Сэндвичи','на чиабатте и фокачче')
    place(pdf,right,y2,col,g['Сэндвичи'],19)
    pdf.footer()
    # Page 2: remaining menu
    pdf.add_page();pdf.banner(2,'брускеты • закуски • дополнения')
    y1=pdf.section(left,38,col,'Брускеты и закуски','к кофе или как лёгкий перекус')
    place(pdf,left,y1,col,g['Брускеты']+g['Фокачча']+g['Закуски'],17)
    y2=pdf.section(right,38,col,'Дополнения','хлеб, десерт и соусы')
    place(pdf,right,y2,col,g['Хлеб']+g['Десерты']+g['Соусы'],19)
    pdf.footer();pdf.set_title('Smart Sandwich Bar — меню A5, 2 страницы');pdf.set_author('Smart Sandwich Bar');pdf.output(str(OUT))
    print(f'Saved {OUT}; pages={pdf.pages_count}; items={len(its)}; bytes={OUT.stat().st_size}')
if __name__=='__main__':main()
