#!/usr/bin/env bash
# Run one worker agent (codex or agy) on one brief, in its own git worktree.
#
# Usage: run_worker.sh <codex|agy> <task-id> <brief-file> [--repo DIR] [--base REF] [--model NAME]
#
# The worker edits files in the worktree and does not commit. The caller reads the diff,
# runs the tests, commits and merges.
# Environment: DISPATCH_TIMEOUT sets the time limit in seconds (default 1800).
# Exit code: 0 done, 75 usage limit reached (try another agent), 1 other failure, 2 bad usage.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PREAMBLE="$SCRIPT_DIR/../assets/worker-preamble.md"

die() { echo "[ERROR] $*" >&2; exit "${2:-1}"; }
info() { echo "[INFO] $*"; }

[ $# -ge 3 ] || die "Usage: run_worker.sh <codex|agy> <task-id> <brief-file> [--repo DIR] [--base REF] [--model NAME]" 2

AGENT="$1"; TASK="$2"; BRIEF="$3"; shift 3
REPO=""; BASE="HEAD"; MODEL=""
while [ $# -gt 0 ]; do
    case "$1" in
        --repo)  REPO="${2:?--repo needs a value}"; shift 2 ;;
        --base)  BASE="${2:?--base needs a value}"; shift 2 ;;
        --model) MODEL="${2:?--model needs a value}"; shift 2 ;;
        *) die "Unknown option: $1" 2 ;;
    esac
done

case "$AGENT" in codex|agy) ;; *) die "Agent must be codex or agy, not '$AGENT'" 2 ;; esac
[[ "$TASK" =~ ^[a-z0-9][a-z0-9._-]*$ ]] || die "Task id must match [a-z0-9][a-z0-9._-]*" 2
[ -f "$BRIEF" ] || die "Brief file not found: $BRIEF" 2
[ -f "$PREAMBLE" ] || die "Preamble not found: $PREAMBLE"

REPO="$(git -C "${REPO:-.}" rev-parse --show-toplevel)" || die "Not a git repository"

# Find the agent binary. mise installs codex under node, so it is not always on PATH.
find_agent() {
    local bin
    bin="$(command -v "$1" 2>/dev/null || true)"
    [ -n "$bin" ] && { echo "$bin"; return; }
    if command -v mise >/dev/null 2>&1; then
        bin="$(mise which "$1" 2>/dev/null || true)"
        [ -n "$bin" ] && { echo "$bin"; return; }
    fi
    bin="$(ls "$HOME"/.local/share/mise/installs/node/*/bin/"$1" 2>/dev/null | tail -n 1 || true)"
    [ -n "$bin" ] && echo "$bin"
}
AGENT_BIN="$(find_agent "$AGENT")"
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
    git -C "$REPO" worktree add -b "$BRANCH" "$WT" "$BASE" >/dev/null \
        || die "Could not create worktree $WT on branch $BRANCH"
    info "Created worktree $WT on branch $BRANCH"
fi

PROMPT="$OUT/$TASK.$AGENT.prompt.md"
LOG="$OUT/$TASK.$AGENT.log"
RESULT="$OUT/$TASK.$AGENT.result.md"
{ cat "$PREAMBLE"; printf '\n\n'; cat "$BRIEF"; } > "$PROMPT"
: > "$RESULT"

info "Starting $AGENT ($AGENT_BIN) on task $TASK"
set +e
case "$AGENT" in
    codex)
        timeout "${DISPATCH_TIMEOUT:-1800}" "$AGENT_BIN" exec -C "$WT" -s workspace-write \
            ${MODEL:+-m "$MODEL"} -o "$RESULT" - < "$PROMPT" > "$LOG" 2>&1
        ;;
    agy)
        (cd "$WT" && timeout "${DISPATCH_TIMEOUT:-1800}" "$AGENT_BIN" -p "$(cat "$PROMPT")" \
            --mode accept-edits --output-format text ${MODEL:+--model "$MODEL"}) > "$RESULT" 2> "$LOG"
        ;;
esac
STATUS=$?
set -e

echo "---"
echo "agent:     $AGENT (exit $STATUS)"
echo "worktree:  $WT"
echo "branch:    $BRANCH"
echo "result:    $RESULT"
echo "log:       $LOG"
echo "changes:"
git -C "$WT" status --short | sed 's/^/  /'
[ -z "$(git -C "$WT" status --short)" ] && echo "  (none)"

if [ "$STATUS" -eq 0 ]; then
    exit 0
fi
if [ "$STATUS" -eq 124 ]; then
    die "$AGENT passed the time limit. Raise DISPATCH_TIMEOUT or split the task."
fi
# Look for a limit message only after a failure, so that code text with "429" does not match.
if cat "$LOG" "$RESULT" | grep -qiE 'rate.?limit|usage limit|quota|too many requests|exhausted|\b429\b'; then
    die "$AGENT reached its usage limit. Send the task to another agent." 75
fi
die "$AGENT failed. Read $LOG"
