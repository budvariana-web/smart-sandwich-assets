#!/usr/bin/env python
"""Prepare/apply one-sheet RU/ME/EN/DE migration for Smart Sandwich Bar.

Usage:
  python migrate_multilingual_menu.py            # read-only snapshot + translation preview
  python migrate_multilingual_menu.py --apply    # append MENU L:T and SETTINGS rows

MENU_ME is intentionally never deleted here. Remove it only after deployed UI
verification confirms the new API and screen cycle.
"""
import argparse
import base64
import datetime as dt
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

ROOT = Path(__file__).resolve().parent
SHEET_ID = "1i4Oz_e_dDuOzIYhOvM-QmEcmCQTpf3qG4SM0U7_Qw-A"
SA_PATH = ROOT / ".credentials/service-account.json"
BACKUP_DIR = ROOT / "backups"
NEW_HEADERS = [
    "Категория (ME)", "Название (ME)", "Описание (ME)",
    "Категория (EN)", "Название (EN)", "Описание (EN)",
    "Категория (DE)", "Название (DE)", "Описание (DE)",
]


def b64url(raw):
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def access_token():
    sa = json.loads(SA_PATH.read_text(encoding="utf-8"))
    now = int(time.time())
    header = b64url(json.dumps({"alg": "RS256", "typ": "JWT"}).encode())
    payload = b64url(json.dumps({
        "iss": sa["client_email"],
        "scope": "https://www.googleapis.com/auth/spreadsheets",
        "aud": "https://oauth2.googleapis.com/token",
        "iat": now, "exp": now + 3600,
    }).encode())
    signed = header + "." + payload
    key = serialization.load_pem_private_key(sa["private_key"].encode(), password=None)
    signature = b64url(key.sign(signed.encode(), padding.PKCS1v15(), hashes.SHA256()))
    request = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=urllib.parse.urlencode({
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": signed + "." + signature,
        }).encode(),
    )
    return json.loads(urllib.request.urlopen(request, timeout=30).read())["access_token"]


class Sheets:
    def __init__(self):
        self.token = access_token()

    def request(self, path, method="GET", body=None, query=""):
        url = "https://sheets.googleapis.com/v4/spreadsheets/" + SHEET_ID + "/" + urllib.parse.quote(path, safe="/!:$")
        if query:
            url += "?" + query
        request = urllib.request.Request(
            url,
            data=json.dumps(body, ensure_ascii=False).encode() if body is not None else None,
            method=method,
            headers={"Authorization": "Bearer " + self.token, "Content-Type": "application/json"},
        )
        try:
            return json.loads(urllib.request.urlopen(request, timeout=60).read())
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"Sheets {method} {path}: {exc.code} {exc.read().decode(errors='replace')[:500]}") from exc

    def values(self, range_name):
        return self.request("values/" + range_name, query="valueRenderOption=FORMATTED_VALUE").get("values", [])


def text(value):
    return str(value or "").strip()


def header_index(headers):
    return {text(name).lower(): index for index, name in enumerate(headers)}


def get(row, indexes, *names):
    for name in names:
        index = indexes.get(name.lower())
        if index is not None and index < len(row) and text(row[index]):
            return text(row[index])
    return ""


def resolved_description(row, indexes):
    return get(row, indexes, "Описание наше", "Описание i-food", "Описание", "description")


def translate_google(source, target, cache):
    source = text(source)
    if not source:
        return ""
    key = (source, target)
    if key in cache:
        return cache[key]
    query = urllib.parse.urlencode({"client": "gtx", "sl": "ru", "tl": target, "dt": "t", "q": source})
    url = "https://translate.googleapis.com/translate_a/single?" + query
    last_error = None
    for attempt in range(3):
        try:
            payload = json.loads(urllib.request.urlopen(url, timeout=30).read())
            result = "".join(part[0] for part in payload[0] if part and part[0]).strip()
            if result:
                cache[key] = result
                return result
        except Exception as exc:  # transient public translation endpoint errors
            last_error = exc
            time.sleep(1 + attempt)
    raise RuntimeError(f"Translation failed for {source[:80]!r} -> {target}: {last_error}")


def build_preview(menu_rows, me_rows):
    menu_header, me_header = menu_rows[0], me_rows[0]
    menu_idx, me_idx = header_index(menu_header), header_index(me_header)
    ru = {}
    me = {}
    for number, row in enumerate(menu_rows[1:], start=2):
        key = get(row, menu_idx, "Порядок", "order", "sort")
        name = get(row, menu_idx, "Название", "name")
        if key and name:
            ru[key] = {"row": number, "category": get(row, menu_idx, "Категория", "category"), "name": name,
                       "description": resolved_description(row, menu_idx)}
    for number, row in enumerate(me_rows[1:], start=2):
        key = get(row, me_idx, "Порядок", "order", "sort")
        name = get(row, me_idx, "Название", "name")
        if key and name:
            me[key] = {"row": number, "category": get(row, me_idx, "Категория", "category"), "name": name,
                       "description": resolved_description(row, me_idx)}
    if set(ru) != set(me):
        raise RuntimeError("MENU and MENU_ME order keys differ: " + json.dumps({"only_MENU": sorted(set(ru) - set(me)), "only_MENU_ME": sorted(set(me) - set(ru))}, ensure_ascii=False))

    cache = {}
    records = []
    for key in sorted(ru, key=lambda value: (float(value) if value.replace('.', '', 1).isdigit() else float('inf'), value)):
        source, montenegrin = ru[key], me[key]
        records.append({
            "orderKey": key, "menuRow": source["row"],
            "ru": {field: source[field] for field in ("category", "name", "description")},
            "me": {field: montenegrin[field] for field in ("category", "name", "description")},
            "en": {field: translate_google(source[field], "en", cache) for field in ("category", "name", "description")},
            "de": {field: translate_google(source[field], "de", cache) for field in ("category", "name", "description")},
        })
    return records


def save_json(name, data):
    BACKUP_DIR.mkdir(exist_ok=True)
    path = BACKUP_DIR / name
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def sheet_ids(api):
    meta = api.request("", query="fields=sheets.properties")
    return {item["properties"]["title"]: item["properties"]["sheetId"] for item in meta["sheets"]}


def apply(api, menu_rows, settings_rows, records):
    menu_header = menu_rows[0]
    if len(menu_header) != 11:
        raise RuntimeError(f"Expected unmodified MENU A:K (11 columns), found {len(menu_header)}")
    target_values = [NEW_HEADERS]
    for record in records:
        target_values.append([
            record["me"]["category"], record["me"]["name"], record["me"]["description"],
            record["en"]["category"], record["en"]["name"], record["en"]["description"],
            record["de"]["category"], record["de"]["name"], record["de"]["description"],
        ])
    end_row = len(target_values)
    api.request("values/MENU!L1:T" + str(end_row), method="PUT", body={"values": target_values}, query="valueInputOption=RAW")

    # settings_rows[0] is the header, so enumerate data rows using their actual
    # 1-based Sheet row numbers (start=2), not their zero-based Python indexes.
    keys = {text(row[0]).lower(): row_number for row_number, row in enumerate(settings_rows[1:], start=2) if row and text(row[0])}
    append = []
    if "показывать категории" not in keys:
        append.append(["Показывать категории", True])
    if "наборов до видео" not in keys:
        append.append(["Наборов до видео", 3])
    if append:
        start = len(settings_rows) + 1
        end = start + len(append) - 1
        api.request("values/SETTINGS!A" + str(start) + ":B" + str(end), method="PUT", body={"values": append}, query="valueInputOption=RAW")
        settings_rows += append
    # settings_rows[0] is the header, so enumerate data rows using their actual
    # 1-based Sheet row numbers (start=2), not their zero-based Python indexes.
    keys = {text(row[0]).lower(): row_number for row_number, row in enumerate(settings_rows[1:], start=2) if row and text(row[0])}

    ids = sheet_ids(api)
    category_row = keys["показывать категории"]
    bundles_row = keys["наборов до видео"]
    api.request(":batchUpdate", method="POST", body={"requests": [
        {"setDataValidation": {"range": {"sheetId": ids["SETTINGS"], "startRowIndex": category_row - 1, "endRowIndex": category_row, "startColumnIndex": 1, "endColumnIndex": 2}, "rule": {"condition": {"type": "BOOLEAN"}, "showCustomUi": True}}},
        {"setDataValidation": {"range": {"sheetId": ids["SETTINGS"], "startRowIndex": bundles_row - 1, "endRowIndex": bundles_row, "startColumnIndex": 1, "endColumnIndex": 2}, "rule": {"condition": {"type": "NUMBER_GREATER_THAN_EQ", "values": [{"userEnteredValue": "1"}]}, "showCustomUi": True}}},
    ]})
    return {"menuWriteRange": f"MENU!L1:T{end_row}", "categorySettingRow": category_row, "bundlesSettingRow": bundles_row}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    api = Sheets()
    menu = api.values("MENU!A1:K200")
    menu_me = api.values("MENU_ME!A1:K200")
    settings = api.values("SETTINGS!A1:B100")
    if not menu or not menu_me:
        raise RuntimeError("MENU or MENU_ME is empty")
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = save_json(f"menu-multilingual-before-{stamp}.json", {"MENU": menu, "MENU_ME": menu_me, "SETTINGS": settings})
    records = build_preview(menu, menu_me)
    preview = save_json("menu-multilingual-preview.json", {"records": records})
    print(json.dumps({"mode": "apply" if args.apply else "preview", "backup": str(backup.relative_to(ROOT)), "preview": str(preview.relative_to(ROOT)), "records": len(records), "sample": records[0]}, ensure_ascii=False))
    if not args.apply:
        return
    result = apply(api, menu, settings, records)
    after = {"MENU": api.values("MENU!A1:T200"), "SETTINGS": api.values("SETTINGS!A1:B100")}
    save_json(f"menu-multilingual-after-{stamp}.json", after)
    headers = after["MENU"][0]
    assert headers[11:20] == NEW_HEADERS, headers
    assert len(after["MENU"]) >= len(records) + 1
    print(json.dumps({"applied": result, "verifyHeaders": headers[11:20], "rows": len(after["MENU"]) - 1}, ensure_ascii=False))


if __name__ == "__main__":
    main()
