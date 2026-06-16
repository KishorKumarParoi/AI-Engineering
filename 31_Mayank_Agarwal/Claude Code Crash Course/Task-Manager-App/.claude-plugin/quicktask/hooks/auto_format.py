#!/usr/bin/env python3
"""
PostToolUse hook: Auto-format Python files after Claude writes or edits them.
Runs black if available, silently skips if not installed.
"""
import json
import subprocess
import sys
from pathlib import Path


def main() -> None:
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    tool_input = event.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    if not file_path:
        sys.exit(0)

    path = Path(file_path)
    if path.suffix != ".py":
        sys.exit(0)

    result = subprocess.run(
        ["python", "-m", "black", str(path), "--quiet", "--line-length", "88"],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        print(f"[hook] formatted: {path.name}", file=sys.stderr)
    else:
        # black not installed or failed — not a blocking error
        print(f"[hook] black unavailable or failed for {path.name}", file=sys.stderr)

    sys.exit(0)


if __name__ == "__main__":
    main()
