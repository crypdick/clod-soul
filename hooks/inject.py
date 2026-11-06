"""Load the soul as context for Claude Code and Codex hooks."""

import json
import sys
from pathlib import Path

# NOTE: SOUL.md loads once per session and fades over long contexts. Tone is
# the rule that fades first, so repeat a short reminder on every prompt.
TONE_REMINDER = (
    "Clod soul reminder: reply as smart caveman. Drop articles, filler, "
    "pleasantries, hedging. Fragments OK. Technical terms, code, and errors "
    "stay exact. Applies to every reply, including answers about this plugin."
)

event = json.load(sys.stdin)["hook_event_name"]
if event == "UserPromptSubmit":
    context = TONE_REMINDER
elif event in ("SessionStart", "SubagentStart"):
    soul = Path(__file__).resolve().parent.parent / "SOUL.md"
    context = soul.read_text(encoding="utf-8")
else:
    raise ValueError(f"Unsupported hook event: {event}")

print(json.dumps({"hookSpecificOutput": {
    "hookEventName": event,
    "additionalContext": context,
}}))
