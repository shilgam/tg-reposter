# workflow_state.md
_Last updated: 2025-06-22_

## State
Phase: CONSTRUCT
Status: RUNNING
CurrentItem: 6

## Plan
1.  **Create Workflow Directory**:
    *   Create the `.github/workflows` directory if it doesn't exist.
2.  **Create CI Docker Compose File**:
    *   Create a new file named `docker-compose.ci.yml`.
    *   Define a `reposter` service that builds the Docker image.
    *   Override the service's command to execute `make test`. This ensures tests run inside the container.
3.  **Create CI Workflow File**:
    *   Create a new file named `.github/workflows/ci.yml`.
4.  **Define Workflow Triggers**:
    *   Configure the workflow to run on all `push` events and all `pull_request` events.
5.  **Define CI Job**:
    *   Create a single job named `ci`.
    *   Specify the runner as `ubuntu-latest`.
6.  **Define Job Steps**:
    *   Use `actions/checkout@v4` to check out the repository code.
    *   Add a step to run the tests using Docker Compose:
        *   Command: `docker-compose -f docker-compose.ci.yml up --build --abort-on-container-exit --exit-code-from reposter`
        *   This command builds the image and runs the test container. The workflow will fail if the tests fail.
7.  **Verify Workflow**:
    *   Instruct the user to commit and push the new files (`.github/workflows/ci.yml` and `docker-compose.ci.yml`).
    *   Ask the user to confirm that the workflow triggers and succeeds on GitHub.
8.  **Update State**: Set item 6 status to `done`, `Phase = CONSTRUCT`, `Status = READY`, `CurrentItem = 7`.

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
| 6  | **GitHub Actions CI** — set up CI to run tests, and Docker build | pending |
| 7  | **Minimal test harness** — add `pytest`, write smoke test for PoC success | pending |
| 8  | **CLI skeleton (Click)** — wrap PoC in `click` (`repost`, `delete`, `sync`) | pending |
| 9  | **File-driven repost logic** — read source URLs, repost, and write destination URLs | pending |
| 10 | **Delete & sync commands** — implement `delete` and `sync` commands per `_CONTEXT.md` | pending |
| 11 | **Robust logging & error handling** — add logging and exit on first error | pending |
| 12 | **Comprehensive unit tests** — add unit tests with mocked Telethon, aim for 90% coverage | pending |
| 13 | **Documentation pass** — expand `README.md` with usage instructions and badges | pending |
| 14 | **Automation for green tests** — enforce passing CI via branch protection rules | pending |

## Log
- Created `Dockerfile`.
- User confirmed `Dockerfile` build was successful and script ran.
- Created `.dockerignore`.
- Created `docker-compose.yml`.
- User confirmed `docker-compose up` and live-reloading.
- Updated `README.md` with Docker and Docker Compose instructions.
- Created `Makefile` and removed linting/formatting targets as requested.
- User confirmed `make help` works correctly.
<!-- AI appends detailed reasoning, tool output, and errors here -->

## Workflow History
<!-- RULE_GIT_COMMIT_01 stores commit SHAs and messages here -->

## ArchiveLog
<!-- RULE_LOG_ROTATE_01 stores condensed summaries here -->