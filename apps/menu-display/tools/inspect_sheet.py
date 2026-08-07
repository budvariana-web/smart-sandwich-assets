#!/usr/bin/env python3
"""Read spreadsheet structure without printing service-account secrets."""
import json
import os
import sys
import time

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SPREADSHEET_ID = "1i4Oz_e_dDuOzIYhOvM-QmEcmCQTpf3qG4SM0U7_Qw-A"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


def quote_sheet_name(name: str) -> str:
    return "'" + name.replace("'", "''") + "'"


def main() -> int:
    key_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not key_path:
        print("GOOGLE_APPLICATION_CREDENTIALS is required", file=sys.stderr)
        return 2

    credentials = service_account.Credentials.from_service_account_file(key_path, scopes=SCOPES)
    api = build("sheets", "v4", credentials=credentials, cache_discovery=False)

    for attempt in range(1, 4):
        try:
            metadata = api.spreadsheets().get(
                spreadsheetId=SPREADSHEET_ID, includeGridData=False
            ).execute()
            break
        except HttpError as error:
            if attempt == 3:
                print(f"Google Sheets API request failed: {error}", file=sys.stderr)
                return 1
            time.sleep(10)

    sheets = metadata["sheets"]
    print(json.dumps({
        "title": metadata["properties"]["title"],
        "sheets": [{"title": sheet["properties"]["title"], "sheetId": sheet["properties"]["sheetId"]} for sheet in sheets],
    }, ensure_ascii=False))

    ranges = [f"{quote_sheet_name(sheet['properties']['title'])}!A1:Z10" for sheet in sheets]
    values = api.spreadsheets().values().batchGet(
        spreadsheetId=SPREADSHEET_ID,
        ranges=ranges,
        valueRenderOption="FORMATTED_VALUE",
    ).execute()
    print(json.dumps({item["range"]: item.get("values", []) for item in values.get("valueRanges", [])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
