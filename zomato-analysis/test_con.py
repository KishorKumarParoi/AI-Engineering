#!/usr/bin/env -S uv run python
# -*- coding: utf-8 -*-
"""
Compatibility Wrapper: test_con.py -> test_conn.py
Redirects seamlessly to the master test runner test_conn.py.
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
TEST_CONN = PROJECT_ROOT / "test_conn.py"

if __name__ == "__main__":
    import runpy
    sys.argv[0] = str(TEST_CONN)
    runpy.run_path(str(TEST_CONN), run_name="__main__")
