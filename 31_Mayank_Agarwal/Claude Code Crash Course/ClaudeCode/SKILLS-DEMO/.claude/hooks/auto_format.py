#!/usr/bin/env python3
"""
PostToolUse hook: Auto-format files after Claude writes or edits them.
Receives JSON on stdin with tool details.
"""

import json
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime


def log_message(message):
    """Append message to logs.txt with timestamp."""
    log_file = Path(__file__).parent.parent.parent / "logs.txt"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a") as f:
        f.write(f"[{timestamp}] {message}\n")


def main():
    time.sleep(5)
    # Read the event data from stdin
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)  # No valid input — allow the action

    # Get the file path from the event
    tool_input = event.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    if not file_path:
        sys.exit(0)

    path = Path(file_path)

    # Format Python files with black
    if path.suffix == ".py":
        result = subprocess.run(
            ["python", "-m", "black", str(path), "--quiet"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            msg = f"black format failed: {result.stderr}"
            print(f"[hook] {msg}", file=sys.stderr)
            log_message(f"❌ {msg}")
        else:
            msg = f"formatted: {path.name}"
            print(f"[hook] {msg}", file=sys.stderr)
            log_message(f"✓ {msg}")

    # Format JavaScript/TypeScript files with prettier
    elif path.suffix in [".js", ".ts", ".jsx", ".tsx", ".json", ".css"]:
        result = subprocess.run(
            ["npx", "prettier", "--write", str(path), "--log-level", "silent"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            msg = f"prettier format failed: {result.stderr}"
            print(f"[hook] {msg}", file=sys.stderr)
            log_message(f"❌ {msg}")
        else:
            msg = f"formatted: {path.name}"
            print(f"[hook] {msg}", file=sys.stderr)
            log_message(f"✓ {msg}")

    sys.exit(0)  # Always allow — PostToolUse can't block anyway


if __name__ == "__main__":
    main()
