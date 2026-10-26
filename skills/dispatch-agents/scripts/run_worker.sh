#!/usr/bin/env bash
# Run Codex as a worker on one brief, in its own git worktree, then run the checks and print a
# short report.
#
# Usage: run_worker.sh <task-id> <brief-file> [--repo DIR] [--base REF] [--model NAME]
#                      [--check CMD]... [--allow GLOB]... [--review]
#
# The worker edits files in the worktree and does not commit. The caller reads the report,
# commits and merges. --check runs a command in the worktree after the worker (repeatable).
# --allow limits the files the worker may change; "*" also matches "/" (repeatable).
# --review asks Codex ("codex exec review") to review the worktree changes; it uses Codex usage.
# Environment: DISPATCH_TIMEOUT (worker, default 1800 s), DISPATCH_CHECK_TIMEOUT (each check,
# default 600 s).
# Exit code: 0 done and clean, 3 needs review, 75 usage limit (wait for the reset),
# 1 worker failure or time limit, 2 bad usage.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PREAMBLE="$SCRIPT_DIR/../assets/worker-preamble.md"
SCHEMA="$SCRIPT_DIR/../assets/result-schema.json"

die() { echo "[ERROR] $1" >&2; exit "${2:-1}"; }
info() { echo "[INFO] $*"; }

USAGE="Usage: run_worker.sh <task-id> <brief-file> [--repo DIR] [--base REF] [--model NAME] [--check CMD]... [--allow GLOB]... [--review]"
[ $# -ge 2 ] || die "$USAGE" 2
case "$1" in codex|agy) die "The agent argument was removed; Codex is the only worker. $USAGE" 2 ;; esac

TASK="$1"; BRIEF="$2"; shift 2
REPO=""; BASE="HEAD"; MODEL=""; CHECKS=(); ALLOW=(); REVIEW=""
while [ $# -gt 0 ]; do
    case "$1" in
        --repo)  REPO="${2:?--repo needs a value}"; shift 2 ;;
        --base)  BASE="${2:?--base needs a value}"; shift 2 ;;
        --model) MODEL="${2:?--model needs a value}"; shift 2 ;;
        --check) CHECKS+=("${2:?--check needs a value}"); shift 2 ;;
        --allow) ALLOW+=("${2:?--allow needs a value}"); shift 2 ;;
        --review) REVIEW=1; shift ;;
        *) die "Unknown option: $1" 2 ;;
    esac
done

[[ "$TASK" =~ ^[a-z0-9][a-z0-9._-]*$ ]] || die "Task id must match [a-z0-9][a-z0-9._-]*" 2
[ -f "$BRIEF" ] || die "Brief file not found: $BRIEF" 2
[ -f "$PREAMBLE" ] && [ -f "$SCHEMA" ] || die "Skill assets are missing in $SCRIPT_DIR/../assets"
command -v python3 >/dev/null || die "python3 is required for the report"

REPO="$(git -C "${REPO:-.}" rev-parse --show-toplevel)" || die "Not a git repository"

# .profile puts the mise shims on PATH; "mise which" covers a shell without them.
CODEX="$(command -v codex 2>/dev/null || mise which codex 2>/dev/null || true)"
[ -n "$CODEX" ] || die "codex is not installed or not on PATH"
# codex is a node script, so its folder (which holds node) must be on PATH.
export PATH="$(dirname "$CODEX"):$PATH"

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

P="$OUT/$TASK"
PROMPT="$P.prompt.md"; EVENTS="$P.events.jsonl"; RESULT="$P.result.json"; LOG="$P.log"
CHECK_LOG="$P.checks.jsonl"; SUMMARY="$P.summary.json"; REVIEW_FILE="$P.review.md"
rm -f "$REVIEW_FILE"
{ cat "$PREAMBLE"; printf '\n\n'; cat "$BRIEF"; } > "$PROMPT"
: > "$RESULT"; : > "$CHECK_LOG"

info "Starting codex on task $TASK"
python3 "$SCRIPT_DIR/notify.py" sent --task "$TASK" --brief "$BRIEF" || true
set +e
timeout "${DISPATCH_TIMEOUT:-1800}" "$CODEX" exec -C "$WT" -s workspace-write --json \
    --output-schema "$SCHEMA" -o "$RESULT" ${MODEL:+-m "$MODEL"} - < "$PROMPT" > "$EVENTS" 2> "$LOG"
STATUS=$?

# Run the checks only when the worker finished; a failed run has nothing to check.
if [ "$STATUS" -eq 0 ]; then
    for cmd in "${CHECKS[@]}"; do
        out="$(cd "$WT" && timeout "${DISPATCH_CHECK_TIMEOUT:-600}" bash -c "$cmd" 2>&1)"
        rc=$?
        python3 -c 'import json,sys; c,r,o=sys.argv[1],int(sys.argv[2]),sys.argv[3]
print(json.dumps({"cmd":c,"exit":r,"tail":o.splitlines()[-20:] if r else []}))' "$cmd" "$rc" "$out" >> "$CHECK_LOG"
    done
    # A second look in a new Codex session; a failed review is not fatal.
    if [ -n "$REVIEW" ]; then
        (cd "$WT" && timeout "${DISPATCH_TIMEOUT:-1800}" "$CODEX" exec review --uncommitted \
            -o "$REVIEW_FILE") > "$P.review.log" 2>&1 || rm -f "$REVIEW_FILE"
    fi
fi
set -e

ALLOW_ARGS=()
for glob in "${ALLOW[@]}"; do ALLOW_ARGS+=(--allow "$glob"); done

echo "---"
exec python3 "$SCRIPT_DIR/worker_report.py" --task "$TASK" --status "$STATUS" \
    --worktree "$WT" --branch "$BRANCH" --base "$START" --events "$EVENTS" --result "$RESULT" --log "$LOG" \
    --checks "$CHECK_LOG" --summary "$SUMMARY" ${REVIEW:+--review "$REVIEW_FILE"} "${ALLOW_ARGS[@]}"
