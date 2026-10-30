---
name: oci-release-deploy
description: Build, verify and deploy immutable Linux amd64 Docker release bundles with an installer-driven Ansible wrapper. Docker is the only engine. Use for release scripts, bundle verification, install.sh, deploy and rollback playbooks, retention and changelog rules.
---

# OCI Release and Ansible Deploy

Use this skill to build a release bundle and deploy it. Inspect the Dockerfiles, Compose file, release scripts, installer, playbooks and deployment docs first.

## Build and verify

- Docker (Buildx and Compose v2) is the only build engine. Do not add Podman or an `--engine` option.
- Accept only a semantic version `vX.Y.Z`. Refuse a dirty worktree, including untracked files, and a non-Linux-x86_64 host.
- Require a `## [vX.Y.Z] - YYYY-MM-DD` section in the changelog and no entries under `[Unreleased]`. The bundle carries the changelog, so commit it before the build.
- Build `linux/amd64`. Take the image list from `docker compose config --images`. Save our images as OCI archives and pinned third-party images with `docker save`.
- Ship only deployment inputs: Compose file, proxy config, `.env.example`, installer, restore script, README, changelog, `VERSION`, `IMAGES`, `BUILD.json` (version, source revision, `"engine":"docker"`, platform) and `SHA256SUMS`. Never ship `.env`, credentials or data.
- The verifier checks root ownership of every member, checksums, file coverage, names, loadable images that restore the exact refs, `linux/amd64`, `pull_policy: never` on every service, and a clean `compose config`. It removes only images it loaded.

## Deploy with Ansible

- The playbooks are thin wrappers. The bundle's `install.sh` does the work: secret generation, image load, migrations, the atomic `current` switch, retention and the health wait. A manual install behaves the same.
- Validate inputs before changing a host: version, bundle, app name, domain, release root and architecture (`ansible_facts`). Check Docker Compose on the host.
- Checksum the local bundle. Copy it with `force: false`, then require the same checksum on the host. Extract to staging, run `sha256sum -c`, and require `VERSION` to equal the requested version.
- Keep the environment file outside the release directories, in a per-app path such as `/etc/<app>/<app>.env` (mode 600). The installer creates it on first install and keeps it on every upgrade. Use the project's own app name; in NMS it is `/etc/nms/nms.env`.
- Prefer no Ansible Vault when the installer generates the secrets on the host (NMS: `SECRET_KEY`, `DATA_ENCRYPTION_KEY`, `POSTGRES_PASSWORD`). Then no secret is in the repo or the inventory. Commit only `inventory.example.yml`; git-ignore the real inventory.
- `env_settings` in the inventory sets non-secret lines of the env file on an upgrade. Refuse the generated secrets there. Put any other secret (SMTP, OIDC) in the env file by hand on the host. If it must come from the controller, keep it out of the committed example, use `no_log`, and encrypt it with Vault only when the real inventory could be committed or shared.
- Before an upgrade, stop when `SECRET_KEY` is empty, shorter than 16 characters, or the public default.
- Health checks run on the target: loopback `/health` first, then the public URL. Use `public_health_url` and `public_health_validate_certs` when the proxy serves only certain names or its own CA.
- Retention belongs to the installer: it keeps the newest N releases (default 3, minimum 2) and never removes volumes. Rollback can reach only retained releases.
- Rollback runs `install.sh --rollback [version]`. It re-points the application and never downgrades the database. Repeat the health checks.
- Never use `down -v`.

## Rules

- Record every user-visible release or deploy change under `[Unreleased]` in the changelog, in the same commit.
- Run `bash -n` on the scripts and `ansible-playbook --syntax-check` with the example inventory. Do not run a live deploy, rollback or secret operation without explicit authorization. Production playbooks that need a sudo password are run by the owner.
