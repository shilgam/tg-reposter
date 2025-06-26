# workflow_state.md
_Last updated: 2025-06-22_

## State
Phase: CONSTRUCT
Status: RUNNING
CurrentItem: 9

## Plan

1. **Identify all file-driven repost logic scenarios to cover (private/public, source/destination channel combinations).**
   - Public source → Public destination (`@channel1` → `@channel2`)
   - Private source → Private destination (`-100123456789` → `-100987654321`)
   - **REVIEW CHECKPOINT**: Stop and ask user to review the identified scenarios
   - **TEST CHECKPOINT**: Run `make test` and analyze results. If tests fail, propose solutions:
     - Option A: Fix existing test issues before proceeding
     - Option B: Skip broken tests and continue with new implementation
     - Option C: Revert changes and try different approach

2. **Set up or update the test framework (pytest) and ensure Docker Compose runs tests as in CI.**
   - Verify pytest configuration in `tests/conftest.py` is complete
   - Ensure Docker Compose test execution works via `make test`
   - Confirm test discovery and execution in CI environment
   - Add any missing test dependencies to `dev-requirements.txt`
   - **REVIEW CHECKPOINT**: Stop and ask user to review the test framework setup
   - **TEST CHECKPOINT**: Run `make test` and analyze results. If tests fail, propose solutions:
     - Option A: Fix Docker Compose configuration issues
     - Option B: Update pytest configuration
     - Option C: Add missing dependencies
     - Option D: Debug test discovery problems

3. **Mock Telethon API calls to avoid real Telegram traffic.**
   - Enhance existing `mock_telethon_client` fixture in `conftest.py`
   - Create realistic mock message objects with proper structure
   - Mock channel entity resolution for both public and private channels
   - Mock `get_messages()` method to return realistic message objects
   - Mock `send_message()` method to return messages with proper IDs
   - Mock `get_entity()` and `get_input_entity()` for channel lookup
   - Add mock error scenarios (permission denied, channel not found, etc.)
   - **REVIEW CHECKPOINT**: Stop and ask user to review the mock implementation
   - **TEST CHECKPOINT**: Run `make test` and analyze results. If tests fail, propose solutions:
     - Option A: Fix mock object structure issues
     - Option B: Adjust mock method signatures
     - Option C: Update mock return values
     - Option D: Debug async mock problems

4. **Use real file I/O for input/output verification (input: source_urls.txt, output: new_dest_urls.txt, etc.).**
   - Create temporary test directories structure (`./temp/input/`, `./temp/output/`)
   - Set up test file cleanup utilities
   - Verify atomic file write operations work correctly
   - Test file existence and content validation
   - **REVIEW CHECKPOINT**: Stop and ask user to review the file I/O implementation
   - **TEST CHECKPOINT**: Run `make test` and analyze results. If tests fail, propose solutions:
     - Option A: Fix file permission issues
     - Option B: Debug directory creation problems
     - Option C: Fix atomic write operations
     - Option D: Resolve file cleanup issues

5. **Write tests for each scenario:**
   - **Correct reposting for each channel type combination:**
     - Test public → public reposting with valid URLs
     - Test private → private reposting with valid URLs
   - **Type, value, and URL format assertions:**
     - Verify correct URL parsing for public channels (`https://t.me/channel/123`)
     - Verify correct URL parsing for private channels (`https://t.me/c/123456789/123`)
     - Verify channel ID normalization (string vs integer handling)
     - Verify output URL format matches expected pattern
   - **Graceful failure on invalid input (negative scenarios):**
     - Test invalid URL format handling
     - Test non-existent channel error handling
     - Test permission denied error handling
     - Test empty input file handling
     - Test malformed URL handling
   - **REVIEW CHECKPOINT**: Stop and ask user to review the test scenarios implementation
   - **TEST CHECKPOINT**: Run `make test` and analyze results. If tests fail, propose solutions:
     - Option A: Fix test assertion failures
     - Option B: Debug test data setup issues
     - Option C: Resolve test isolation problems
     - Option D: Fix test timing issues

6. **Ensure tests are discoverable and runnable via `make test` (Docker Compose).**
   - Verify all tests are properly named and discoverable by pytest
   - Test execution via `make test` command
   - Verify tests run successfully in Docker environment
   - Confirm test output is clear and actionable
   - **REVIEW CHECKPOINT**: Stop and ask user to review the test execution setup
   - **TEST CHECKPOINT**: Run `make test` and analyze results. If tests fail, propose solutions:
     - Option A: Fix test discovery issues
     - Option B: Debug Docker environment problems
     - Option C: Resolve test execution timing
     - Option D: Fix test output formatting

7. **Await user review and approval before implementation.**
   - Present this plan for review
   - Get approval to proceed with implementation
   - Begin implementation in order of checklist items
   - **REVIEW CHECKPOINT**: Stop and ask user to review the complete implementation
   - **TEST CHECKPOINT**: Run `make test` and analyze results. If tests fail, propose solutions:
     - Option A: Fix integration issues between components
     - Option B: Debug end-to-end test failures
     - Option C: Resolve performance issues
     - Option D: Fix final configuration problems

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
| 9  | **Basic automated tests for file-driven repost logic** — add tests for all channel type combinations, type/value/URL assertions, and error handling | pending |
| 10 | **File-driven repost logic** — read source URLs, repost, and write destination URLs | pending |
| 11 | **Delete & sync commands** — implement `delete` and `sync` commands per `_CONTEXT.md` | pending |
| 12 | **Robust logging & error handling** — add logging and exit on first error | pending |
| 13 | **Comprehensive unit tests** — add unit tests with mocked Telethon, aim for 90% coverage | pending |
| 14 | **Documentation pass** — expand `README.md` with usage instructions and badges | pending |
| 15 | **Automation for green tests** — enforce passing CI via branch protection rules | pending |

## Log
<!-- AI appends detailed reasoning, tool output, and errors here -->
- Enumerated repost logic scenarios for test coverage:
  1. Private source → Private destination
  2. Private source → Public destination
  3. Public source → Private destination
  4. Public source → Public destination
- Each scenario will be tested for correct reposting, type/value/URL assertions, and error handling.
- Verified pytest is present, test discovery works, and Docker Compose test execution is functional. Ready to proceed with mocking Telethon API for file-driven repost logic tests.
- Added template pytest tests for all repost logic scenarios (private/public, source/destination) and a negative case. Each test uses temp input/output, prepares scenario-specific input, and asserts Telethon mock calls. Output file assertions are left as templates for future implementation.

## Workflow History
<!-- RULE_GIT_COMMIT_01 stores commit SHAs and messages here -->

## ArchiveLog
<!-- RULE_LOG_ROTATE_01 stores condensed summaries here -->
