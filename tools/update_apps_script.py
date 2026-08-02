#!/usr/bin/env python3
"""Upload a new version of the existing Smart Sandwich Bar Apps Script deployment."""
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
SCOPES = [
    "https://www.googleapis.com/auth/script.projects",
    "https://www.googleapis.com/auth/script.deployments",
]
SOURCE_FILES = [
    ("Code", "SERVER_JS", "Code.gs"),
    ("Index", "HTML", "Index.html"),
    ("Assets", "HTML", "Assets.html"),
    ("appsscript", "JSON", "appsscript.json"),
]


def secure_write(path: Path, content: str) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(content, encoding="utf-8")
    os.chmod(temporary, stat.S_IRUSR | stat.S_IWUSR)
    temporary.replace(path)
    os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)


def get_credentials() -> Credentials:
    credentials = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if not credentials.valid:
        if not credentials.expired or not credentials.refresh_token:
            raise RuntimeError("Пользовательская OAuth-сессия недействительна. Нужна повторная авторизация.")
        credentials.refresh(Request())
        secure_write(TOKEN_FILE, credentials.to_json())
    return credentials


def build_files() -> list[dict[str, str]]:
    return [
        {"name": name, "type": file_type, "source": (PROJECT_DIR / filename).read_text(encoding="utf-8")}
        for name, file_type, filename in SOURCE_FILES
    ]


def web_app_details(deployment: dict) -> tuple[list[str], list[dict]]:
    web_apps = [entry.get("webApp", {}) for entry in deployment.get("entryPoints", []) if entry.get("webApp")]
    return (
        [entry.get("url") for entry in web_apps if entry.get("url")],
        [entry.get("entryPointConfig", {}) for entry in web_apps],
    )


def main() -> int:
    if not RESULT_FILE.exists():
        raise RuntimeError("Не найден deployment.json: сначала создайте исходное развёртывание.")
    if not TOKEN_FILE.exists():
        raise RuntimeError("Нет авторизованной OAuth-сессии Apps Script.")

    record = json.loads(RESULT_FILE.read_text(encoding="utf-8"))
    script_id = record.get("scriptId")
    deployment_id = record.get("deploymentId")
    if not script_id or not deployment_id:
        raise RuntimeError("В deployment.json отсутствует scriptId или deploymentId.")

    api = build("script", "v1", credentials=get_credentials(), cache_discovery=False)
    api.projects().updateContent(scriptId=script_id, body={"files": build_files()}).execute()
    version = api.projects().versions().create(
        scriptId=script_id,
        body={"description": "Embedded tuna menu image and EUR price display"},
    ).execute()
    deployment = api.projects().deployments().update(
        scriptId=script_id,
        deploymentId=deployment_id,
        body={
            "deploymentConfig": {
                "scriptId": script_id,
                "versionNumber": version["versionNumber"],
                "manifestFileName": "appsscript",
                "description": "Public cafe menu board",
            }
        },
    ).execute()

    urls, config = web_app_details(deployment)
    record.update({
        "status": "deployed",
        "versionNumber": version["versionNumber"],
        "webAppUrls": urls or record.get("webAppUrls", []),
        "webAppConfig": config or record.get("webAppConfig", []),
    })
    secure_write(RESULT_FILE, json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({
        "status": "updated",
        "versionNumber": record["versionNumber"],
        "webAppUrls": record["webAppUrls"],
        "webAppConfig": record["webAppConfig"],
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"Update error: {error}", file=sys.stderr)
        raise SystemExit(1)
