#!/usr/bin/env python3
"""Test the calculator MCP server."""

import json
import subprocess
import sys


def test_calculator():
    """Test calculator operations."""
    # Start the calculator server
    process = subprocess.Popen(
        [sys.executable, "calculator_mcp.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # Test: 5 + 2
    request = {
        "method": "tools/call",
        "params": {"name": "add", "arguments": {"a": 5, "b": 2}},
    }

    process.stdin.write(json.dumps(request) + "\n")
    process.stdin.flush()

    response = process.stdout.readline()
    result = json.loads(response)

    process.terminate()
    process.wait()

    return result


if __name__ == "__main__":
    result = test_calculator()
    print(f"5 + 2 = {result.get('result')}")
    print(f"Full response: {json.dumps(result, indent=2)}")
