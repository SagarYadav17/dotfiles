---
name: changelog-manager
description: Create or maintain a project-root CHANGELOG.MD using the Keep a Changelog format, written in ASD-STE100 Simplified Technical English, and update project guidance so future notable changes are recorded there.
---

# Changelog Manager

Use this skill when a project needs a new changelog, an existing changelog updated, or project instructions revised to require changelog maintenance.

## Default location and naming

- Unless the user explicitly names another directory, create or update `CHANGELOG.MD` at the project root.
- If the project already has a changelog with a different casing or established name (for example `CHANGELOG.md`, `HISTORY.md`, or `NEWS.md`), update that existing file instead of creating a duplicate. Preserve the project's established filename unless the user explicitly requests `CHANGELOG.MD`.
- Do not create a missing README, AGENTS, CLAUDE, or other guidance file merely to add this convention. Update relevant files that already exist.

## Changelog format

Follow [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/):

- Write for humans; record curated, notable changes rather than dumping commit history.
- Keep `## [Unreleased]` at the top for changes that have not shipped.
- Keep released versions in reverse chronological order, with ISO 8601 dates (`YYYY-MM-DD`).
- Group entries under only the applicable headings: `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, and `Security`.
- Use concise, user-facing descriptions written in Simplified Technical English (see below). Include breaking changes and deprecations clearly.
- Mention Semantic Versioning when the project uses it, but do not invent versions or release dates.
- Omit empty category headings. Mark a withdrawn release as `[YANKED]` when applicable.

## Writing style: ASD-STE100 (80% weight)

Write entries in ASD-STE100 Simplified Technical English. Use the `ste-output` skill for the rules, the word list and the 80/20 exceptions. If that skill is not available, apply these minimum rules: one topic per sentence, 20 words maximum, active voice, simple words, exact technical names in code format.

Changelog rules on top of STE:

- Most entries are one sentence of 8-12 words.
- State the result for the user, not the implementation. Leave detail to the design or configuration documents and refer to them.
- Keep only the facts a reader needs to upgrade or operate: new features, changed behaviour, removed items, fixed faults, mandatory upgrade steps, output format changes.

Example:

- Not STE: "The SM now leverages a robust event index that is written as hourly CRC-checked segments under `.evpend` and published after the transaction COMMIT, replacing in-memory pairing."
- STE: "Event index (`SM_EVENT_INDEX_DIR_<N>`, mandatory), with compaction in each SM."

When the user asks to compact or clean a changelog, rewrite `Unreleased` in this style: merge related bullets, remove superseded or contradictory entries, and keep every upgrade step and output change. Do not rewrite released versions unless the user asks.

When creating a new file, use this minimal starting point unless the project has a stronger convention:

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]
```

When updating an existing file, preserve its history, links, local conventions, and headings unless they conflict with the requested change. Add entries to `Unreleased` rather than rewriting released history.

## Update project guidance

After creating or updating the changelog, inspect the project root and nearby documentation for existing guidance files, including case-insensitive matches for:

- `README.md`
- `AGENTS.md`
- `CLAUDE.md`
- contributor/developer instructions, contribution guides, release notes, or equivalent project docs

Add a short, appropriately placed instruction that notable changes must be added to the project's changelog (normally `CHANGELOG.MD`) under `Unreleased`, using the Keep a Changelog categories and ASD-STE100 Simplified Technical English. Mention the actual changelog path if it is not at the root. Avoid duplicating the note in every document: update the most relevant project guidance files, including `README.md` and agent instructions when they exist and are intended for contributors or coding agents.

If a guidance file already contains a changelog rule, refine it only when needed; do not add a duplicate.

## Updating entries

Before editing, inspect the current diff or requested work so the entry reflects user-visible impact. Categorize changes by effect, not by commit type. If the user does not provide wording, summarize the actual change without claiming unverified behavior. Keep unrelated changes out of the changelog.

Finish by checking that the changelog exists at the intended path, `Unreleased` is present and near the top, and the guidance note points to the same file.
