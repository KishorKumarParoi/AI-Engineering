#!/usr/bin/env python3
"""
PreToolUse hook: Block dangerous bash commands before they execute.
Exit code 2 = block the action (sends message to Claude via stderr).
Exit code 0 = allow the action.
"""
import json
import sys
import re

# Commands that should never run
BLOCKED_PATTERNS = [
    r"rm\s+-rf\s+[/~\.]",      # rm -rf on root, home, or current dir
    r"rm\s+-rf\s+\*",           # rm -rf *
    r"rm\s+-r\s+\*",           # rm -r *
    r"git\s+reset\s+--hard",   # hard reset (destroys uncommitted work)
    r"DROP\s+TABLE",            # SQL destructive operations
    r"DROP\s+DATABASE",
    r"chmod\s+777",             # insecure permission changes
    r"curl\s+.*\|\s*bash",      # curl | bash (remote code execution)
    r"wget\s+.*\|\s*sh",        # wget | sh
]

def main():
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    tool_name = event.get("tool_name", "")
    tool_input = event.get("tool_input", {})

    # Only inspect Bash tool calls
    if tool_name != "Bash":
        sys.exit(0)

    command = tool_input.get("command", "")

    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            # Exit code 2 = block. Message to stderr goes to Claude.
            print(
                f"BLOCKED by security hook: command matches dangerous pattern '{pattern}'.\n"
                f"Command was: {command}\n"
                f"Please find a safer alternative.",
                file=sys.stderr
            )
            sys.exit(2)  # ← This is the emergency brake

    sys.exit(0)  # Allow all other commands

if __name__ == "__main__":
    main()