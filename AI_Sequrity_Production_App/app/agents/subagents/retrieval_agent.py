import logging
from typing import Dict, Any, List
from app.agents.state import SupervisorState
from app.services.reranker import hybrid_reranker

logger = logging.getLogger("SecurityRetrievalAgent")

# Embedded enterprise security runbooks & compliance baseline documents
BASELINE_SECURITY_POLICIES = [
    {
        "id": "SEC-POL-01",
        "title": "Enterprise AI Security Policy: LLM Input Validation & WAF Gating",
        "content": "All external user prompts must traverse the BotShield WAF. Inbound queries matching direct instruction overrides, prompt injection, or DAN jailbreak patterns must be rejected at the edge with HTTP 403. PII, API tokens, and credentials must be sanitized before ingestion.",
        "category": "Input Validation & Defense"
    },
    {
        "id": "SEC-POL-02",
        "title": "Incident Response Runbook: Active Zero-Day & Exploit Mitigation",
        "content": "Upon identification of an active exploit or high-severity CVE (CVSS >= 8.5), the incident commander must: 1) Verify exploit vector with Exploit Analyst, 2) Prepare WAF IP ban rules, 3) Stage input sanitization patch, 4) Submit to Human-in-the-Loop supervisor gate before deployment.",
        "category": "Incident Response"
    },
    {
        "id": "SEC-POL-03",
        "title": "Human-in-the-Loop (HITL) Governance & Autonomous Action Guardrails",
        "content": "Autonomous agents are strictly forbidden from committing financial mutations, modifying production firewall rules, or terminating production hosts without authenticated dual-key human approval. State must be snapshotted in PostgreSQL checkpointer.",
        "category": "Governance & Compliance"
    },
    {
        "id": "SEC-POL-04",
        "title": "Model Context Protocol (MCP) Secure Microservices Standard",
        "content": "Tool invocations across external domains must implement the Anthropic Model Context Protocol (MCP) using strict JSON-RPC schemas over TLS. In-process fallback handlers must be configured to prevent cascade failures.",
        "category": "Architecture Standard"
    },
    {
        "id": "SEC-POL-05",
        "title": "Cryptographic Key Management & Secret Rotation Policy",
        "content": "API keys (OpenAI, Groq, Portkey, Qdrant) must never be logged or echoed in responses. Secret leakage in output must trigger immediate automated PII redaction and security ops alert.",
        "category": "Secret Protection"
    }
]


def retrieval_agent_node(state: SupervisorState) -> Dict[str, Any]:
    """
    Agent 3: Enterprise Knowledge & Dual-Tier RAG Retrieval.
    - Searches enterprise security baseline policies and incident runbooks.
    - Applies Dual-Tier Hybrid Re-ranking:
        Tier 1: FlashRank local cross-encoder (<15ms, $0 cost).
        Tier 2: Cohere v3.5 deep cross-attention precision (if API key configured).
    """
    query = state.get("current_query", "")
    logger.info(f"📚 [Agent 3: SecurityRetrieval] Retrieving policies & runbooks for: '{query[:60]}'")

    # In a full deployment, this queries Qdrant vector store.
    # We combine vector candidates with enterprise policy corpus.
    candidates = list(BASELINE_SECURITY_POLICIES)

    # Apply Principal Engineer Hybrid Re-Ranker (Cohere v3.5 + FlashRank ONNX + Lexical BM25 RRF)
    ranked_docs = hybrid_reranker.rerank(query, candidates, top_k=3, mode="hybrid_rrf")

    formatted_docs = []
    for doc in ranked_docs:
        formatted_docs.append({
            "id": doc.get("id"),
            "title": doc.get("title"),
            "content": doc.get("content"),
            "category": doc.get("category"),
            "rerank_score": doc.get("rerank_score", 0.0),
            "rrf_score": doc.get("rrf_score", doc.get("rerank_score", 0.0)),
            "cohere_score": doc.get("cohere_score"),
            "flashrank_score": doc.get("flashrank_score"),
            "lexical_score": doc.get("lexical_score"),
            "ranker": doc.get("ranker", "hybrid_rrf_ensemble")
        })

    completed = list(state.get("completed_steps", []))
    completed.append("policy_retrieval")

    return {
        "retrieved_documents": formatted_docs,
        "completed_steps": completed,
        "status": f"Retrieved and hybrid re-ranked {len(formatted_docs)} enterprise policies via {ranked_docs[0].get('ranker', 'hybrid_rrf')}."
    }
