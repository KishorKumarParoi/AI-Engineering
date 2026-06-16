# QuickTask

A simple task manager built entirely by a team of Claude Code sub-agents.

## What Gets Built
- `src/models.py` — Task dataclass with validation  
- `src/storage.py` — JSON file persistence
- `src/cli.py` — Command-line interface
- `src/api.py` — Flask REST API (5 endpoints)
- `tests/` — Full pytest suite

## The Agent Team

| Agent | Role | Model |
|-------|------|-------|
| `planner` | Reads requirements → writes PLAN.md | Sonnet |
| `code-writer` | Builds models + storage | Sonnet |
| `service-writer` | Builds CLI + API | Sonnet |
| `test-writer` | Writes + runs test suite | Sonnet |
| `quality-improver` | Final review + fixes | Sonnet |

## How to Run the Demo

**Option A — Full pipeline via skill:**
```
/build-app
```

**Option B — Agent by agent (recommended for teaching):**
```
@planner read CLAUDE.md and write PLAN.md
@code-writer implement Phase 1 from PLAN.md
@service-writer implement Phase 2 from PLAN.md
@test-writer write and run the full test suite
@quality-improver do a final quality pass and write QUALITY_REPORT.md
```

## After Build — Try It Out

```bash
# Install dependencies
pip install -r requirements.txt

# CLI
python -m src.cli add "Buy groceries" --priority high
python -m src.cli add "Read book" --priority low
python -m src.cli list
python -m src.cli complete 1
python -m src.cli list --status pending

# API
python src/api.py          # starts on http://localhost:5000
curl http://localhost:5000/tasks
curl -X POST http://localhost:5000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Test task", "priority": "normal"}'

# Tests
python -m pytest tests/ -v
```
