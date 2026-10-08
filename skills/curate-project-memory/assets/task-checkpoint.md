Use `scripts/project_context.py checkpoint` to generate `Tasks/task-<generated-id>.md`; do not construct its metadata manually.

Checkpoint JSON contains a one-line `objective`, `agent` (`claude` or `codex`), `status` (`active`, `blocked`, or `completed`), and arrays of one-line summaries: `constraints`, `completed`, `verification`, `blockers`, `next_actions`, and `decision_links`. Decision links are project-relative Obsidian links to existing reviewed notes, such as `[[Decisions/Auth flow]]`.

For an update, include the returned `task_id` and `expected_revision` (the previous `saved_revision`). Git branch, revision, dirty state, changed paths, and fingerprint are inspected by the helper. It renders metadata plus readable sections for each field. Empty arrays are valid; guesses, credentials, transcripts, and machine-specific paths are not.
