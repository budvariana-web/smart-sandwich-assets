#!/usr/bin/env python3
"""Sync i-food.me menu into Google Sheet MENU tab (Smart Sandwich Bar TV board)."""
import json, time, base64, urllib.parse, urllib.request

SHEET_ID = '1i4Oz_e_dDuOzIYhOvM-QmEcmCQTpf3qG4SM0U7_Qw-A'
SA_PATH = '.credentials/service-account.json'
IMG_BASE = 'https://api.i-food.me/files/assets/img/ImagesPages/products/'

# ---------- 1. SA token ----------
with open(SA_PATH) as f:
    sa = json.load(f)

now = int(time.time())
def b64url(d): return base64.urlsafe_b64encode(d).rstrip(b'=').decode()
header = {'alg': 'RS256', 'typ': 'JWT'}
payload = {
    'iss': sa['client_email'],
    'scope': 'https://www.googleapis.com/auth/spreadsheets',
    'aud': 'https://oauth2.googleapis.com/token',
    'iat': now, 'exp': now + 3600,
}
signing_input = b64url(json.dumps(header).encode()) + '.' + b64url(json.dumps(payload).encode())
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
key = serialization.load_pem_private_key(sa['private_key'].encode(), password=None)
sig = key.sign(signing_input.encode(), padding.PKCS1v15(), hashes.SHA256())
jwt = signing_input + '.' + b64url(sig)
req = urllib.request.Request('https://oauth2.googleapis.com/token',
    data=urllib.parse.urlencode({'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer', 'assertion': jwt}).encode())
access = json.loads(urllib.request.urlopen(req).read())['access_token']

def sheets(path, method='GET', body=None):
    url = f'https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/{path}'
    data = json.dumps(body).encode() if body else None
    r = urllib.request.Request(url, data=data, method=method,
        headers={'Authorization': f'Bearer {access}', 'Content-Type': 'application/json'})
    try:
        resp = urllib.request.urlopen(r)
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print(f'ERROR {method} {path}: {e.code} {e.read().decode()[:400]}')
        raise

# ---------- 2. Build rows ----------
data = json.load(open('ifood-full-menu.json', encoding='utf-8'))
fm = data['food_maker_menu']
texts = data['menu_lang_texts']

CAT_RU = {
    'Smart_Sandwich_Bar__Burgers': 'Бургеры',
    'Smart_Sandwich_Bar__Sandwiches': 'Сэндвичи',
    'Smart_Sandwich_Bar__Bruschetta': 'Брускеты',
    'Smart_Sandwich_Bar__Focaccia': 'Фокачча',
    'Smart_Sandwich_Bar__Appetizers': 'Закуски',
    'Smart_Sandwich_Bar__Bread': 'Хлеб',
    'Smart_Sandwich_Bar__Desserts': 'Десерты',
    'Smart_Sandwich_Bar__Sauces': 'Соусы',
}

# Manual clean names (i-food ru names are noisy)
CLEAN_NAMES = {
    'Smart_Sandwich_Bar__Black_Beef_Burger': 'МАЧО БУРГЕР',
    'Smart_Sandwich_Bar__Pink_Chicken_Burger': 'БЕЛЛА БУРГЕР',
    'Smart_Sandwich_Bar__Burger_Combo_Burger_Fries_Sauce': 'Сет МАЧО БУРГЕР: бургер, фри, соус',
    'Smart_Sandwich_Bar__kombo_bella_burger': 'Сет «Белла Бургер»: бургер, фри, соус',
    'Smart_Sandwich_Bar__Neapolitano_Sandwich': 'Сэндвич «Неаполитано»',
    'Smart_Sandwich_Bar__Roasted_Pork_Sandwich_Ukrainian_Vibe': 'Сэндвич «Украинский вайб»',
    'Smart_Sandwich_Bar__Mortadella_Sandwich': 'Сэндвич «Неаполитано Плюс»',
    'Smart_Sandwich_Bar__Prosciutto_Sandwich': 'Сэндвич «Монтенегро Лав»',
    'Smart_Sandwich_Bar__Catalan_Chicken_Sandwich': 'Сэндвич с курицей по-каталонски',
    'Smart_Sandwich_Bar__Salami_Sandwich': 'Сэндвич с салями',
    'Smart_Sandwich_Bar__Bruschetta_with_Caramelized_Onion_and_Prosciutto': 'Брускетта с карамелизированным луком и пршутом',
    'Smart_Sandwich_Bar__Bruschetta_with_Cherry_Tomatoes_Olives_and_Salami': 'Брускета с черри, маслинами и салями',
    'Smart_Sandwich_Bar__Focaccia_with_Olives_and_Cheese': 'Фокачча с маслинами и сыром',
    'Smart_Sandwich_Bar__Arancini': 'Аранчини',
    'Smart_Sandwich_Bar__Garlic_Rye_Croutons': 'Чесночные гренки из ржаного хлеба',
    'Smart_Sandwich_Bar__Garlic_Croutons_Set_3_Sauces': 'Сет: гренки + 3 соуса',
    'Smart_Sandwich_Bar__French_Fries': 'Картофель фри',
    'Smart_Sandwich_Bar__Ciabatta': 'Чиабатта',
    'Smart_Sandwich_Bar__Orange_Cake': 'Апельсиновый кекс «Таормина»',
    'Smart_Sandwich_Bar__Caramelized_Onion': 'Карамелизированный лук',
    'Smart_Sandwich_Bar__Aioli': 'Айоли',
    'Smart_Sandwich_Bar__Marinade_Sauce': 'Маринада',
    'Smart_Sandwich_Bar__BBQ_Sauce': 'Соус BBQ',
    'Smart_Sandwich_Bar__Spicy_Ketchup': 'Острый кетчуп',
    'Smart_Sandwich_Bar__ketchup': 'Кетчуп',
}

def clean_desc(key):
    # Manual descriptions for noisy items
    MANUAL_DESC = {
        'Smart_Sandwich_Bar__Black_Beef_Burger': 'Чёрная булочка бриош (выпекаем сами), авторский соус с лёгкой остринкой, говяжья котлета (только мясо и специи), сыр Чеддер, карамелизированный лук, свежий помидор, листья салата.',
        'Smart_Sandwich_Bar__Burger_Combo_Burger_Fries_Sauce': 'Чёрный МАЧО бургер с говядиной, картофель фри с копчёной паприкой и соус на выбор: кетчуп, кетчуп с чили или айоли с французской горчицей (хенд мейд).',
        # Drafts added 2026-08-02 for items with no i-food description
        'Smart_Sandwich_Bar__Salami_Sandwich': 'Чиабатта (выпекаем сами), итальянская салями, свежий помидор, листья салата и соус на выбор. Разогревается в пресс-гриле до хрустящей корочки.',
        'Smart_Sandwich_Bar__Bruschetta_with_Caramelized_Onion_and_Prosciutto': 'Хрустящий поджаренный хлеб, карамелизированный лук и нежный пршут.',
        'Smart_Sandwich_Bar__Bruschetta_with_Cherry_Tomatoes_Olives_and_Salami': 'Хрустящий поджаренный хлеб с томатами черри, маслинами и салями.',
        'Smart_Sandwich_Bar__Focaccia_with_Olives_and_Cheese': 'Домашняя фокачча (выпекаем сами) с маслинами и сыром. Целая фокачча — как закуска или основа для сэндвича.',
        'Smart_Sandwich_Bar__French_Fries': 'Золотистый картофель фри (150 г). Подаётся с соусом на выбор: кетчуп, кетчуп с чили или айоли.',
        'Smart_Sandwich_Bar__Caramelized_Onion': 'Сладкий томлёный лук — идеальная добавка к бургерам, гренкам и сэндвичам.',
        'Smart_Sandwich_Bar__Aioli': 'Домашний соус айоли (хенд мейд) с французской горчицей — к бургерам, фри и гренкам.',
        'Smart_Sandwich_Bar__Spicy_Ketchup': 'Кетчуп с чили — пикантная острота для бургеров, фри и гренок.',
        'Smart_Sandwich_Bar__ketchup': 'Классический кетчуп — к бургерам, фри и гренкам.',
    }
    if key in MANUAL_DESC:
        return MANUAL_DESC[key]
    raw = texts.get(key + '__description', {}).get('ru', '')
    if not raw:
        return ''
    # remove promo lines about yellow bun today
    raw = raw.replace('<br>', ' ').replace('<br/>', ' ').replace('<br />', ' ')
    for phrase in ['ТОЛЬКО СЕГОДНЯ', 'только сегодня', 'Только СЕГОДНЯ', 'ВКУС НЕ МЕНЯЕТСЯ', 'вкус не меняется']:
        idx = raw.find(phrase)
        if idx != -1:
            end = raw.find('.', idx)
            raw = (raw[:idx] + raw[end+1:]) if end != -1 else raw[:idx]
    raw = raw.replace(' ,', ',').replace(',,', ',').replace('  ', ' ')
    raw = ' '.join(raw.split()).strip()
    raw = raw.strip(' ,.').strip()
    return raw[:220]

rows = []
skip = {'Smart_Sandwich_Bar__sandwich_test'}  # test item, no price/photo
order = 10

# i-food items sorted by display_order
items_sorted = sorted(
    [(k, v) for k, v in fm.items() if v.get('is_active') and not v.get('is_deleted') and k not in skip],
    key=lambda kv: kv[1].get('display_order', 0)
)
for key, item in items_sorted:
    cat_code = item.get('category_code', '')
    category = CAT_RU.get(cat_code, cat_code.replace('Smart_Sandwich_Bar__', ''))
    name = CLEAN_NAMES.get(key) or texts.get(key, {}).get('ru', key).split(' – ')[0].split(' — ')[0].strip()
    price_val = item.get('no_version_price') or item.get('version_price')
    price = f'{price_val:.2f} €'.replace('.', ',') if price_val else ''
    desc = clean_desc(key)
    img = item.get('image', '')
    photo = IMG_BASE + urllib.parse.quote(img) if img else ''
    rows.append([category, name, desc, price, '', 'Да', order, photo, ''])
    order += 10

# Drinks (not on i-food, keep from current sheet)
drinks = [
    ['Напитки', 'Лимонад', 'Домашний, 0.4 л', '2,80 €', '', 'Да', order, 'asset:lemonade', ''],
    ['Напитки', 'Американо', 'Классический чёрный кофе', '2,00 €', '', 'Да', order + 10, 'asset:americano', ''],
]
rows.extend(drinks)

print(f'Total rows: {len(rows)}')
for r in rows:
    print(f'  {r[0]:10} | {r[1][:45]:45} | {r[3]:8} | {r[7][:50]}')

# ---------- 3. Write to sheet ----------
# Preserve header row 1, replace rows 2..N
n = len(rows)
range_a = f'MENU!A2:F{n+1}'
range_h = f'MENU!H2:I{n+1}'
# A-F then H-I (skip G 'Порядок'? No — G holds order values, plain numbers, write A-I directly)
range_all = f'MENU!A2:I{n+1}'
values = [r[:9] for r in rows]  # A..I (9 cols)
sheets(f'values/{range_all}?valueInputOption=RAW', method='PUT',
       body={'range': range_all, 'majorDimension': 'ROWS', 'values': values})
print(f'\nWritten {n} rows to {range_all}')

# ---------- 4. Verify ----------
check = sheets(f'values/MENU!A1:I{n+2}?valueRenderOption=FORMATTED_VALUE')
print(f'\nVerify: {len(check.get("values", []))} rows read back')
for r in check.get('values', [])[:5]:
    print(' ', r[:6])
