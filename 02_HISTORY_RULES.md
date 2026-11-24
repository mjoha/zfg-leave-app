# Authentic Git history and future replay contract

The goal is an *authentic authored code progression* suitable for later replay, NOT pretending that actual development took 30 calendar days. Fictional development days are assigned narrative timestamps; real commit metadata must remain truthful.

## Commit discipline
- Never fabricate SHAs. Create commits only for actual file changes, with useful messages like `F-005: add request form`.
- Make a few meaningful commits per ticket as needed. No arbitrary commit-count quotas and no empty/no-op changes for density.
- Keep changes focused enough for a later screen to show a sensible diff and review.
- Never overwrite/rebase previously approved days or release tags without explicit consent.
- Tickets must be tied to existing committed code, not just descriptions.

## No replay journal
Do not add `history/` files, day journals, release manifests, simulated meetings, prompt transcripts, or other replay events. Those belong in a separate project. Commit messages with ticket IDs, and annotated release tags, are the record that stays in this repository.

## Defect narrative
- `04_BUG_ARCS.json` contains optional candidates. Some are expressly ineligible due to scheduling conflicts. Validate *actual* feature/fix chronology before using any arc.
- Defect insertion should be ordinary flawed business logic at most; never weaken authentication, permissions, privacy, or data integrity in a way that can escape the demo.
- A bug storyline is valid only if tests/smoke steps demonstrate its behavior in the old checkpoint and verify the corrected behavior in a later checkpoint.
- If the planned bug is not present, address the ticket as a real preventive fix, test-hardening, or correct another discovered defect. Do not claim an invented regression occurred.

## Releases
- Release tag format: `replay/day-03`, `replay/day-06`, etc.
- Put the schema revision, seed command, and build/run commands in the annotated tag message after the checklist passes. Do not add a separate manifest file.
- Release snapshots must be independently reproducible with a fresh database and the seed command at that tag. A running release must not migrate a newer database backward.
- Keep stable `data-testid` selectors on the controls that browser checks need. Document them in the README when they change.

## No fictional activity yet
Do not generate Teams conversations, fake AI prompt transcripts, pretend meeting recordings or simulated mouse movement as part of target-app development. Those will be created later from actual Git code changes and product state.
