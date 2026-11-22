#!/usr/bin/env python3
"""Regenerate the public video-player manifest from SETTINGS → видео urls.

Run this immediately after a successful RAW playlist update. The video player
uses this same manifest, so it cannot drift from the TV-menu playlist.
"""
import json
import re
import time
from pathlib import Path
from google.oauth2 import service_account
from googleapiclient.discovery import build

ROOT = Path(__file__).resolve().parents[2]
SHEET_ID = '1i4Oz_e_dDuOzIYhOvM-QmEcmCQTpf3qG4SM0U7_Qw-A'
BASE = 'https://budvariana-web.github.io/smart-sandwich-assets/assets/videos/'
OUT = ROOT / 'assets' / 'video-player' / 'playlist.json'
KEY = ROOT / '.credentials' / 'service-account.json'

creds = service_account.Credentials.from_service_account_file(KEY, scopes=['https://www.googleapis.com/auth/spreadsheets.readonly'])
api = build('sheets', 'v4', credentials=creds, cache_discovery=False)
rows = api.spreadsheets().values().get(spreadsheetId=SHEET_ID, range='SETTINGS!A:B', valueRenderOption='FORMATTED_VALUE').execute().get('values', [])
raw = next((row[1] if len(row) > 1 else '' for row in rows if row and str(row[0]).strip().lower() in ('видео urls', 'video urls')), None)
if raw is None:
    raise SystemExit('video urls setting not found')
seen, urls = set(), []
for name in re.split(r'[,;\n]+', raw):
    name = name.strip()
    url = name if name.startswith(('https://', 'http://')) else BASE + name
    if name and url not in seen:
        seen.add(url); urls.append(url)
if not urls:
    raise SystemExit('playlist is empty')
OUT.write_text(json.dumps({'generatedAt': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'playlistCount': len(urls), 'videoUrls': urls}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'manifest': str(OUT), 'playlistCount': len(urls)}, ensure_ascii=False))
