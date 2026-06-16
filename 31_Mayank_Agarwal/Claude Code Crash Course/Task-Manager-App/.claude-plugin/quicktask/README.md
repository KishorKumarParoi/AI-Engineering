# QuickTask Plugin

A Claude Code plugin that bundles project configuration, custom agents, and development tools for the QuickTask task manager project.

## What's Included

### Agents
- **planner** — Breaks down requirements into implementation plans
- **code-writer** — Writes core Python logic (models, storage)
- **service-writer** — Implements CLI and REST API layers
- **test-writer** — Builds comprehensive pytest test suites
- **quality-improver** — Performs final code quality pass
- **security-auditor** — Comprehensive security review

### Skills
- **build-app** — Orchestrates the complete QuickTask build pipeline

### Hooks
- **auto_format** — Auto-formats Python files with Black after writes/edits
- **session_logger** — Logs all session activity to `.claude/logs/activity.log`

### Configuration
- **CLAUDE.md** — Project brain with architecture, rules, and standards
- **settings.json** — Default development settings

## Installation

The plugin is already installed in local scope for this project. To enable it across your team:

```bash
# Share the .claude-plugin/quicktask directory with your team via version control
# Team members will automatically have access to the plugin
```

## Usage

The plugin provides:
- All 6 custom agents ready to use via `/agents` or automatic invocation
- Build automation via the `/build-app` skill
- Automatic code formatting and session logging
- Project-wide coding standards via CLAUDE.md

## Project Structure

```
QuickTask
├── src/
│   ├── models.py       (Task dataclass + validation)
│   ├── storage.py      (JSON read/write)
│   ├── cli.py          (argparse CLI)
│   └── api.py          (Flask REST API)
├── tests/
├── .claude-plugin/quicktask/  ← You are here
└── data/
```

## Tech Stack

- **Language:** Python 3.10+
- **CLI:** argparse (stdlib only)
- **API:** Flask 3.x
- **Storage:** JSON file
- **Tests:** pytest

## Quality Standards

- Test coverage target: 80%+ on src/
- Type hints on all functions
- One-line docstrings minimum
- Functions over 30 lines should be split
- Consistent JSON API responses: `{"data": ..., "error": null}`
