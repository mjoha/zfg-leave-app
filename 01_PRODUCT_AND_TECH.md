# Product and technical contract

## Scope
A local, fictional company leave-management application. Two simple user roles: employee and administrator. Employee creates and views requests; admin approves/rejects and administers appropriate data. No integrations with external HR, messaging, calendar or AI services. App itself must be usable in a browser, not merely a backend API. Public-facing project name remains provisional.

## Stable technology
- Python 3.12 (pin the chosen minor version for all releases).
- FastAPI + Jinja2 for server-side pages; plain CSS and small vanilla JavaScript, no frontend compilation/build pipeline.
- SQLite + SQLAlchemy + Alembic. Run migration commands explicitly; don't rely on destructive auto-create in the real app.
- Pytest; add Playwright smoke tests if feasible, but do not require a live third-party service.
- One web service port `8000`; Dockerfile and docker-compose.yml using bind/volume only for persistent local data. `GET /health` returns a lightweight success response.
- Dependency versions pinned for reproducibility; no remote assets needed at runtime. Initial image build may download pinned dependencies.

## Functional boundaries
- Store only fictional demo user data. Use secure password hashing, normal server-side authorization checks, sensible session cookie settings; don't intentionally seed security holes.
- No external mail sending; present actions in the local UI. ICS/CSV export produces downloadable local files.
- Admin role is intentionally simple. Fine-grained enterprise permissions are out of scope.
- Explicitly handle validation and errors. A planned bug may break a *non-security* edge case in a known intermediate version only if documented and later repaired.
- Deterministic seed fixture and reset command for each release. Avoid hardcoding a current-calendar year so replay remains meaningful later.

## Local user experience
- Desktop-first but readable on tablets; conventional links/forms work. Basic accessibility (labels, keyboard interaction, contrast).
- Every feature should have visible effect or verifiable output. Don't create decorative controls with no behavior.
- Stable `data-testid` anchors for important flows, retained when possible across releases. Future replay browser automation will rely on them.
- README has build, run, seed, test, reset instructions and fictional demo credentials.

## Version boundaries
- Every third fictional day (03,06,...,30), provide a runnable release with a tagged SHA and fresh seed data.
- Small internal commits between release points may be broken; release tags may not.
- Avoid requiring multiple runtime stacks across history; if a breaking change is unavoidable, document exactly how the historical version runs.
