"""
AI Platform Golden Path Project Template.
Blueprint for bootstrapping any new enterprise AI microservice adhering to Phases 0 - 5.

Includes:
- FastAPI with BotShield ASGI WAF rate limiting and honeypots.
- PII filter & Luhn credit card tokenization.
- Prompt injection defense.
- Transactional Outbox event generation with idempotency keys.
- Real-time G-Eval evaluation hook and Prometheus telemetry.
"""

import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

from app.middleware.bot_shield import BotShieldMiddleware
from app.security import pii_engine, injection_shield, DefenseAction
from app.patterns import outbox_manager
from app.evaluation import geval_evaluator, metrics_service

# 1. Initialize Golden Path FastAPI Application
app = FastAPI(
    title="Golden Path Enterprise AI Microservice",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 2. Attach Edge Defense Shield
app.add_middleware(BotShieldMiddleware)


class StandardAIRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=4096, description="User prompt")
    tenant_id: str = Field(default="tenant_default", description="Multi-tenant identifier")
    idempotency_key: Optional[str] = Field(default=None, description="Client idempotency key")


class StandardAIResponse(BaseModel):
    query: str
    sanitized_query: str
    pii_detected: bool
    answer: str
    geval_score: float
    latency_ms: float
    cost_usd: float


@app.post("/api/v1/generate", response_model=StandardAIResponse)
def generate(payload: StandardAIRequest):
    t0 = time.perf_counter()
    raw_query = payload.query

    # Step 1: PII Tokenization
    pii_scan = pii_engine.scan_and_mask(raw_query)
    effective_query = pii_scan.sanitized_text

    # Step 2: Prompt Injection Neutralization
    inj_scan = injection_shield.scan(effective_query)
    if inj_scan.action == DefenseAction.BLOCK:
        raise HTTPException(
            status_code=403,
            detail=f"Query rejected by prompt injection defense: {inj_scan.rationale}"
        )

    # Step 3: Core AI Generation (Synthesized output)
    simulated_answer = f"Verified response for query: '{effective_query}' adhering to enterprise policy."

    # Step 4: G-Eval Groundedness Verification Hook
    eval_report = geval_evaluator.evaluate_full(
        query=effective_query,
        response=simulated_answer,
        contexts=["Enterprise security guidelines and compliance mandates."]
    )

    elapsed_ms = (time.perf_counter() - t0) * 1000

    # Step 5: Transactional Outbox Event Publishing
    outbox_manager.create_event(
        aggregate_type="AI_INFERENCE_QUERY",
        aggregate_id=payload.tenant_id,
        event_type="INFERENCE_COMPLETED",
        payload={
            "tenant_id": payload.tenant_id,
            "latency_ms": elapsed_ms,
            "geval_score": eval_report.overall_score,
            "has_pii": pii_scan.has_pii,
        },
        idempotency_key=payload.idempotency_key
    )

    # Step 6: Telemetry & Cost Recording
    cost = metrics_service.record_query(
        latency_ms=elapsed_ms,
        prompt_tokens=len(raw_query.split()),
        completion_tokens=len(simulated_answer.split()),
        status="success",
        geval_score=eval_report.overall_score
    )

    return StandardAIResponse(
        query=raw_query,
        sanitized_query=effective_query,
        pii_detected=pii_scan.has_pii,
        answer=simulated_answer,
        geval_score=eval_report.overall_score,
        latency_ms=round(elapsed_ms, 1),
        cost_usd=cost
    )


@app.get("/health")
def health():
    return {"status": "ok", "platform": "Enterprise Golden Path", "shield": "Active"}
