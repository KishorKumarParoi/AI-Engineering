"""Flask REST API for QuickTask."""

from datetime import datetime
from typing import Any

from flask import Flask, jsonify, request

from src.models import (
    ValidationError,
    create_task,
    validate,
    VALID_PRIORITIES,
    VALID_STATUSES,
)
from src.storage import load_tasks, save_tasks, get_next_id, find_task, StorageError

# Response format constants
RESPONSE_DATA_KEY = "data"
RESPONSE_ERROR_KEY = "error"

# Status codes
STATUS_OK = 200
STATUS_CREATED = 201
STATUS_NO_CONTENT = 204
STATUS_BAD_REQUEST = 400
STATUS_NOT_FOUND = 404
STATUS_SERVER_ERROR = 500


def create_app() -> Flask:
    """Create and configure Flask app.

    Returns:
        Configured Flask application instance
    """
    app = Flask(__name__)

    @app.errorhandler(Exception)
    def handle_error(error: Exception) -> tuple[Any, int]:
        """Handle uncaught exceptions and return consistent JSON error response.

        Args:
            error: Exception instance

        Returns:
            JSON error response with 500 status
        """
        return error_response("Internal server error", STATUS_SERVER_ERROR)

    @app.route("/tasks", methods=["GET"])
    def list_tasks() -> tuple[Any, int]:
        """List all tasks, optionally filtered by status.

        Query Parameters:
            status (optional): Filter by "pending" or "done"

        Returns:
            JSON response with list of tasks
        """
        try:
            tasks = load_tasks()

            # Filter by status if provided
            status_filter = request.args.get("status")
            if status_filter:
                tasks = [t for t in tasks if t.status == status_filter]

            # Convert to dicts
            from src.models import to_dict

            task_dicts = [to_dict(t) for t in tasks]

            return success_response(task_dicts, STATUS_OK)

        except StorageError as e:
            return error_response(str(e), STATUS_SERVER_ERROR)

    @app.route("/tasks", methods=["POST"])
    def create_task_endpoint() -> tuple[Any, int]:
        """Create a new task.

        JSON Body:
            title (required): Task title (1-200 chars)
            priority (optional): "low", "normal", or "high" (default: "normal")
            notes (optional): Task notes (max 500 chars)

        Returns:
            JSON response with created task (201 status)
        """
        try:
            # Parse JSON
            data = request.get_json()
            if not data:
                return error_response("Request body must be JSON", STATUS_BAD_REQUEST)

            # Extract fields
            title = data.get("title")
            if not title:
                return error_response(
                    "Missing required field: title", STATUS_BAD_REQUEST
                )

            priority = data.get("priority", "normal")
            notes = data.get("notes", "")

            # Validate priority
            if priority not in VALID_PRIORITIES:
                return error_response(
                    f"Invalid priority. Must be one of: {', '.join(VALID_PRIORITIES)}",
                    STATUS_BAD_REQUEST,
                )

            # Load tasks and get next ID
            tasks = load_tasks()
            next_id = get_next_id(tasks)

            # Create task
            task = create_task(
                task_id=next_id,
                title=title,
                priority=priority,
                status="pending",
                created_at=datetime.now().isoformat(),
                notes=notes,
            )

            # Save and return
            tasks.append(task)
            save_tasks(tasks)

            from src.models import to_dict

            return success_response(to_dict(task), STATUS_CREATED)

        except ValidationError as e:
            return error_response(str(e), STATUS_BAD_REQUEST)
        except StorageError as e:
            return error_response(str(e), STATUS_SERVER_ERROR)

    @app.route("/tasks/<int:task_id>", methods=["GET"])
    def get_task(task_id: int) -> tuple[Any, int]:
        """Get a single task by ID.

        Args:
            task_id: Task ID

        Returns:
            JSON response with task (200) or error (404)
        """
        try:
            tasks = load_tasks()
            task = find_task(tasks, task_id)

            if not task:
                return error_response(f"Task #{task_id} not found", STATUS_NOT_FOUND)

            from src.models import to_dict

            return success_response(to_dict(task), STATUS_OK)

        except StorageError as e:
            return error_response(str(e), STATUS_SERVER_ERROR)

    @app.route("/tasks/<int:task_id>", methods=["PATCH"])
    def update_task(task_id: int) -> tuple[Any, int]:
        """Update a task.

        JSON Body (all fields optional):
            title: New title
            priority: New priority ("low", "normal", or "high")
            status: New status ("pending" or "done")
            notes: New notes

        Returns:
            JSON response with updated task (200) or error (404/400)
        """
        try:
            # Parse JSON
            data = request.get_json()
            if not data:
                return error_response("Request body must be JSON", STATUS_BAD_REQUEST)

            # Load tasks
            tasks = load_tasks()
            task = find_task(tasks, task_id)

            if not task:
                return error_response(f"Task #{task_id} not found", STATUS_NOT_FOUND)

            # Update fields if provided
            if "title" in data:
                task.title = data["title"]

            if "priority" in data:
                priority = data["priority"]
                if priority not in VALID_PRIORITIES:
                    return error_response(
                        f"Invalid priority. Must be one of: {', '.join(VALID_PRIORITIES)}",
                        STATUS_BAD_REQUEST,
                    )
                task.priority = priority

            if "status" in data:
                status = data["status"]
                if status not in VALID_STATUSES:
                    return error_response(
                        f"Invalid status. Must be one of: {', '.join(VALID_STATUSES)}",
                        STATUS_BAD_REQUEST,
                    )
                task.status = status

            if "notes" in data:
                task.notes = data["notes"]

            # Validate updated task
            validate(task)

            # Save and return
            save_tasks(tasks)

            from src.models import to_dict

            return success_response(to_dict(task), STATUS_OK)

        except ValidationError as e:
            return error_response(str(e), STATUS_BAD_REQUEST)
        except StorageError as e:
            return error_response(str(e), STATUS_SERVER_ERROR)

    @app.route("/tasks/<int:task_id>", methods=["DELETE"])
    def delete_task(task_id: int) -> tuple[Any, int]:
        """Delete a task.

        Args:
            task_id: Task ID

        Returns:
            Empty response (204) or error (404)
        """
        try:
            tasks = load_tasks()
            task = find_task(tasks, task_id)

            if not task:
                return error_response(f"Task #{task_id} not found", STATUS_NOT_FOUND)

            # Remove and save
            tasks = [t for t in tasks if t.id != task_id]
            save_tasks(tasks)

            return "", STATUS_NO_CONTENT

        except StorageError as e:
            return error_response(str(e), STATUS_SERVER_ERROR)

    return app


def success_response(data: Any, status: int = STATUS_OK) -> tuple[Any, int]:
    """Build a successful JSON response.

    Args:
        data: Response data
        status: HTTP status code (default: 200)

    Returns:
        Tuple of (JSON response dict, status code)
    """
    return jsonify({RESPONSE_DATA_KEY: data, RESPONSE_ERROR_KEY: None}), status


def error_response(message: str, status: int = STATUS_BAD_REQUEST) -> tuple[Any, int]:
    """Build an error JSON response.

    Args:
        message: Error message
        status: HTTP status code (default: 400)

    Returns:
        Tuple of (JSON response dict, status code)
    """
    return jsonify({RESPONSE_DATA_KEY: None, RESPONSE_ERROR_KEY: message}), status


# Create app instance for running directly
app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
