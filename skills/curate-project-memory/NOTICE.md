Ported from [DuncanMain/project-memory-core](https://github.com/DuncanMain/project-memory-core) under the MIT License.

The original local port targeted Claude Code. This version restores shared use by Claude and Codex against the same Obsidian vault and machine-local registry.

- Adds agent-neutral orientation, Codex UI metadata, and managed guidance for both agents, preserving existing imports and symlinks.
- Adds a standard-library continuity helper for repository/worktree resolution, task resume, guarded progress checkpoints, and installation.
- Extends configuration version 1 with optional automation settings; existing configurations keep their defaults.
- Extends context ranking and health checks for task checkpoints. The existing note templates, review lifecycle, and secret-filtering policy remain available.
- Retains the legacy Claude orientation asset filename for compatibility.

No upstream plugin manifests or documentation site are included. Shared continuity is local; it does not synchronize private agent memory stores or capture full transcripts.
