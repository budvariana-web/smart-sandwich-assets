#!/usr/bin/env python3
"""Fill empty descriptions in the MENU sheet for items that have none.

Data source of truth = Google Sheet (the TV board reads from there).
This only touches the 'Описание' column (C) for rows whose description is
empty; everything else is preserved.

Drafts written here are marked in the sheet and can be edited by the user.
"""
import json
import time
import base64
import urllib.parse
import urllib.request

SHEET_ID = '1i4Oz_e_dDuOzIYhOvM-QmEcmCQTpf3qG4SM0U7_Qw-A'
SA_PATH = r'C:\Users\Asus\AppData\Local\hermes\projects\smart-sandwich-bar\.credentials\service-account.json'

# Draft descriptions for items that have none (editable in the sheet)
NEW_DESCRIPTIONS = {
    'Сэндвич с салями': 'Чиабатта (выпекаем сами), итальянская салями, свежий помидор, листья салата и соус на выбор. Разогревается в пресс-гриле до хрустящей корочки.',
    'Брускетта с карамелизированным луком и пршутом': 'Хрустящий поджаренный хлеб, карамелизированный лук и нежный пршут.',
    'Брускета с черри, маслинами и салями': 'Хрустящий поджаренный хлеб с томатами черри, маслинами и салями.',
    'Фокачча с маслинами и сыром': 'Домашняя фокачча (выпекаем сами) с маслинами и сыром. Целая фокачча — как закуска или основа для сэндвича.',
    'Картофель фри': 'Золотистый картофель фри (150 г). Подаётся с соусом на выбор: кетчуп, кетчуп с чили или айоли.',
    'Карамелизированный лук': 'Сладкий томлёный лук — идеальная добавка к бургерам, гренкам и сэндвичам.',
    'Айоли': 'Домашний соус айоли (хенд мейд) с французской горчицей — к бургерам, фри и гренкам.',
    'Острый кетчуп': 'Кетчуп с чили — пикантная острота для бургеров, фри и гренок.',
    'Кетчуп': 'Классический кетчуп — к бургерам, фри и гренкам.',
}

# ---------- SA JWT ----------
with open(SA_PATH) as f:
    sa = json.load(f)

now = int(time.time())


def b64url(d):
    return base64.urlsafe_b64encode(d).rstrip(b'=').decode()


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
    data=urllib.parse.urlencode({'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
                                 'assertion': jwt}).encode())
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


# ---------- Read MENU ----------
check = sheets('values/MENU!A1:I60?valueRenderOption=FORMATTED_VALUE')
rows = check.get('values', [])
print(f'Read {len(rows)} rows from MENU')

headers = rows[0] if rows else []
print('Headers:', headers)

# Column C = description (index 2)
filled, skipped = [], []
for i, row in enumerate(rows[1:], start=2):  # sheet row number = i
    name = (row[1] if len(row) > 1 else '').strip()
    desc = (row[2] if len(row) > 2 else '').strip()
    if not name:
        continue
    if name in NEW_DESCRIPTIONS:
        if desc:
            skipped.append((name, 'already has description'))
        else:
            filled.append((i, name, NEW_DESCRIPTIONS[name]))
    else:
        skipped.append((name, 'no draft needed'))

print(f'\nTo fill: {len(filled)}')
for i, name, d in filled:
    print(f'  row {i}: {name}')

# ---------- Write only C for filled rows ----------
if filled:
    body = {'valueInputOption': 'RAW', 'data': []}
    for i, name, d in filled:
        body['data'].append({
            'range': f'MENU!C{i}',
            'majorDimension': 'ROWS',
            'values': [[d]],
        })
    resp = sheets('values:batchUpdate', method='POST', body=body)
    print(f'\nUpdated {len(resp.get("valueInputs", []))} cells')

# ---------- Verify ----------
check2 = sheets('values/MENU!A2:C40?valueRenderOption=FORMATTED_VALUE')
for row in check2.get('values', []):
    name = (row[1] if len(row) > 1 else '').strip()
    desc = (row[2] if len(row) > 2 else '').strip()
    if name in NEW_DESCRIPTIONS:
        status = 'OK' if desc else 'STILL EMPTY!'
        print(f'  [{status}] {name}: {desc[:60]}...' if desc else f'  [{status}] {name}')
