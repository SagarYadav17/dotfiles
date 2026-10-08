---
name: oci-release
description: Build or review immutable Linux amd64 OCI release-bundle workflows for a containerized API, including checksums, metadata, verification, and rollback-safe packaging.
---

# OCI Release Workflow

Use this skill when a repository needs a repeatable OCI release archive for a containerized service. Inspect the existing Dockerfile, Compose files, release scripts, and deployment documentation first.

- Validate a semantic release version and refuse official builds from dirty worktrees.
- Treat rootless Podman as the default and primary engine for local, CI, and production OCI builds. Keep Docker Buildx as an explicit secondary/backup path only (for developer fallback or environments without Podman); require a clear engine override such as `--engine docker`, and fail clearly when the selected engine or required tools are unavailable.
- Build for `linux/amd64`, save a portable OCI archive, and package only deployment inputs: Compose or Podman deployment config, proxy config, `.env.example`, README, changelog, metadata, and checksums. Podman builds must remain rootless and must not require a Podman socket, privileged container, or rootful daemon. Docker fallback builds must preserve the same archive, checksum, metadata, and verification contract. Never include `.env`, credentials, persistent data, or a separately deployed storefront.
- Record version, source revision, and build engine; checksum every shipped file.
- Verify archive naming, required files, absence of `.env`, checksums, image loadability, and Linux/amd64 architecture.
- Document first install, upgrade, health checks, persistence safeguards (never `down -v`), rollback to a retained release, and the release retention policy (how many versions are kept and how old release directories, bundles, and images are pruned without touching volumes).

Keep release paths and filenames consistent, reuse existing scripts, and update release documentation/changelog when behavior changes. Document Podman as the primary path and Docker as the explicit fallback, and run the relevant verifier checks for each supported engine. Run shell syntax checks and safe verifier tests; do not build or publish a production image without explicit authorization.
