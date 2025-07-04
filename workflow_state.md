# workflow_state.md
_Last updated: 2025-07-03_

## State
Phase: CONSTRUCT
Status: IN_PROGRESS
CurrentItem: 14

## Plan
<!-- The AI fills this in during the BLUEPRINT phase -->
Item 10: File-driven repost logic implementation - COMPLETED
Item 11: Refactor file logic for test/user data separation - COMPLETED
Item 12: Add custom sleep interval to repost command - COMPLETED
Item 13: Add delete command with CLI and Makefile support - COMPLETED
Item 14: Resend messages with multiple media files - PLAN PROPOSED

Step 1: Analyze Telethon's support for multi-media (album) messages and identify the correct API usage (send_album, send_file, etc.).
Step 2: Update the repost logic to detect when a source message contains multiple media files (album/grouped_id) and collect all related media.
Step 3: Implement logic to repost all media in the group as a single album to the destination channel, preserving captions and order.
Step 4: Update file I/O logic to correctly record new destination URLs for each message in the album, maintaining mapping to the source.
Step 5: Add/extend unit tests to cover reposting of multi-media messages, including edge cases (mixed media types, missing captions, etc.).
Step 6: Update CLI and Makefile as needed to support the new logic (if interface changes are required).
Step 7: Update documentation and usage examples to reflect multi-media repost support.

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
1. Prompt user to commit changes with a generated message (e.g., `Phase X: [brief description]`). Suggest multiple messages and let the user choose.
2. Suggest creating a new branch for significant changes (e.g., `git checkout -b feature/new-thing`).
3. **Upon user confirmation**, execute the `git add .` and `git commit` commands.
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
| 15 | **Add sync (repost + delete) command with CLI/Makefile** | pending |
| 16 | **Keep Markdown/HTML formatting when reposting messages** | pending |

## Log
<!-- AI appends detailed reasoning, tool output, and errors here -->
2025-07-04: Step 7 completed for Item 14 (multi-media reposting). No documentation or usage example updates made per user decision. All plan steps complete; ready to transition to VALIDATE phase.
Checklist for Step 7:
- [x] Documentation reviewed
- [x] No update required (user decision)
- [x] Ready for VALIDATE phase


## Workflow History
<!-- RULE_GIT_COMMIT_01 stores commit SHAs and messages here -->

## ArchiveLog
<!-- RULE_LOG_ROTATE_01 stores condensed summaries here -->

## Blueprint History
<!-- RULE_BLUEPRINT_ARCHIVE_01 stores previous blueprint versions here -->
<!-- Format: ### Blueprint [YYYY-MM-DD HH:MM:SS] - ID: [UUID-short] -->
<!-- Each archived blueprint is stored under its timestamped heading -->
