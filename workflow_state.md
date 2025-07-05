# workflow_state.md
_Last updated: 2025-07-03_

## State
Phase: BLUEPRINT
Status: NEEDS_PLAN_APPROVAL
CurrentItem: 16

## Plan
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
   - [ ] Implementation complete (`project_config.md` > Step 1)
   - [ ] Tests executed and analyzed (`project_config.md`  > Step 2)
   - [ ] ALL tests pass (zero "FAILED" entries)
   - [ ] Real account verification executed (`project_config.md` > Step 3)
   - [ ] ALL verification commands succeed (zero errors)
   - [ ] Trigger **RULE_GIT_COMMIT_01** to prompt for version control
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
      2-7. Draft commit subjects (optional body indented)
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

## Workflow History
<!-- RULE_GIT_COMMIT_01 stores commit SHAs and messages here -->

## ArchiveLog
<!-- RULE_LOG_ROTATE_01 stores condensed summaries here -->

## Blueprint History
<!-- RULE_BLUEPRINT_ARCHIVE_01 stores previous blueprint versions here -->
<!-- Format: ### Blueprint [YYYY-MM-DD HH:MM:SS] - ID: [UUID-short] -->
<!-- Each archived blueprint is stored under its timestamped heading -->
