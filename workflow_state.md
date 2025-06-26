# workflow_state.md
_Last updated: 2025-06-22_

## State
Phase: ANALYZE
Status: READY
CurrentItem: 11

## Plan
Item 10: File-driven repost logic implementation - COMPLETED
Item 11: Delete & sync commands implementation

**Current Implementation Pattern (from Makefile):**
- All commands use `make <command> ARGS="--option1=value1 --option2=value2"`
- CLI commands receive arguments via Click options
- Commands run in Docker container via `docker-compose run --rm reposter`

**Requirements from _CONTEXT.md (updated for current pattern):**

1. **`make delete` command:**
   - Usage: `make delete ARGS="--delete-urls=<file>"`
   - If `--delete-urls` not provided, auto-detect most recent `dest_urls_to_delete.txt` in `./temp/output/`
   - Delete each URL in the file from the destination channel (inferred from URLs)
   - After final successful deletion, rename file to `{TIMESTAMP}_deleted.txt`
   - Stop immediately on any error (data integrity first)

2. **`make sync` command:**
   - Usage: `make sync ARGS="--destination=<channel> --source=<file>"`
   - Run the full repost algorithm first
   - Only upon success, perform the delete algorithm using auto-detected `dest_urls_to_delete.txt`
   - Abort on any error

**Implementation Plan:**

1. **Add delete functionality to `src/reposter.py`:**
   - Create `delete_from_file(delete_urls_file=None)` function
   - Auto-detect most recent `dest_urls_to_delete.txt` if delete_urls_file is None
   - Parse URLs from list file and extract message IDs and destination channel
   - Use Telethon to delete messages from destination channel (inferred from URLs)
   - Stop immediately on any error (like repost operation)
   - Rename file to `{TIMESTAMP}_deleted.txt` on success

2. **Add sync functionality to `src/reposter.py`:**
   - Create `sync_operation(destination, source=None)` function
   - Run `repost_from_file()` first with source and destination
   - On success, run `delete_from_file()` with auto-detected delete list
   - Handle errors and abort on any failure

3. **Update CLI commands in `src/cli.py`:**
   - Update `delete()` command: add only `--delete-urls` (optional) option
   - Update `sync()` command: add `--destination` (required), `--source` (optional) options
   - Connect CLI to new reposter functions

4. **Add tests for new functionality:**
   - Test delete command with explicit delete URLs file
   - Test delete command with auto-detection of most recent `dest_urls_to_delete.txt`
   - Test sync command end-to-end with auto-detection
   - Test error handling and immediate stop on failures

5. **Update Makefile integration:**
   - Ensure `make delete ARGS="--delete-urls=<file>"` works
   - Ensure `make sync ARGS="--destination=<channel> --source=<file>"` works

**Files to modify:**
- `src/reposter.py` - Add delete and sync functions
- `src/cli.py` - Update CLI commands with proper Click options
- `tests/` - Add new test files for delete and sync functionality

**Design decisions confirmed:**
1. ✅ Sync command uses auto-detection for delete list (no `--delete-list` option)
2. ✅ Use `dest_urls_to_delete.txt` naming pattern (not `*_old_dest_urls.txt`)
3. ✅ Delete operation stops immediately on any error (data integrity first)

The file-driven repost logic is already fully implemented and working:

1. ✅ **CLI Integration**: `make repost ARGS="--source=file --destination=channel"` command works
2. ✅ **File Reading**: Reads source URLs from input files (`./temp/input/source_urls.txt`)
3. ✅ **Message Reposting**: Uses Telethon to repost messages to destination channels
4. ✅ **Output Writing**: Writes new destination URLs to `./temp/output/new_dest_urls.txt`
5. ✅ **Atomic Operations**: Uses `os.replace` for atomic file writes
6. ✅ **Channel Support**: Handles both public and private channels correctly
7. ✅ **Error Handling**: Proper error handling and exit codes
8. ✅ **URL Parsing**: Correctly parses Telegram URLs for both public and private channels
9. ✅ **Channel ID Normalization**: Properly converts channel IDs (e.g., 2763892937 → -1002763892937)

**Test Results:**
- Public → Public: `make repost ARGS="--source=./temp/input/_source_public.txt --destination=dummy_channel991"` ✅
- Private → Private: `make repost ARGS="--source=./temp/input/_source_private.txt --destination=2763892937"` ✅
- Output file created: `./temp/output/new_dest_urls.txt` with correct URLs ✅

## Rules
> **Keep every major section under an explicit H2 (`##`) heading so the agent can locate them unambiguously.**

### [PHASE: ANALYZE]
1. Read **project_config.md**, relevant code & docs.
2. Summarize requirements. *No code or planning.*

### [PHASE: BLUEPRINT]
1. Decompose task into ordered steps.
2. Write pseudocode or file-level diff outline under **## Plan**.
3. Set `Status = NEEDS_PLAN_APPROVAL` and await user confirmation.

### [PHASE: CONSTRUCT]
1. Follow the approved **## Plan** exactly.
2. After each atomic change:
   - run test / linter commands specified in `project_config.md`
   - capture tool output in **## Log**
3. On success of all steps, set `Phase = VALIDATE`.

### [PHASE: VALIDATE]
1. Rerun full test suite & any E2E checks.
2. If clean, set `Status = COMPLETED`.
3. Trigger **RULE_ITERATE_01** when applicable.
4. Trigger **RULE_GIT_COMMIT_01** to prompt for version control.

---

### RULE_INIT_01
Trigger ▶ `Phase == INIT`
Action ▶ Ask user for first high-level task → `Phase = ANALYZE, Status = RUNNING`.

### RULE_ITERATE_01
Trigger ▶ `Status == COMPLETED && Items contains unprocessed rows`
Action ▶
1. Set `CurrentItem` to next unprocessed row in **## Items**.
2. Clear **## Log**, reset `Phase = ANALYZE, Status = READY`.

### RULE_LOG_ROTATE_01
Trigger ▶ `length(## Log) > 5 000 chars`
Action ▶ Summarise the top 5 findings from **## Log** into **## ArchiveLog**, then clear **## Log**.

### RULE_SUMMARY_01
Trigger ▶ `Phase == VALIDATE && Status == COMPLETED`
Action ▶
1. Read `project_config.md`.
2. Construct the new changelog line: `- <One-sentence summary of completed work>`.
3. Find the `## Changelog` heading in `project_config.md`.
4. Insert the new changelog line immediately after the `## Changelog` heading and its following newline (making it the new first item in the list).

---

### Git Workflow
> Rules for interacting with the Git version control system.

#### RULE_GIT_COMMIT_01
Trigger ▶ `Phase == VALIDATE && Status == COMPLETED`
Action ▶
1. Prompt user to commit changes with a generated message (e.g., `Phase X: [brief description]`).
2. Suggest creating a new branch for significant changes (e.g., `git checkout -b feature/new-thing`).
3. Upon user confirmation, execute the `git add .` and `git commit` commands.
4. Retrieve the new commit SHA using `git rev-parse HEAD`.
5. Prepend the SHA and commit message to `## Workflow History`.

#### RULE_GIT_ROLLBACK_01
Trigger ▶ User command like "revert to..." or "rollback to..." followed by a description.
Action ▶
1. Search `## Workflow History` for the SHA corresponding to the description.
2. If found, execute `git checkout <SHA>`.
3. If not found, inform the user.

#### RULE_GIT_DIFF_01
Trigger ▶ User command like "diff..." or "compare..." with two descriptions.
Action ▶
1. Find the two SHAs from `## Workflow History` based on the descriptions.
2. If found, execute `git diff <SHA1> <SHA2>`.
3. If not found, inform the user.

#### RULE_GIT_GUIDANCE_01
Trigger ▶ User asks for help with Git (e.g., "how do I use git?").
Action ▶ Provide a brief list of common Git commands (`commit`, `branch`, `checkout`, `diff`).

---

## Items
| id | description | status |
|----|-------------|--------|
| 1  | **Environment & deps** — Pin Python ≥3.12, set up `pip` and `venv`, add `telethon`. Use an `asdf` config file if desired | done |
| 2  | **Proof-of-Concept script** — hard-code IDs, resend 1 text message end-to-end | done |
| 3  | **PoC Script Execution & Verification** — Manually run the script to confirm it works end-to-end | done |
| 4  | **Dockerization** — create a slim Alpine `Dockerfile` with an entrypoint | done |
| 5  | **Makefile workflow** — add Makefile targets for all main development and runtime tasks | done |
| 6  | **GitHub Actions CI** — set up CI to run tests, and Docker build | done |
| 7  | **Minimal test harness** — add `pytest`, write smoke test for PoC success | done |
| 8  | **CLI skeleton (Click)** — wrap PoC in `click` (`repost`, `delete`, `sync`) | done |
| 9  | **Basic automated tests for file-driven repost logic** — add tests for all channel type combinations, type/value/URL assertions, and error handling | done |
| 10 | **File-driven repost logic** — read source URLs, repost, and write destination URLs | done |
| 11 | **Delete & sync commands** — implement `delete` and `sync` commands per `_CONTEXT.md` | pending |
| 12 | **Robust logging & error handling** — add logging and exit on first error | pending |
| 13 | **Comprehensive unit tests** — add unit tests with mocked Telethon, aim for 90% coverage | pending |
| 14 | **Documentation pass** — expand `README.md` with usage instructions and badges | pending |
| 15 | **Automation for green tests** — enforce passing CI via branch protection rules | pending |

## Log
2025-06-22: VALIDATE phase completed for Item 9. All 20 tests passing in Docker environment. Test coverage includes:
- Channel type combinations (public→public, private→private, public→private, private→public)
- URL parsing and formatting for both public and private channels
- Error handling for invalid URLs, non-existent channels, permission errors
- File I/O operations with atomic writes and cleanup
- Integration scenarios with mixed channel types
- Mock Telethon API calls working correctly
- Test framework properly configured with pytest-asyncio
- Docker Compose test execution working via `make test`

Moving to Item 10: File-driven repost logic implementation.

2025-06-22: ANALYZE phase completed for Item 10. File-driven repost logic is already fully implemented and functional:
- CLI command `make repost ARGS="--source=file --destination=channel"` working correctly
- Successfully tested public→public and private→private reposting scenarios
- File I/O operations working with atomic writes to `./temp/output/new_dest_urls.txt`
- URL parsing and channel ID normalization working correctly
- All requirements from _CONTEXT.md satisfied
- Moving to VALIDATE phase to confirm functionality.

2025-06-22: VALIDATE phase completed for Item 10. File-driven repost logic fully functional:
- All 20 tests passing in Docker environment
- CLI commands tested successfully: public→public and private→private reposting
- File I/O operations working with atomic writes
- URL parsing and channel ID normalization working correctly
- Output files generated correctly in `./temp/output/new_dest_urls.txt`
- All requirements from _CONTEXT.md satisfied

Moving to Item 11: Delete & sync commands implementation.

## Workflow History
<!-- RULE_GIT_COMMIT_01 stores commit SHAs and messages here -->

## ArchiveLog
<!-- RULE_LOG_ROTATE_01 stores condensed summaries here -->
