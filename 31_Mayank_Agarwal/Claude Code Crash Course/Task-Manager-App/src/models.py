"""Task data model with validation."""

from dataclasses import dataclass
from typing import Any

# Valid priority values
VALID_PRIORITIES: list[str] = ["low", "normal", "high"]

# Valid status values
VALID_STATUSES: list[str] = ["pending", "done"]

# Validation constraints
MIN_TITLE_LENGTH: int = 1
MAX_TITLE_LENGTH: int = 200
MAX_NOTES_LENGTH: int = 500


@dataclass
class Task:
    """Task data model with 6 fields."""

    id: int
    title: str
    priority: str
    status: str
    created_at: str
    notes: str = ""


class ValidationError(ValueError):
    """Custom exception for task validation errors."""

    pass


def validate(task: Task) -> None:
    """Validate a Task instance and raise ValidationError if any field is invalid.

    Validates:
    - title: 1-200 characters, non-empty
    - priority: one of "low", "normal", "high"
    - status: one of "pending", "done"
    - notes: max 500 characters
    - created_at: non-empty string (assumes ISO 8601 format)

    Args:
        task: Task instance to validate

    Raises:
        ValidationError: if any field is invalid
    """
    # Validate title
    if not task.title or not task.title.strip():
        raise ValidationError("Title cannot be empty")
    if len(task.title) < MIN_TITLE_LENGTH:
        raise ValidationError(f"Title must be at least {MIN_TITLE_LENGTH} character")
    if len(task.title) > MAX_TITLE_LENGTH:
        raise ValidationError(f"Title must be {MAX_TITLE_LENGTH} characters or fewer")

    # Validate priority
    if task.priority not in VALID_PRIORITIES:
        raise ValidationError(f"Priority must be one of: {', '.join(VALID_PRIORITIES)}")

    # Validate status
    if task.status not in VALID_STATUSES:
        raise ValidationError(f"Status must be one of: {', '.join(VALID_STATUSES)}")

    # Validate notes
    if len(task.notes) > MAX_NOTES_LENGTH:
        raise ValidationError(f"Notes must be {MAX_NOTES_LENGTH} characters or fewer")

    # Validate created_at
    if not task.created_at or not str(task.created_at).strip():
        raise ValidationError("created_at cannot be empty")


def to_dict(task: Task) -> dict[str, Any]:
    """Convert Task instance to JSON-serializable dictionary.

    Args:
        task: Task instance to convert

    Returns:
        Dictionary with all Task fields
    """
    return {
        "id": task.id,
        "title": task.title,
        "priority": task.priority,
        "status": task.status,
        "created_at": task.created_at,
        "notes": task.notes,
    }


def from_dict(data: dict[str, Any]) -> Task:
    """Create Task instance from dictionary, with full validation.

    Args:
        data: Dictionary with at least id, title, priority, status, created_at

    Returns:
        Validated Task instance

    Raises:
        ValidationError: if required fields are missing or invalid
        KeyError: if required fields are missing
        TypeError: if field types are wrong
    """
    # Extract required fields
    try:
        task_id = data["id"]
        title = data["title"]
        priority = data["priority"]
        status = data["status"]
        created_at = data["created_at"]
    except KeyError as e:
        raise ValidationError(f"Missing required field: {e}") from e

    # Extract optional fields
    notes = data.get("notes", "")

    # Create Task instance
    task = Task(
        id=task_id,
        title=title,
        priority=priority,
        status=status,
        created_at=created_at,
        notes=notes,
    )

    # Validate all fields
    validate(task)

    return task


def create_task(
    task_id: int,
    title: str,
    priority: str = "normal",
    status: str = "pending",
    created_at: str = "",
    notes: str = "",
) -> Task:
    """Create a new Task instance with full validation.

    Args:
        task_id: Unique task identifier
        title: Task title (1-200 characters)
        priority: Task priority ("low", "normal", or "high"), defaults to "normal"
        status: Task status ("pending" or "done"), defaults to "pending"
        created_at: ISO 8601 datetime string of creation time
        notes: Optional notes (max 500 characters), defaults to empty string

    Returns:
        Validated Task instance

    Raises:
        ValidationError: if any field is invalid
    """
    task = Task(
        id=task_id,
        title=title,
        priority=priority,
        status=status,
        created_at=created_at,
        notes=notes,
    )
    validate(task)
    return task
