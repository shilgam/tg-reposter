# _project_config.md

Last-Updated: 2025-06-22

## Project Goal

Automate copying every message from a Telegram channel to channel so that the posts look freshly authored—no forwarding trace, no original-sender metadata.

## Tech Stack

- **Language(s):** Python ≥ 3.12 (strict type-hinting)
- **Framework(s) & Libraries:** Telethon 1.x, Click (CLI), asyncio
- **Build / Tooling:** Poetry, Ruff, isort, pytest, Make, Docker

## Critical Patterns & Conventions

- **No forwarding ever** – use Telethon `send_*` methods exclusively.
- Directory layout:
  ```
  ./temp/input/   # source_urls.txt, dest_urls_to_delete.txt
  ./temp/output/  # new_dest_urls.txt, *_old_dest_urls.txt, *_deleted.txt
  ```
- **Atomic file writes**: write to a temp file then `os.replace`.
- **Timestamp format**: `YYYYMMDD_HHMMSS` (24-h; add `_mmm` for ms when needed).
- CLI commands (`make login | repost | delete | sync`) must be **idempotent** and exit non-zero on any unhandled error.
- Coding standards: PEP 8, Ruff rules, black line length = 88, isort-style imports.
- Async patterns: `async with TelegramClient(...)` for clear lifecycle; catch `FloodWait` and back-off.
- Secrets never live in code — load via  `.env`.
- Every new feature ships with unit tests that stub Telegram I/O.
- Docs avoid tables unless tables are essential.

## Constraints

- **Rate limits**: respect Telegram’s `FloodWait`; default 2 s delay between sends (configurable).
- **Data integrity**: stop immediately on first failure; never leave partial state.
- **Security**: keep `*.session` files out of VCS; redact PII in logs.
- **Compliance**: accommodate channel owners’ privacy requirement of stripping original metadata.

## Tokenization Settings

- Estimated chars-per-token: 3.5
- Max tokens per message: 8 000
- Plan for summary when **workflow_state.md** exceeds ~12 K chars.

---

## Changelog
<!-- The agent prepends the latest summary here as a new list item after each VALIDATE phase -->