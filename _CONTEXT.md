# Telegram Message Copier – Project Context for LLMs

## 1  Project Snapshot

Copy every message from a **private** Telegram channel to a **public** channel as if it were posted fresh––no forwarding trace, no original‑sender metadata. Implemented in Python with the Telethon library and exposed through a thin CLI + Makefile wrapper.

## 2  Why This Exists

Channel owners often need to mirror content without showing where it came from. Doing that manually is tedious and error‑prone. This tool automates the job while letting an operator (or a cron task) decide whether to run steps one‑by‑one or in a single shot.

## 3  Core Capabilities

* Repost text, captions, single photos, and multi‑photo albums.
* Preserve Markdown/HTML formatting exactly.
* Use Telethon `send_*` methods – **never** Telegram’s native "forward".
* Optionally delete any previously posted messages whose URLs are supplied.
* Adjustable pause between messages for rate‑limit safety.

## 4  Inputs & Outputs

### Input files (all inside `./temp/input/`)

* `source_urls.txt` – one Telegram message URL per line (private channel)
* `dest_urls_to_delete.txt` – optional list of message URLs to remove from the public channel

### Output files (inside `./temp/output/`)

* `new_dest_urls.txt` – URLs of freshly created messages
* `{TIMESTAMP}_old_dest_urls.txt` – auto‑archived copy of any pre‑existing `new_dest_urls.txt`
* `{TIMESTAMP}_deleted.txt` – confirms a batch of deletions

Timestamps follow `YYYYMMDD_HHMMSS` (24‑hour clock, with optional milliseconds if precision matters).

## 5  CLI Commands & Typical Workflows

### 5.1  Primary Commands

```
make login        # one‑time user auth (Telethon session file)
make repost SRC=source_urls.txt
make delete LIST=dest_urls_to_delete.txt
make sync  SRC=source_urls.txt DEL=dest_urls_to_delete.txt
```

### 5.2  Human‑in‑the‑loop Workflow

1. `make repost` – user verifies new posts.
2. `make delete` – user verifies deletions.

### 5.3  Fully Automatic Workflow

A single `make sync` runs **repost** then **delete** sequentially, aborting on any error.

## 6  Detailed Command Logic (Reference for Contributors & LLM)

### 6.1  `make repost`

1. Ensure `new_dest_urls.txt` exists; if not, create it.
2. If it exists and is non‑empty:

   * Copy it to `{TIMESTAMP}_old_dest_urls.txt` inside the same output directory.
   * Truncate the original file.
3. For every URL in `source_urls.txt`:

   * Re‑post the message via Telethon.
   * Append the new public‑channel URL to `new_dest_urls.txt` immediately.
4. On any exception, log and exit without touching remaining URLs.

### 6.2  `make delete`

1. Determine the list file:

   * If `LIST=` arg is given, use it.
   * Otherwise, pick the most recent `*_old_dest_urls.txt` in `./temp/output/`.
2. Delete each URL in the file from the public channel.
3. After the final successful deletion, rename the file to `{TIMESTAMP}_deleted.txt`.

### 6.3  `make sync`

Runs the full **repost** algorithm and, only upon success, performs the **delete** algorithm on the archived list.

## 7  Error Handling & Exit Codes

* Any uncaught error stops the current command and returns a non‑zero exit status.
* Print stack traces and clear, actionable log messages.
* Never continue processing after a failed step—data integrity first.

## 8  Security / Privacy Notes

* Telethon creates a `*.session` file on first login. This file **must remain untracked** (`.gitignore` already covers it).
* Do **not** embed phone numbers, API IDs, or hashes in source code or docs.

## 9  Out of Scope

* Telegram **Bot** API – we rely on user sessions only.
* Real‑time daemon or bidirectional sync.
* Web or GUI front‑end.

## 10  Developer & LLM Guidelines

1. **Python ≥ 3.10** with type hints, `ruff` or `flake8` cleanliness, and `isort`‑style imports.
2. Follow Telethon best practices—rate‑limit handling, `asyncio` patterns, and context managers for client lifecycle.
3. Use **Click** for any CLI expansions; keep commands idempotent.
4. File operations must be atomic (write‑to‑temp → rename) to avoid race conditions.
5. All new features require unit tests. Test edge cases: empty files, invalid URLs, partial failures, missing permissions.
6. Keep documentation in this `CONTEXT.md` current; update when interfaces change.
7. Never store secrets in code; encourage env vars or `.env` files loaded via `python‑dotenv` if needed.
8. When generating docs, avoid tables unless absolutely necessary—some downstream parsers strip them.

## 11  How LLM Should Use This File

* Treat every section above as a contract: do **not** deviate from constraints without explicit user approval.
* Re‑state assumptions in code comments so future maintainers see them without opening this doc.
* Prefer small, reviewable pull requests and incremental PR descriptions.
* If uncertain, ask the user for clarification instead of guessing.
