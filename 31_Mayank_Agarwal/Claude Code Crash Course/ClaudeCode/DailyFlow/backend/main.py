import services
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class _CatchAllMiddleware(BaseHTTPMiddleware):
    """Return JSON error responses so CORS headers are applied before the browser sees them."""

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        try:
            return await call_next(request)
        except Exception as exc:
            return JSONResponse(status_code=500, content={"detail": str(exc)})


app = FastAPI(title="DailyPulse API")

# Order matters: _CatchAllMiddleware added first (inner), CORSMiddleware added second (outer).
# Actual request flow: CORS → CatchAll → routes.
# Exceptions caught by CatchAll bubble back through CORS, which attaches the allow-origin header.
app.add_middleware(_CatchAllMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TaskCreate(BaseModel):
    title: str


class TaskBreakdownRequest(BaseModel):
    task_description: str


@app.get("/briefing")
def get_briefing() -> dict:
    """Return today's morning briefing."""
    return services.get_briefing()


@app.get("/ai-news")
def get_ai_news() -> dict:
    """Fetch latest AI and tech news."""
    return services.get_ai_news()


@app.get("/tasks")
def get_tasks() -> list[dict]:
    """Return all tasks."""
    return services.read_tasks()


@app.post("/tasks", status_code=201)
def create_task(payload: TaskCreate) -> dict:
    """Create a task with AI-generated subtasks."""
    return services.create_task(payload.title)


@app.put("/tasks/{task_id}/complete")
def complete_task(task_id: str) -> dict:
    """Mark a task as complete."""
    task = services.complete_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: str) -> None:
    """Remove a task by id."""
    if not services.delete_task(task_id):
        raise HTTPException(status_code=404, detail="Task not found")


@app.post("/tasks/breakdown")
def get_task_breakdown(payload: TaskBreakdownRequest) -> dict:
    """Generate a detailed breakdown with time estimates for a task."""
    return services.get_task_breakdown(payload.task_description)


@app.get("/standup")
def get_standup() -> dict:
    """Generate a standup from today's completed tasks."""
    return {"standup": services.get_standup()}


@app.get("/insights")
def get_insights() -> dict:
    """Generate productivity insights from today's task patterns."""
    return {"insights": services.get_insights()}
