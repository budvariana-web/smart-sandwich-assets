#!/usr/bin/env python3
"""Initialize the confirmed empty Smart Sandwich Bar spreadsheet with a menu template."""
import os
import sys
from google.oauth2 import service_account
from googleapiclient.discovery import build

SPREADSHEET_ID = "1i4Oz_e_dDuOzIYhOvM-QmEcmCQTpf3qG4SM0U7_Qw-A"
WRITE_SCOPE = ["https://www.googleapis.com/auth/spreadsheets"]
MENU_HEADERS = ["Категория", "Название", "Описание", "Цена", "Старая цена", "В наличии", "Порядок", "Фото", "Бейдж"]
MENU_ROWS = [
    ["Бургеры", "Классический бургер", "Говяжья котлета, сыр, свежие овощи", 490, "", "Да", 10, "", "Хит"],
    ["Бургеры", "Чеддер BBQ", "Двойной сыр, луковый конфитюр, BBQ", 560, 620, "Да", 20, "", "−10%"],
    ["Бургеры", "Куриный спайси", "Куриное филе, чили, сыр, халапеньо", 510, "", "Да", 30, "", ""],
    ["Сэндвичи", "Индейка BBQ", "Индейка, салат, домашний соус", 420, 470, "Да", 10, "", "−10%"],
    ["Сэндвичи", "Тунец и авокадо", "Тунец, авокадо, огурец, зелень", 450, "", "Да", 20, "", ""],
    ["Сэндвичи", "Песто моцарелла", "Моцарелла, томаты, соус песто", 390, "", "Да", 30, "", ""],
    ["Закуски", "Картофель фри", "Хрустящий картофель, соус на выбор", 220, "", "Да", 10, "", ""],
    ["Напитки", "Лимонад", "Домашний, 0.4 л", 250, "", "Да", 10, "", ""],
    ["Напитки", "Американо", "Классический чёрный кофе", 180, "", "Да", 20, "", ""],
]
SETTINGS_ROWS = [
    ["Параметр", "Значение"],
    ["Бренд", "SMART SANDWICH BAR"],
    ["Обновление сек", 60],
    ["Перелистывание сек", 15],
]


def main() -> int:
    key_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not key_path:
        print("GOOGLE_APPLICATION_CREDENTIALS is required", file=sys.stderr)
        return 2

    credentials = service_account.Credentials.from_service_account_file(key_path, scopes=WRITE_SCOPE)
    api = build("sheets", "v4", credentials=credentials, cache_discovery=False)
    metadata = api.spreadsheets().get(spreadsheetId=SPREADSHEET_ID, includeGridData=False).execute()
    sheets = {item["properties"]["title"]: item["properties"] for item in metadata["sheets"]}

    requests = []
    if "MENU" not in sheets:
        # The user explicitly chose to populate the verified-empty first sheet.
        first = metadata["sheets"][0]["properties"]
        requests.append({
            "updateSheetProperties": {
                "properties": {"sheetId": first["sheetId"], "title": "MENU", "gridProperties": {"frozenRowCount": 1}},
                "fields": "title,gridProperties.frozenRowCount",
            }
        })
    if "SETTINGS" not in sheets:
        requests.append({"addSheet": {"properties": {"title": "SETTINGS", "gridProperties": {"frozenRowCount": 1}}}})
    if requests:
        api.spreadsheets().batchUpdate(spreadsheetId=SPREADSHEET_ID, body={"requests": requests}).execute()
    new_metadata = api.spreadsheets().get(spreadsheetId=SPREADSHEET_ID, includeGridData=False).execute()
    sheet_ids = {item["properties"]["title"]: item["properties"]["sheetId"] for item in new_metadata["sheets"]}

    api.spreadsheets().values().batchUpdate(
        spreadsheetId=SPREADSHEET_ID,
        body={
            "valueInputOption": "USER_ENTERED",
            "data": [
                {"range": "MENU!A1:I10", "values": [MENU_HEADERS] + MENU_ROWS},
                {"range": "SETTINGS!A1:B4", "values": SETTINGS_ROWS},
            ],
        },
    ).execute()

    header_format = {
        "backgroundColor": {"red": 0.06, "green": 0.10, "blue": 0.09},
        "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 0.99, "blue": 0.96}},
        "horizontalAlignment": "CENTER",
        "verticalAlignment": "MIDDLE",
    }
    sizes = [130, 210, 330, 100, 115, 110, 90, 240, 100]
    format_requests = []
    for title, width in (("MENU", 9), ("SETTINGS", 2)):
        sheet_id = sheet_ids[title]
        format_requests.append({
            "repeatCell": {
                "range": {"sheetId": sheet_id, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": width},
                "cell": {"userEnteredFormat": header_format},
                "fields": "userEnteredFormat(backgroundColor,textFormat.bold,textFormat.foregroundColor,horizontalAlignment,verticalAlignment)",
            }
        })
    menu_id = sheet_ids["MENU"]
    for index, size in enumerate(sizes):
        format_requests.append({
            "updateDimensionProperties": {
                "range": {"sheetId": menu_id, "dimension": "COLUMNS", "startIndex": index, "endIndex": index + 1},
                "properties": {"pixelSize": size},
                "fields": "pixelSize",
            }
        })
    format_requests.extend([
        {"repeatCell": {"range": {"sheetId": menu_id, "startRowIndex": 1, "endRowIndex": 501, "startColumnIndex": 3, "endColumnIndex": 5}, "cell": {"userEnteredFormat": {"numberFormat": {"type": "NUMBER", "pattern": "#,##0 ₽"}}}, "fields": "userEnteredFormat.numberFormat"}},
        {"setDataValidation": {"range": {"sheetId": menu_id, "startRowIndex": 1, "endRowIndex": 501, "startColumnIndex": 5, "endColumnIndex": 6}, "rule": {"condition": {"type": "ONE_OF_LIST", "values": [{"userEnteredValue": "Да"}, {"userEnteredValue": "Нет"}]}, "showCustomUi": True, "strict": True}}},
    ])
    api.spreadsheets().batchUpdate(spreadsheetId=SPREADSHEET_ID, body={"requests": format_requests}).execute()

    print("Initialized MENU (9 test items) and SETTINGS sheets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
