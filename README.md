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

## Running leave-app

Python 3.12.10. From the repository root:

```text
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -r requirements-dev.txt
.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

On macOS or Linux, use `.venv/bin/python` instead of `.venv\Scripts\python`.

Initialize the local database before registering anyone. This creates missing tables and does not erase an existing file:

```text
.venv\Scripts\python -m app.db_init
```

Open `http://127.0.0.1:8000/`. `GET /health` returns `{"status":"ok"}`. Create an employee account at `http://127.0.0.1:8000/register`. Registration does not sign you in, and no demo account is seeded yet.

Tests, with the local CI-equivalent command (no network and no external services):

```text
.venv\Scripts\python scripts/ci_local.py
```

That command checks for Python 3.12, compiles `app` and `tests`, and runs `pytest -q`.

Container (port 8000):

```text
docker compose up --build
```
