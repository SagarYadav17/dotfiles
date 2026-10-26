#!/usr/bin/env python3
"""Make the short report of one worker run. run_worker.sh calls this after the worker and the checks.

It reads the Codex JSONL events, the check results and the worktree diff. It writes
<out>/<task>.summary.json, prints a few lines for the orchestrator, and exits with the run's
final code.

Exit code: 0 done and clean, 3 needs review (check failed, flags, or status not done),
75 usage limit, 1 worker failure.
"""

import argparse
import fnmatch
import json
import re
import subprocess
import sys
from pathlib import Path

import notify

LIMIT_RE = re.compile(
    r"rate.?limit|usage limit|quota|too many requests|credits|exhausted|\b429\b|\b402\b", re.I
)
# Matches test files by folder (tests/, __tests__/, spec/) or by name (test_x.py, x_test.go, x.test.ts).
TEST_RE = re.compile(
    r"(^|/)(tests?|__tests__|spec|specs)/|(^|/)test_[^/]*$|_test\.[^/]+$|\.(test|spec)\.[^/]+$"
)
DEPENDENCY_FILES = {
    "package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lock", "bun.lockb",
    "pyproject.toml", "uv.lock", "poetry.lock", "Pipfile", "Pipfile.lock", "setup.py", "setup.cfg",
    "go.mod", "go.sum", "Cargo.toml", "Cargo.lock", "Gemfile", "Gemfile.lock",
    "composer.json", "composer.lock",
}


def read_json(path):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return None


def worker_output(events_path, result_path, log_path):
    """Return (structured result or None, token usage dict, Codex's own error messages)."""
    errors, usage = [], {}
    for line in Path(events_path).read_text(errors="replace").splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        kind = event.get("type")
        if kind == "turn.completed":
            usage = event.get("usage") or {}
        elif kind in ("error", "turn.failed"):
            error = event.get("error")
            errors.append(str(event.get("message") or (error or {}).get("message") or error or event))
    # Tool output goes to the events; stderr holds only Codex's own progress and error lines.
    log_tail = Path(log_path).read_text(errors="replace").splitlines()[-20:] if Path(log_path).exists() else []
    return read_json(result_path), usage, errors, log_tail


def changed_files(worktree, base):
    status = subprocess.run(
        ["git", "-C", worktree, "status", "--porcelain", "-uall"], capture_output=True, text=True
    ).stdout.splitlines()
    files = [line[3:].split(" -> ")[-1] for line in status if line.strip()]
    commits = subprocess.run(
        ["git", "-C", worktree, "rev-list", "--count", f"{base}..HEAD"], capture_output=True, text=True
    ).stdout.strip()
    # Tracked files with removed or changed lines. New tests and added lines are not a risk;
    # a weakened test always removes or changes a line.
    numstat = subprocess.run(
        ["git", "-C", worktree, "diff", "--numstat", base], capture_output=True, text=True
    ).stdout.splitlines()
    edited = {parts[2] for parts in (line.split("\t") for line in numstat) if len(parts) == 3 and parts[1] not in ("0", "-")}
    return files, int(commits or 0), edited


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True)
    parser.add_argument("--status", type=int, required=True, help="exit code of the worker")
    parser.add_argument("--worktree", required=True)
    parser.add_argument("--branch", required=True)
    parser.add_argument("--base", required=True, help="commit the worktree started from")
    parser.add_argument("--events", required=True)
    parser.add_argument("--result", required=True)
    parser.add_argument("--log", required=True)
    parser.add_argument("--checks", required=True, help="JSON lines from run_worker.sh, one per check")
    parser.add_argument("--allow", action="append", default=[])
    parser.add_argument("--summary", required=True)
    parser.add_argument("--review", help="Codex review file, when --review was given")
    args = parser.parse_args()
    review = None
    if args.review:
        review = Path(args.review).read_text(errors="replace").strip() if Path(args.review).is_file() else "not run (Codex review failed)"

    result, usage, errors, log_tail = worker_output(args.events, args.result, args.log)
    files, commits, edited = changed_files(args.worktree, args.base)
    checks = [json.loads(line) for line in Path(args.checks).read_text().splitlines() if line.strip()]

    flags = []
    if args.allow:
        outside = [f for f in files if not any(fnmatch.fnmatch(f, glob) for glob in args.allow)]
        flags += [f"outside-allow: {f}" for f in outside]
    flags += [f"test-edited: {f} (lines removed or changed)" for f in files if TEST_RE.search(f) and f in edited]
    flags += [f"dependency-file: {f}" for f in files if Path(f).name in DEPENDENCY_FILES]
    if commits:
        flags.append(f"worker-commits: {commits} commit(s) on {args.branch}")

    if args.status == 124:
        outcome, code = "timeout", 1
    elif args.status != 0:
        if not errors:
            errors = [line for line in log_tail if line.strip()][-3:]
        limit = any(LIMIT_RE.search(message) for message in errors)
        outcome, code = ("limit", 75) if limit else ("failed", 1)
    else:
        if not result:
            # The worker ended without a reply.
            errors = [line for line in log_tail if line.strip()][-3:]
        worker_status = (result or {}).get("status", "no-result")
        failed_checks = [c for c in checks if c["exit"] != 0]
        clean = worker_status == "done" and not failed_checks and not flags
        outcome, code = worker_status, (0 if clean else 3)

    summary = {
        "task": args.task, "outcome": outcome, "exit": code,
        "worktree": args.worktree, "branch": args.branch,
        "changed": files, "flags": flags, "checks": checks,
        "worker": result, "review": review, "usage": usage, "errors": errors,
        "log": args.log, "result": args.result, "review_file": args.review,
    }
    Path(args.summary).write_text(json.dumps(summary, indent=2) + "\n")
    notify.send(notify.finished_text(summary))

    tokens = " ".join(f"{k}={v}" for k, v in usage.items() if k in ("input_tokens", "output_tokens", "total_tokens"))
    print(f"task: {args.task}  outcome: {outcome}  exit: {code}")
    print(f"worktree: {args.worktree}  branch: {args.branch}")
    if tokens:
        print(f"tokens: {tokens}")
    print(f"changed ({len(files)}): {', '.join(files) or 'none'}")
    for flag in flags:
        print(f"flag: {flag}")
    for check in checks:
        state = "PASS" if check["exit"] == 0 else f"FAIL (exit {check['exit']})"
        print(f"check: {state}  {check['cmd']}")
        for line in check.get("tail", []):
            print(f"  | {line}")
    if result:
        print(f"worker: {result.get('status')}  open: {result.get('open')}")
    if review is not None:
        # Long reviews stay in the file; the first 600 characters show the verdict.
        print(f"review: {review[:600]}{' […]' if len(review) > 600 else ''}")
    for message in errors:
        print(f"error: {message[:300]}")
    if code == 1 and not errors:
        print(f"read the log: {args.log}")
    print(f"summary: {args.summary}")
    return code


if __name__ == "__main__":
    sys.exit(main())
