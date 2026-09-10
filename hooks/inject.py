"""Load the soul as context for Claude Code and Codex hooks."""

import json
import sys
from pathlib import Path

event = json.load(sys.stdin)["hook_event_name"]
if event not in ("SessionStart", "SubagentStart"):
    raise ValueError(f"Unsupported hook event: {event}")

soul = Path(__file__).resolve().parent.parent / "SOUL.md"
print(json.dumps({"hookSpecificOutput": {
    "hookEventName": event,
    "additionalContext": soul.read_text(encoding="utf-8"),
}}))
