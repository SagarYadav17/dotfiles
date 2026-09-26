---
name: bruno-api-docs
description: Create and maintain repository-local Bruno OpenCollection YAML API collections from backend routes and schemas, keeping requests, auth, payloads, examples, environments, and execution checks aligned with the backend. Do not create Bruno .bru files.
---

# Bruno OpenCollection YAML API Collections

Use this skill when documenting or updating APIs in a repository-local Bruno collection using the OpenCollection YAML format. The collection root is `opencollection.yml`; request files use `.yml` and may be nested in folders. The backend is authoritative: inspect routers/controllers, request/response schemas, auth dependencies, and any generated OpenAPI before editing. Output OpenCollection YAML, never Bruno `.bru` request files.

Default organization rules:

- Unless the user explicitly asks otherwise, divide requests into logical API groups using folders. Do not flatten all requests into one directory.
- Unless the user explicitly asks otherwise, create the collection at the repository root in `bruno/`.
- Use this default layout: `bruno/opencollection.yml`, `bruno/environments/local.yml`, one `folder.yml` per API group, and one `.yml` request file per endpoint under its group folder.
- Keep `opencollection.yml` as the collection marker and use `bundled: false` for this directory-based layout. Use `bundled: true` only when the user explicitly requests a standalone collection file.
- Add `bruno/environments/local.yml` with safe local placeholders such as `base_url`, `session_id`, and `csrf_token`; never commit real credentials, tokens, or production URLs.
- If the user explicitly names a different output directory or asks for a flat/standalone collection, follow that instruction for the current task.

- Represent each executable request with `info`, `http`, `runtime`, `settings`, and optional `docs` sections. Use `opencollection: 1.0.0` and `bundled: true` for a standalone collection, or a root `opencollection.yml` with nested request `.yml` files for a directory collection.
- Keep method, URL, query/path parameters, headers, content type, auth, request body, scripts/assertions, and documentation synchronized with backend routes and serializers. Use `{{base_url}}`, `{{csrf_token}}`, `{{session_cookie}}`, and other environment variables for servers, tokens, IDs, and secrets; never store real credentials or customer data.
- Prefer collection-level defaults for shared headers/auth and request-level overrides only when needed. Add representative success and important failure assertions (validation, auth, not-found, conflict, rate limit) without making mutating calls against production.
- When a backend endpoint, auth requirement, body, query parameter, or response contract changes, update the matching OpenCollection request in the same change. If a generated OpenAPI schema exists, use it as an input/reference, not as the output format.
- Verify OpenCollection YAML against the published schema (`https://schema.opencollection.com/opencollection/v1.0.0.json`), validate YAML syntax, duplicate request names/sequences, path-template parameters, environment variable references, and that documented routes point to current backend behavior.

Keep YAML importable by Bruno/OpenCollection tooling. Do not create `.bru` files, an OpenAPI document in place of the collection, or perform mutating requests against production merely to verify documentation.
