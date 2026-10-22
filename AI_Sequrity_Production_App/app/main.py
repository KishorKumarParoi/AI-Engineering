# ============================================================
# CRITICAL: logfire MUST be configured before ALL other imports
# so that spans from all modules are captured from the start.
# ============================================================
import logfire
import os
from dotenv import load_dotenv

load_dotenv()
logfire.configure(token=os.getenv("LOGFIRE_TOKEN"))

# Now safe to import app modules - logfire is already active
from fastapi import FastAPI, Response, HTTPException
from app.config import settings
from app.agents.graph import rag_agent
from app.guardrails import initialize_rails, guard
from app.middleware.bot_shield import BotShieldMiddleware

from pydantic import BaseModel, Field
from typing import Optional


# Initialize FastAPI
app = FastAPI(
    title="Enterprise Agentic RAG API",
    description="Production RAG with NeMo Guardrails, LangGraph Multi-Agent, and Bot Defense Shield",
    version="2.0.0",
)

# Attach Enterprise Bot Attack & Rate Limiting Shield
app.add_middleware(BotShieldMiddleware)


@app.on_event("startup")
def startup_event():
    initialize_rails()


class QueryRequest(BaseModel):
    q: str = Field(..., min_length=1, max_length=4096, description="User query prompt")
    thread_id: Optional[str] = Field("default_user", max_length=128, description="Session thread ID")


@app.get("/")
def home():
    return {
        "message": "Enterprise LangGraph RAG API is live and protected.",
        "defense": "BotShield active",
        "version": "2.0.0",
    }


@app.get("/health")
def health_check():
    """Liveness probe for Cloud Run, Kubernetes, and monitoring health checks."""
    return {
        "status": "healthy",
        "project_id": settings.PROJECT_ID,
        "location": settings.LOCATION,
        "gcp_doc_ai_processor": settings.GCP_DOC_AI_PROCESSOR_ID,
        "gcp_raw_bucket": settings.GCP_RAW_BUCKET,
        "gcp_processed_bucket": settings.GCP_PROCESSED_BUCKET,
        "qdrant_collection": settings.QDRANT_COLLECTION,
        "guardrails": "initialized",
        "bot_shield": "active",
    }


@app.get("/ready")
def readiness_check():
    """
    Readiness probe — verifies that critical external dependencies are reachable.
    Returns 200 if critical services (Neon Postgres, Qdrant, Portkey, Jina) are operational.
    """
    from app.services.health.connection_checker import check_all_connections
    from fastapi.responses import JSONResponse

    results = check_all_connections()
    checks = {name: result.to_dict()["status"] for name, result in results.items()}
    critical_healthy = all(
        results[k].healthy for k in ("postgres", "qdrant", "llm_gateway", "jina_embeddings", "jina_reranker")
        if k in results
    )
    status_code = 200 if critical_healthy else 503
    return JSONResponse(
        status_code=status_code,
        content={"status": "ready" if critical_healthy else "not_ready", "checks": checks},
    )



@app.get("/graph")
def get_graph_image():
    """
    Returns the Mermaid image of the agent's workflow.
    """
    try:
        png_bytes = rag_agent.get_graph().draw_mermaid_png()
        return Response(content=png_bytes, media_type="image/png")
    except Exception as e:
        return {"error": f"Could not generate graph image: {e}"}
    
    
@app.post("/query")
def query(request: QueryRequest):
    """
    Executes the LangGraph RAG flow with memory using a POST request.
    """
    q = request.q
    thread_id = request.thread_id

    initial_state = {
        "messages": [{"role": "user", "content": q}],
        "current_query": q,
        "documents": [],
        "plan": ["Start"],
        "status": "Initializing Graph..."
    }
    
    # Configuration for Memory (Thread ID)
    config = {"configurable": {"thread_id": thread_id}}
    
    try:
        # Gate 1: NeMo Guardrails — blocks off-topic, jailbreaks, and handles dialog
        rail_fired, rail_response = guard(q)
        if rail_fired:
            logfire.info(f"🛡️ Request blocked by guardrails | thread={thread_id}")
            return {
                "question": q,
                "answer": rail_response,
                "thought_process": ["Intent: Guardrails Fired", "Retrieval: Skipped"],
                "status": "Blocked by guardrails.",
                "sources": []
            }

        # Gate 2: LangGraph RAG pipeline
        # Run the graph synchronously to preserve Logfire context variables
        final_output = rag_agent.invoke(initial_state, config=config)
        
        return {
            "question": q,
            "answer": final_output.get("final_answer"),
            "thought_process": final_output.get("plan"),
            "status": final_output.get("status"),
            "sources": final_output.get("documents", [])
        }
    except Exception as e:
        logfire.error(f"❌ Backend Execution Failed: {e}")
        return {
            "question": q,
            "answer": "I apologize, but I encountered an internal error while processing your request. Please try again later.",
            "thought_process": ["Error encountered during execution."],
            "status": "error",
            "sources": []
        }
