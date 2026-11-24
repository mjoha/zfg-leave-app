# Local Leave App – Cursor production kit

This repository is the *target application* for a later zero-player-game replay. **Do not build the game, simulated desktop, chat, or playback engine now.** The app must be functional and locally runnable at recorded release checkpoints.

## Start here
1. Open this folder as a new Cursor project (copy specification files into repo root).
2. Give Cursor `CURSOR_MASTER_PROMPT.md` and ask it to complete **Day 01 only**.
3. Review actual code, running tests, and commits. Then use `CURSOR_NEXT_DAY_PROMPT.md` for Day 02, etc.
4. Every third day is a tagged, runnable checkpoint: 03, 06, …, 30.

## Documents
- `CURSOR_MASTER_PROMPT.md` – primary implementation prompt.
- `CURSOR_NEXT_DAY_PROMPT.md` – recurring per-day instruction.
- `01_PRODUCT_AND_TECH.md` – product/architecture constraints.
- `02_HISTORY_RULES.md` – real commits, metadata, reproducibility.
- `03_30_DAY_BACKLOG.csv` – 120 scheduled tickets, four per day.
- `04_BUG_ARCS.json` – *optional candidate* bug storylines; validate dates first. Its `eligible: false` entries must not be staged.
- `05_RELEASE_CHECKLIST.md` – release quality gate.
- `06_REPLAY_CONTRACT_EXAMPLE.json` – future-only metadata example (not a mandated schema).

## Key rule
Never fabricate commits, test results, successful builds, or a bug that was never demonstrated. New features must actually work. Replays can later add fictional narrative around genuine code history.

## Quickstart

Python 3.12.10. From the repository root:

```text
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -r requirements-dev.txt
.venv\Scripts\python -m app.db_init
.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

On macOS or Linux, use `.venv/bin/python` instead of `.venv\Scripts\python`.

`db_init` creates any missing tables in the local SQLite file. It does not delete existing accounts. Starting `uvicorn` does not create the database; run `db_init` first. The container command does both.

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

There is no seeded demo account yet.

1. Create an employee at `http://127.0.0.1:8000/register`. Registration stores the account and does not sign you in.
2. Sign in at `http://127.0.0.1:8000/login`. The session cookie is named `leave_session`. It is HttpOnly, SameSite=Lax, and expires after 8 hours. Sign-in then opens your profile.
3. On the profile page, change the display name. Email and role stay as stored.
4. Use Sign out in the header to clear the session.

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

Stop the app, delete `data/leave.db` and `data/session_secret`, then run `python -m app.db_init` again. That removes local accounts and invalidates old session cookies. Nothing in the database is a real credential.

### Tests

The local CI-equivalent command does not use a network or an external service. It checks for Python 3.12, compiles `app` and `tests`, and runs `pytest -q`:

```text
.venv\Scripts\python scripts/ci_local.py
```

### Container

Port 8000. The image initializes the database, then serves the app. The SQLite file and session secret persist in `./data` on the host.

```text
docker compose up --build
```

Health: `http://127.0.0.1:8000/health`.
