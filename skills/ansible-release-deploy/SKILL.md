---
name: ansible-release-deploy
description: Create or update Ansible deployment and rollback workflows for immutable OCI release bundles, with safe first-install secrets handling and changelog.md maintenance.
---

# Ansible Release Deployment

Use this skill when deploying a versioned OCI bundle to a VPS with Ansible. Inspect playbooks, inventory/vault examples, Compose configuration, and release documentation before editing.

- Validate all required inputs before mutating a host: version, bundle, engine, app identity, domain, release root, Compose project, and OCI archive list.
- Check and checksum the local bundle, copy without overwriting a different bundle, and enforce immutable version directories.
- Refuse to replace a `current` path that is not a symlink. Switch atomically through a temporary symlink and preserve the server `.env` on upgrades.
- Require encrypted vault variables for first install; use `no_log` for secrets and never commit credentials. Validate Compose before starting services.
- Load images, run migrations in documented order, start Compose, wait for loopback health, assert required services, then verify public HTTPS health from the controller.
- Rollback targets a retained release, requires its `.env` and Compose file, never deletes persistent volumes, and repeats health/service checks.
- Enforce release retention so old releases do not pile up: after a fully healthy deploy (never on rollback or failure), keep the newest N versions by semver (configurable, default 3, minimum 2) plus whatever `current` points at, and prune the rest: release directory, uploaded bundle, and that version's images, then dangling layers. Match only semantic-version directory names, never prune the just-deployed or active release, and never remove volumes. Document the retention setting and that rollback can only target retained versions.

Every user-visible deployment workflow change must update the repository's `changelog.md` (or established case-equivalent such as `CHANGELOG.md`) with a concise Unreleased entry. Preserve existing format and do not invent release dates.

Run Ansible syntax checks and static validation with example inventory/vault files. Do not run a live deployment, rollback, or secret operation without explicit authorization.
