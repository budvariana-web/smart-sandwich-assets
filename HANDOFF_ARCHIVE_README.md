# Safe handoff archive

This archive contains the portable, non-secret part of the Smart Sandwich Bar menu project.

## Included

- Apps Script backend and display source (`Code.gs`, `Index.html`, `Assets.html`, `appsscript.json`)
- current project handoff (`HANDOFF.md`) and base operating guide (`README.md`)
- deployment record (`deployment.json`) with Sheet/App Script/deployment IDs and public `/exec` URL
- UI test (`tests/render-test.js`)
- safe Sheet-inspection/setup helpers (`tools/inspect_sheet.py`, `tools/setup_sheet.py`)
- selected source image files used for the embedded menu assets

## Intentionally excluded

- OAuth clients, authorization/session tokens, service-account files, cookies, passwords and API keys
- deployment records containing project-specific administrative identifiers
- scripts that reference a private credential cache or need an owner's OAuth session
- historical screenshots, caches and Python bytecode

For deployment/access procedures, read `HANDOFF.md`. The owner must grant fresh, least-privilege access through a secure channel; do not paste credentials into Telegram.
