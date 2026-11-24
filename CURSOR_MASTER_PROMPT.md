# Cursor master prompt – build the target application only

You are developing a real, local-first leave-request web application that will later serve as the target of a separate satirical zero-player game's *pre-recorded* development history. Your deliverable NOW is the functioning application and its authentic Git evolution, NOT any game engine or animated interface.

Read, in order: `README.md`, `01_PRODUCT_AND_TECH.md`, `02_HISTORY_RULES.md`, `03_30_DAY_BACKLOG.csv`, `04_BUG_ARCS.json`, `05_RELEASE_CHECKLIST.md`.

## Mission
- Implement the 120 backlog tickets in their scheduled order across 30 *fictional development days*, four tickets/day. The fictional days are story labels, not a request to spend 30 actual days.
- **On this invocation implement Day 01 ONLY**. Never skip ahead. Afterward stop and report what is working, actual commit SHAs, exact test commands/results, and next-day blockers. Do not claim to have executed any checks you did not run.
- Build with Python, FastAPI, Jinja2 templates, modest vanilla JS/HTMX only if necessary, SQLite, SQLAlchemy, Alembic, Pytest. Keep local operation simple, no external calls or CDN assets. Build a single target-app container with one exposed HTTP port. Docker Compose may be included for ease of startup, but no Redis, queues, mailserver, cloud API or AI API.
- Use a neutral working name (e.g. `leave-app`) until product naming is decided.
- Real functionality is mandatory: no dead buttons, nonworking placeholder endpoints, fake test output, or fabricated release notes.
- Keep all evolving versions on a consistent stack and preserve app startup at verified release checkpoints.

## Git and narrative constraints
- Initialize Git if needed; use genuine small commits that reflect actual implementation, tests, and fixes. Include ticket IDs in subjects and meaningful body messages when useful.
- Avoid generating empty commits or rewriting history to make it appear more complex.
- Do not write replay journals, `history/` metadata, simulated meetings, or prompt transcripts. Ticket IDs in commit messages are the link between backlog and code.
- At the end of days 03,06,...,30 follow `05_RELEASE_CHECKLIST.md`. Tag a checkpoint only if clean-checkout rebuild + smoke tests pass.
- Any *intentional* defect must be a safe, local, testable business-logic regression, not an auth/privacy/security vulnerability. It must be introduced only after the affected feature exists, and it must be fixed later. Optional arcs in the supplied JSON are suggestions, not orders. Don't introduce a defect merely because a future bug ticket is scheduled.

## Demo and UI
- Create reproducible local demo accounts/data as functionality becomes available; never commit real credentials or personal data.
- Mark key controls with stable `data-testid` attributes (e.g. login, submit-request, approve-request) to support later browser automation across selected releases.
- Use durable migrations and version-aligned sample data; each tagged release must run against its own fresh database, not the latest database file.
- Visually readable, functional local UI is more important than fancy effects.

## Work process
1. Inspect backlog for target day; check dependencies, resolve obviously invalid ordering conservatively, and document deviations.
2. Implement one ticket at a time with tests. Commit genuinely after each coherent set of changes.
3. Run tests and basic HTTP smoke tests. Fix blocking issues and commit fixes honestly.
4. On a release day, run the checklist and tag only after it passes. Stop after the assigned day. Do not add a history journal commit.

Start Day 01 now. Do not build subsequent days or any ZPG components.
