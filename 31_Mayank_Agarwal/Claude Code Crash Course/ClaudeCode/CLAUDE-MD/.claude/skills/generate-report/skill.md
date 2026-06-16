---
name: generate-report
description: >
  Generates a daily project status report by reading all Python
  files in /src, summarising what each module does, identifying
  any TODO comments, and writing a clean markdown report to /reports/.
  Use when asked to generate a report, summarise the codebase,
  or create a status update.
trigger: /generate-report
---

# Goal
Generate a comprehensive daily status report for the project.

# Inputs
- Target directory: /src (default) or user-specified path
- Report output location: /reports/YYYY-MM-DD-status.md
- Include TODOs: yes (default)

# Steps

## Step 1: Scan the codebase
Read all {FILE-TYPE} files in the target directory.
For each file, extract:
- What the module does (based on its docstring and function names)
- Any TODO, FIXME, or HACK comments
- How many functions it contains

## Step 2: Summarise findings
Compile the per-file information into:
- A one-paragraph project overview
- A per-module breakdown (file name, purpose, function count)
- A consolidated TODO list with file references

## Step 3: Write the report
Create a markdown file at /reports/YYYY-MM-DD-status.md with:
- Date at the top
- Project overview section
- Per-module breakdown table
- Consolidated TODO list
- A "Health summary" — overall state of the codebase

## Step 4: Confirm completion
Print a confirmation message with:
- How many files were scanned
- How many TODOs were found
- The path to the report file





