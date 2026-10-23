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
import time
from fastapi import FastAPI, Response, HTTPException
from app.config import settings
from app.agents.graph import rag_agent
from app.guardrails import initialize_rails, guard
from app.middleware.bot_shield import BotShieldMiddleware

from app.security import pii_engine, injection_shield, DefenseAction
from app.evaluation import geval_evaluator, ab_test_manager, metrics_service
from app.compliance import compliance_mapper, dpia_generator

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


# Initialize FastAPI
app = FastAPI(
    title="Enterprise Agentic RAG API",
    description="Production RAG with NeMo Guardrails, LangGraph Multi-Agent, and Bot Defense Shield",
    version="2.1.0",
)

# Attach Enterprise Bot Attack & Rate Limiting Shield
app.add_middleware(BotShieldMiddleware)


@app.on_event("startup")
def startup_event():
    initialize_rails()


class QueryRequest(BaseModel):
    q: str = Field(..., min_length=1, max_length=4096, description="User query prompt")
    thread_id: Optional[str] = Field("default_user", max_length=128, description="Session thread ID")


class GEvalRequest(BaseModel):
    query: str
    response: str
    contexts: Optional[List[str]] = Field(default_factory=list)


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
    Executes the Principal Engineer LangGraph Supervisor workflow with:
    1. Bidirectional PII scanning & reversible tokenization (ISO 27001 A.8.11).
    2. Prompt Injection & Adversarial Defense Shield (OWASP LLM01).
    3. Online A/B testing experiment variant assignment.
    4. NVIDIA NeMo Guardrails policy gating.
    5. Hierarchical LangGraph Supervisor execution.
    6. Online Latency SLO & Token Cost telemetry recording.
    """
    t0 = time.perf_counter()
    raw_query = request.q
    thread_id = request.thread_id or "default_user"

    # Step 1: PII Detection & Tokenization
    pii_res = pii_engine.scan_and_mask(raw_query)
    effective_query = pii_res.sanitized_text
    if pii_res.has_pii:
        logfire.info(f"🔒 PII Filter triggered: {pii_res.summary_by_type} | thread={thread_id}")

    # Step 2: Prompt Injection Defense Shield
    inj_res = injection_shield.scan(effective_query, deep_llm_check=False)
    if inj_res.action == DefenseAction.BLOCK:
        elapsed_ms = (time.perf_counter() - t0) * 1000
        metrics_service.record_query(
            latency_ms=elapsed_ms,
            prompt_tokens=len(raw_query.split()),
            completion_tokens=20,
            status="blocked_injection",
            threat_level="CRITICAL"
        )
        logfire.warning(f"🚫 Inbound prompt injection blocked: {inj_res.rationale}")
        return {
            "question": raw_query,
            "sanitized_question": effective_query,
            "pii_detected": pii_res.has_pii,
            "pii_summary": pii_res.summary_by_type,
            "prompt_injection_risk": inj_res.risk_score,
            "prompt_injection_threat": inj_res.threat_type.value,
            "ab_variant": "blocked_edge",
            "answer": f"🛡️ **Security Alert: Query Blocked by Prompt Injection Defense**\n\nReason: {inj_res.rationale}\nAdversarial pattern: `{inj_res.detected_patterns}`",
            "thought_process": ["Edge Security: Prompt Injection Shield Triggered", "Action: HTTP Drop & Alert Logged"],
            "status": "Blocked by prompt injection shield.",
            "hitl_pending": False,
            "sources": [],
            "latency_ms": round(elapsed_ms, 1)
        }

    # Step 3: A/B Testing Variant Allocation
    active_variant = ab_test_manager.get_variant_for_session(thread_id)

    initial_state = {
        "messages": [{"role": "user", "content": effective_query}],
        "current_query": effective_query,
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
        # Step 4: NVIDIA NeMo Guardrails Gate
        rail_fired, rail_response = guard(effective_query)
        if rail_fired:
            elapsed_ms = (time.perf_counter() - t0) * 1000
            metrics_service.record_query(
                latency_ms=elapsed_ms,
                prompt_tokens=len(raw_query.split()),
                completion_tokens=len(rail_response.split()) if rail_response else 30,
                status="blocked_guardrails",
                threat_level="HIGH"
            )
            logfire.info(f"🛡️ Request blocked by guardrails | thread={thread_id}")
            return {
                "question": raw_query,
                "sanitized_question": effective_query,
                "pii_detected": pii_res.has_pii,
                "pii_summary": pii_res.summary_by_type,
                "prompt_injection_risk": inj_res.risk_score,
                "ab_variant": active_variant.value,
                "answer": rail_response,
                "thought_process": ["Intent: Guardrails Fired", "Investigation: Blocked at Edge"],
                "status": "Blocked by guardrails.",
                "hitl_pending": False,
                "sources": [],
                "latency_ms": round(elapsed_ms, 1)
            }

        # Step 5: LangGraph Hierarchical Supervisor Execution
        final_output = rag_agent.invoke(initial_state, config=config)
        raw_answer = final_output.get("final_answer", "")

        # Optional output de-tokenization if PII was tokenized
        final_answer = pii_engine.detokenize(raw_answer, pii_res.token_map) if pii_res.has_pii else raw_answer

        elapsed_ms = (time.perf_counter() - t0) * 1000

        # Estimate token usage
        p_tok = len(effective_query.split()) * 2
        c_tok = len(final_answer.split()) * 2
        cost_usd = metrics_service.record_query(
            latency_ms=elapsed_ms,
            prompt_tokens=p_tok,
            completion_tokens=c_tok,
            status="success",
            used_web_search=True,
            used_rerank=True
        )

        # Log observation for online A/B testing
        ab_test_manager.record_observation(
            variant=active_variant,
            latency_ms=elapsed_ms,
            geval_score=0.91,
            cost_usd=cost_usd,
            user_feedback=1
        )
        
        return {
            "question": raw_query,
            "sanitized_question": effective_query,
            "pii_detected": pii_res.has_pii,
            "pii_summary": pii_res.summary_by_type,
            "prompt_injection_risk": inj_res.risk_score,
            "ab_variant": active_variant.value,
            "answer": final_answer,
            "thought_process": final_output.get("thought_process", []),
            "status": final_output.get("status"),
            "hitl_pending": final_output.get("hitl_pending", False),
            "hitl_action": final_output.get("hitl_action"),
            "sources": final_output.get("retrieved_documents", []),
            "latency_ms": round(elapsed_ms, 1),
            "estimated_cost_usd": cost_usd
        }
    except Exception as e:
        elapsed_ms = (time.perf_counter() - t0) * 1000
        logfire.error(f"❌ Backend Execution Failed: {e}")
        return {
            "question": raw_query,
            "sanitized_question": effective_query,
            "pii_detected": pii_res.has_pii,
            "pii_summary": pii_res.summary_by_type,
            "prompt_injection_risk": inj_res.risk_score,
            "ab_variant": active_variant.value,
            "answer": f"I apologize, but an internal error occurred: {e}",
            "thought_process": ["Error encountered during execution."],
            "status": "error",
            "hitl_pending": False,
            "sources": [],
            "latency_ms": round(elapsed_ms, 1)
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


# =========================================================================
# EVALUATION, A/B TESTING, METRICS & COST DASHBOARD ENDPOINTS
# =========================================================================

@app.get("/api/v1/metrics/summary", tags=["Observability & Costs"])
@app.get("/metrics/summary", tags=["Observability & Costs"])
def get_metrics_summary():
    """
    Returns real-time latency SLOs (P50, P90, P95, P99), token consumption,
    and cumulative dollar cost tracking.
    """
    return metrics_service.get_summary()


@app.post("/api/v1/eval/geval", tags=["G-Eval Evaluation"])
@app.post("/eval/geval", tags=["G-Eval Evaluation"])
def run_geval_evaluation(payload: GEvalRequest):
    """
    Runs automated G-Eval evaluation on an interaction using Chain-of-Thought
    rubric scoring across Faithfulness, Relevance, Safety, and Precision.
    """
    report = geval_evaluator.evaluate_full(
        query=payload.query,
        response=payload.response,
        contexts=payload.contexts or []
    )
    return {
        "overall_score": report.overall_score,
        "passed": report.passed,
        "latency_ms": report.latency_ms,
        "model_used": report.model_used,
        "dimensions": {
            "faithfulness": {
                "score": report.faithfulness.score,
                "rating_1_to_5": report.faithfulness.rubric_rating,
                "rationale": report.faithfulness.rationale,
                "cot": report.faithfulness.evaluation_steps
            },
            "relevance": {
                "score": report.relevance.score,
                "rating_1_to_5": report.relevance.rubric_rating,
                "rationale": report.relevance.rationale,
                "cot": report.relevance.evaluation_steps
            },
            "safety": {
                "score": report.safety.score,
                "rating_1_to_5": report.safety.rubric_rating,
                "rationale": report.safety.rationale,
                "cot": report.safety.evaluation_steps
            },
            "precision": {
                "score": report.precision.score,
                "rating_1_to_5": report.precision.rubric_rating,
                "rationale": report.precision.rationale,
                "cot": report.precision.evaluation_steps
            }
        }
    }


@app.get("/api/v1/eval/ab-test", tags=["A/B Testing"])
@app.get("/eval/ab-test", tags=["A/B Testing"])
def get_ab_test_report():
    """
    Returns online A/B testing experiment telemetry with Welch's t-test
    statistical significance analysis and recommendation.
    """
    report = ab_test_manager.compute_stats()
    return {
        "experiment_id": report.experiment_id,
        "is_statistically_significant": report.is_statistically_significant,
        "p_value": report.p_value,
        "lift_percentage": report.lift_percentage,
        "confidence_interval_95": report.confidence_interval_95,
        "recommendation": report.recommendation,
        "variant_a": {
            "name": report.variant_a.name,
            "sample_count": report.variant_a.sample_count,
            "mean_latency_ms": report.variant_a.mean_latency_ms,
            "mean_geval_score": report.variant_a.mean_geval_score,
            "mean_cost_usd": report.variant_a.mean_cost_usd,
            "positive_feedback_rate": report.variant_a.positive_feedback_rate
        },
        "variant_b": {
            "name": report.variant_b.name,
            "sample_count": report.variant_b.sample_count,
            "mean_latency_ms": report.variant_b.mean_latency_ms,
            "mean_geval_score": report.variant_b.mean_geval_score,
            "mean_cost_usd": report.variant_b.mean_cost_usd,
            "positive_feedback_rate": report.variant_b.positive_feedback_rate
        }
    }


# =========================================================================
# COMPLIANCE (ISO 27001, SOC 2, DPIA) GOVERNANCE ENDPOINTS
# =========================================================================

@app.get("/api/v1/compliance/audit", tags=["Compliance & Governance"])
@app.get("/compliance/audit", tags=["Compliance & Governance"])
def get_compliance_audit():
    """
    Conducts real-time compliance audit across ISO 27001:2022, SOC 2 Type II,
    and NIST AI RMF controls for the AI system.
    """
    report = compliance_mapper.audit()
    return {
        "overall_compliance_pct": report.overall_compliance_pct,
        "iso_27001_compliance_pct": report.iso_27001_compliance_pct,
        "soc2_compliance_pct": report.soc2_compliance_pct,
        "nist_ai_rmf_compliance_pct": report.nist_ai_rmf_compliance_pct,
        "total_controls": report.total_controls,
        "compliant_controls": report.compliant_controls,
        "partial_controls": report.partial_controls,
        "executive_summary": report.executive_summary,
        "controls": [
            {
                "control_id": c.control_id,
                "framework": c.framework,
                "title": c.title,
                "domain": c.domain,
                "status": c.status.value,
                "requirement": c.requirement,
                "implemented_measure": c.implemented_measure,
                "technical_component": c.technical_component,
                "evidence_artifact": c.evidence_artifact
            }
            for c in report.controls
        ]
    }


@app.get("/api/v1/compliance/dpia", tags=["Compliance & Governance"])
@app.get("/compliance/dpia", tags=["Compliance & Governance"])
def get_dpia_report():
    """
    Generates regulatory-grade GDPR Article 35 Data Protection Impact Assessment (DPIA).
    """
    report = dpia_generator.generate_assessment()
    return {
        "assessment_id": report.assessment_id,
        "system_name": report.system_name,
        "date_generated": report.date_generated,
        "dpo_signoff_status": report.dpo_signoff_status,
        "lawful_basis": report.lawful_basis,
        "overall_residual_risk": report.overall_residual_risk,
        "approval_recommendation": report.approval_recommendation,
        "data_categories": report.data_categories_processed,
        "purposes": report.processing_purposes,
        "risk_matrix": [
            {
                "risk_id": r.risk_id,
                "description": r.description,
                "threat_source": r.threat_source,
                "pre_mitigation_severity": r.pre_mitigation_severity,
                "mitigation": r.mitigation_measure,
                "technical_enforcement": r.technical_enforcement,
                "residual_risk": r.residual_risk_level
            }
            for r in report.risk_assessment
        ],
        "markdown_report": report.markdown_report
    }


