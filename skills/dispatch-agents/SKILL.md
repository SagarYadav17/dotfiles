---
name: dispatch-agents
description: Orchestrate coding work with Codex CLI workers. Claude plans, splits the work, sends each task to Codex in its own git worktree, then reviews a short report and merges. Use when the user asks to delegate, dispatch or parallelize coding tasks to Codex, or to save Claude usage on large coding work.
---

# Dispatch Agents

Claude is the orchestrator. Codex is the worker. Claude plans, writes the briefs, reads the reports and merges. Codex writes the code. `scripts/run_worker.sh` does the mechanical work: worktree, worker run, checks and diff flags. A script costs no tokens, so Claude reads only a short report.

Use this skill only for tasks that are large enough to repay the cost of a brief and a review. Do small edits yourself.

**This skill or the Codex plugin?** The Codex plugin (`codex:codex-rescue`, `/codex:rescue`) sends one request to Codex in the current checkout. It has no worktree, no checks and no allow-list. Use it for a second opinion, a diagnosis or a one-off fix that you review yourself. Use this skill when there are several tasks, when tasks must not touch the main checkout, or when the work must pass checks before a merge.

## Before you start

1. Make sure Codex has capacity. The newest file in `~/.codex/sessions/` holds `rate_limits` with `used_percent` and `resets_at`. If you cannot tell, ask the user.
2. Make sure the repository has a clean working tree and a known base branch. Run `git status --short`.
3. `python3` must be on `PATH`. The script finds `codex` on `PATH` or through `mise which`.

## Split the work

1. Split the goal into tasks that can run on their own.
2. Two tasks must not change the same file. If they must, run them one after the other or join them into one task.
3. Each task needs a check that a machine can run (a test, a type check, a build). If there is none, write the check first or do the task yourself.
4. Give each task a short id: lower case, digits, `.`, `_`, `-` (for example `api-pagination`).
5. Give the whole goal an id too, and make one local integration branch for it: `git branch dispatch/<goal-id> <base-branch>`. All task branches start from it and merge back into it. The base branch gets only one squashed commit at the end (see "Review and merge").

## Write the brief

The worker does not see this conversation. Write the brief to a file in `$TMPDIR`, in short and clear sentences. The brief states:

- **Goal:** one or two sentences.
- **Files:** the files to read and change. Name the files that the worker must not change.
- **Rules:** conventions that the worker cannot guess from the code.
- **Checks:** the exact commands that must pass.
- **Done:** what the finished result looks like.

To fill **Rules** cheaply: if the project is registered in `curate-project-memory`, run one context pack for the goal and copy the relevant decisions and constraints into the brief. Do this once for all tasks, not once per task.

Codex reads the same skills as Claude, through `~/.agents/skills`. To make the worker follow a skill, name it in the brief, for example "Use the skill `bruno-api-docs`". Then the brief can be shorter.

`assets/worker-preamble.md` is added to every brief by the script. It tells the worker:

- to stay in its directory and not to commit,
- to use a skill only when the brief names it,
- not to use project memory or `dispatch-agents`,
- to reply in the JSON format of `assets/result-schema.json`.

## Send the task

Run the script in the background for each task, so that tasks run at the same time:

```bash
scripts/run_worker.sh <task-id> <brief-file> \
    --base dispatch/<goal-id> \
    --check '<command>' [--check '<command>']... \
    --allow '<glob>' [--allow '<glob>']... \
    [--review] [--repo DIR] [--model NAME]
```

- `--check` runs a command in the worktree after the worker stops. Always give the checks from the brief. The worker's own report about checks is not proof.
- `--allow` lists the files that the worker may change. `*` also matches `/`, so `src/*` covers all of `src/`.
- `--base dispatch/<goal-id>` starts the task from the integration branch. Always give it.
- `--review` starts a new Codex session (`codex exec review --uncommitted`) to review the worktree changes after the checks pass. The report shows the first 600 characters, and the full text is in `<task-id>.review.md`. The review uses Codex usage, not Claude tokens. Use it for risky tasks. The review is advice: it does not change the exit code.

The script:

1. Creates the worktree `<repo>-wt/<task-id>` on the branch `agent/<task-id>`, or reuses it.
2. Runs Codex with `-s workspace-write`.
3. Runs each check, then compares the diff with the allow-list.
4. Writes all files to `<repo>-wt/.out/<task-id>.*` and prints a short report.

`DISPATCH_TIMEOUT` sets the time limit of the worker in seconds (default 1800). `DISPATCH_CHECK_TIMEOUT` sets the limit of each check (default 600).

| Exit code | Meaning | Action |
|-----------|---------|--------|
| 0 | The worker reported `done`. All checks passed. There are no flags. | Commit and merge (see below). |
| 3 | Review needed: a check failed, a flag is set, or the worker reported `partial`, `blocked` or no result. | Read only the lines in the report. Then fix the brief and run again, or fix it yourself. |
| 75 | Codex reached its usage limit. | Tell the user the reset time. Do the task yourself only if the user agrees. The worktree keeps any partial edits. |
| 1 | The worker failed or passed its time limit. | Read the `error:` lines. Read the log only when they do not explain the failure. |
| 2 | Bad arguments. | Fix the command. |

A second run with the same task id reuses the worktree. Tell Codex in the brief what is already done.

## The report

The report is a few lines, for example:

```
task: api-pagination  outcome: done  exit: 3
tokens: input_tokens=48781 output_tokens=367
changed (2): src/api.py, tests/test_api.py
flag: test-edited: tests/test_api.py (lines removed or changed)
check: PASS  pytest -q
worker: done  open: none
```

The flags are:

- `outside-allow`: a changed file that no `--allow` glob covers.
- `test-edited`: an existing test file with removed or changed lines. New tests and added lines get no flag.
- `dependency-file`: a changed manifest or lockfile, such as `package.json` or `uv.lock`.
- `worker-commits`: the worker made commits, against the rules.

The full data is in `<task-id>.summary.json`.

## Discord notices (optional)

If a Discord webhook URL is in `~/.config/dispatch-agents/discord-webhook` (or in `DISPATCH_DISCORD_WEBHOOK`), the script posts one line to the channel:

- when a task starts: the task id and the first line of the brief's **Goal**,
- when a task ends: the outcome, the exit code, the checks passed, the tokens and the flag names.

Without a URL, nothing is posted. A failed post prints a warning and does not stop the work. The lines never hold code, diffs, logs, error text or file paths. Never write secrets or customer data in the **Goal** line, because that line goes to Discord.

When a goal is finished, post the end notice:

```bash
scripts/notify.py goal --goal <goal-id> --text "3 tasks · 1 squashed commit · not pushed"
```

The notices are for the user only. Agents do not read them. Agents pass data only through the files in `.out/`.

## Review and merge

Read the report first. Read more only where the report points:

1. Exit 0: read `git -C <worktree> diff --stat` and the Codex review, if you asked for one. Read the full diff only for files that are risky for this project, or where the review found a problem.
2. A flag: read the diff of the flagged files only.
3. A failed check: the report shows the last 20 lines. Read the full output only if those lines do not show the cause.
4. If the result is wrong, write a short follow-up brief and run the script again with the same task id.
5. If the result is right, commit in the worktree with a short message (`git -C <worktree> add -A && git -C <worktree> commit -m "<task-id>"`). This commit is local and temporary.
6. Merge the task branch into the integration branch: `git -C <integration-worktree> merge --no-ff agent/<task-id>`. Use a worktree for `dispatch/<goal-id>`, or check it out in the main checkout when that checkout is clean.
7. After all task merges, run the full checks on the integration branch.

Merge the tasks one at a time. Fix a merge conflict yourself. Do not give conflicts to a worker.

## Finish: one commit on the base branch

The task commits and merges stay local. The base branch gets the whole goal as one commit:

1. Check out the base branch in the main checkout. Make sure it is clean.
2. Run `git merge --squash dispatch/<goal-id>`. This stages all changes and makes no commit.
3. Run the full checks again.
4. Commit once. The message names the goal and lists each part in one line. Follow the repository's commit style.
5. Do not push. Push only when the user asks, and push only the base branch.

Never push `agent/*` or `dispatch/*` branches. Never squash or rewrite commits that are already on a remote.

## Clean up

After the squashed commit, the task and integration branches are not needed. Ask the user, then remove them:

```bash
git worktree remove <worktree>           # for each task, and for the integration worktree
git branch -D agent/<task-id>            # for each task
git branch -D dispatch/<goal-id>
```

`-D` is necessary because a squash merge does not mark the branches as merged. Before you delete a branch, make sure the squashed commit holds its changes: `git diff dispatch/<goal-id> <base-branch>` must show no difference.

## Limits

- Codex runs without prompts, in its sandbox. It can change only files in its worktree. Do not use options that remove the sandbox (`--dangerously-bypass-approvals-and-sandbox`).
- The script finds a usage limit by words such as `usage limit`, `quota`, `429` and `402`. It searches only Codex's own error messages, not tool output. The real Codex limit message is not tested yet. If Codex reports a limit in other words, the script returns 1.
- Codex can use the network only as its sandbox allows. A task that needs the network (install a package, call an API) is better done by you.
- Do not put secrets in a brief. The brief is saved in `.out/`.
