#!/usr/bin/env python3
"""
Multi-event hook: Logs all Claude Code session activity to .claude/logs/activity.log
Fires on SessionStart, PostToolUse (Bash/Write/Read), and Stop.
Zero tokens — pure local execution.
"""
import json
import sys
from datetime import datetime
from pathlib import Path

LOG_DIR = Path(".claude/logs")
LOG_FILE = LOG_DIR / "activity.log"


def ensure_log_dir() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def log(message: str) -> None:
    ensure_log_dir()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")


def main() -> None:
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    event_name = event.get("hook_event_name", "")

    if event_name == "SessionStart":
        session_id = event.get("session_id", "unknown")
        log(f"=== SESSION START (id: {session_id[:8]}...) ===")

    elif event_name == "Stop":
        log("=== SESSION STOP ===\n")

    elif event_name == "PostToolUse":
        tool = event.get("tool_name", "unknown")
        tool_input = event.get("tool_input", {})

        if tool == "Bash":
            cmd = tool_input.get("command", "")[:120]
            log(f"BASH    | {cmd}")

        elif tool == "Write":
            path = tool_input.get("file_path", "unknown")
            log(f"WRITE   | {path}")

        elif tool == "Edit":
            path = tool_input.get("file_path", "unknown")
            log(f"EDIT    | {path}")

        elif tool == "Read":
            path = tool_input.get("file_path", "unknown")
            log(f"READ    | {path}")

    sys.exit(0)


if __name__ == "__main__":
    main()
