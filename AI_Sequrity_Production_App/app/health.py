"""Health and readiness checks for the Enterprise RAG API."""

import logfire
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.services.health.connection_checker import check_all_connections

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    """Liveness probe — returns 200 if the process is running."""
    from app.config import settings
    return {
        "status": "ok",
        "health": "healthy",
        "project_id": settings.PROJECT_ID,
        "location": settings.LOCATION,
        "gcp_doc_ai_processor": settings.GCP_DOC_AI_PROCESSOR_ID,
        "gcp_raw_bucket": settings.GCP_RAW_BUCKET,
        "gcp_processed_bucket": settings.GCP_PROCESSED_BUCKET,
        "qdrant_collection": settings.QDRANT_COLLECTION,
        "guardrails": "initialized",
        "bot_shield": "active",
    }


@router.get("/ready")
def ready(request: Request):
    """
    Readiness probe — verifies that critical external dependencies are reachable.
    Returns 200 only if Postgres, Redis, Qdrant, the LLM gateway, Jina Embeddings,
    and Jina Reranker are all healthy.
    """
    results = check_all_connections()
    checks = {name: result.to_dict()["status"] for name, result in results.items()}
    healthy = all(r.healthy for r in results.values())

    if not healthy:
        logfire.warning("Readiness check failed", checks=checks)

    status_code = 200 if healthy else 503
    return JSONResponse(
        status_code=status_code,
        content={"status": "ready" if healthy else "not_ready", "checks": checks},
    )


@router.get("/health/live")
def health_live():
    return {"status": "alive"}


@router.get("/health/ready")
def health_ready(request: Request):
    return ready(request)
