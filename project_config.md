# project_config.md

Last-Updated: 2025-07-03

## Project Goal

Automate copying every message from a Telegram channel to channel so that the posts look freshly authored—no forwarding trace, no original-sender metadata, and (optionally) deleting prior posts on demand.

## Tech Stack

- **Language(s):** Python ≥ 3.12 (strict type-hinting)
- **Framework(s) & Libraries:** Telethon 1.x, Click (CLI), asyncio,
- **Build / Tooling:** pytest, Make, Docker Compose

## Core Capabilities

- Repost **text, captions, single photos, and multi-photo albums**
- Preserve Markdown / HTML formatting verbatim
- Always use Telethon `send_*` methods — never forward
- **Optionally delete** destination messages supplied via list file

## Workflows & Command Logic

- **Workflows:**
  - *Human-in-the-loop*:
    1. Run `make repost ARGS="--destination=<channel>"` – writes to `YYYYMMDD_HHMMSS_{slug}.txt` and, if a prior un-tagged run exists, renames that file to `…_{slug}.marked_for_deletion.txt`.
    2. Run `make delete ARGS="--destination=<channel>"` – auto-detects the most-recent `…_{slug}.marked_for_deletion.txt`, deletes those posts, then renames the file to `…_{slug}.deleted_at_YYYYMMDD_HHMMSS.txt`.
  - *Fully automatic*:
    - Run `make sync ARGS="--destination=<channel> --source=<file>"` to perform both repost and delete steps in sequence, aborting on any error. The sync command is now implemented and accepts the same flags as repost and delete. The delete command silently ignores extra shared flags, so you can use unified ARGS for all commands.

- **Command logic:**
  - `make repost`:
      • Reads URLs from `source_urls.txt`.
      • Writes destination URLs to `YYYYMMDD_HHMMSS_{slug}.txt` via atomic move.
      • If a previous untagged file for the same destination exists it is renamed to `…_{slug}.marked_for_deletion.txt`.
  - `make delete`:
      • Auto-detects the latest `…_{slug}.marked_for_deletion.txt` when `--delete-urls` is omitted (you must still supply `--destination` so the slug can be derived).
      • Deletes all URLs in that file and then renames it to `…_{slug}.deleted_at_YYYYMMDD_HHMMSS.txt`.
      • Silently ignores extra shared flags (`--source`, `--sleep`) so you can reuse the same ARGS string.
  - `make sync`: Runs `repost` and, if successful, `delete` using the new destination URLs. Accepts the same flags as repost and delete, aborts on any error.

## Critical Patterns & Conventions

### Development Workflow

1. **After each atomic code change:**
   - Assess if current sub-step is complete and tests should pass.
   - If fixes are still missing, continue working—don't run tests prematurely.

2. **When you believe the code is ready:**
   - Run tests (`make test`)
   - **Analyze the test output carefully:**
     - Look for keywords: "FAILED", "ERROR", "FAIL", "AssertionError", "SystemExit"
     - If any tests show "FAILED" status, the tests have failed
     - Read the error messages and stack traces completely
     - Identify the root cause of each failure
   - If tests fail:
     - Analyze each failure's root cause
     - Propose specific solutions for each identified issue
     - Ask user to choose the best approach
     - Implement the chosen solution
     - Repeat from step 2 (run tests again)
   - If ALL tests pass (no "FAILED" entries): proceed to step 3.

3. **Real account verification:**
   - Execute verification commands:
     ```
     make sync ARGS="--source=./data/input/_source_private.txt --destination=2763892937"
     # list can be extended
     ```
   - For each command: analyze output for errors.
   - If errors found: propose solutions, ask user to choose, then repeat from step 2.
     - If no errors - proceed to next phase
   - Only proceed to next phase if all commands succeed.
     - If no errors - proceed to proceed to step 4.

4. Trigger **RULE_GIT_COMMIT_01** to prompt for version control

- **Directory layout:**
  ```
  ./data/input/         # Persistent user input files
  ./data/output/        # Persistent user output files
  ./tests/data/input/   # Ephemeral test input files (mirrors ./data/input/)
  ./tests/data/output/  # Ephemeral test output files (mirrors ./data/output/)
  ```
  - All files in `./data/` are persistent and user-facing; files in `./tests/data/` are temporary and for automated tests only.

- **Key file roles:**
  - `source_urls.txt`: input, one Telegram message URL per line (required)
  - `YYYYMMDD_HHMMSS_{slug}.txt`: output from `make repost` (new message URLs).
  - `YYYYMMDD_HHMMSS_{slug}.marked_for_deletion.txt`: output; previous run waiting to be deleted.
  - `YYYYMMDD_HHMMSS_{slug}.deleted_at_YYYYMMDD_HHMMSS.txt`: confirms deletions.

- **Other conventions:**
  - Timestamps: `YYYYMMDD_HHMMSS` (24h, optional ms)
  - CLI commands (`make login | repost | delete | sync`) must be **idempotent** and exit non-zero on any unhandled error.
  - Coding standards: PEP 8, Ruff rules, black line length = 88, isort-style imports.
  - Secrets never live in code — load via  `.env`.
  - Every new feature ships with unit tests that stub Telegram I/O.
  - Unit tests use nested classes to organize by functional area.
  - Docs avoid tables unless tables are essential.
  - `make delete` defaults to `new_dest_urls.txt` when `--delete-urls` is omitted (for easier interactive use). Use `make delete ARGS="--delete-urls=<file>"` to specify a file explicitly.

## Constraints

- **Rate limits**: respect Telegram's `FloodWait`; default 2 s delay between sends (configurable).
- **Data integrity**: stop immediately on first failure; never leave partial state.
- **No Bot API** – tool must authenticate with a **user session**, never a bot token

## Tokenization Settings

- Estimated chars-per-token: 3.5
- Max tokens per message: 8 000
- Plan for summary when **workflow_state.md** exceeds ~12 K chars.

---

## Changelog
- Added sync command (repost + delete) with Makefile support, unified ARGS, robust flag handling, and full test/E2E coverage.
- Added support for reposting Telegram albums (multi-media/grouped messages) as single albums, preserving captions and order, with full test and E2E coverage.
- Added delete command with CLI and Makefile support, including file auto-detection, robust error handling, and comprehensive test coverage.
- Refactored file logic to strictly separate user data (./data/) from test data (./tests/data/), ensuring atomic file operations and test isolation.
- Completed file-driven repost logic implementation with CLI integration, supporting both public and private channels with atomic file operations.
- Implemented comprehensive automated tests for file-driven repost logic covering all channel type combinations, URL parsing, error handling, and file I/O operations.
- Set up GitHub Actions CI to run tests and Docker build.
- Implemented a containerized smoke test with pytest to ensure basic application integrity.
- Added custom sleep interval support to repost command with --sleep CLI option, environment variable override, and comprehensive test coverage.

<!-- The agent prepends the latest summary here as a new list item after each VALIDATE phase -->
