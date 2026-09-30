Ported from [DuncanMain/project-memory-core](https://github.com/DuncanMain/project-memory-core) (MIT License), which builds this skill for OpenAI Codex.

Changes made for Claude Code:

- Rewrote `SKILL.md` and `references/automatic-orientation.md` to drop Codex's "attach vault as a secondary folder" step — Claude Code has ordinary filesystem access to any local path, so no attach step is needed.
- Orientation block now installs into `CLAUDE.md` instead of `AGENTS.md`; renamed `assets/agents-project-memory.md` to `assets/claude-project-memory.md` (content unchanged).
- Relabeled a few source-attribution strings ("Codex work session" -> "Claude work session").
- Dropped the Codex plugin manifest (`.codex-plugin/`), the Codex agent manifest (`skills/curate-project-memory/agents/openai.yaml`), and the GitHub Pages docs site (`docs/`) — none of these apply to a Claude Code skill.

Everything else (note templates, Obsidian Bases views, the stdlib-only Python scripts, and the machine-local config schema/location) is unchanged and interoperates with the original Codex plugin against the same vault and config file.
