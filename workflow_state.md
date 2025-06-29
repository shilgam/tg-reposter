# workflow_state.md
_Last updated: 2025-06-29_

## State
Phase: ANALYZE
Status: READY
CurrentItem: 11

## Plan
Item 10: File-driven repost logic implementation - COMPLETED
Item 11: Refactor file logic for test/user data separation

**Refactor: Ensure test isolation and user data safety**

- Refactor file handling logic to:
  - Use atomic file renaming (os.replace) for all file moves and writes.
  - Store all user-generated files in the `./data/` directory.
  - Store all test-generated files in a separate `./tests/data/` directory.
  - Ensure that running tests never overwrites, deletes, or interferes with user data files.
  - Update tests and file paths accordingly to maintain strict separation between user and test data.

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
| 11 | **Refactor file logic for test/user data separation** | pending |
| 12 | **Add custom sleep interval to repost command** | pending |
| 13 | **Add delete command with CLI and Makefile support** | pending |
| 14 | **Add sync (repost + delete) command with CLI/Makefile** | pending |
| 15 | **Repost all attachments from Telegram albums** | pending |
| 16 | **Output only first media group link to file** | pending |
| 17 | **Resend messages with multiple media files** | pending |

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
- File I/O operations working with atomic writes to `./data/output/new_dest_urls.txt`
- URL parsing and channel ID normalization working correctly
- All requirements from _CONTEXT.md satisfied
- Moving to VALIDATE phase to confirm functionality.

2025-06-22: VALIDATE phase completed for Item 10. File-driven repost logic fully functional:
- All 20 tests passing in Docker environment
- CLI commands tested successfully: public→public and private→private reposting
- File I/O operations working with atomic writes
- URL parsing and channel ID normalization working correctly
- Output files generated correctly in `./data/output/new_dest_urls.txt`
- All requirements from _CONTEXT.md satisfied

Moving to Item 11: Delete & sync commands implementation.

## Workflow History
<!-- RULE_GIT_COMMIT_01 stores commit SHAs and messages here -->

## ArchiveLog
<!-- RULE_LOG_ROTATE_01 stores condensed summaries here -->
