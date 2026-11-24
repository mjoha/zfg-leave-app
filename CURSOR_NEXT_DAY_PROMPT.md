# Cursor next-day prompt

Continue the existing **target leave application only**. Do not implement the ZPG or replay UI.

1. Read `README.md`, `CURSOR_MASTER_PROMPT.md`, `01_PRODUCT_AND_TECH.md`, `02_HISTORY_RULES.md`, and `03_30_DAY_BACKLOG.csv` plus relevant bug arcs.
2. Determine the last completed fictional day from the backlog and the ticket IDs already in Git commits. Implement **only the next uncompleted day** (four tickets), in CSV order, respecting dependencies.
3. Keep the stack, migrations, demo seed, selectors, and local startup working. Add meaningful tests and actual commits with ticket IDs.
4. Do not create `history/` journals or other replay metadata. If today is a multiple of 3, run the full release checklist and tag only after successful verification.
5. Give a concise report: completed tickets, SHAs, tests run (exact commands and outcomes), what the app now visibly does, release/tag if any, deviations/blockers. Then STOP. Do not work ahead.

Begin the next uncompleted day.
