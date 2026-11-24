# Release checkpoint checklist (Days 03, 06, 09, 12, 15, 18, 21, 24, 27, 30)

- [ ] Git working tree clean; exact commit SHA captured
- [ ] `docker compose build` succeeds from clean checkout
- [ ] `docker compose up -d` starts app with fresh isolated demo DB
- [ ] `GET /health` returns expected status
- [ ] Seeded user and administrator can sign in
- [ ] Core action at current feature level works (request -> review -> decision when available)
- [ ] Automated suite actually executed; exit status and output captured
- [ ] At least one relevant smoke scenario run and verified
- [ ] No external network needed at runtime; no third-party embedded assets
- [ ] Release manifest includes SHA, schema revision, seed version, image build command
- [ ] Release tag created only **after** verification

**Remember:** An old release is reproduced with a **fresh matching database**, not with the newest persisted SQLite DB.
