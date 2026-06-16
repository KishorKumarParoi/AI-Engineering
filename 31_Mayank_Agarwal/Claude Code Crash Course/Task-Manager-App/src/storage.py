"""JSON file storage for tasks."""

import json
from pathlib import Path
from typing import Any

from src.models import Task, from_dict, to_dict

# Storage configuration
DATA_DIR: Path = Path("data")
TASKS_FILE: Path = DATA_DIR / "tasks.json"


class StorageError(Exception):
    """Custom exception for storage-related errors."""

    pass


def _ensure_data_dir() -> None:
    """Create data directory if it doesn't exist.

    Raises:
        StorageError: if directory cannot be created
    """
    try:
        DATA_DIR.mkdir(exist_ok=True)
    except (OSError, IOError) as e:
        raise StorageError(f"Cannot create data directory: {e}") from e


def load_tasks() -> list[Task]:
    """Load all tasks from JSON file.

    Returns empty list if file doesn't exist. Parses JSON and converts
    each dict to a Task instance using from_dict().

    Returns:
        List of Task instances (empty list if file not found)

    Raises:
        StorageError: if JSON file is corrupted or cannot be read
    """
    if not TASKS_FILE.exists():
        return []

    try:
        with open(TASKS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise StorageError(f"Corrupt data file: {e}") from e
    except (OSError, IOError) as e:
        raise StorageError(f"Cannot read data file: {e}") from e

    # Convert dict list to Task list
    try:
        tasks: list[Task] = [from_dict(item) for item in data]
        return tasks
    except (TypeError, KeyError, ValueError) as e:
        raise StorageError(f"Invalid task data in file: {e}") from e


def save_tasks(tasks: list[Task]) -> None:
    """Write tasks to JSON file with pretty formatting.

    Creates data directory if it doesn't exist. Writes tasks as JSON array
    with 2-space indentation.

    Args:
        tasks: List of Task instances to save

    Raises:
        StorageError: if directory cannot be created or file cannot be written
    """
    _ensure_data_dir()

    # Convert Task instances to dicts
    task_dicts: list[dict[str, Any]] = [to_dict(task) for task in tasks]

    try:
        with open(TASKS_FILE, "w", encoding="utf-8") as f:
            json.dump(task_dicts, f, indent=2)
    except (OSError, IOError) as e:
        raise StorageError(f"Cannot write data file: {e}") from e


def get_next_id(tasks: list[Task]) -> int:
    """Get the next available task ID.

    Returns 1 if task list is empty, otherwise returns max(task.id) + 1.

    Args:
        tasks: List of Task instances

    Returns:
        Next available ID (always >= 1)
    """
    if not tasks:
        return 1
    return max(task.id for task in tasks) + 1


def find_task(tasks: list[Task], task_id: int) -> Task | None:
    """Find a task by ID in a list of tasks.

    Args:
        tasks: List of Task instances to search
        task_id: ID of task to find

    Returns:
        Task instance if found, None otherwise
    """
    for task in tasks:
        if task.id == task_id:
            return task
    return None
