# QuickTask — Project Brain

## What We Are Building
A simple task manager with three layers:
- **Core logic** (`src/models.py`, `src/storage.py`) — Task data model + JSON file storage
- **CLI** (`src/cli.py`) — Command-line interface using `argparse`
- **REST API** (`src/api.py`) — Flask API with 5 endpoints
- **Tests** (`tests/`) — pytest suite covering all layers

## Tech Stack
- Language: Python 3.10+
- CLI: argparse (stdlib only — no click)
- API: Flask 3.x
- Storage: JSON file at `data/tasks.json`
- Tests: pytest

## Project Structure (what we are building toward)
```
quicktask/
├── .claude/            ← you are here
├── src/
│   ├── __init__.py
│   ├── models.py       ← Task dataclass + validation
│   ├── storage.py      ← JSON read/write
│   ├── cli.py          ← argparse CLI
│   └── api.py          ← Flask REST API
├── tests/
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_storage.py
│   ├── test_cli.py
│   └── test_api.py
├── data/               ← created at runtime
├── requirements.txt
├── PLAN.md             ← written by planner agent
└── README.md
```

## Core Rules for All Agents
1. **Python only** — no Node, no TypeScript, no other languages
2. **Type hints everywhere** — every function must be fully typed
3. **Docstrings on every function** — one-line minimum
4. **No external dependencies beyond Flask and pytest** — keep it simple
5. **Error handling** — every function that can fail must handle it gracefully
6. **Constants at the top** — no magic strings buried in functions

## Task Data Model
```python
@dataclass
class Task:
    id: int
    title: str              # 1-200 chars, required
    priority: str           # "low" | "normal" | "high"
    status: str             # "pending" | "done"
    created_at: str         # ISO 8601 datetime string
    notes: str = ""         # optional, max 500 chars
```

## API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET    | /tasks | List all tasks (filter: ?status=pending) |
| POST   | /tasks | Create a task |
| GET    | /tasks/:id | Get one task |
| PATCH  | /tasks/:id | Update task (title, priority, status, notes) |
| DELETE | /tasks/:id | Delete a task |

## CLI Commands
```
python -m src.cli add "Buy milk" --priority high
python -m src.cli list
python -m src.cli list --status pending
python -m src.cli complete 1
python -m src.cli delete 1
python -m src.cli show 1
```

## Quality Standards
- Test coverage target: 80%+ on src/
- No bare `except:` — always catch specific exceptions
- Functions over 30 lines should be split
- All API responses use consistent JSON: `{"data": ..., "error": null}`
