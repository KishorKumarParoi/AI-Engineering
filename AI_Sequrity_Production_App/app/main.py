# ============================================================
# CRITICAL: logfire MUST be configured before ALL other imports
# so that spans from all modules are captured from the start.
# ============================================================
import logfire
import os
from dotenv import load_dotenv

load_dotenv()
logfire_token = os.getenv("LOGFIRE_TOKEN")
if logfire_token and logfire_token.strip():
    logfire.configure(token=logfire_token.strip())
else:
    logfire.configure(send_to_logfire=False)

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


class HITLDecisionRequest(BaseModel):
    thread_id: str = Field(..., description="Thread ID of the interrupted session awaiting sign-off")
    decision: str = Field(..., description="'approved' to authorize sensitive security action, 'rejected' to decline")
    supervisor_notes: Optional[str] = Field(default="", description="Supervisor justification or audit notes")


@app.get("/")
def home():
    return {
        "message": "Enterprise AI Security Supervisor & Multi-Agent Intelligence API is live and protected.",
        "defense": "BotShield WAF v2.0 active",
        "agents": [
            "ThreatResearcher (Tavily + Serper)",
            "ExploitAnalyst (OWASP LLM Red-Teaming)",
            "SecurityRetrieval (Dual-Tier FlashRank + Cohere RAG)",
            "ComplianceAuditor (NIST/ISO Audit & Reflection Critic)",
            "RemediationPatcher (Active Defense Hotfix)"
        ],
        "version": "2.0.0",
    }


from app.health import router as health_router
app.include_router(health_router)


@app.get("/graph")
def get_graph_image():
    """
    Returns the Mermaid image of the supervisor multi-agent workflow.
    """
    try:
        png_bytes = rag_agent.get_graph().draw_mermaid_png()
        return Response(content=png_bytes, media_type="image/png")
    except Exception as e:
        return {"error": f"Could not generate graph image: {e}"}


@app.post("/query")
def query(request: QueryRequest):
    """
    Executes the Principal Engineer LangGraph Supervisor workflow with 5 specialized sub-agents.
    """
    q = request.q
    thread_id = request.thread_id

    initial_state = {
        "messages": [{"role": "user", "content": q}],
        "current_query": q,
        "thread_id": thread_id,
        "task_plan": [],
        "active_agent": "supervisor_planner",
        "completed_steps": [],
        "threat_intel": {},
        "exploit_analysis": {},
        "retrieved_documents": [],
        "compliance_audit": {},
        "remediation_proposal": {},
        "critique_feedback": None,
        "iteration_count": 0,
        "max_iterations": 3,
        "loop_status": "START",
        "hitl_pending": False,
        "hitl_action": None,
        "final_answer": "",
        "thought_process": [],
        "status": "Initializing Supervisor Graph...",
        "sources": []
    }
    
    config = {"configurable": {"thread_id": thread_id}}
    
    try:
        # Gate 1: NeMo Guardrails
        rail_fired, rail_response = guard(q)
        if rail_fired:
            logfire.info(f"🛡️ Request blocked by guardrails | thread={thread_id}")
            return {
                "question": q,
                "answer": rail_response,
                "thought_process": ["Intent: Guardrails Fired", "Investigation: Blocked at Edge"],
                "status": "Blocked by guardrails.",
                "hitl_pending": False,
                "sources": []
            }

        # Gate 2: LangGraph Hierarchical Supervisor Execution
        final_output = rag_agent.invoke(initial_state, config=config)
        
        return {
            "question": q,
            "answer": final_output.get("final_answer"),
            "thought_process": final_output.get("thought_process", []),
            "status": final_output.get("status"),
            "hitl_pending": final_output.get("hitl_pending", False),
            "hitl_action": final_output.get("hitl_action"),
            "sources": final_output.get("retrieved_documents", [])
        }
    except Exception as e:
        logfire.error(f"❌ Backend Execution Failed: {e}")
        return {
            "question": q,
            "answer": f"I apologize, but an internal error occurred: {e}",
            "thought_process": ["Error encountered during execution."],
            "status": "error",
            "hitl_pending": False,
            "sources": []
        }


# =========================================================================
# PRINCIPAL HITL GOVERNANCE & PROTOCOL MANAGEMENT ENDPOINTS
# =========================================================================

@app.get("/api/v1/hitl/pending/{thread_id}", tags=["HITL Governance"])
def get_pending_hitl_action(thread_id: str):
    """Inspects if an active session is interrupted awaiting supervisor authorization."""
    from app.hitl.manager import security_hitl_manager
    action = security_hitl_manager.get_pending(thread_id)
    if not action:
        return {"status": "none", "pending": False, "thread_id": thread_id}
    return {
        "status": "pending_approval",
        "pending": True,
        "action": action.dict(),
    }


@app.post("/api/v1/hitl/approve", tags=["HITL Governance"])
def resolve_hitl_action(payload: HITLDecisionRequest):
    """Human-in-the-Loop decision endpoint for supervisors to authorize or reject security mutations."""
    from app.hitl.manager import security_hitl_manager
    action = security_hitl_manager.resolve(
        thread_id=payload.thread_id,
        decision=payload.decision,
        supervisor_notes=payload.supervisor_notes or "",
    )
    if not action:
        return {
            "status": "error",
            "decision": payload.decision,
            "message": f"No pending action found for thread '{payload.thread_id}'."
        }
    return {
        "status": "success",
        "action_id": action.action_id,
        "decision": action.status,
        "message": f"Security action '{action.tool_name}' successfully resolved with status '{action.status}'.",
        "resolution_summary": action.resolution_summary,
    }


@app.get("/api/v1/mcp/status", tags=["Model Context Protocol"])
def get_mcp_status():
    """Returns real-time health and connectivity of the FastMCP Security Server."""
    from app.mcp.security_client import security_mcp_client
    return security_mcp_client.check_health()


@app.get("/api/v1/search/health", tags=["Web Reconnaissance"])
def get_search_health():
    """Validates connectivity of Tavily and Serper web intelligence engines."""
    from app.services.search import search_service
    return {
        "tavily_configured": bool(search_service.tavily_key),
        "serper_configured": bool(search_service.serper_key),
        "engines_active": [
            e for e, active in [("tavily", bool(search_service.tavily_key)), ("serper", bool(search_service.serper_key))] if active
        ] or ["local_simulated_feed"]
    }


@app.get("/api/v1/reranker/benchmark", tags=["Dual-Tier Re-Ranking"])
def get_reranker_benchmark():
    """Compares FlashRank (local in-process ONNX) vs Cohere v3.5 vs Hybrid RRF vs Cascade re-ranking."""
    import time
    from app.services.reranker import hybrid_reranker
    test_docs = [
        {"id": "doc1", "text": "BotShield WAF blocks SQL injection, scanner User-Agents, and honeypot traps."},
        {"id": "doc2", "text": "LangGraph multi-agent systems coordinate autonomous agents with cyclic state graphs."},
        {"id": "doc3", "text": "NeMo Guardrails enforces Colang policies and blocks prompt injection."},
        {"id": "doc4", "text": "FastMCP standardizes tool execution across microservices over JSON-RPC."},
        {"id": "doc5", "text": "A standard chocolate cake recipe with cocoa powder and flour."}
    ]
    query = "How to block SQL injection and prompt injection in LangGraph agents?"
    
    # 1. FlashRank Benchmark
    t0 = time.perf_counter()
    flash_res = hybrid_reranker.rerank_flashrank(query, test_docs, top_k=3)
    flash_dur_ms = (time.perf_counter() - t0) * 1000

    # 2. Cohere Benchmark
    cohere_dur_ms = None
    cohere_status = "unconfigured"
    cohere_top_1 = None
    cohere_res = []
    if hybrid_reranker.cohere_key:
        try:
            t1 = time.perf_counter()
            cohere_res = hybrid_reranker.rerank_cohere(query, test_docs, top_k=3)
            cohere_dur_ms = (time.perf_counter() - t1) * 1000
            cohere_status = "operational"
            cohere_top_1 = cohere_res[0].get("text") if cohere_res else None
        except Exception as e:
            cohere_status = f"failed: {e}"

    # 3. Hybrid RRF Ensemble Benchmark
    t2 = time.perf_counter()
    rrf_res = hybrid_reranker.rerank(query, test_docs, top_k=3, mode="hybrid_rrf")
    rrf_dur_ms = (time.perf_counter() - t2) * 1000

    # 4. Cascade Dual-Tier Benchmark
    t3 = time.perf_counter()
    cascade_res = hybrid_reranker.rerank(query, test_docs, top_k=3, mode="cascade")
    cascade_dur_ms = (time.perf_counter() - t3) * 1000

    return {
        "benchmark_query": query,
        "flashrank": {
            "status": "operational",
            "latency_ms": round(flash_dur_ms, 2),
            "top_1": flash_res[0].get("text") if flash_res else None,
            "top_1_score": round(flash_res[0].get("rerank_score", 0.0), 4) if flash_res else None,
            "cost": "$0.00 (Local In-Process ONNX)"
        },
        "cohere_v3_5": {
            "status": cohere_status,
            "latency_ms": round(cohere_dur_ms, 2) if cohere_dur_ms else "N/A",
            "top_1": cohere_top_1,
            "top_1_score": round(cohere_res[0].get("rerank_score", 0.0), 4) if cohere_res else None,
            "cost": "$1.00 / 1k queries (Hosted Cloud API)"
        },
        "hybrid_rrf_ensemble": {
            "status": "operational",
            "latency_ms": round(rrf_dur_ms, 2),
            "top_1": rrf_res[0].get("text") if rrf_res else None,
            "rrf_score": rrf_res[0].get("rrf_score") if rrf_res else None,
            "method": "Reciprocal Rank Fusion (Cohere 0.50 + FlashRank 0.35 + Lexical 0.15)"
        },
        "cascade_dual_tier": {
            "status": "operational",
            "latency_ms": round(cascade_dur_ms, 2),
            "top_1": cascade_res[0].get("text") if cascade_res else None,
            "method": "FlashRank candidate prune (50 -> 15) -> Cohere deep cross-attention"
        },
        "engine_metrics": hybrid_reranker.get_metrics(),
        "recommendation": "Use 'hybrid_rrf' for security critical evaluations and 'cascade' for high-throughput API endpoints."
    }

