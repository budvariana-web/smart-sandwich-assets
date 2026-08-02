#!/usr/bin/env python3
"""Add checkbox column K 'Показывать' to MENU sheet (display toggle).

- K1 header: 'Показывать'
- K2..K{last} = TRUE (all items visible by default, preserving any existing K)
- K2..K200: native Google Sheets checkbox data validation (BOOLEAN)

Sync (sync_ifood_to_sheet.py) preserves K for existing items and defaults
new rows to TRUE. Code.gs skips items whose K is explicitly FALSE.

Run: python add_visibility_column.py
"""
import json, time, base64, urllib.parse, urllib.request

SHEET_ID = '1i4Oz_e_dDuOzIYhOvM-QmEcmCQTpf3qG4SM0U7_Qw-A'
SA_PATH = '.credentials/service-account.json'

with open(SA_PATH) as f:
    sa = json.load(f)
now = int(time.time())
def b64url(d): return base64.urlsafe_b64encode(d).rstrip(b'=').decode()
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
        print(f'ERROR {method} {path}: {e.code} {e.read().decode()[:400]}')
        raise

# ---------- read current data ----------
cur = sheets('values/MENU!A1:K60?valueRenderOption=FORMATTED_VALUE')
rows = cur.get('values', [])
print(f'Read {len(rows)} rows')

# Existing K values (preserve) keyed by row
existing_k = {}
for i, row in enumerate(rows):
    if i == 0:
        continue
    if len(row) >= 2 and row[1].strip():
        existing_k[i + 1] = row[10] if len(row) > 10 else ''

last_row = max([i + 1 for i, row in enumerate(rows) if len(row) >= 2 and row[1].strip()] or [2])
print(f'Last data row: {last_row}')

# Build K values: TRUE for every named row (preserve existing non-empty)
k_values = []
for r in range(2, last_row + 1):
    existing = existing_k.get(r, '')
    if existing not in ('', None):
        k_values.append(existing)
    else:
        k_values.append(True)  # default visible

# ---------- 1. Write header + values ----------
range_k = f'MENU!K1:K{last_row}'
values = [['Показывать']] + [[v] for v in k_values]
sheets(f'values/{range_k}?valueInputOption=USER_ENTERED', method='PUT',
       body={'range': range_k, 'majorDimension': 'ROWS', 'values': values})
print(f'Header + {len(k_values)} values written to {range_k}')

# ---------- 2. Apply checkbox validation (BOOLEAN) on K2:K200 ----------
# NOTE: structural endpoint uses ':batchUpdate' (colon), NOT '/batchUpdate'
# (the slash form returns an HTML error page from the web frontend).
body = {'requests': [{
    'setDataValidation': {
        'range': {'sheetId': 0, 'startRowIndex': 1, 'endRowIndex': 200,
                  'startColumnIndex': 10, 'endColumnIndex': 11},
        'rule': {'condition': {'type': 'BOOLEAN'}, 'showCustomUi': True}
    }
}]}
sheets(':batchUpdate', method='POST', body=body)
print('Checkbox validation applied to K2:K200')

# ---------- 3. Verify values ----------
check = sheets(f'values/MENU!A1:K{last_row}?valueRenderOption=FORMATTED_VALUE')
print(f'\nVerify ({len(check.get("values", []))} rows):')
for row in check.get('values', []):
    name = (row[1] if len(row) > 1 else '').strip()
    if not name:
        continue
    k = row[10] if len(row) > 10 else ''
    print(f'  K={str(k):5} | {name[:45]}')
