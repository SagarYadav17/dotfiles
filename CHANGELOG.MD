# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- Skill `dispatch-agents`: Claude plans and reviews. Codex and `agy` do the coding in separate git worktrees. The script `run_worker.sh` runs one worker and returns code 75 when the worker reaches its usage limit.
- `.profile`: adds the mise shims to `PATH`. Bash, non-interactive shells and desktop apps now find `node` and `codex`. `install.sh` backs up an existing `~/.profile` before `stow` links it.

### Changed

- The README gives one `winget install` command for Windows. You do not need to clone the repository.

### Removed

- `install.ps1` and all other Windows setup (Python, `graphify`, skill links, Git line endings).
- The `*.ps1` rule in `.gitattributes`.

## [1.0.1] - 2026-10-15

### Changed

- `install.ps1` now installs Python 3.14, Visual Studio Code, and Spotify.
- `install.ps1` no longer installs Antigravity, Chrome, Teams, or Zed.

## [1.0.0] - 2026-10-08

First tagged release. Supports Ubuntu, Fedora, RHEL and Windows.

### Added

- Skill `ste-output`: writes and rewrites text in ASD-STE100 Simplified Technical English.
- `install.ps1`: Windows setup with `winget`, a global Python from `uv`, `graphify` and skill links.
- `install.ps1` sets `core.autocrlf=input` and `core.eol=lf` for Git.
- `.gitattributes`: LF for text files, CRLF for `*.ps1`.
- `.gitconfig` reads `~/.gitconfig.work` for repositories under `~/work/`. The file is not tracked.
- `.claude/CLAUDE.md`: tracked global instructions for Claude Code and Codex.
- `install.sh` enables EPEL on RHEL.
- Skill `curate-project-memory`: `project_context.py` for shared project context, with tests.
- `.gitignore`.

### Changed

- `~/.codex/AGENTS.md` is a link to `.claude/CLAUDE.md`. The two files cannot differ.
- `graphify` installs its own skill with `graphify install`. The skill folder `skills/graphify` is not tracked.
- `install.sh` links single files with `stow --no-folding` and backs up existing files first.
- Skill `changelog-manager` uses `ste-output` for the writing style.
- Skills `curate-project-memory` and `ansible-release-deploy` have updated instructions.
- `minecraft-hud` moved from `skills/` to `plugins/`.

### Removed

- `nvm` from `.zshrc`. Use `mise`.
- Package managers other than `apt` and `dnf` from `install.sh`.

### Fixed

- `.stow-local-ignore` patterns now start with `/`, so stow does not link repository files into `$HOME`.
- `changelog-manager` had its writing-style section twice.
