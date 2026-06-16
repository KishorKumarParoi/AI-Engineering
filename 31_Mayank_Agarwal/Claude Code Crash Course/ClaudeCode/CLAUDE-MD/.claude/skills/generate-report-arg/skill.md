
---
name: generate-report
description: >
  Generates a status report for a Python project.
  Usage: /generate-report [source_dir] [output_dir]
  Defaults: source_dir=src, output_dir=reports
trigger: /generate-report
---

# Goal
Generate a project status report for the directory: $ARGUMENTS[1] (default: src)
Output to: $ARGUMENTS[2] (default: reports)

# Steps
## Step 1: Determine target directory
If $ARGUMENTS[1] is provided, use that as the source directory.
Otherwise, default to ./src

## Step 2: Scan
Run scripts/scan_codebase.py $ARGUMENTS[1]
...