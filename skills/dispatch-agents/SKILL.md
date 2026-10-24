---
name: dispatch-agents
description: Orchestrate coding work across worker agents (Codex CLI and Antigravity CLI, agy). Claude plans, splits the work, sends each task to a worker in its own git worktree, then reviews the diff and merges. Use when the user asks to delegate, dispatch or parallelize coding tasks to codex or agy, or to spread work across subscriptions by available usage.
---

# Dispatch Agents

Claude is the orchestrator. Codex and `agy` are workers. Claude plans, writes the briefs, reviews the diffs and merges. The workers write the code.

Use this skill only for tasks that are large enough to repay the cost of a brief and a review. Do small edits yourself.

## Before you start

1. Ask the user which workers have capacity now, and any preference (for example "codex first"). Claude cannot read the usage of other tools.
2. Make sure the repository has a clean working tree and a known base branch. Run `git status --short`.
3. Run `command -v codex agy` only to see what is on `PATH`. `scripts/run_worker.sh` also finds `codex` under `mise`.

## Split the work

1. Split the goal into tasks that can run on their own.
2. Two tasks must not change the same file. If they must, run them one after the other or give both to one worker.
3. A task must have a check that a machine can run (a test, a type check, a build). If there is none, write the check first or do the task yourself.
4. Give each task a short id: lower case, digits, `.`, `_`, `-` (for example `api-pagination`).

## Write the brief

The worker does not see this conversation. Write the brief to a file in `$TMPDIR`. The brief states:

- **Goal:** one or two sentences.
- **Files:** the files to read and change. Name the files that the worker must not change.
- **Rules:** conventions that the worker cannot guess from the code.
- **Checks:** the exact commands that must pass.
- **Done:** what the finished result looks like.

`assets/worker-preamble.md` is added to every brief by the script. It tells the worker not to commit, to stay in its directory, and to end with `Changed`, `Checks` and `Open`.

## Send the task

Run the script in the background for each task, so that tasks run at the same time:

```bash
scripts/run_worker.sh <codex|agy> <task-id> <brief-file> [--repo DIR] [--base REF] [--model NAME]
```

The script:

1. Creates the worktree `<repo>-wt/<task-id>` on the branch `agent/<task-id>`.
2. Runs the worker there. Codex uses `-s workspace-write`. `agy` uses `--mode accept-edits`.
3. Writes the prompt, the log and the final reply to `<repo>-wt/.out/`.
4. Prints the changed files.

`DISPATCH_TIMEOUT` sets the time limit in seconds (default 1800).

| Exit code | Meaning | Action |
|-----------|---------|--------|
| 0 | The worker finished. | Review the result. |
| 75 | The worker reached its usage limit. | Tell the user. Send the task to the other worker. The worktree keeps any partial edits. |
| 1 | Other failure, or time limit. | Read the log. Fix the brief or split the task. |
| 2 | Bad arguments. | Fix the command. |

If a task goes to a second worker after code 75, the same worktree is reused. Read the partial diff first. Then tell the second worker in the brief what is already done.

## Review and merge

Do not trust the worker's report. For each task:

1. Read the final reply in `.out/<task-id>.<agent>.result.md`.
2. Read the full diff: `git -C <worktree> diff` (also `git status` for new files).
3. Run the checks yourself in the worktree.
4. Look for edited tests, new dependencies and changes outside the named files. Reject these unless the brief allowed them.
5. If the result is wrong, write a short follow-up brief and run the script again with the same task id and the same or the other worker.
6. If the result is right, commit in the worktree (`git -C <worktree> add -A && git -C <worktree> commit`), then merge the branch `agent/<task-id>` into the base branch.
7. After all merges, run the full checks on the base branch.

Merge the tasks one at a time. Fix a merge conflict yourself. Do not give conflicts to a worker.

## Clean up

When the user accepts the result, remove each worktree and branch:

```bash
git worktree remove <worktree> && git branch -d agent/<task-id>
```

Ask the user first. Never delete a worktree that holds work that is not merged.

## Limits

- Workers run with a sandbox and without prompts. They can change only files in their worktree. Do not use options that remove the sandbox (`--dangerously-bypass-approvals-and-sandbox`, `--dangerously-skip-permissions`).
- Workers can use the network only as their sandbox allows. A task that needs the network (install a package, call an API) is better done by you.
- Do not put secrets in a brief. The brief is saved in `.out/`.
- The script has not been tested for the usage-limit path (exit 75). It matches words such as `rate limit`, `quota` and `429` in the log after a failure. If an agent reports a limit in other words, the script returns 1. Read the log.
