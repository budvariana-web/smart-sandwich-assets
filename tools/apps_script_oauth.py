#!/usr/bin/env python3
"""One-time user OAuth for safely managing this cafe's Apps Script project."""
from __future__ import annotations

import argparse
import json
import os
import stat
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from google_auth_oauthlib.flow import Flow

SCOPES = [
    "https://www.googleapis.com/auth/script.projects",
    "https://www.googleapis.com/auth/script.deployments",
]
STATE_DIR = Path.home() / ".hermes/profiles/telegram8592349055/cache/smart-sandwich-oauth"
PENDING_FILE = STATE_DIR / "pending.json"
TOKEN_FILE = STATE_DIR / "user_token.json"
REDIRECT_URI = "http://localhost"
# OAuthlib rejects HTTP by default. The only allowed non-HTTPS callback here is
# the OAuth-installed-app loopback URI; all authorization endpoints remain HTTPS.
os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")


def secure_write(path: Path, payload: dict) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.chmod(temp, 0o600)
    temp.replace(path)
    os.chmod(path, 0o600)


def load_pending() -> dict:
    if not PENDING_FILE.exists():
        raise RuntimeError("Нет ожидающей OAuth-сессии. Сначала запустите команду start.")
    return json.loads(PENDING_FILE.read_text(encoding="utf-8"))


def start(client_file: str) -> None:
    flow = Flow.from_client_secrets_file(
        client_file,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
        autogenerate_code_verifier=True,
    )
    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    secure_write(PENDING_FILE, {
        "client_file": client_file,
        "state": state,
        "code_verifier": flow.code_verifier,
        "scopes": SCOPES,
        "redirect_uri": REDIRECT_URI,
    })
    print(auth_url)


def finish(redirect_url: str) -> None:
    pending = load_pending()
    parsed = urlparse(redirect_url)
    query = parse_qs(parsed.query)
    if query.get("state", [None])[0] != pending["state"]:
        raise RuntimeError("OAuth state не совпал. Запустите start и используйте только свежую ссылку.")
    if "error" in query:
        raise RuntimeError("Google вернул ошибку: " + query["error"][0])
    if not query.get("code"):
        raise RuntimeError("В URL нет OAuth-кода.")

    flow = Flow.from_client_secrets_file(
        pending["client_file"],
        scopes=pending["scopes"],
        state=pending["state"],
        redirect_uri=pending["redirect_uri"],
    )
    flow.code_verifier = pending["code_verifier"]
    flow.fetch_token(authorization_response=redirect_url)
    secure_write(TOKEN_FILE, json.loads(flow.credentials.to_json()))
    PENDING_FILE.unlink(missing_ok=True)
    print(json.dumps({
        "status": "authenticated",
        "token_file": str(TOKEN_FILE),
        "scopes": list(flow.credentials.scopes or []),
    }, ensure_ascii=False))


def show_status() -> None:
    if not TOKEN_FILE.exists():
        print(json.dumps({"status": "not_authenticated"}))
        return
    mode = stat.S_IMODE(TOKEN_FILE.stat().st_mode)
    token = json.loads(TOKEN_FILE.read_text(encoding="utf-8"))
    print(json.dumps({"status": "authenticated", "mode": oct(mode), "scopes": token.get("scopes", [])}, ensure_ascii=False))


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    start_parser = sub.add_parser("start")
    start_parser.add_argument("--client-file", required=True)
    finish_parser = sub.add_parser("finish")
    finish_parser.add_argument("--redirect-url", required=True)
    sub.add_parser("status")
    args = parser.parse_args()
    try:
        if args.command == "start":
            start(args.client_file)
        elif args.command == "finish":
            finish(args.redirect_url)
        else:
            show_status()
    except Exception as error:
        print(f"OAuth error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
