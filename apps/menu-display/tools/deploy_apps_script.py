#!/usr/bin/env python3
"""Create, upload and deploy the Smart Sandwich Bar bound Apps Script project."""
from __future__ import annotations

import json
import os
import stat
import sys
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

PROJECT_DIR = Path(__file__).resolve().parents[1]
PROFILE_CACHE = Path.home() / ".hermes/profiles/telegram8592349055/cache/smart-sandwich-oauth"
TOKEN_FILE = PROFILE_CACHE / "user_token.json"
RESULT_FILE = PROJECT_DIR / "deployment.json"
SPREADSHEET_ID = "1i4Oz_e_dDuOzIYhOvM-QmEcmCQTpf3qG4SM0U7_Qw-A"
SCOPES = [
    "https://www.googleapis.com/auth/script.projects",
    "https://www.googleapis.com/auth/script.deployments",
]


def secure_write(path: Path, content: str) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(content, encoding="utf-8")
    os.chmod(temporary, 0o600)
    temporary.replace(path)
    os.chmod(path, 0o600)


def get_credentials() -> Credentials:
    credentials = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if not credentials.valid:
        if not credentials.expired or not credentials.refresh_token:
            raise RuntimeError("Пользовательская OAuth-сессия недействительна. Нужна повторная авторизация.")
        credentials.refresh(Request())
        secure_write(TOKEN_FILE, credentials.to_json())
    return credentials


def source_file(name: str) -> str:
    return (PROJECT_DIR / name).read_text(encoding="utf-8")


def main() -> int:
    if RESULT_FILE.exists():
        print(f"Deployment record already exists: {RESULT_FILE}", file=sys.stderr)
        return 2
    if not TOKEN_FILE.exists():
        print("No authorized user token found", file=sys.stderr)
        return 2

    api = build("script", "v1", credentials=get_credentials(), cache_discovery=False)
    project = api.projects().create(body={
        "title": "Smart Sandwich Bar — Menu Display",
        "parentId": SPREADSHEET_ID,
    }).execute()
    script_id = project["scriptId"]

    files = [
        {"name": "Code", "type": "SERVER_JS", "source": source_file("Code.gs")},
        {"name": "Index", "type": "HTML", "source": source_file("Index.html")},
        {"name": "Assets", "type": "HTML", "source": source_file("Assets.html")},
        {"name": "appsscript", "type": "JSON", "source": source_file("appsscript.json")},
    ]
    try:
        api.projects().updateContent(scriptId=script_id, body={"files": files}).execute()
        version = api.projects().versions().create(
            scriptId=script_id,
            body={"description": "Initial menu-board release"},
        ).execute()
        deployment = api.projects().deployments().create(
            scriptId=script_id,
            body={
                "versionNumber": version["versionNumber"],
                "manifestFileName": "appsscript",
                "description": "Public cafe menu board",
            },
        ).execute()
    except Exception:
        print(json.dumps({"scriptId": script_id, "status": "created_but_not_fully_deployed"}), file=sys.stderr)
        raise

    web_apps = [entry.get("webApp", {}) for entry in deployment.get("entryPoints", []) if entry.get("webApp")]
    result = {
        "status": "deployed",
        "scriptId": script_id,
        "versionNumber": version["versionNumber"],
        "deploymentId": deployment.get("deploymentId"),
        "webAppUrls": [entry.get("url") for entry in web_apps if entry.get("url")],
        "webAppConfig": [entry.get("entryPointConfig", {}) for entry in web_apps],
    }
    secure_write(RESULT_FILE, json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"Deploy error: {error}", file=sys.stderr)
        raise SystemExit(1)
