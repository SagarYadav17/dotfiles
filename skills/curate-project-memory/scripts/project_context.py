#!/usr/bin/env python3
"""Resolve shared project context and save guarded cross-agent task checkpoints.

Standard library only. No model calls, transcript capture, or network access.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile
import time
import uuid

from build_context_pack import rank_context, terms
from check_vault_health import FRONTMATTER, SECRET_PATTERNS, UNIX_PATH, WINDOWS_PATH, properties

SKILL = Path(__file__).resolve().parents[1]
TASK_ID = re.compile(r"task-[0-9a-f]{12}\Z")
PROJECT_ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
AUTO_DEFAULTS = {"load_on_start": False, "save_progress": False, "save_confirmed_decisions": False}
LIST_FIELDS = ("constraints", "completed", "verification", "blockers", "next_actions", "decision_links")
SECTIONS = {"objective": "Objective", "constraints": "User constraints", "completed": "Completed work",
            "changed_paths": "Changed paths", "verification": "Verification results", "blockers": "Blockers",
            "next_actions": "Next actions", "decision_links": "Decision links"}


def config_location() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData/Local"))) / "ProjectMemory"
    elif sys.platform == "darwin":
        base = Path.home() / "Library/Application Support/ProjectMemory"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))) / "project-memory"
    return base / "config.json"


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def atomic_write(path: Path, text: str) -> bool:
    # Resolve existing symlinks; never replace the symlink itself.
    path = path.resolve()
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = path.stat().st_mode & 0o777 if path.exists() else 0o600
    fd, temporary = tempfile.mkstemp(prefix=".pmc-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return True


@contextmanager
def project_lock(config: Path, name: str, timeout: float = 2.0):
    """OS locks release on process exit; no stale lock files to recover manually."""
    directory = config.resolve().parent / "locks"
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / (name + ".lock")).open("a+b") as stream:
        if stream.tell() == 0:
            stream.write(b"0")
            stream.flush()
        deadline = time.monotonic() + timeout
        while True:
            try:
                if os.name == "nt":
                    import msvcrt
                    stream.seek(0)
                    msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError:
                if time.monotonic() >= deadline:
                    raise ValueError("Project memory is being updated; retry after reading its latest state.")
                time.sleep(0.05)
        try:
            yield
        finally:
            if os.name == "nt":
                stream.seek(0)
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def load_config(path: Path) -> dict:
    return validate_config(json.loads(path.read_text(encoding="utf-8")))


def validate_config(data: dict) -> dict:
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise ValueError("Unsupported project-memory configuration.")
    if data.get("mode") not in {"review", "manual"} or not isinstance(data.get("projects"), dict):
        raise ValueError("Invalid project-memory mode or registrations.")
    if not isinstance(data.get("vault_path"), str) or not Path(data["vault_path"]).is_absolute():
        raise ValueError("vault_path must be an absolute local path.")
    summaries = data.get("session_summaries")
    if not isinstance(summaries, dict) or not isinstance(summaries.get("enabled"), bool):
        raise ValueError("Invalid session_summaries configuration.")
    if set(summaries) - {"enabled", "path"} or summaries.get("path") is not None and not isinstance(summaries["path"], str):
        raise ValueError("Invalid session-summary settings.")
    if set(data) - {"schema_version", "mode", "vault_path", "session_summaries", "projects", "automation"}:
        raise ValueError("Unsupported configuration properties.")
    automation = data.get("automation", {})
    if not isinstance(automation, dict) or set(automation) - AUTO_DEFAULTS.keys():
        raise ValueError("Invalid project-memory automation settings.")
    if any(not isinstance(value, bool) for value in automation.values()):
        raise ValueError("Automation settings must be booleans.")
    for project_id, entry in data["projects"].items():
        if not PROJECT_ID.fullmatch(project_id) or not isinstance(entry, dict):
            raise ValueError("Invalid project registration.")
        if set(entry) - {"name", "repo_path", "vault_folder"}:
            raise ValueError("Unsupported project registration fields.")
        if any(not isinstance(entry.get(key), str) or not entry[key] for key in ("name", "repo_path", "vault_folder")):
            raise ValueError("Project registration requires name, repo_path, and vault_folder.")
        if not Path(entry["repo_path"]).is_absolute():
            raise ValueError("Registered repository paths must be absolute.")
        contained(Path(data["vault_path"]), entry["vault_folder"])
    return data


def contained(root: Path, relative: str) -> Path:
    value = PurePosixPath(relative.replace("\\", "/"))
    if value.is_absolute() or ".." in value.parts or re.match(r"^[A-Za-z]:", relative):
        raise ValueError("Project-relative path required.")
    path = (root / value).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("Path escapes the project folder.")
    return path


def git(repo: Path, *arguments: str, optional: bool = False) -> bytes:
    result = subprocess.run(["git", "-C", str(repo), *arguments], capture_output=True, timeout=30)
    if result.returncode and not optional:
        raise ValueError("Could not inspect Git checkout; no project memory was changed.")
    return result.stdout if not result.returncode else b""


def git_identity(repo: Path) -> tuple[Path, Path]:
    root = Path(os.fsdecode(git(repo, "rev-parse", "--show-toplevel")).strip()).resolve()
    common = Path(os.fsdecode(git(root, "rev-parse", "--path-format=absolute", "--git-common-dir")).strip()).resolve()
    return root, common


def snapshot(root: Path) -> dict:
    revision = git(root, "rev-parse", "--verify", "HEAD", optional=True).decode().strip()
    branch = git(root, "symbolic-ref", "--quiet", "--short", "HEAD", optional=True).decode().strip() or "(detached)"
    status = git(root, "status", "--porcelain=v1", "-z")
    tracked = git(root, "diff", "--name-only", "-z") + git(root, "diff", "--cached", "--name-only", "-z")
    untracked = git(root, "ls-files", "--others", "--exclude-standard", "-z")
    paths = sorted({os.fsdecode(item) for item in (tracked + untracked).split(b"\0") if item})
    fingerprint = hashlib.sha256(revision.encode() + status + git(root, "diff", "--cached", "--binary") + git(root, "diff", "--binary"))
    for item in untracked.split(b"\0"):
        if item:
            path = root / os.fsdecode(item)
            try:
                stat = path.lstat()
                fingerprint.update(item + str((stat.st_size, stat.st_mtime_ns)).encode())
            except FileNotFoundError:
                fingerprint.update(item + b"missing")
    return {"branch": branch, "revision": revision or "unborn", "dirty": bool(status),
            "changed_paths": paths, "git_fingerprint": fingerprint.hexdigest()}


def resolve(config: Path, repo: Path) -> dict:
    if not config.is_file():
        return {"registered": False, "reason": "configuration_missing"}
    data = load_config(config)
    try:
        root, common = git_identity(repo)
    except ValueError:
        return {"registered": False, "reason": "not_a_git_checkout"}
    matches = []
    for project_id, entry in data["projects"].items():
        try:
            _, registered_common = git_identity(Path(entry["repo_path"]))
        except ValueError:
            continue
        if common == registered_common:
            matches.append((project_id, entry))
    if len(matches) > 1:
        raise ValueError("Several project registrations refer to this repository; resolve the duplicate registration.")
    if not matches:
        return {"registered": False, "reason": "repository_not_registered"}
    project_id, entry = matches[0]
    folder = contained(Path(data["vault_path"]), entry["vault_folder"])
    available = folder.is_dir() and (Path(data["vault_path"]) / ".obsidian").is_dir()
    if available:
        overview = folder / "Project.md"
        available = overview.is_file() and properties(overview.read_text(encoding="utf-8")).get("project_id") == project_id
    return {"registered": True, "project_id": project_id, "name": entry["name"], "repository_root": str(root),
            "project_folder": str(folder), "available": available,
            "automation": {**AUTO_DEFAULTS, **data.get("automation", {})}, "mode": data["mode"]}


def read_task(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    match = FRONTMATTER.search(text)
    if not match:
        raise ValueError("Checkpoint has no metadata.")
    metadata = {}
    for line in match.group(1).splitlines():
        key, separator, value = line.partition(":")
        if separator:
            metadata[key] = json.loads(value.strip())
    required = {"type", "task_id", "project_id", "status", "updated", "agent", "branch", "revision", "dirty", "git_fingerprint"}
    if not required <= metadata.keys() or metadata["type"] != "task-checkpoint":
        raise ValueError("Incomplete checkpoint metadata.")
    if not TASK_ID.fullmatch(metadata["task_id"]) or path.stem != metadata["task_id"]:
        raise ValueError("Checkpoint ID does not match its filename.")
    data = dict(metadata)
    for key, heading in SECTIONS.items():
        section = re.search(rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)", text, re.M | re.S)
        if not section:
            raise ValueError("Incomplete checkpoint sections.")
        body = section.group(1).strip()
        data[key] = body if key == "objective" else [line[2:] for line in body.splitlines() if line.startswith("- ")]
    validate_payload({key: data[key] for key in ("objective", "status", "agent", *LIST_FIELDS)})
    if not isinstance(data["dirty"], bool) or not all(isinstance(data[key], str) for key in ("branch", "revision", "git_fingerprint", "project_id")):
        raise ValueError("Invalid checkpoint Git metadata.")
    data.update({"file": str(path), "saved_revision": digest(text)})
    return data


def tasks(folder: Path, project_id: str) -> tuple[list[dict], list[str]]:
    result, warnings = [], []
    for path in sorted((folder / "Tasks").glob("task-*.md")):
        try:
            contained(folder, "Tasks/" + path.name)
            item = read_task(path)
            if item["project_id"] != project_id:
                raise ValueError("Wrong project ID.")
            result.append(item)
        except (ValueError, OSError, TypeError, KeyError):
            warnings.append("Invalid checkpoint: Tasks/" + path.name)
    return result, warnings


def same_branch(task: dict, state: dict) -> bool:
    return task["branch"] == state["branch"] and (state["branch"] != "(detached)" or task["revision"] == state["revision"])


def resume(config: Path, repo: Path, query: str = "", task_id: str | None = None, code_paths: list[str] | None = None) -> dict:
    result = resolve(config, repo)
    if not result.get("registered"):
        return result
    state = snapshot(Path(result["repository_root"]))
    result.update({"git": state, "warnings": [], "selected_task": None, "task_candidates": []})
    if not result["available"]:
        result["warnings"].append("Configured vault or project overview is unavailable; project context was not loaded.")
        return result
    folder = Path(result["project_folder"])
    ranked = rank_context(folder, query, code_paths)
    result["foundational"] = [{**item, "path": str(contained(folder, item["file"]))} for item in ranked["foundational"]]
    result["notes"] = [{**item, "path": str(contained(folder, item["file"]))} for item in ranked["selected"]]
    for name in ("Project Home.md", "Current State.md", "Handoff.md"):
        if not (folder / name).is_file():
            result["warnings"].append("Missing project context: " + name)
    for item in result["foundational"]:
        props = properties(Path(item["path"]).read_text(encoding="utf-8"))
        if props.get("review_after"):
            try:
                if datetime.fromisoformat(props["review_after"]).date() < datetime.now(timezone.utc).date():
                    result["warnings"].append("Project note is due for evidence review: " + item["file"])
            except ValueError:
                result["warnings"].append("Invalid review date in " + item["file"])
    all_tasks, warnings = tasks(folder, result["project_id"])
    result["task_count"] = len(all_tasks)
    result["warnings"].extend(warnings)
    named = re.search(r"\btask-[0-9a-f]{12}\b", query)
    task_id = task_id or (named.group() if named else None)
    selected = None
    if task_id:
        selected = next((task for task in all_tasks if task["task_id"] == task_id), None)
        result["selection"] = "explicit" if selected else "task_not_found"
        if selected and not same_branch(selected, state):
            result["selection"] = "branch_mismatch"
            result["warnings"].append("Named task belongs to another branch or detached revision; do not resume it in this checkout.")
            selected = None
    else:
        eligible = [task for task in all_tasks if task["status"] != "completed" and same_branch(task, state)]
        meaningful = terms([query]) - {"continue", "resume", "please", "task", "work", "working", "the", "this", "project", "on", "with", "from", "where", "left", "off"}
        relevant = [task for task in eligible if meaningful & terms([task["objective"], *task["constraints"], *task["next_actions"]])] if meaningful else eligible
        result["task_candidates"] = [{key: task[key] for key in ("task_id", "objective", "status", "branch", "file", "saved_revision")} for task in relevant]
        result["selection"] = "ambiguous" if len(relevant) > 1 else "sole_relevant" if relevant else "no_matching_task"
        if len(relevant) == 1:
            selected = relevant[0]
    result["other_branch_tasks"] = [{key: task[key] for key in ("task_id", "objective", "branch")} for task in all_tasks if task["status"] != "completed" and not same_branch(task, state)]
    if selected:
        result["selected_task"] = selected
        if selected["git_fingerprint"] != state["git_fingerprint"]:
            result["warnings"].append("Checkout changed since the checkpoint; verify recorded progress and checks before continuing.")
    return result


def validate_payload(data: dict) -> None:
    allowed = {"objective", "status", "agent", "task_id", "expected_revision", *LIST_FIELDS}
    if not isinstance(data, dict) or set(data) - allowed:
        raise ValueError("Unsupported checkpoint fields; transcripts and arbitrary session data are not accepted.")
    if not isinstance(data.get("objective"), str) or not data["objective"].strip() or "\n" in data["objective"] or "\r" in data["objective"]:
        raise ValueError("objective must be a non-empty single-line summary.")
    if data.get("status") not in {"active", "blocked", "completed"} or data.get("agent") not in {"claude", "codex"}:
        raise ValueError("Checkpoint requires active/blocked/completed status and claude/codex agent.")
    for field in LIST_FIELDS:
        value = data.get(field)
        if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() or "\n" in item or "\r" in item for item in value):
            raise ValueError(field + " must be a list of non-empty single-line summaries.")
    serialized = json.dumps(data, ensure_ascii=False)
    if any(pattern.search(serialized) for pattern in SECRET_PATTERNS) or re.search(r"\b(?:Bearer\s+[A-Za-z0-9._~-]{12,}|(?:postgres(?:ql)?|mysql|redis)://[^\s/]+:[^\s@]+@)", serialized, re.I):
        raise ValueError("Possible credential-like content; checkpoint was not saved. Values withheld.")
    if UNIX_PATH.search(serialized) or WINDOWS_PATH.search(serialized):
        raise ValueError("Use repository-relative paths in checkpoints; keep machine paths in local configuration.")
    if data.get("task_id") is not None and (not isinstance(data["task_id"], str) or not TASK_ID.fullmatch(data["task_id"])):
        raise ValueError("Invalid task ID.")
    if data.get("expected_revision") is not None and (not isinstance(data["expected_revision"], str) or not re.fullmatch(r"[0-9a-f]{64}", data["expected_revision"])):
        raise ValueError("Invalid saved revision.")
    if any(not re.fullmatch(r"\[\[[^\]\n]+\]\]", link) for link in data["decision_links"]):
        raise ValueError("decision_links must contain Obsidian wikilinks to reviewed notes.")


def render_task(data: dict) -> str:
    metadata = ("type", "task_id", "project_id", "status", "updated", "agent", "branch", "revision", "dirty", "git_fingerprint")
    lines = ["---", *(key + ": " + json.dumps(data[key], ensure_ascii=False) for key in metadata), "---", "", "# Task checkpoint", ""]
    for key, heading in SECTIONS.items():
        lines.extend(["## " + heading, ""])
        lines.extend([data[key]] if key == "objective" else ["- " + item for item in data[key]])
        lines.append("")
    return "\n".join(lines)


def managed(text: str, block: str, marker: str = "project-memory") -> str:
    start, end = "<!-- " + marker + ":start -->", "<!-- " + marker + ":end -->"
    if text.count(start) != text.count(end) or text.count(start) > 1:
        raise ValueError("Malformed or duplicate managed project-memory block; preserve the file for review.")
    if start in text:
        return re.sub(re.escape(start) + r".*?" + re.escape(end), lambda _: block.rstrip(), text, count=1, flags=re.S)
    return text + ("" if text.endswith("\n\n") or not text else "\n" if text.endswith("\n") else "\n\n") + block.rstrip() + "\n"


def update_handoff(folder: Path, project_id: str) -> bool:
    path = contained(folder, "Handoff.md")
    original = path.read_text(encoding="utf-8") if path.exists() else (SKILL / "assets/handoff.md").read_text().replace("{{project_id}}", project_id).replace("{{date}}", datetime.now(timezone.utc).date().isoformat())
    current, _ = tasks(folder, project_id)
    active = [item for item in current if item["status"] != "completed"]
    lines = ["<!-- project-memory:tasks:start -->", "## Active task checkpoints", "",
             "Progress below is branch-scoped. Verify the checkout before resuming.", ""]
    lines.extend("- [[Tasks/" + item["task_id"] + "]] - " + item["objective"] + " (" + item["status"] + ", branch `" + item["branch"] + "`)." for item in active)
    if not active:
        lines.append("No active task checkpoints.")
    lines.extend(["", "<!-- project-memory:tasks:end -->"])
    return atomic_write(path, managed(original, "\n".join(lines), "project-memory:tasks"))


def checkpoint(config: Path, repo: Path, payload: dict) -> dict:
    validate_payload(payload)
    result = resolve(config, repo)
    if not result.get("registered") or not result.get("available"):
        raise ValueError("Registered project context is unavailable; checkpoint was not saved.")
    if not result["automation"]["save_progress"]:
        raise ValueError("Automatic checkpoints are disabled; enable save_progress before saving.")
    folder, root = Path(result["project_folder"]), Path(result["repository_root"])
    with project_lock(config, result["project_id"]):
        state = snapshot(root)
        task_id = payload.get("task_id") or "task-" + uuid.uuid4().hex[:12]
        path = contained(folder, "Tasks/" + task_id + ".md")
        previous = read_task(path) if path.exists() else None
        if previous:
            if previous["project_id"] != result["project_id"] or not same_branch(previous, state):
                raise ValueError("Checkpoint belongs to another project, branch, or detached revision.")
            if payload.get("expected_revision") != previous["saved_revision"]:
                raise ValueError("Stale checkpoint revision; resume and reconcile the latest checkpoint before retrying.")
        elif payload.get("task_id") or payload.get("expected_revision"):
            raise ValueError("Existing task checkpoint not found; do not silently recreate it.")
        for link in payload["decision_links"]:
            target = link[2:-2].split("|", 1)[0].split("#", 1)[0]
            candidate = contained(folder, target if target.endswith(".md") else target + ".md")
            if not candidate.is_file():
                raise ValueError("Decision link does not resolve inside this project.")
        data = {key: payload[key] for key in ("objective", "status", "agent", *LIST_FIELDS)}
        data.update(state)
        for changed in data["changed_paths"]:
            # Git paths can name deleted files; validate containment without resolving symlinks.
            if PurePosixPath(changed).is_absolute() or ".." in PurePosixPath(changed).parts or "\n" in changed:
                raise ValueError("Invalid repository-relative changed path.")
        data.update({"type": "task-checkpoint", "task_id": task_id, "project_id": result["project_id"],
                     "updated": datetime.now(timezone.utc).replace(microsecond=0).isoformat()})
        comparable = [key for key in data if key not in {"updated", "agent"}]
        unchanged = previous is not None and all(previous.get(key) == data[key] for key in comparable)
        text = path.read_text(encoding="utf-8") if unchanged else render_task(data)
        if not unchanged:
            atomic_write(path, text)
        warnings = []
        try:
            handoff_updated = update_handoff(folder, result["project_id"])
        except (OSError, ValueError):
            handoff_updated = False
            warnings.append("Checkpoint saved, but the handoff index could not be updated; inspect Handoff.md.")
        return {"task_id": task_id, "saved_revision": digest(text), "file": str(path), "unchanged": unchanged,
                "handoff_updated": handoff_updated, "warnings": warnings}


def install(config: Path, registrations: dict | None = None, enable: bool = False,
            home: Path | None = None, codex_home: Path | None = None, dry_run: bool = False) -> dict:
    home = home or Path.home()
    codex_home = codex_home or Path(os.environ.get("CODEX_HOME", str(home / ".codex")))
    with project_lock(config, "install"):
        data = load_config(config)
        for key, value in (registrations or {}).items():
            if key in data["projects"] and data["projects"][key] != value:
                raise ValueError("Registration differs from an existing project; reconcile it explicitly before installing.")
            data["projects"][key] = value
        if enable:
            data["automation"] = dict.fromkeys(AUTO_DEFAULTS, True)
        # Validate the merged configuration before any instructions or config are changed.
        validate_config(data)
        if not (Path(data["vault_path"]) / ".obsidian").is_dir():
            raise ValueError("Configured Obsidian vault is unavailable; installation did not change instructions.")
        planned: dict[Path, str] = {}

        def plan(path: Path, block: str, initial: str = "", within: Path | None = None):
            actual = path.resolve()
            if within is not None and not actual.is_relative_to(within.resolve()):
                raise ValueError("Instruction symlink points outside its repository; inspect it before installation.")
            text = planned.get(actual, actual.read_text(encoding="utf-8") if actual.exists() else initial)
            planned[actual] = managed(text, block)

        template = (SKILL / "assets/project-memory.md").read_text(encoding="utf-8")
        for project_id, entry in data["projects"].items():
            if not PROJECT_ID.fullmatch(project_id) or any(not isinstance(entry.get(key), str) or not entry[key] for key in ("name", "repo_path", "vault_folder")):
                raise ValueError("Invalid registration supplied to installer.")
            root, _ = git_identity(Path(entry["repo_path"]))
            if root != Path(entry["repo_path"]).resolve():
                raise ValueError("Register the repository root, not a nested directory or worktree subfolder.")
            folder = contained(Path(data["vault_path"]), entry["vault_folder"])
            overview = folder / "Project.md"
            if not overview.is_file() or properties(overview.read_text()).get("project_id") != project_id:
                raise ValueError("Registration does not match its vault Project.md.")
            block = template.replace("{{project_id}}", project_id)
            override = root / "AGENTS.override.md"
            agents = override if override.exists() and override.read_text().strip() else root / "AGENTS.md"
            claude = root / "CLAUDE.md"
            if not claude.exists() and (root / ".claude/CLAUDE.md").exists():
                claude = root / ".claude/CLAUDE.md"
            initial = "# Repository instructions\n\nRead `CLAUDE.md` for this repository's existing build, test, and operational conventions.\n" if not agents.exists() and claude.exists() else ""
            plan(agents, block, initial, root)
            if claude.is_symlink():
                plan(claude, block, within=root)
            elif claude.exists():
                imports_agents = re.search(r"^\s*@(?:\./)?(?:AGENTS(?:\.override)?\.md)\s*$", claude.read_text(), re.M)
                if imports_agents:
                    imported = root / imports_agents.group().strip()[1:].removeprefix("./")
                    plan(imported, block, within=root)
                else:
                    plan(claude, block, within=root)
            else:
                planned[claude] = "@" + agents.name + "\n"
        global_block = (SKILL / "assets/global-project-memory.md").read_text(encoding="utf-8")
        override = codex_home / "AGENTS.override.md"
        plan(override if override.exists() and override.read_text().strip() else codex_home / "AGENTS.md", global_block)
        plan(home / ".claude/CLAUDE.md", global_block)
        planned[config.resolve()] = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
        changed = [str(path) for path, text in planned.items() if not path.exists() or path.read_text(encoding="utf-8") != text]
        if not dry_run:
            for path, text in planned.items():
                atomic_write(path, text)
        return {"projects": sorted(data["projects"]), "changed_files": changed, "dry_run": dry_run,
                "automation": {**AUTO_DEFAULTS, **data.get("automation", {})}}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=config_location())
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("resolve", "resume", "checkpoint"):
        command = sub.add_parser(name)
        command.add_argument("--repo", type=Path, default=Path.cwd())
        if name == "resume":
            command.add_argument("--query", default="")
            command.add_argument("--task-id")
            command.add_argument("--code-path", action="append", default=[])
    command = sub.add_parser("install")
    command.add_argument("--registrations", type=Path, help="JSON object keyed by project ID; existing registrations are preserved")
    command.add_argument("--enable-automation", action="store_true")
    command.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        if args.command == "resolve":
            result = resolve(args.config, args.repo)
        elif args.command == "resume":
            result = resume(args.config, args.repo, args.query, args.task_id, args.code_path)
        elif args.command == "checkpoint":
            raw = sys.stdin.read(65537)
            if len(raw) > 65536:
                raise ValueError("Checkpoint input exceeds 64 KiB; provide a concise summary.")
            result = checkpoint(args.config, args.repo, json.loads(raw))
        else:
            registrations = json.loads(args.registrations.read_text()) if args.registrations else None
            result = install(args.config, registrations, args.enable_automation, dry_run=args.dry_run)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except (ValueError, OSError, KeyError, TypeError, subprocess.TimeoutExpired):
        # Never echo JSON input, file content, or subprocess output in errors.
        error = sys.exc_info()[1]
        message = str(error) if type(error) is ValueError else "Project memory operation failed; inspect configuration, permissions, and input shape. Values withheld."
        print(json.dumps({"error": message}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
