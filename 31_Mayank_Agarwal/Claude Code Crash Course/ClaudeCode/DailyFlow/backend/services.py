import json
import os
import uuid
from datetime import datetime, date, timezone
from pathlib import Path

from openai import OpenAI
from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()

_client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
)

_tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
_MODEL = "google/gemini-2.5-flash"
_TAVILY_ENABLED = os.getenv("TAVILY_ENABLED", "false").lower() == "true"

DATA_DIR = Path(__file__).parent / "data"
TASKS_FILE = DATA_DIR / "tasks.json"
BRIEFING_FILE = DATA_DIR / "briefing.json"


# ── file I/O ──────────────────────────────────────────────────────────────────


def read_tasks() -> list[dict]:
    """Read all tasks from tasks.json."""
    if not TASKS_FILE.exists():
        return []
    with open(TASKS_FILE) as f:
        return json.load(f)


def write_tasks(tasks: list[dict]) -> None:
    """Persist tasks list to tasks.json."""
    with open(TASKS_FILE, "w") as f:
        json.dump(tasks, f, indent=2, default=str)


# ── date helpers ──────────────────────────────────────────────────────────────


def today_str() -> str:
    """Return today's date as an ISO string (YYYY-MM-DD)."""
    return date.today().isoformat()


def filter_today(tasks: list[dict]) -> list[dict]:
    """Return tasks created today."""
    today = today_str()
    return [t for t in tasks if t.get("created_at", "").startswith(today)]


def filter_completed_today(tasks: list[dict]) -> list[dict]:
    """Return tasks completed today."""
    today = today_str()
    return [
        t
        for t in tasks
        if t.get("completed") and (t.get("completed_at") or "").startswith(today)
    ]


# ── OpenRouter ────────────────────────────────────────────────────────────────


def _ask_gemini(prompt: str) -> str:
    """Send a prompt via OpenRouter and return the text response. Raises RuntimeError on failure."""
    try:
        response = _client.chat.completions.create(
            model=_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
        )
        return response.choices[0].message.content.strip()
    except Exception as exc:
        raise RuntimeError(f"OpenRouter error: {exc}") from exc


def _strip_fences(raw: str) -> str:
    """Remove markdown code fences that Gemini sometimes wraps around JSON."""
    return (
        raw.strip()
        .removeprefix("```json")
        .removeprefix("```")
        .removesuffix("```")
        .strip()
    )


def _fetch_web_tip() -> str | None:
    """Fetch a productivity tip from the web via Tavily. Returns None on failure."""
    if not _TAVILY_ENABLED or not os.getenv("TAVILY_API_KEY"):
        return None

    try:
        today = today_str()
        query = f"productivity tip for developers {today}"
        response = _tavily_client.search(query=query, max_results=1)

        if response.get("results"):
            result = response["results"][0]
            return result.get("content") or result.get("title")
        return None
    except Exception:
        return None


# ── business logic ────────────────────────────────────────────────────────────


def _read_briefings() -> dict:
    """Read the full briefings store (date → briefing dict)."""
    if not BRIEFING_FILE.exists():
        return {}
    with open(BRIEFING_FILE) as f:
        return json.load(f)


def _write_briefings(briefings: dict) -> None:
    """Persist the full briefings store."""
    with open(BRIEFING_FILE, "w") as f:
        json.dump(briefings, f, indent=2)


def get_briefing() -> dict:
    """Return today's briefing, generating it via Gemini if not yet cached."""
    today = today_str()
    briefings = _read_briefings()

    if today in briefings:
        return briefings[today]

    try:
        prompt = (
            "You are a productivity coach. Generate a morning briefing with exactly three fields:\n"
            "1. quote: a short motivational quote (one sentence)\n"
            "2. focus_tip: a practical focus tip for the day (one sentence)\n"
            "3. message: an encouraging message under 50 words\n\n"
            "Reply with a JSON object only — no markdown, no extra text."
        )
        raw = _ask_gemini(prompt)
        try:
            briefing = json.loads(_strip_fences(raw))
        except json.JSONDecodeError:
            briefing = {"quote": raw, "focus_tip": "", "message": ""}
    except RuntimeError:
        # Fallback when Gemini API fails
        briefing = {
            "quote": "Every day is a chance to improve.",
            "focus_tip": "Start your day by identifying your top 3 priorities.",
            "message": "Focus on what matters most. You've got this!"
        }

    briefing["date"] = today

    # Fetch web tip if enabled, gracefully degrade if unavailable
    web_tip = _fetch_web_tip()
    if web_tip:
        briefing["web_tip"] = web_tip

    briefings[today] = briefing
    _write_briefings(briefings)

    return briefing


def create_task(title: str) -> dict:
    """Create a new task with AI-generated subtasks and persist it. Falls back to manual breakdown if AI fails."""
    prompt = (
        f"Break this task into 3 to 5 concrete, actionable subtasks:\n\nTask: {title}\n\n"
        "Reply with a JSON array of strings only — no markdown, no extra text. "
        'Example: ["subtask 1", "subtask 2", "subtask 3"]'
    )
    subtasks = []
    try:
        raw = _ask_gemini(prompt)
        parsed = json.loads(_strip_fences(raw))
        if isinstance(parsed, list):
            subtasks = parsed
    except (RuntimeError, json.JSONDecodeError):
        # AI failed or returned invalid JSON — use fallback
        subtasks = ["Break this task down manually"]

    task = {
        "id": str(uuid.uuid4()),
        "title": title,
        "subtasks": subtasks,
        "completed": False,
        "completed_at": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    tasks = read_tasks()
    tasks.append(task)
    write_tasks(tasks)

    return task


def complete_task(task_id: str) -> dict | None:
    """Mark a task complete. Returns the updated task, or None if not found."""
    tasks = read_tasks()
    for task in tasks:
        if task["id"] == task_id:
            task["completed"] = True
            task["completed_at"] = datetime.now(timezone.utc).isoformat()
            write_tasks(tasks)
            return task
    return None


def delete_task(task_id: str) -> bool:
    """Remove a task by id. Returns True if deleted, False if not found."""
    tasks = read_tasks()
    filtered = [t for t in tasks if t["id"] != task_id]
    if len(filtered) == len(tasks):
        return False
    write_tasks(filtered)
    return True


def get_standup() -> str:
    """Generate a professional standup from today's completed tasks."""
    tasks = read_tasks()
    done = filter_completed_today(tasks)

    if not done:
        return "No tasks were completed today yet."

    try:
        completed_lines = "\n".join(f"- {t['title']}" for t in done)
        pending = [t["title"] for t in filter_today(tasks) if not t.get("completed")]
        pending_lines = "\n".join(f"- {p}" for p in pending) if pending else "None"

        prompt = (
            "Write a concise professional standup update based on these tasks.\n\n"
            f"Completed today:\n{completed_lines}\n\n"
            f"Still pending:\n{pending_lines}\n\n"
            "Format:\n"
            "**Yesterday / Today:** [what was done]\n"
            "**Up Next:** [what's planned]\n"
            "**Blockers:** [any blockers, or 'None']\n\n"
            "Keep it under 100 words."
        )
        return _ask_gemini(prompt)
    except RuntimeError:
        completed_lines = "\n".join(f"- {t['title']}" for t in done)
        pending = [t["title"] for t in filter_today(tasks) if not t.get("completed")]
        pending_lines = "\n".join(f"- {p}" for p in pending) if pending else "None"
        return f"**Yesterday / Today:** {len(done)} tasks completed\n**Up Next:** {len([t for t in filter_today(tasks) if not t.get('completed')])} tasks pending\n**Blockers:** None"


def get_insights() -> str:
    """Generate productivity insights from today's task patterns."""
    tasks = read_tasks()
    all_today = filter_today(tasks)

    if not all_today:
        return "No tasks recorded today yet."

    try:
        total = len(all_today)
        completed = [t for t in all_today if t.get("completed")]
        completion_rate = round(len(completed) / total * 100)

        task_summary = json.dumps(
            [
                {
                    "title": t["title"],
                    "completed": t["completed"],
                    "completed_at": t.get("completed_at"),
                }
                for t in all_today
            ],
            indent=2,
        )

        prompt = (
            "Analyse these task completion patterns and give 3 short productivity insights.\n\n"
            f"Tasks today (total: {total}, completed: {len(completed)}, rate: {completion_rate}%):\n"
            f"{task_summary}\n\n"
            "Cover: peak productivity window (if determinable), completion rate observation, "
            "one actionable improvement suggestion. Be concise — under 120 words total."
        )
        return _ask_gemini(prompt)
    except RuntimeError:
        total = len(all_today)
        completed = [t for t in all_today if t.get("completed")]
        completion_rate = round(len(completed) / total * 100) if total > 0 else 0
        return f"Today's Summary: {total} tasks created, {len(completed)} completed ({completion_rate}%). Keep building momentum!"


def get_task_breakdown(task_description: str) -> dict:
    """Generate a detailed task breakdown with time estimates for each subtask."""
    prompt = (
        f"Create a detailed breakdown for this task with time estimates:\n\nTask: {task_description}\n\n"
        "Reply with a JSON object with this structure:\n"
        "{\n"
        '  "title": "brief task name",\n'
        '  "subtasks": [\n'
        '    {"step": "subtask description", "estimated_minutes": 15},\n'
        '    {"step": "next subtask", "estimated_minutes": 30}\n'
        "  ],\n"
        '  "total_estimated_minutes": 45,\n'
        '  "notes": "optional context or tips"\n'
        "}\n\n"
        "Reply with only valid JSON — no markdown, no extra text."
    )
    raw = _ask_gemini(prompt)
    try:
        breakdown = json.loads(_strip_fences(raw))
        # Validate structure
        if not isinstance(breakdown, dict):
            breakdown = {}
    except json.JSONDecodeError:
        breakdown = {}

    # Ensure required fields exist
    if "title" not in breakdown:
        breakdown["title"] = task_description
    if "subtasks" not in breakdown:
        breakdown["subtasks"] = []
    if "total_estimated_minutes" not in breakdown:
        breakdown["total_estimated_minutes"] = 0
    if "notes" not in breakdown:
        breakdown["notes"] = ""

    return breakdown


def get_ai_news() -> dict:
    """Fetch latest AI and tech news from Tavily."""
    if not _TAVILY_ENABLED or not os.getenv("TAVILY_API_KEY"):
        return {"news": [], "error": "Tavily not enabled"}

    try:
        response = _tavily_client.search(
            query="latest AI technology news and developments",
            max_results=5
        )
        news_items = []
        for result in response.get("results", []):
            news_items.append({
                "title": result.get("title", ""),
                "content": result.get("content", "")[:200],
                "source": result.get("source", ""),
            })
        return {"news": news_items}
    except Exception:
        return {"news": [], "error": "Could not fetch AI news"}
