#!/usr/bin/env bash
# Run one worker agent (codex or agy) on one brief, in its own git worktree, then run the checks
# and print a short report.
#
# Usage: run_worker.sh <codex|agy> <task-id> <brief-file> [--repo DIR] [--base REF] [--model NAME]
#                      [--check CMD]... [--allow GLOB]...
#
# The worker edits files in the worktree and does not commit. The caller reads the report,
# commits and merges. --check runs a command in the worktree after the worker (repeatable).
# --allow limits the files the worker may change; "*" also matches "/" (repeatable).
# Environment: DISPATCH_TIMEOUT (worker, default 1800 s), DISPATCH_CHECK_TIMEOUT (each check,
# default 600 s).
# Exit code: 0 done and clean, 3 needs review, 75 usage limit (try another agent),
# 1 worker failure or time limit, 2 bad usage.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PREAMBLE="$SCRIPT_DIR/../assets/worker-preamble.md"
SCHEMA="$SCRIPT_DIR/../assets/result-schema.json"
# agy takes the prompt as one argument, and Linux limits one argument to 128 KiB.
MAX_PROMPT_BYTES=100000

die() { echo "[ERROR] $1" >&2; exit "${2:-1}"; }
info() { echo "[INFO] $*"; }

USAGE="Usage: run_worker.sh <codex|agy> <task-id> <brief-file> [--repo DIR] [--base REF] [--model NAME] [--check CMD]... [--allow GLOB]..."
[ $# -ge 3 ] || die "$USAGE" 2

AGENT="$1"; TASK="$2"; BRIEF="$3"; shift 3
REPO=""; BASE="HEAD"; MODEL=""; CHECKS=(); ALLOW=()
while [ $# -gt 0 ]; do
    case "$1" in
        --repo)  REPO="${2:?--repo needs a value}"; shift 2 ;;
        --base)  BASE="${2:?--base needs a value}"; shift 2 ;;
        --model) MODEL="${2:?--model needs a value}"; shift 2 ;;
        --check) CHECKS+=("${2:?--check needs a value}"); shift 2 ;;
        --allow) ALLOW+=("${2:?--allow needs a value}"); shift 2 ;;
        *) die "Unknown option: $1" 2 ;;
    esac
done

case "$AGENT" in codex|agy) ;; *) die "Agent must be codex or agy, not '$AGENT'" 2 ;; esac
[[ "$TASK" =~ ^[a-z0-9][a-z0-9._-]*$ ]] || die "Task id must match [a-z0-9][a-z0-9._-]*" 2
[ -f "$BRIEF" ] || die "Brief file not found: $BRIEF" 2
[ -f "$PREAMBLE" ] && [ -f "$SCHEMA" ] || die "Skill assets are missing in $SCRIPT_DIR/../assets"
command -v python3 >/dev/null || die "python3 is required for the report"

REPO="$(git -C "${REPO:-.}" rev-parse --show-toplevel)" || die "Not a git repository"

# .profile puts the mise shims on PATH; "mise which" covers a shell without them.
AGENT_BIN="$(command -v "$AGENT" 2>/dev/null || mise which "$AGENT" 2>/dev/null || true)"
[ -n "$AGENT_BIN" ] || die "$AGENT is not installed or not on PATH"
# codex is a node script, so its folder (which holds node) must be on PATH.
export PATH="$(dirname "$AGENT_BIN"):$PATH"

WT_ROOT="$(dirname "$REPO")/$(basename "$REPO")-wt"
WT="$WT_ROOT/$TASK"
BRANCH="agent/$TASK"
OUT="$WT_ROOT/.out"
mkdir -p "$OUT"

if [ -d "$WT" ]; then
    info "Reusing worktree $WT (earlier edits stay in place)"
else
    git -C "$REPO" worktree add -b "$BRANCH" "$WT" "$BASE" >/dev/null 2>&1 \
        || die "Could not create worktree $WT on branch $BRANCH"
    info "Created worktree $WT on branch $BRANCH"
fi
START="$(git -C "$WT" rev-parse HEAD)"

P="$OUT/$TASK.$AGENT"
PROMPT="$P.prompt.md"; RAW="$P.raw"; RESULT="$P.result.json"; LOG="$P.log"
CHECK_LOG="$P.checks.jsonl"; SUMMARY="$P.summary.json"
{
    cat "$PREAMBLE"
    # Headless agy denies every shell command and then ends the turn with no reply.
    if [ "$AGENT" = agy ]; then
        printf '\nThis run cannot execute shell commands. Do not try to run any command, not even to read files or run tests. Use only your file tools to read and edit files.\n'
    fi
    printf '\n\n'
    cat "$BRIEF"
} > "$PROMPT"
: > "$RESULT"; : > "$CHECK_LOG"
if [ "$AGENT" = agy ] && [ "$(wc -c < "$PROMPT")" -gt "$MAX_PROMPT_BYTES" ]; then
    die "The brief is too large for agy (limit $MAX_PROMPT_BYTES bytes with the preamble). Shorten it." 2
fi

info "Starting $AGENT on task $TASK"
set +e
case "$AGENT" in
    codex)
        timeout "${DISPATCH_TIMEOUT:-1800}" "$AGENT_BIN" exec -C "$WT" -s workspace-write --json \
            --output-schema "$SCHEMA" -o "$RESULT" ${MODEL:+-m "$MODEL"} - < "$PROMPT" > "$RAW" 2> "$LOG"
        ;;
    agy)
        (cd "$WT" && timeout "${DISPATCH_TIMEOUT:-1800}" "$AGENT_BIN" -p "$(cat "$PROMPT")" \
            --mode accept-edits --output-format json --json-schema "$SCHEMA" ${MODEL:+--model "$MODEL"}) \
            > "$RAW" 2> "$LOG"
        ;;
esac
STATUS=$?

# Run the checks only when the worker finished; a failed run has nothing to check.
if [ "$STATUS" -eq 0 ]; then
    for cmd in "${CHECKS[@]}"; do
        out="$(cd "$WT" && timeout "${DISPATCH_CHECK_TIMEOUT:-600}" bash -c "$cmd" 2>&1)"
        rc=$?
        python3 -c 'import json,sys; c,r,o=sys.argv[1],int(sys.argv[2]),sys.argv[3]
print(json.dumps({"cmd":c,"exit":r,"tail":o.splitlines()[-20:] if r else []}))' "$cmd" "$rc" "$out" >> "$CHECK_LOG"
    done
fi
set -e

ALLOW_ARGS=()
for glob in "${ALLOW[@]}"; do ALLOW_ARGS+=(--allow "$glob"); done

echo "---"
exec python3 "$SCRIPT_DIR/worker_report.py" --agent "$AGENT" --task "$TASK" --status "$STATUS" \
    --worktree "$WT" --branch "$BRANCH" --base "$START" --raw "$RAW" --result "$RESULT" --log "$LOG" \
    --checks "$CHECK_LOG" --summary "$SUMMARY" "${ALLOW_ARGS[@]}"
