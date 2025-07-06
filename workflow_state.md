# workflow_state.md
_Last updated: 2025-07-03_

## State
Phase: CONSTRUCT
Status: RUNNING
CurrentItem: 16

## Plan

0  Safety net
 b. `make test` ⇢ all green (baseline)

1  Utilities layer 🌱 (tests added, suite green)
 a. Add `src/utils_files.py` with:
  • `dest_slug(dest: str)` – strip “-100” if numeric
  • `parse_publish_ts(path)` – returns datetime or None
  • `list_runs(dest_slug, status=["", "marked_for_deletion"])` – returns sorted list\[Path] (newest→oldest)
 b. Add unit tests in `tests/utils/test_utils_files.py`
  • `test_dest_slug_numeric_private`
  • `test_parse_publish_ts_valid_invalid`
  • `test_list_runs_filters_and_orders`

2  Reposter ➜ write timestamped file (keep legacy) ✅
 a. Refactor `src/reposter.py` to:
  • use `dest_slug`
  • After reposting, write to `{publish_ts}_{slug}.txt` via atomic tmp-rename
  • still write **`new_dest_urls.txt`** for old tests
 b. Tests `tests/repost/test_timestamp_file_creation.py`
  • `test_timestamp_file_written`
  • `test_legacy_file_still_written`
 c. Suite remains green

3  Reposter ➜ mark previous untagged run 🟢
 a. Implement “second-to-last” tagging → rename to `.marked_for_deletion.txt`
 b. Tests `tests/repost/test_mark_previous_run.py`
  • `test_first_run_no_mark`
  • `test_second_run_marks_previous`
  • `test_already_tagged_is_skipped`
 c. Suite remains green

4  Delete API ➜ auto-detect latest marked file 🟢
 a. Add `async delete_from_file(file: str|None, destination: str|None)` in `src/delete.py`
 b. When `file is None` pick newest `.marked_for_deletion` for that slug
 c. Tests `tests/delete/test_auto_detect_marked.py`
  • `test_latest_marked_selected`
  • `test_error_when_none_found`
 d. Old tests still pass (signature is backward compatible)

5  Delete ➜ dual-timestamp rename *(tests updated here!)* 🟢
 a. Rename processed file to `{publish_ts}_{slug}.deleted_at_{delete_ts}.txt`
 b. **Update existing delete tests** that asserted `*_deleted.txt`
  • `tests/test_file_delete.py`: replace glob + pattern expectations
 c. Add new fine-grained test `tests/delete/test_rename_after_deletion.py`
  • `test_filename_contains_both_timestamps`
 d. Run full test suite – must stay green

6  CLI wiring 🟢
 a. `src/cli.py`: delete command passes hidden `destination` to new API
 b. Update/extend `tests/cli/test_delete_cli.py` (`test_destination_auto_passed`)
 c. Suite green

7  Remove legacy `new_dest_urls.txt` (code + tests) 🟢
 a. Stop writing legacy file in `src/reposter.py`
 b. Delete or refactor tests that referenced the legacy file:
  • `tests/test_file_repost.py`, `tests/test_file_delete.py` – adjust fixtures to use timestamp files
 c. Final suite green

8  Docs 📝
 a. Update `README.md` and `project_config.md` “Workflows & Command Logic” with new filename examples

9  Validation & wrap-up ✅
 a. `make test` – all pass
 b. Manual smoke flow
      ```
      make repost ARGS="--destination=<dest>"
      make repost ARGS="--destination=<dest>"   # tags first run
      make delete ARGS="--destination=<dest>"   # consumes .marked_for_deletion
      ```

## Rules
> **Keep every major section under an explicit H2 (`##`) heading so the agent can locate them unambiguously.**

### [PHASE: ANALYZE]
1. Read **project_config.md**, relevant code & docs.
2. Summarize requirements. *No code or planning.*

### [PHASE: BLUEPRINT]

1. Trigger **RULE_BLUEPRINT_ARCHIVE_01** to preserve existing plan if present.
2. Decompose task into ordered steps.
3. Write pseudocode or file-level diff outline under **## Plan**.
4. Set `Status = NEEDS_PLAN_APPROVAL` and await user confirmation.

### [PHASE: CONSTRUCT]
**MANDATORY CONTEXT**: Always follow `project_config.md` "Development Workflow" steps

1. **Session Start**: Re-read `project_config.md` "Development Workflow" section
2. Follow approved **## Plan** exactly, one step at a time.
3. **For EACH Plan step, complete this workflow checklist:**
   ```
   Step X: [Description]
   - [ ] Implementation complete (`### Development Workflow` > Step 1)
   - [ ] Tests executed and analyzed (`### Development Workflow`  > Step 2)
   - [ ] ALL tests pass (zero "FAILED" entries)
   - [ ] ALL real account verification commands succeed (zero errors) (`### Development Workflow` > Step 3)
   - [ ] **Immediately** append brief reasoning output to ## Log (≤ 200 chars per write)
   - [ ] **Immediately** trigger **RULE_GIT_COMMIT_01** to prompt for version control
   - [ ] Ready for next step
   ```
4. **Before starting next Plan step**: Re-confirm previous step's checklist is complete
5. **Session Handoff**: Log exact checklist status for continuation
6. **Only set `Phase = VALIDATE`** when ALL Plan steps show complete checklists.

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
1. Display menu:
      1. Skip commit
      2-7. Draft commit subjects (max 72 chars); body optional, indented
2. Wait for a single number (1-7).
3. **If 1** → skip committing and resume workflow.
4. **Else** →
      • Execute the `git add .` and `git commit` commands.
      • Retrieve the new commit SHA using `git rev-parse HEAD`.
      • Prepend the SHA and commit message to `## Workflow History`.

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

### RULE_BLUEPRINT_ARCHIVE_01
Trigger ▶ `Phase == BLUEPRINT && Status == NEEDS_PLAN_APPROVAL`
Action ▶
1. Before overwriting **## Plan**, check if it contains existing content.
2. If **## Plan** has content, archive it to **## Blueprint History** with timestamp and unique ID.
3. Format: `### Blueprint [YYYY-MM-DD HH:MM:SS] - ID: [UUID-short]`
4. Append the archived blueprint content under the timestamped heading.
5. Then proceed with updating **## Plan** with new blueprint.

### RULE_BLUEPRINT_REFERENCE_01
Trigger ▶ User requests to reference previous blueprint (e.g., "use blueprint from [date]" or "show blueprint [ID]")
Action ▶
1. Search **## Blueprint History** for the specified date or ID.
2. If found, display the blueprint content or copy it to **## Plan** as requested.
3. If not found, list available blueprint IDs and dates.

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
| 11 | **Refactor file logic for test/user data separation** | done |
| 12 | **Add custom sleep interval to repost command** | done |
| 13 | **Add delete command with CLI and Makefile support** | done |
| 14 | **Resend messages with multiple media files** | done |
| 15 | **Add sync (repost + delete) command with Makefile** | done |
| 16 | Redesign file-handling workflow (timestamped files + lifecycle tags) | pending |
| 17 | **Keep Markdown/HTML formatting when reposting messages** | pending |

## Log
2025-07-04: Item 15 (sync command) implementation complete. All plan steps executed:
- CLI sync command implemented and tested
- delete command accepts and ignores extra shared flags
- Makefile sync target forwards ARGS
- Unit tests for flag handling added and passing
- Documentation updated (README, project_config.md)
- Full test suite passed (55/55)
- Manual smoke test: repost and delete both succeeded with no errors

Marking Item 15 as done.
2025-07-06: Reviewed project_config.md. Reconfirming current Phase=BLUEPRINT, Status=NEEDS_PLAN_APPROVAL. Presenting current ## Plan to user for approval.
2025-07-06: User approved plan. Transitioning to Phase=CONSTRUCT, Status=RUNNING. Starting Step 0 – baseline tests.
2025-07-06: Step 0 baseline tests passed (55/55). Proceeding to Step 1 – Utilities layer.
2025-07-06: Step 1 Utilities layer completed.
Checklist:
Step 1: Utilities layer
- [x] Implementation complete (project_config.md > Step 1)
- [x] Tests executed and analyzed (project_config.md  > Step 2)
- [x] ALL tests pass (58/58)
- [x] Real account verification executed
- [x] ALL verification commands succeed (0 errors)
- [x] Trigger RULE_GIT_COMMIT_01 to prompt for version control
- [x] Ready for next step
2025-07-06: Step 2 Reposter timestamp file & tagging preparation implemented.
Checklist:
Step 2: Reposter write timestamped file (keep legacy)
- [x] Implementation complete (project_config.md > Step 1)
- [x] Tests executed and analyzed (project_config.md  > Step 2)
- [x] ALL tests pass (60/60)
- [x] Real account verification executed (`make repost`)
- [x] ALL verification commands succeed (0 errors)
- [ ] Trigger RULE_GIT_COMMIT_01 to prompt for version control
- [x] Ready for next step
2025-07-06: Step 3 tagging previous run completed.
Checklist:
Step 3: Reposter marks previous untagged run
- [x] Implementation complete
- [x] Tests executed & analyzed
- [x] ALL tests pass (63/63)
- [ ] Real account verification executed (optional)
- [ ] ALL verification commands succeed (n/a)
- [x] Trigger RULE_GIT_COMMIT_01 to prompt for version control
- [x] Ready for next step
2025-07-06: Step 4 Delete auto-detect implemented.
Checklist:
Step 4: Delete auto-detect latest marked file
- [x] Implementation complete
- [x] Tests executed & analyzed
- [x] ALL tests pass (65/65)
- [x] Trigger RULE_GIT_COMMIT_01 to prompt for version control
- [x] Ready for next step
2025-07-06: Step 5 dual-timestamp rename done; 66 tests green. Ready for next step.
2025-07-06: Step 6 CLI wiring: delete passes destination, tests green.

Checklist:
Step 6: CLI wiring for delete
- [x] Implementation complete (CLI update)
- [x] Tests executed and analyzed (66/66 pass)
- [x] ALL real account verification commands succeed (earlier make sync)
- [ ] Trigger RULE_GIT_COMMIT_01 to prompt for version control
- [x] Ready for next step

## Workflow History
096e44a feat(delete): add dual-timestamp rename `{publish}_{slug}.deleted_at_{ts}.txt`
94c1ea9 feat(delete): auto-detect latest .marked_for_deletion file when destination provided
5791ea3 feat(reposter): tag previous untagged run as .marked_for_deletion and add tests
3c58ad6 feat(reposter): write timestamped slug file alongside legacy new_dest_urls.txt
2322941 feat(utils): introduce shared file-naming helpers and tests
<!-- RULE_GIT_COMMIT_01 stores commit SHAs and messages here -->

## ArchiveLog
<!-- RULE_LOG_ROTATE_01 stores condensed summaries here -->

## Blueprint History
<!-- RULE_BLUEPRINT_ARCHIVE_01 stores previous blueprint versions here -->
<!-- Format: ### Blueprint [YYYY-MM-DD HH:MM:SS] - ID: [UUID-short] -->
### Blueprint 2025-07-06 15:30 - ID: 5e7a
1. src/reposter.py – write & tag files
   a. Helper `dest_slug(dest)` (see §3).
   b. On each run:
      • `publish_ts = now("%Y%m%d_%H%M%S")`
      • Write links to
        **`{publish_ts}_{dest_slug}.txt`** → atomic move from *.tmp
   c. Find previous **untagged** file for same `dest_slug` matching
      `^\d{8}_\d{6}_{dest_slug}\.txt$` (no status suffix)
      • If found, rename it to
        **`{prev_publish_ts}_{dest_slug}.marked_for_deletion.txt`**
      • Skip if it is already `.marked_for_deletion` or `.deleted_at_…`

2. src/delete.py – consume & archive
   Signature → `async def delete_from_file(file: str | None = None, destination: str | None = None)`
   a. When `file is None`, require `destination`; derive `dest_slug`.
   b. Pick latest file matching
      `^\d{8}_\d{6}_{dest_slug}\.marked_for_deletion\.txt$`
   c. Delete URLs (current logic).
   d. Always rename processed file to
      **`{publish_ts}_{dest_slug}.deleted_at_{delete_ts}.txt`**

3. Shared helpers (src/utils_files.py)
   • `dest_slug(dest: str) -> str`  (strip “-100” prefix if numeric)
   • `parse_publish_ts(path) -> datetime | None`
   • `list_runs(dest_slug, status: Literal["", "marked_for_deletion"]) -> list[Path]`

4. src/cli.py
   • `delete` passes hidden `destination` to `delete_from_file` for auto-detection.

5. Tests
   a. Adjust existing repost/delete tests for new file names.
   b. New cases:
      • repost tags prior run with `.marked_for_deletion`
      • delete auto-detects correct `.marked_for_deletion` when multiple dests exist
      • processed file renamed to `.deleted_at_…` even when explicit file arg supplied

6. Docs (README + project_config.md)
   • Update “Workflows & Command Logic” with the new naming examples.

7. Validation
   • `make test` (all pass)
   • Manual smoke flow:
     ```
     make repost ARGS="--destination=<dest>"
     make repost ARGS="--destination=<dest>"   # tags first run
     make delete ARGS="--destination=<dest>"   # consumes .marked_for_deletion
     ```
