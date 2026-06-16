"""Command-line interface for QuickTask using argparse."""

import argparse
import sys
from datetime import datetime
from typing import NoReturn

from src.models import ValidationError, create_task, VALID_PRIORITIES
from src.storage import load_tasks, save_tasks, get_next_id, find_task, StorageError


def format_task_row(task: object) -> str:
    """Format a single task for tabular display.

    Args:
        task: Task instance with id, title, priority, status attributes

    Returns:
        Formatted row string
    """
    return f"{task.id:<4} | {task.title:<30} | {task.priority:<8} | {task.status:<8}"


def print_table_header() -> None:
    """Print the header row for task table."""
    print("ID   | Title                          | Priority | Status  ")
    print("-" * 60)


def cmd_add(args: argparse.Namespace) -> None:
    """Handle the 'add' subcommand.

    Creates a new task with the given title and optional priority.

    Args:
        args: Namespace with title and priority attributes
    """
    try:
        # Load existing tasks to determine next ID
        tasks = load_tasks()
        next_id = get_next_id(tasks)

        # Validate priority
        if args.priority not in VALID_PRIORITIES:
            print(
                f"Error: Invalid priority '{args.priority}'. Must be one of: {', '.join(VALID_PRIORITIES)}",
                file=sys.stderr,
            )
            sys.exit(1)

        # Create new task
        task = create_task(
            task_id=next_id,
            title=args.title,
            priority=args.priority,
            status="pending",
            created_at=datetime.now().isoformat(),
            notes=getattr(args, "notes", ""),
        )

        # Save tasks
        tasks.append(task)
        save_tasks(tasks)

        # Print success message
        print(f"✓ Task #{task.id} created: {task.title} [{task.priority}]")

    except ValidationError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except StorageError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_list(args: argparse.Namespace) -> None:
    """Handle the 'list' subcommand.

    Lists all tasks, optionally filtered by status.

    Args:
        args: Namespace with optional status attribute
    """
    try:
        tasks = load_tasks()

        # Filter by status if provided
        if args.status:
            tasks = [t for t in tasks if t.status == args.status]

        if not tasks:
            print("No tasks found.")
            return

        # Print table
        print_table_header()
        for task in tasks:
            print(format_task_row(task))

    except StorageError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_show(args: argparse.Namespace) -> None:
    """Handle the 'show' subcommand.

    Displays details for a specific task by ID.

    Args:
        args: Namespace with task_id attribute
    """
    try:
        tasks = load_tasks()
        task = find_task(tasks, args.task_id)

        if not task:
            print(f"Error: Task #{args.task_id} not found", file=sys.stderr)
            sys.exit(1)

        # Print task details
        print(f"Task #{task.id}: {task.title}")
        print(f"Priority:  {task.priority}")
        print(f"Status:    {task.status}")
        print(f"Created:   {task.created_at}")
        if task.notes:
            print(f"Notes:     {task.notes}")

    except StorageError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_complete(args: argparse.Namespace) -> None:
    """Handle the 'complete' subcommand.

    Marks a task as done.

    Args:
        args: Namespace with task_id attribute
    """
    try:
        tasks = load_tasks()
        task = find_task(tasks, args.task_id)

        if not task:
            print(f"Error: Task #{args.task_id} not found", file=sys.stderr)
            sys.exit(1)

        # Update status
        task.status = "done"
        save_tasks(tasks)

        print(f"✓ Task #{task.id} marked as done")

    except StorageError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_delete(args: argparse.Namespace) -> None:
    """Handle the 'delete' subcommand.

    Removes a task by ID.

    Args:
        args: Namespace with task_id attribute
    """
    try:
        tasks = load_tasks()
        task = find_task(tasks, args.task_id)

        if not task:
            print(f"Error: Task #{args.task_id} not found", file=sys.stderr)
            sys.exit(1)

        # Remove task
        tasks = [t for t in tasks if t.id != args.task_id]
        save_tasks(tasks)

        print(f"✓ Task #{args.task_id} deleted")

    except StorageError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_update(args: argparse.Namespace) -> None:
    """Handle the 'update' subcommand.

    Updates one or more fields of a task.

    Args:
        args: Namespace with task_id and optional title, priority, status, notes
    """
    try:
        tasks = load_tasks()
        task = find_task(tasks, args.task_id)

        if not task:
            print(f"Error: Task #{args.task_id} not found", file=sys.stderr)
            sys.exit(1)

        # Update fields if provided
        if hasattr(args, "title") and args.title:
            task.title = args.title

        if hasattr(args, "priority") and args.priority:
            if args.priority not in VALID_PRIORITIES:
                print(
                    f"Error: Invalid priority '{args.priority}'. Must be one of: {', '.join(VALID_PRIORITIES)}",
                    file=sys.stderr,
                )
                sys.exit(1)
            task.priority = args.priority

        if hasattr(args, "status") and args.status:
            task.status = args.status

        if hasattr(args, "notes") and args.notes is not None:
            task.notes = args.notes

        # Validate the updated task
        from src.models import validate

        validate(task)

        # Save
        save_tasks(tasks)
        print(f"✓ Task #{task.id} updated")

    except ValidationError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except StorageError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def main(args: list[str] | None = None) -> None:
    """Entry point for the QuickTask CLI.

    Parses command-line arguments and dispatches to appropriate handler.

    Args:
        args: List of command-line arguments (defaults to sys.argv[1:])
    """
    parser = argparse.ArgumentParser(
        description="QuickTask — manage your tasks", exit_on_error=False
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # 'add' command
    add_parser = subparsers.add_parser("add", help="Create a new task")
    add_parser.add_argument("title", help="Task title")
    add_parser.add_argument(
        "--priority",
        default="normal",
        help="Priority level: low, normal, or high (default: normal)",
    )
    add_parser.add_argument("--notes", default="", help="Optional task notes")
    add_parser.set_defaults(func=cmd_add)

    # 'list' command
    list_parser = subparsers.add_parser("list", help="List all tasks")
    list_parser.add_argument(
        "--status", choices=["pending", "done"], help="Filter by status"
    )
    list_parser.set_defaults(func=cmd_list)

    # 'show' command
    show_parser = subparsers.add_parser("show", help="Show task details")
    show_parser.add_argument("task_id", type=int, help="Task ID")
    show_parser.set_defaults(func=cmd_show)

    # 'complete' command
    complete_parser = subparsers.add_parser("complete", help="Mark task as done")
    complete_parser.add_argument("task_id", type=int, help="Task ID")
    complete_parser.set_defaults(func=cmd_complete)

    # 'delete' command
    delete_parser = subparsers.add_parser("delete", help="Delete a task")
    delete_parser.add_argument("task_id", type=int, help="Task ID")
    delete_parser.set_defaults(func=cmd_delete)

    # 'update' command
    update_parser = subparsers.add_parser("update", help="Update a task")
    update_parser.add_argument("task_id", type=int, help="Task ID")
    update_parser.add_argument("--title", help="New title")
    update_parser.add_argument("--priority", help="New priority: low, normal, or high")
    update_parser.add_argument(
        "--status", choices=["pending", "done"], help="New status"
    )
    update_parser.add_argument("--notes", help="New notes")
    update_parser.set_defaults(func=cmd_update)

    # Parse arguments
    try:
        parsed_args = parser.parse_args(args)
    except SystemExit as e:
        if e.code != 0:
            sys.exit(1)
        sys.exit(0)

    # Dispatch to handler
    try:
        parsed_args.func(parsed_args)
    except AttributeError:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
