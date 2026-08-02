#!/usr/bin/env python3
"""Sync i-food.me menu into Google Sheet MENU tab (Smart Sandwich Bar TV board).

Column model (MENU):
  A Категория | B Название | C Описание i-food | D Цена | E Старая цена
  F В наличии | G Порядок  | H Фото            | I Бейдж | J Описание наше

- C ('Описание i-food') is OWNED by this script: rewritten from the i-food API
  (menu_lang_texts '<item>__description') on every run. Empty if API has none.
- J ('Описание наше') is USER-OWNED: this script never overwrites a non-empty
  value. It reads existing J from the sheet and preserves it. Only fills J with
  defaults for drinks that are not on i-food at all.
- Effective description (what the TV board shows) is computed by Code.gs:
  J (ours) wins if non-empty, otherwise C (i-food).
"""
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

# Default 'ours' descriptions for drinks (not on i-food); user can edit in sheet
DRINK_DESC = {
    'Лимонад': 'Домашний, 0.4 л',
    'Американо': 'Классический чёрный кофе',
}

def clean_desc(key):
    """i-food description (column C) — cleaned from menu_lang_texts only.
    No manual overrides here: those live in column J ('Описание наше')."""
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

# ---------- 2b. Read current sheet (preserve column J - 'ours' descriptions) ----------
existing_j = {}
existing_k = {}
try:
    cur = sheets('values/MENU!A2:K60?valueRenderOption=FORMATTED_VALUE')
    for row in cur.get('values', []):
        if len(row) >= 2:
            existing_j[row[1].strip()] = (row[9] if len(row) > 9 else '').strip()
            # K: checkbox -> TRUE/FALSE string, empty -> default TRUE
            k = (row[10] if len(row) > 10 else '').strip()
            existing_k[row[1].strip()] = k.lower() if k in ('true', 'false') else 'true'
    print(f'Read {len(existing_j)} existing sheet rows (preserve J, K)')
except Exception as e:
    print(f'WARN: could not read existing J/K ({e})')

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
    desc_c = clean_desc(key)                      # C: i-food description (owned)
    desc_j = existing_j.get(name, '')             # J: preserve user's 'ours'
    img = item.get('image', '')
    photo = IMG_BASE + urllib.parse.quote(img) if img else ''
    visible = existing_k.get(name, 'true')  # K: preserve checkbox, default TRUE
    rows.append([category, name, desc_c, price, '', 'Да', order, photo, '', desc_j, visible])
    order += 10

# Drinks (not on i-food): C empty, J = existing or default
drinks = [
    ['Напитки', 'Лимонад', '', '2,80 €', '', 'Да', order, 'asset:lemonade', '', existing_j.get('Лимонад') or DRINK_DESC['Лимонад'], existing_k.get('Лимонад', 'true')],
    ['Напитки', 'Американо', '', '2,00 €', '', 'Да', order + 10, 'asset:americano', '', existing_j.get('Американо') or DRINK_DESC['Американо'], existing_k.get('Американо', 'true')],
]
rows.extend(drinks)

print(f'Total rows: {len(rows)}')
for r in rows:
    print(f'  {r[0]:10} | {r[1][:45]:45} | C={r[2][:25]:25} | {r[3]:8} | J={r[9][:25]:25} | K={r[10]}')

# ---------- 3. Write to sheet (A..K) ----------
n = len(rows)
range_all = f'MENU!A2:K{n+1}'
values = [r[:11] for r in rows]  # A..K (11 cols)
sheets(f'values/{range_all}?valueInputOption=RAW', method='PUT',
       body={'range': range_all, 'majorDimension': 'ROWS', 'values': values})
print(f'\nWritten {n} rows to {range_all}')

# ---------- 4. Verify ----------
check = sheets(f'values/MENU!A1:K{n+2}?valueRenderOption=FORMATTED_VALUE')
print(f'\nVerify: {len(check.get("values", []))} rows read back')
for r in check.get('values', [])[:6]:
    print(' ', r[:11])
