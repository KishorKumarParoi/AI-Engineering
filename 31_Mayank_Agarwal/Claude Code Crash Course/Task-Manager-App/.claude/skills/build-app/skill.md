---
name: build-app
description: >
  Orchestrates the complete QuickTask build pipeline using all five specialist
  agents in sequence: planner → code-writer → service-writer → test-writer →
  quality-improver. Use this skill to build the entire application from scratch
  with one command. Each agent must confirm completion before the next starts.
trigger: /build-app
effort: normal
---

# Goal
Build the complete QuickTask application by running all five specialist agents
in sequence. Each agent confirms completion before the next one starts.

# Pre-Flight Check
Before starting, verify:
1. CLAUDE.md exists and is readable
2. No src/ directory exists yet (we are building from scratch)
3. requirements.txt exists

If src/ already exists — stop and ask the user if they want to rebuild.

# Pipeline

## Step 1: Plan (planner agent)
Invoke the planner agent with:
"Read CLAUDE.md and write a detailed PLAN.md covering all four implementation
phases. Do not write any code."

Wait for the planner to confirm: "PLAN.md written"
Verify PLAN.md exists before proceeding.

## Step 2: Core Logic (code-writer agent)
Invoke the code-writer agent with:
"Read PLAN.md and CLAUDE.md. Implement Phase 1: create src/__init__.py,
src/models.py, and src/storage.py with full type hints, docstrings, and
validation. Run the sanity check before reporting done."

Wait for code-writer to confirm: "Core logic complete"
Verify src/models.py and src/storage.py exist before proceeding.

## Step 3: Service Layer (service-writer agent)
Invoke the service-writer agent with:
"Read PLAN.md, CLAUDE.md, and all src/ files. Implement Phase 2: create
src/cli.py and src/api.py. Run both the CLI check and API check before
reporting done."

Wait for service-writer to confirm: "Service layer complete"
Verify src/cli.py and src/api.py exist before proceeding.

## Step 4: Tests (test-writer agent)
Invoke the test-writer agent with:
"Read all files in src/ and CLAUDE.md. Write a comprehensive pytest suite
in tests/ covering all four source modules. Run the tests and report results."

Wait for test-writer to confirm: "Tests complete"
Verify tests/ directory exists before proceeding.

## Step 5: Quality Pass (quality-improver agent)
Invoke the quality-improver agent with:
"Read all files in src/ and tests/. Perform a full quality pass: type hints,
docstrings, error handling, magic values. Fix issues in-place, re-run tests,
write QUALITY_REPORT.md."

Wait for quality-improver to confirm: "Quality pass complete"

# Completion

Print a final summary:
```
╔══════════════════════════════════════╗
║     QuickTask Build Complete ✓       ║
╠══════════════════════════════════════╣
║ Phase 1 — Core Logic      DONE  ✓   ║
║ Phase 2 — Service Layer   DONE  ✓   ║
║ Phase 3 — Tests           DONE  ✓   ║
║ Phase 4 — Quality Pass    DONE  ✓   ║
╠══════════════════════════════════════╣
║ Run app:  python -m src.cli --help   ║
║ Run API:  python src/api.py          ║
║ Run tests: python -m pytest tests/  ║
╚══════════════════════════════════════╝
```

Then ask: "Would you like me to demo the app by running a few CLI commands?"
