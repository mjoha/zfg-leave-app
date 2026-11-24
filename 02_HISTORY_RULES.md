# Authentic Git history and future replay contract

The goal is an *authentic authored code progression* suitable for later replay, NOT pretending that actual development took 30 calendar days. Fictional development days are assigned narrative timestamps; real commit metadata must remain truthful.

## Commit discipline
- Never fabricate SHAs. Create commits only for actual file changes, with useful messages like `F-005: add request form`.
- Make a few meaningful commits per ticket as needed. No arbitrary commit-count quotas and no empty/no-op changes for density.
- Keep changes focused enough for a later screen to show a sensible diff and review.
- Never overwrite/rebase previously approved days or release tags without explicit consent.
- Tickets must be tied to existing committed code, not just descriptions.

## Journal
Under `history/days/day-XX.json`, write a factual record including:
```
{
  "day": 3,
  "tickets": ["F-005", "F-006", "C-002", "C-004"],
  "commits": [{"sha":"ACTUAL_SHA", "ticket":"F-005", "message":"..."}],
  "tests": [{"command":"pytest -q", "exit_code":0, "summary":"..."}],
  "release": null,
  "notes": []
}
```
Resolve real commit IDs after commit creation; if metadata requires a commit of its own, don't create a circular self-reference. Record the implementation SHA, not the metadata commit itself.

## Defect narrative
- `04_BUG_ARCS.json` contains optional candidates. Some are expressly ineligible due to scheduling conflicts. Validate *actual* feature/fix chronology before using any arc.
- Defect insertion should be ordinary flawed business logic at most; never weaken authentication, permissions, privacy, or data integrity in a way that can escape the demo.
- A bug storyline is valid only if tests/smoke steps demonstrate its behavior in the old checkpoint and verify the corrected behavior in a later checkpoint.
- If the planned bug is not present, address the ticket as a real preventive fix, test-hardening, or correct another discovered defect. Do not claim an invented regression occurred.

## Releases
- Release tag format: `replay/day-03`, `replay/day-06`, etc.
- `history/releases/day-XX.json` must contain actual SHA, Python/dependency lock reference, database schema revision, seed version, build/run commands, smoke outcome, and optionally screenshot locations.
- Release snapshots must be independently reproducible with fresh DB/seed. A running release isn't allowed to migrate the user’s main DB backward.
- For future browser playback, record stable selectors and documented routes at checkpoints. `06_REPLAY_CONTRACT_EXAMPLE.json` is only an example for a later separate game.

## No fictional activity yet
Do not generate Teams conversations, fake AI prompt transcripts, pretend meeting recordings or simulated mouse movement as part of target-app development. Those will be created later from actual Git code changes and product state.
