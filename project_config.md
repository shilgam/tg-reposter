# project_config.md

Last-Updated: 2025-06-22

## Project Goal

Automate copying every message from a Telegram channel to channel so that the posts look freshly authored—no forwarding trace, no original-sender metadata, and (optionally) deleting prior posts on demand.

## Tech Stack

- **Language(s):** Python ≥ 3.12 (strict type-hinting)
- **Framework(s) & Libraries:** Telethon 1.x, Click (CLI), asyncio
- **Build / Tooling:** Poetry, isort, pytest, Make, Docker

## Development Workflow

### LLM Assistant Step-by-Step Instructions

1. **After each atomic code change:**
   - Assess if current sub-step is complete and tests should pass.
   - If fixes are still missing, continue working—don't run tests prematurely.

2. **When you believe the code is ready:**
   - Run `make test`.
   - **Analyze the test output carefully:**
     - Look for keywords: "FAILED", "ERROR", "FAIL", "AssertionError", "SystemExit"
     - If any tests show "FAILED" status, the tests have failed
     - Read the error messages and stack traces completely
     - Identify the root cause of each failure
   - If tests fail:
     - Analyze each failure's root cause using the Test Failure Analysis Protocol below
     - Propose specific solutions for each identified issue
     - Ask user to choose the best approach
     - Implement the chosen solution
     - Repeat from step 2 (run tests again)
   - If ALL tests pass (no "FAILED" entries): proceed to step 3.

3. **Real account verification:**
   - Use saved `${DEST_CHANNEL_ID}` or prompt user if needed.
   - Execute verification commands sequentially (example):
     ```
     make repost ARGS="--source=./temp/input/_source_private.txt --destination=2763892937"
     ```
   - For each command: analyze output for errors.
   - If errors found: propose solutions, ask user to choose, then repeat from step 2.
   - Only proceed to next phase if all commands succeed.

**Notes:**
- Verification command list must be explicitly defined and can be extended.
- Repeat all steps after every fix until both test and verification stages pass.
- Require explicit user approval before proceeding to next phase.

## Core Capabilities

- Repost **text, captions, single photos, and multi-photo albums**
- Preserve Markdown / HTML formatting verbatim
- Always use Telethon `send_*` methods — never forward
- **Optionally delete** destination messages supplied via list file

## Workflows & Command Logic

- **Workflows:**
  - *Human-in-the-loop*:
    1. Run `make repost ARGS="--destination=<channel>"` to create new posts and verify them.
    2. Run `make delete` to remove old posts (auto-detects `dest_urls_to_delete.txt`) and verify deletions.
  - *Fully automatic*:
    - Run `make sync ARGS="--destination=<channel> --source=<file>"` to perform both repost and delete steps in sequence, aborting on any error.

- **Command logic:**
  - `make repost`: Ensure or clear `new_dest_urls.txt` (archive if needed), repost each URL from `source_urls.txt`, appending new URLs. Stop on first error.
  - `make delete`: Use provided list or latest archive, delete each URL, then rename the file to `{TIMESTAMP}_deleted.txt`.
  - `make sync`: Runs `repost` and, if successful, `delete` using the archived list.

## Critical Patterns & Conventions

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
  - `dest_urls_to_delete.txt`: input, optional, URLs to delete
  - `new_dest_urls.txt`: output, new message URLs
  - `{TIMESTAMP}_old_dest_urls.txt`: output, archived previous URLs
  - `{TIMESTAMP}_deleted.txt`: output, confirms deletions

- **Other conventions:**
  - Timestamps: `YYYYMMDD_HHMMSS` (24h, optional ms)
  - CLI commands (`make login | repost | delete | sync`) must be **idempotent** and exit non-zero on any unhandled error.
  - Coding standards: PEP 8, Ruff rules, black line length = 88, isort-style imports.
  - Secrets never live in code — load via  `.env`.
  - Every new feature ships with unit tests that stub Telegram I/O.
  - Docs avoid tables unless tables are essential.
  - `make delete` defaults to the most recent `dest_urls_to_delete.txt` when `--delete-urls` is omitted (for easier interactive use). Use `make delete ARGS="--delete-urls=<file>"` to specify a file explicitly.

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
- Refactored file logic to strictly separate user data (./data/) from test data (./tests/data/), ensuring atomic file operations and test isolation.
- Completed file-driven repost logic implementation with CLI integration, supporting both public and private channels with atomic file operations.
- Implemented comprehensive automated tests for file-driven repost logic covering all channel type combinations, URL parsing, error handling, and file I/O operations.
- Set up GitHub Actions CI to run tests and Docker build.
- Implemented a containerized smoke test with pytest to ensure basic application integrity.
- Added custom sleep interval support to repost command with --sleep CLI option, environment variable override, and comprehensive test coverage.

<!-- The agent prepends the latest summary here as a new list item after each VALIDATE phase -->
