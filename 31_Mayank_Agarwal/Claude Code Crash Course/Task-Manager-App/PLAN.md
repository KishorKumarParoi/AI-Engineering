# Implementation Plan — QuickTask

## Project Overview
A three-layer task management system: Core Logic → Service Layer → Tests. The system persists tasks to JSON, exposes them via Flask REST API, and provides a CLI interface using argparse.

**Tech Stack:** Python 3.10+, Flask 3.x, pytest, argparse (stdlib), JSON file storage

---

## Phase 1: Core Logic — Models & Storage

### Purpose
Establish the data model and persistence layer. These modules are the foundation for CLI and API.

### Files to Create

#### `src/__init__.py`
Empty module initializer. Allows `from src import ...` imports.

#### `src/models.py`
Define the Task data model with validation.

**Responsibility:**
- Task dataclass with fields: id, title, priority, status, created_at, notes
- Field validation (title 1-200 chars, notes max 500 chars, priority in ["low", "normal", "high"], status in ["pending", "done"])
- Conversion methods: Task → dict (for JSON serialization), dict → Task (for deserialization)
- Constants for valid priorities and statuses at module level

**Key function signatures:**
```python
# Constants
VALID_PRIORITIES: list[str]  # ["low", "normal", "high"]
VALID_STATUSES: list[str]    # ["pending", "done"]

# Dataclass
@dataclass
class Task:
    id: int
    title: str
    priority: str
    status: str
    created_at: str
    notes: str = ""

# Methods (instance or static)
def validate(task: Task) -> None:
    """Raise ValueError if any field is invalid."""

def to_dict(task: Task) -> dict:
    """Convert Task to JSON-serializable dict."""

def from_dict(data: dict) -> Task:
    """Convert dict to Task, validating all fields."""
```

#### `src/storage.py`
Manage JSON file I/O for task persistence.

**Responsibility:**
- Read tasks from `data/tasks.json` (or return empty list if file doesn't exist)
- Write tasks to `data/tasks.json` with pretty formatting
- Auto-create `data/` directory if missing
- Handle file I/O errors gracefully (IOError, json.JSONDecodeError)
- Track next ID across load/save cycles (max(ids) + 1 or 1 if empty)
- No in-memory cache—always read/write from disk to ensure consistency

**Key function signatures:**
```python
DATA_DIR: str  # "data"
DATA_FILE: str  # "data/tasks.json"

def load_tasks() -> list[Task]:
    """Load all tasks from JSON file, return empty list if file missing."""

def save_tasks(tasks: list[Task]) -> None:
    """Write tasks to JSON file. Create data/ directory if needed."""

def get_next_id(tasks: list[Task]) -> int:
    """Return the next available task ID."""
```

---

## Phase 2: Service Layer — CLI & API

### Purpose
Build the user-facing interfaces (CLI and REST) using the core logic from Phase 1.

### Files to Create

#### `src/cli.py`
Command-line interface using argparse (stdlib only, no Click).

**Responsibility:**
- Parse arguments for 6 commands: add, list, show, complete, delete, update (or variations)
- Call storage functions to load/save
- Display formatted output to stdout (tables or lists)
- Handle user input validation and task not found errors
- Main entry point as `if __name__ == "__main__"` (allows `python -m src.cli`)

**CLI Command Signatures:**
```
add TITLE [--priority PRIORITY]                     → Create task, print ID
list [--status STATUS]                              → List all/filtered tasks
show ID                                             → Print task details
complete ID                                         → Mark task as "done"
delete ID                                           → Remove task
update ID [--title TITLE] [--priority PRIORITY] ... → Update task fields
```

**Key function signatures:**
```python
def parse_arguments(args: list[str]) -> Namespace:
    """Parse CLI args and return argparse Namespace."""

def handle_add(title: str, priority: str = "normal") -> None:
    """Create task, save, print success message with ID."""

def handle_list(status: str | None = None) -> None:
    """Load tasks, filter by status if provided, print formatted table."""

def handle_show(task_id: int) -> None:
    """Load tasks, find by ID, print details or "not found" message."""

def handle_complete(task_id: int) -> None:
    """Mark task as "done", save, print success message."""

def handle_delete(task_id: int) -> None:
    """Remove task by ID, save, print success message."""

def main(args: list[str] | None = None) -> None:
    """Entry point: parse args, dispatch to handler, catch exceptions."""
```

#### `src/api.py`
Flask REST API with 5 endpoints.

**Responsibility:**
- Flask app factory or singleton
- 5 endpoints with consistent JSON response format: `{"data": ..., "error": null}`
- Error responses: `{"data": null, "error": "message"}`
- HTTP status codes: 200 (GET, PATCH), 201 (POST), 204 (DELETE), 400 (bad input), 404 (not found), 500 (server error)
- Query parameter filtering (e.g., GET /tasks?status=pending)
- Call storage/models for all business logic

**API Endpoints:**
```
GET    /tasks                    → List all tasks, optional ?status=pending filter
POST   /tasks                    → Create task (JSON body: title, priority, notes)
GET    /tasks/<int:task_id>      → Get one task by ID
PATCH  /tasks/<int:task_id>      → Update task fields (JSON body: title, priority, status, notes)
DELETE /tasks/<int:task_id>      → Delete task by ID
```

**Key function signatures:**
```python
def create_app() -> Flask:
    """Factory function to create and configure Flask app."""

@app.route("/tasks", methods=["GET"])
def list_tasks() -> tuple[dict, int]:
    """Load tasks, filter by status query param, return JSON list."""

@app.route("/tasks", methods=["POST"])
def create_task() -> tuple[dict, int]:
    """Parse JSON body, create task, save, return created task with 201."""

@app.route("/tasks/<int:task_id>", methods=["GET"])
def get_task(task_id: int) -> tuple[dict, int]:
    """Load tasks, find by ID, return 404 if not found."""

@app.route("/tasks/<int:task_id>", methods=["PATCH"])
def update_task(task_id: int) -> tuple[dict, int]:
    """Parse JSON, update task fields, save, return updated task."""

@app.route("/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id: int) -> tuple[dict, int]:
    """Delete task by ID, save, return 204 (no content)."""

def json_response(data: Any, error: str | None = None, status: int = 200) -> tuple[dict, int]:
    """Helper to build consistent {"data": ..., "error": ...} response."""
```

---

## Phase 3: Test Suite — Comprehensive Coverage

### Purpose
Ensure all layers (models, storage, CLI, API) are tested with 80%+ coverage and proper error paths.

### Files to Create

#### `tests/__init__.py`
Empty module initializer.

#### `tests/test_models.py`
Unit tests for Task model and validation.

**What to test:**
- Task instantiation with valid fields
- Field validation (title length, notes length, priority enum, status enum)
- to_dict() serialization (includes all fields, no extra keys)
- from_dict() deserialization with valid and invalid data
- Invalid data raises ValueError with clear message
- Edge cases: empty string title (invalid), 200-char title (valid), 500-char notes (valid), 501-char notes (invalid)
- Dataclass defaults (notes defaults to "")

**Critical paths to cover:**
```python
test_task_creation_valid()
test_task_validation_title_too_short()
test_task_validation_title_too_long()
test_task_validation_invalid_priority()
test_task_validation_invalid_status()
test_task_validation_notes_too_long()
test_task_to_dict()
test_task_from_dict_valid()
test_task_from_dict_invalid_priority()
test_task_from_dict_missing_field()
test_task_from_dict_notes_defaults_empty_string()
```

#### `tests/test_storage.py`
Unit tests for JSON file I/O.

**What to test:**
- load_tasks() returns empty list if file doesn't exist
- load_tasks() parses valid JSON and returns Task objects
- load_tasks() raises error (JSONDecodeError) on corrupted JSON
- save_tasks() creates data/ directory if missing
- save_tasks() writes valid JSON that can be read back
- save_tasks() empty list writes valid empty JSON array
- get_next_id() returns 1 for empty list
- get_next_id() returns max(ids) + 1 for non-empty list
- Concurrent file access doesn't corrupt data (write then read returns same tasks)
- File permissions errors are caught and logged/raised appropriately

**Critical paths to cover:**
```python
test_load_tasks_file_not_found()
test_load_tasks_valid_json()
test_load_tasks_corrupted_json()
test_save_tasks_creates_directory()
test_save_tasks_valid_json()
test_save_tasks_empty_list()
test_get_next_id_empty_list()
test_get_next_id_non_empty_list()
test_save_then_load_roundtrip()
test_save_tasks_permission_error()
```

#### `tests/test_cli.py`
Integration tests for CLI commands.

**What to test:**
- parse_arguments() correctly parses all commands and options
- handle_add() creates task, saves, outputs ID
- handle_add() with invalid priority returns error
- handle_list() displays all tasks formatted
- handle_list() with --status=pending filters correctly
- handle_show() displays task by ID
- handle_show() task not found returns error message
- handle_complete() marks task as done and saves
- handle_delete() removes task and saves
- handle_delete() task not found returns error
- CLI catches exceptions and outputs user-friendly messages
- Exit codes are reasonable (0 for success, 1 for error)

**Critical paths to cover:**
```python
test_cli_add_valid()
test_cli_add_invalid_priority()
test_cli_list_all()
test_cli_list_filtered_by_status()
test_cli_show_found()
test_cli_show_not_found()
test_cli_complete()
test_cli_delete_found()
test_cli_delete_not_found()
test_cli_invalid_command()
test_cli_missing_required_argument()
```

#### `tests/test_api.py`
Integration tests for Flask endpoints.

**What to test:**
- GET /tasks returns 200 with list of tasks
- GET /tasks?status=pending filters correctly
- POST /tasks with valid JSON creates task, returns 201, includes created task in response
- POST /tasks missing required field returns 400
- POST /tasks invalid priority returns 400
- GET /tasks/:id returns 200 with task
- GET /tasks/:id not found returns 404
- PATCH /tasks/:id updates task fields, returns 200 with updated task
- PATCH /tasks/:id missing task returns 404
- PATCH /tasks/:id invalid data returns 400
- DELETE /tasks/:id returns 204
- DELETE /tasks/:id not found returns 404
- All responses follow {"data": ..., "error": ...} format
- Error responses have non-null "error" field

**Critical paths to cover:**
```python
test_api_list_tasks()
test_api_list_tasks_filter_by_status()
test_api_create_task_valid()
test_api_create_task_missing_title()
test_api_create_task_invalid_priority()
test_api_get_task_found()
test_api_get_task_not_found()
test_api_update_task_found()
test_api_update_task_not_found()
test_api_update_task_invalid_data()
test_api_delete_task_found()
test_api_delete_task_not_found()
test_api_response_format_consistent()
```

---

## Phase 4: Quality Pass — Refinement & Polish

### Purpose
Ensure code quality, completeness, and maintainability before delivery.

### What to Check

#### Type Hints Completeness
- Every function has argument types and return type
- Use `list[Task]`, `dict[str, Any]`, `Task | None` (Python 3.10+ syntax)
- No bare `Any` types without justification
- Command line parsing returns `Namespace` with type-checked attributes

#### Docstring Coverage
- Every function has at least a one-line docstring
- Longer functions (15+ lines) have parameter and return descriptions
- Docstrings follow Google or NumPy style consistently
- Example: `"""Load all tasks from file. Return empty list if file missing."""`

#### Error Handling
- No bare `except:` clauses—catch specific exceptions
- Catch: `FileNotFoundError`, `json.JSONDecodeError`, `IOError`, `ValueError`, `KeyError`, `TypeError`
- User-facing errors (CLI/API) return friendly messages, not tracebacks
- Server errors in API return 500 status with generic error message

#### Function Size
- Flag any function over 30 lines and split if logical
- CLI handlers should be 20-30 lines (argument parsing + business logic + output)
- API handlers should be 15-25 lines (parse request + call storage + format response)

#### Constants & Config
- No magic strings (e.g., "data/tasks.json" hardcoded multiple times)
- All constants at module level in UPPER_CASE
- JSON format keys ("data", "error") defined as constants
- HTTP status codes defined as constants if used multiple times

#### Response Format Consistency
- All API responses follow `{"data": ..., "error": null}` or `{"data": null, "error": "msg"}`
- DELETE returns 204 with empty body (no JSON)
- POST returns 201 with created resource in "data"
- GET/PATCH return 200 with resource in "data"
- 404/400/500 responses include error message

#### Test Quality
- All test functions follow naming: `test_<unit>_<scenario>`
- Fixtures (temp files, sample data) are isolated and cleaned up
- Test isolation: no shared state between tests
- Use pytest fixtures or setup/teardown for file I/O

#### Import Organization
- Standard library imports first, then third-party (Flask, pytest), then local
- No circular imports
- src.models imported in storage, storage imported in cli/api

---

## Implementation Order

**Dependency Graph:**
```
1. src/models.py       (no dependencies)
2. src/storage.py      (depends on models)
3. src/cli.py          (depends on storage, models)
4. src/api.py          (depends on storage, models)
5. tests/*             (depend on all of above)
```

### Step-by-Step Execution

1. **Code-Writer Agent — Phase 1a: `src/__init__.py`**
   - Create empty init file
   - Allows module imports

2. **Code-Writer Agent — Phase 1b: `src/models.py`**
   - Task dataclass with 6 fields
   - VALID_PRIORITIES and VALID_STATUSES constants
   - validate(task) function
   - to_dict(task) and from_dict(dict) functions
   - Full type hints, docstrings on all functions

3. **Code-Writer Agent — Phase 1c: `src/storage.py`**
   - DATA_DIR and DATA_FILE constants
   - load_tasks() with error handling
   - save_tasks(tasks) with directory creation
   - get_next_id(tasks) helper
   - Full type hints, docstrings, exception handling

4. **Service-Writer Agent — Phase 2a: `src/cli.py`**
   - parse_arguments(args) using argparse
   - Six command handlers: handle_add, handle_list, handle_show, handle_complete, handle_delete, handle_update
   - main() entry point
   - Call storage functions, format output
   - Full type hints, docstrings, error handling

5. **Service-Writer Agent — Phase 2b: `src/api.py`**
   - create_app() Flask factory
   - 5 endpoint handlers
   - json_response(data, error, status) helper
   - Full type hints, docstrings, error handling
   - Consistent status codes and response format

6. **Test-Writer Agent — Phase 3a: `tests/__init__.py`**
   - Create empty init file

7. **Test-Writer Agent — Phase 3b: `tests/test_models.py`**
   - 10-12 test functions covering all validation paths
   - Fixtures for sample Task objects
   - Assert on all field types and constraints

8. **Test-Writer Agent — Phase 3c: `tests/test_storage.py`**
   - 8-10 test functions covering load, save, get_next_id
   - Fixtures for temp files and sample tasks
   - Clean up temp files after tests

9. **Test-Writer Agent — Phase 3d: `tests/test_cli.py`**
   - 10-12 test functions covering all commands
   - Mock file I/O or use temp files
   - Capture stdout for output assertions

10. **Test-Writer Agent — Phase 3e: `tests/test_api.py`**
    - 12-14 test functions covering all endpoints
    - Flask test client fixture
    - Assert on status codes and response format

11. **Quality-Improver Agent — Phase 4**
    - Audit all type hints (no bare `Any`, all functions fully typed)
    - Verify docstrings on every function
    - Check for bare `except:` (should find none)
    - Measure test coverage (report if < 80% on src/)
    - Check function lengths (split any > 30 lines)
    - Verify all constants are at module level
    - Verify API response format consistency
    - Refactor repetitive code in tests

---

## Risks and Watch Points

1. **File I/O and Concurrency**
   - If multiple processes write to tasks.json simultaneously, data can corrupt
   - Mitigation: Ensure save_tasks() always reads → modify → write atomically
   - Watch: Don't assume file exists; always handle FileNotFoundError

2. **ID Collision**
   - If an ID is deleted, get_next_id() might return a duplicate
   - Mitigation: Track max(id) + 1, not just count
   - Watch: Test explicitly that deleted IDs are not reused

3. **JSON Serialization of datetime**
   - created_at is ISO 8601 string, not datetime object
   - Watch: Don't convert to/from datetime.datetime in models (keep as string)
   - Reason: JSON can't serialize datetime; store strings only

4. **argparse and sys.exit()**
   - argparse calls sys.exit(2) on parse errors by default
   - Watch: In tests, this will crash test runner; use try/except or mock sys.exit
   - Mitigation: Set `exit_on_error=False` in ArgumentParser (Python 3.9+)

5. **Flask test client and state**
   - Each test should use a fresh app instance
   - Watch: Don't share app or tasks.json between tests
   - Mitigation: Use pytest fixture with `app.app_context()` and temp data file

6. **API vs CLI Data Validation**
   - Both should reject invalid input (e.g., priority="invalid")
   - Watch: Don't validate in only one place; use models.py for truth
   - Mitigation: Both CLI and API call models.validate() or from_dict()

7. **Priority and Status Enums**
   - These are stored as strings in JSON, not Python enums
   - Watch: When hardcoding checks, use the VALID_* constants, not string literals
   - Reason: Simplifies JSON I/O; avoid `if priority == "normal"` directly in conditionals

8. **Default Response Format in Errors**
   - API must return `{"data": null, "error": "message"}` on all errors
   - Watch: Don't return 500 with HTML error; always return JSON
   - Mitigation: Add error handler decorator in Flask app

9. **Test Isolation and Fixtures**
   - If test_storage.py uses real files in data/, tests can interfere with each other
   - Watch: Use pytest's `tmp_path` fixture or monkeypatch DATA_FILE to temp location
   - Mitigation: Each test gets its own temp file; no shared state

10. **CLI Output Formatting**
    - No strict formatting requirements specified (table vs. list)
    - Watch: Be consistent; if you use a table, use it for all list commands
    - Mitigation: Define a single format_tasks(tasks) helper and reuse

11. **Update Command Complexity**
    - PATCH endpoint allows partial updates (some fields optional)
    - Watch: Don't require all fields; allow updating just title, or just priority
    - Mitigation: Parse JSON, check which keys are present, only update those

12. **Status Code 204 No Content**
    - DELETE returns 204 with empty body
    - Watch: Flask returns empty string by default; ensure no JSON is sent
    - Mitigation: Use `return "", 204` or `return None, 204`

---

## Testing Strategy

### Unit Test Scope
- `test_models.py`: Pure function tests, no file I/O, no network
- Test all validation rules (title, priority, status, notes constraints)
- Use `pytest.raises(ValueError)` to assert validation failures

### Integration Test Scope
- `test_storage.py`: File I/O with temp files (use pytest tmp_path fixture)
- `test_cli.py`: Command parsing and handler logic; mock storage or use temp files
- `test_api.py`: Flask routes with test client; mock storage or use temp files

### Mocking Strategy
- storage.load_tasks() and storage.save_tasks() can be mocked in CLI/API tests
- Alternatively, use real temp files to test end-to-end (integration style)
- Prefer real temp files for storage tests (verify actual JSON format)
- Prefer mocks for CLI/API if testing argument parsing vs. business logic

### Coverage Target
- Aim for 80%+ coverage on src/ (models, storage, cli, api)
- Exception paths: test at least one error case per function
- Edge cases: test boundary conditions (empty strings, max lengths, empty lists)

---

## Deliverables Checklist

- [ ] src/__init__.py (empty)
- [ ] src/models.py (Task + validation, 150 LOC)
- [ ] src/storage.py (load/save/get_next_id, 100 LOC)
- [ ] src/cli.py (argparse + 6 handlers, 200 LOC)
- [ ] src/api.py (Flask + 5 endpoints, 180 LOC)
- [ ] tests/__init__.py (empty)
- [ ] tests/test_models.py (12 test functions, 150 LOC)
- [ ] tests/test_storage.py (10 test functions, 120 LOC)
- [ ] tests/test_cli.py (12 test functions, 180 LOC)
- [ ] tests/test_api.py (14 test functions, 250 LOC)
- [ ] requirements.txt (Flask, pytest, Python 3.10+)
- [ ] README.md (installation, usage, testing)
- [ ] data/ directory (created at runtime)

**Estimated Total:**
- Source code: ~630 LOC
- Test code: ~700 LOC
- Total: ~1,330 LOC

---

## Definition of Done

1. All files created with correct structure
2. All functions have type hints and docstrings
3. No bare `except:` clauses
4. Test coverage >= 80% on src/
5. All CLI commands work: add, list, show, complete, delete
6. All API endpoints respond with correct status codes and JSON format
7. No functions over 30 lines (exceptions documented in review)
8. requirements.txt includes Flask and pytest
9. README.md explains setup and usage
10. Code passes `python -m pytest tests/` with all green
