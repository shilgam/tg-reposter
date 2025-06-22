### High-Level Implementation Plan

- [ ] **Environment & deps** — Pin Python ≥3.12, set up `poetry`, add `telethon`. Use an `asdf` config file if desired
- [ ] **Proof-of-Concept script** — hard-code IDs, resend 1 text message end-to-end
- [ ] **Dockerization** — create a slim Alpine `Dockerfile` with an entrypoint
- [ ] **Makefile workflow** — add Makefile targets for all main development and runtime tasks
- [ ] **GitHub Actions CI** — set up CI to run tests, and Docker build
- [ ] **Minimal test harness** — add `pytest`, write smoke test for PoC success
- [ ] **CLI skeleton (Click)** — wrap PoC in `click` (`repost`, `delete`, `sync`)
- [ ] **File-driven repost logic** — read source URLs, repost, and write destination URLs
- [ ] **Delete & sync commands** — implement `delete` and `sync` commands per `_CONTEXT.md`
- [ ] **Robust logging & error handling** — add logging and exit on first error
- [ ] **Comprehensive unit tests** — add unit tests with mocked Telethon, aim for 90% coverage
- [ ] **Documentation pass** — expand `README.md` with usage instructions and badges
- [ ] **Automation for green tests** — enforce passing CI via branch protection rules
