#!/usr/bin/env python3
"""Post one short dispatch event to a Discord channel. Optional: without a webhook it does nothing.

The webhook URL comes from DISPATCH_DISCORD_WEBHOOK or ~/.config/dispatch-agents/discord-webhook.
A message holds only task ids, codes, counts and flag names, never code, diffs, logs or
error text. A failed post never fails the caller.

Usage:
  notify.py sent   --task ID --brief FILE
  notify.py goal   --goal ID --text "3 tasks · 1 squashed commit · not pushed"
  (run_worker.sh calls send() from worker_report.py for the finished-task event)
"""

import argparse
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

WEBHOOK_FILE = Path.home() / ".config/dispatch-agents/discord-webhook"
ICONS = {0: "✅", 3: "⚠️", 75: "⛔", 1: "❌"}


def webhook_url():
    url = os.environ.get("DISPATCH_DISCORD_WEBHOOK", "").strip()
    if not url and WEBHOOK_FILE.is_file():
        url = WEBHOOK_FILE.read_text().strip()
    return url if url.startswith("https://") else ""


def send(text):
    url = webhook_url()
    if not url:
        return
    # parse: [] stops @everyone and other mentions; Discord rejects the default urllib user agent.
    body = json.dumps({"content": text[:1900], "allowed_mentions": {"parse": []}}).encode()
    request = urllib.request.Request(
        url, data=body, method="POST",
        headers={"Content-Type": "application/json", "User-Agent": "dispatch-agents (notify.py)"},
    )
    try:
        urllib.request.urlopen(request, timeout=5).close()
    except Exception as error:  # noqa: BLE001 - a notice must never stop the work
        print(f"[WARN] Discord notice not sent: {type(error).__name__}", file=sys.stderr)


def brief_goal(path):
    """The first line of the brief's Goal part, or its first line."""
    lines = [line.strip() for line in Path(path).read_text(errors="replace").splitlines() if line.strip()]
    for line in lines:
        match = re.match(r"^[-*\s]*\**goal:?\**:?\s*(.+)", line, re.I)
        if match:
            return match.group(1)[:120]
    return lines[0][:120] if lines else ""


def finished_text(summary):
    s = summary
    parts = [f"{ICONS.get(s['exit'], '❔')} {s['task']} · {s['outcome']} · exit {s['exit']}"]
    if s["checks"]:
        passed = sum(1 for c in s["checks"] if c["exit"] == 0)
        parts.append(f"checks {passed}/{len(s['checks'])} PASS")
    tokens = s["usage"].get("total_tokens") or (
        (s["usage"].get("input_tokens") or 0) + (s["usage"].get("output_tokens") or 0)
    )
    if tokens:
        parts.append(f"{round(tokens / 1000)}k tokens")
    # Flag names only; the file paths stay on this machine.
    names = sorted({flag.split(":")[0] for flag in s["flags"]})
    if names:
        parts.append("flags: " + ", ".join(names))
    return " · ".join(parts)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("event", choices=["sent", "goal"])
    parser.add_argument("--task")
    parser.add_argument("--brief")
    parser.add_argument("--goal")
    parser.add_argument("--text", default="")
    args = parser.parse_args()
    if args.event == "sent":
        send(f"📤 {args.task} → codex · {brief_goal(args.brief)}")
    else:
        send(f"🏁 {args.goal} · {args.text}")


if __name__ == "__main__":
    main()
