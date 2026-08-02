#!/usr/bin/env python3
"""One-time migration: split MENU description column into two.

- C (was 'Описание') -> renamed 'Описание i-food'   (sync-owned, from API)
- J (new)             -> 'Описание наше'             (user-owned, manual)

Rule applied per row:
  api = cleaned description from i-food for this item ('' if none)
  if api and C == api          -> keep C=api, J=''
  if api and C and C != api    -> manual override: J=C, C=api
  if api and not C             -> C=api, J=''
  if not api and C             -> manual/draft/drink: J=C, C=''
  if not api and not C         -> J='', C=''

Run: python migrate_desc_columns.py
"""
import json
import time
import base64
import urllib.parse
import urllib.request

SHEET_ID = '1i4Oz_e_dDuOzIYhOvM-QmEcmCQTpf3qG4SM0U7_Qw-A'
SA_PATH = r'C:\Users\Asus\AppData\Local\hermes\projects\smart-sandwich-bar\.credentials\service-account.json'
API_JSON = r'C:\Users\Asus\AppData\Local\hermes\projects\smart-sandwich-bar\ifood-full-menu.json'

# Same mapping as sync_ifood_to_sheet.py (name -> key), built below
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
NAME_TO_KEY = {v: k for k, v in CLEAN_NAMES.items()}

# ---------- load API data ----------
data = json.load(open(API_JSON, encoding='utf-8'))
fm = data['food_maker_menu']
texts = data['menu_lang_texts']


def clean_desc(key):
    """Copy of clean_desc from sync_ifood_to_sheet.py (API side only)."""
    raw = texts.get(key + '__description', {}).get('ru', '')
    if not raw:
        return ''
    raw = raw.replace('<br>', ' ').replace('<br/>', ' ').replace('<br />', ' ')
    for phrase in ['ТОЛЬКО СЕГОДНЯ', 'только сегодня', 'Только СЕГОДНЯ', 'ВКУС НЕ МЕНЯЕТСЯ', 'вкус не меняется']:
        idx = raw.find(phrase)
        if idx != -1:
            end = raw.find('.', idx)
            raw = (raw[:idx] + raw[end + 1:]) if end != -1 else raw[:idx]
    raw = raw.replace(' ,', ',').replace(',,', ',').replace('  ', ' ')
    raw = ' '.join(raw.split()).strip()
    raw = raw.strip(' ,.').strip()
    return raw[:220]


# ---------- SA JWT ----------
with open(SA_PATH) as f:
    sa = json.load(f)
now = int(time.time())


def b64url(d):
    return base64.urlsafe_b64encode(d).rstrip(b'=').decode()


header = {'alg': 'RS256', 'typ': 'JWT'}
payload = {'iss': sa['client_email'], 'scope': 'https://www.googleapis.com/auth/spreadsheets',
           'aud': 'https://oauth2.googleapis.com/token', 'iat': now, 'exp': now + 3600}
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
        print(f'ERROR {method} {path}: {e.code} {e.read().decode()[:300]}')
        raise


# ---------- read current sheet ----------
check = sheets('values/MENU!A1:J60?valueRenderOption=FORMATTED_VALUE')
rows = check.get('values', [])
print(f'Read {len(rows)} rows')

new_c = []   # (rowIndex, value) 1-based sheet row
new_j = []
plan = []

for i, row in enumerate(rows):
    rn = i + 1  # sheet row number
    if rn == 1:
        continue  # header handled separately
    name = (row[1] if len(row) > 1 else '').strip()
    cur_c = (row[2] if len(row) > 2 else '').strip()
    cur_j = (row[9] if len(row) > 9 else '').strip()
    if not name:
        continue
    key = NAME_TO_KEY.get(name)
    api = clean_desc(key) if key else ''
    if api and cur_c == api:
        # API description, unchanged -> keep in C, J empty
        plan.append((rn, name, 'API', cur_c[:40], ''))
        new_j.append((rn, cur_j))  # preserve whatever J already had
    elif api and cur_c:
        # manual override of an API item -> move to J, C gets fresh API text
        plan.append((rn, name, 'MOVE->J', cur_c[:40], api[:40]))
        new_c.append((rn, api))
        new_j.append((rn, cur_c))
    elif api:
        # C empty, API has text -> fill C
        plan.append((rn, name, 'API-FILL', '', api[:40]))
        new_c.append((rn, api))
        new_j.append((rn, cur_j))
    elif cur_c:
        # no API text -> manual/draft/drink -> J
        plan.append((rn, name, 'MANUAL->J', cur_c[:40], ''))
        new_j.append((rn, cur_c))
    else:
        plan.append((rn, name, 'EMPTY', '', ''))
        new_j.append((rn, cur_j))

print(f'\n{"row":>3} {"name":<44} {"action":<10} C(now) / J(->)')
for rn, name, action, cval, apival in plan:
    print(f'{rn:>3} {name[:44]:<44} {action:<10} {cval[:36]} | {apival[:36]}')

# ---------- write ----------
body = {'valueInputOption': 'RAW', 'data': [
    {'range': 'MENU!C1', 'majorDimension': 'ROWS', 'values': [['Описание i-food']]},
    {'range': 'MENU!J1', 'majorDimension': 'ROWS', 'values': [['Описание наше']]},
]}
if new_c:
    ranges = ['C' + str(r) for r, _ in new_c]
    body['data'].extend([{'range': f'MENU!C{r}', 'majorDimension': 'ROWS', 'values': [[v]]} for r, v in new_c])
if new_j:
    body['data'].extend([{'range': f'MENU!J{r}', 'majorDimension': 'ROWS', 'values': [[v]]} for r, v in new_j])
resp = sheets('values:batchUpdate', method='POST', body=body)
print(f'\nUpdated {len(resp.get("valueInputs", []))} cells')

# ---------- verify ----------
check2 = sheets('values/MENU!A1:K60?valueRenderOption=FORMATTED_VALUE')
print('\nVerify (after migration):')
for row in check2.get('values', []):
    name = (row[1] if len(row) > 1 else '').strip()
    if not name:
        continue
    c = (row[2] if len(row) > 2 else '').strip()
    j = (row[9] if len(row) > 9 else '').strip()
    eff = j or c
    src = 'OURS' if j else ('IFOOD' if c else 'NONE')
    print(f'  {name[:42]:<44} [{src:<5}] eff={eff[:50]}')
