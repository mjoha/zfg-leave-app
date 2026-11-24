# Local Leave App – Cursor production kit

This repository is the *target application* for a later zero-player-game replay. **Do not build the game, simulated desktop, chat, or playback engine now.** The app must be functional and locally runnable at recorded release checkpoints.

## Start here
1. Read the quickstart below to run the app.
2. Continue development from `03_30_DAY_BACKLOG.csv`, one fictional day at a time. Ticket IDs belong in commit subjects.
3. Every third day is a tagged, runnable checkpoint: 03, 06, …, 30. Follow `05_RELEASE_CHECKLIST.md` and tag only after the checks pass.
4. Replay timelines, meetings, prompts, and simulated events belong in a separate project. Do not add them here.

## Documents
- `CURSOR_MASTER_PROMPT.md` – primary implementation prompt.
- `CURSOR_NEXT_DAY_PROMPT.md` – recurring per-day instruction.
- `01_PRODUCT_AND_TECH.md` – product/architecture constraints.
- `02_HISTORY_RULES.md` – commit, defect, and release-tag rules.
- `03_30_DAY_BACKLOG.csv` – 120 scheduled tickets, four per day.
- `04_BUG_ARCS.json` – optional candidate bug storylines; validate dates first. Its `eligible: false` entries must not be staged.
- `05_RELEASE_CHECKLIST.md` – release quality gate.

## Key rule
Never fabricate commits, test results, successful builds, or a bug that was never demonstrated. New features must actually work. This repository stores the application and its Git history, not a replay journal.

## Quickstart

Python 3.12.10. From the repository root:

```text
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -r requirements-dev.txt
.venv\Scripts\python -m app.db_init
.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

On macOS or Linux, use `.venv/bin/python` instead of `.venv\Scripts\python`.

`db_init` applies the Alembic migrations in `alembic/versions` and does not delete existing accounts. The current head revision is `0001_initial`. Starting `uvicorn` does not migrate the database; run `db_init` first. The container migrates, seeds demo data, and then serves.

Open `http://127.0.0.1:8000/`.

### Health check

`GET /health` does not read the database or a session. A running process returns HTTP 200 and this body:

```text
{"status":"ok"}
```

```text
curl http://127.0.0.1:8000/health
```

### Use the app

Load fictional demo accounts after the tables exist:

```text
.venv\Scripts\python -m app.seed
```

| Email | Password | Role |
| --- | --- | --- |
| `employee@example.com` | `employee-demo-pass` | Employee, with one pending request for 2001-06-12 through 2001-06-14 |
| `admin@example.com` | `admin-demo-pass` | Administrator |

Running the seed again does not duplicate those rows or reset a display name you already changed. The container runs this seed on startup. These passwords are fake local demo values.

1. Or create another employee at `http://127.0.0.1:8000/register`. Registration stores the account and does not sign you in.
2. Sign in at `http://127.0.0.1:8000/login`. The session cookie is named `leave_session`. It is HttpOnly, SameSite=Lax, and expires after 8 hours. Sign-in then opens your profile.
3. On the profile page, change the display name. Email and role stay as stored.
4. Use Sign out in the header to clear the session.
5. While signed in, open New request and submit a start date, end date, and reason. The end date must be on or after the start date. My requests then lists only that account's pending requests.

### Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `APP_NAME` | `leave-app` | Name shown in the header and titles |
| `DATABASE_URL` | `sqlite:///./data/leave.db` | SQLAlchemy database URL |
| `LEAVE_DATA_DIR` | `data` | Directory for `leave.db` when `DATABASE_URL` is unset, and for the session secret file |
| `SESSION_SECRET` | random file `data/session_secret` | Signs the session cookie. Set this to keep the same secret across restarts without the file |
| `SESSION_HTTPS_ONLY` | off | When `true`, the session cookie is marked Secure. Leave it off for local HTTP |

Restart the process after changing session settings. The value used at startup is the one that signs cookies.

### Reset local data

Stop the app, delete `data/leave.db` and `data/session_secret`, then run `python -m app.db_init` and `python -m app.seed` again. That removes local accounts, restores the demo rows, and invalidates old session cookies. Nothing in the database is a real credential.

### Tests

The local CI-equivalent command does not use a network or an external service. It checks for Python 3.12, compiles `app` and `tests`, and runs `pytest -q`:

```text
.venv\Scripts\python scripts/ci_local.py
```

### Container

Port 8000. The image initializes the database, loads the demo seed, then serves the app. The SQLite file and session secret persist in `./data` on the host.

```text
docker compose up --build
```

Health: `http://127.0.0.1:8000/health`.

## Browser selectors

Interactive controls and important page states use stable `data-testid` attributes. `tests/test_selectors.py` checks that these values are still present:

| Page | Selectors |
| --- | --- |
| Signed-out home | `brand-link`, `nav-home`, `nav-register`, `nav-login`, `landing-title`, `landing-summary`, `landing-register`, `landing-login` |
| Register | `register-form`, `register-email`, `register-display-name`, `register-password`, `register-password-confirm`, `register-submit`, `register-error` |
| Account created | `registration-success`, `registration-success-login`, `registration-success-home` |
| Sign in | `login-form`, `login-email`, `login-password`, `login-submit`, `login-error` |
| Signed-in home | `nav-new-request`, `nav-profile`, `nav-user`, `logout-form`, `logout-submit`, `signed-in-name` |
| New leave request | `request-form`, `request-start`, `request-end`, `request-reason`, `request-submit`, `request-error` |
| My requests | `nav-requests`, `request-list`, `request-row`, `request-status`, `request-detail-link`, `request-empty`, `request-saved`, `request-list-new` |
| Request details | `request-detail`, `request-detail-dates`, `request-detail-days`, `request-detail-reason`, `request-status`, `request-detail-submitted`, `request-detail-back` |
| Profile | `profile-display-name`, `profile-email`, `profile-role`, `profile-created`, `profile-form`, `profile-display-name-input`, `profile-submit`, `profile-saved`, `profile-error` |
| Missing page | `not-found`, `not-found-home` |
| Database not ready | `database-unavailable`, `database-unavailable-register` |

`register-error`, `login-error`, `profile-error`, `profile-saved`, and the database page appear only in those states.
