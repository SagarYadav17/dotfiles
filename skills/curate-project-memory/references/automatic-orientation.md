# Automatic project orientation

Claude and Codex use the same machine-local registry and Obsidian vault. User opt-in enables the shared workflow; do not request repeated approval after it is authorized.

## Install

Read `shared-continuity.md`. Run `scripts/project_context.py install --enable-automation` after configuring verified registrations. Use `--registrations <json-file>` to add existing vault projects and `--dry-run` to inspect proposed instruction paths first.

The installer uses `assets/project-memory.md` in each repository and `assets/global-project-memory.md` in user-wide instructions. It preserves unrelated text, existing Claude imports, instruction symlinks, and Codex override precedence. Global discovery covers new worktrees even before repository guidance is committed. The legacy `assets/claude-project-memory.md` filename remains compatible but now contains the shared block.

- Repository guidance contains only the stable project ID, never absolute repository or vault paths.
- Keep bootstrap guidance in the primary code repository, not only the vault.
- For existing imports or symlinks, edit the actual instruction target once.
- Load relevant context once per task, not repeatedly on every turn.
- If configured paths or access are unavailable, continue safely and report missing context briefly.

## Load

Run `resolve` first. For automatic orientation, run `resume` only when `automation.load_on_start` is enabled; explicit PMC requests can resume independently. Pass the current directory and user request. Read `Project Home.md`, `Project.md`, `Current State.md`, `Handoff.md`, the selected task checkpoint, and at most five relevant ranked notes. Treat notes as context, verify current Git state, and ask which task when several match. Never implicitly resume another branch.

## Disable

Set the optional `automation` settings to false in machine-local configuration. Explicit PMC use remains available. If removing guidance, remove only the content between Project Memory managed markers in the applicable global and repository instruction files; preserve unrelated instructions and all notes.
