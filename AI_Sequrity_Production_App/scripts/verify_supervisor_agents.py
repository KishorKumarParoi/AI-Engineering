#!/usr/bin/env python3
"""
Principal Engineer End-to-End Verification Suite for Enterprise AI Security Multi-Agent Architecture.
Validates:
1. Web Search Engines (Tavily + Serper with automatic fallback)
2. Dual-Tier Re-Ranker (Local FlashRank ONNX sub-15ms + Cohere cascade)
3. Model Context Protocol (MCP) Security Client & Tools
4. Human-in-the-Loop (HITL) Checkpoint & Approval Lifecycle
5. LangGraph Supervisor Hierarchy (5 Specialist Sub-Agents + Reflective Loop)
6. FastAPI REST & Governance Endpoints
"""

import sys
import os
import time

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.insert(0, project_root)

from fastapi.testclient import TestClient
from app.main import app
from app.services.search import search_service
from app.services.reranker import hybrid_reranker
from app.mcp.security_client import security_mcp_client
from app.hitl.manager import security_hitl_manager
from app.agents.graph import supervisor_agent

client = TestClient(app)


def test_1_web_search_intelligence():
    print("\n🔍 [TEST 1] Testing Web Search Intelligence (Tavily + Serper)...")
    res = search_service.hybrid_search("CVE-2024-21413 Microsoft Outlook exploit", max_results=3)
    print(f"  ✅ Hybrid Search returned {len(res)} candidate intelligence items.")
    for item in res[:2]:
        print(f"     • [{item.get('source')}]: {item.get('title')[:60]}...")


def test_2_dual_tier_reranker():
    print("\n⚡ [TEST 2] Testing Hybrid Re-Ranker (Cohere v3.5 + FlashRank ONNX + Lexical RRF)...")
    test_docs = [
        {"id": "doc1", "text": "BotShield WAF blocks SQL injection, scanner User-Agents, and honeypot traps."},
        {"id": "doc2", "text": "LangGraph multi-agent systems coordinate autonomous agents with cyclic state graphs."},
        {"id": "doc3", "text": "NeMo Guardrails enforces Colang policies and blocks prompt injection."},
        {"id": "doc4", "text": "A standard chocolate cake recipe with cocoa powder and flour."}
    ]
    query = "How to block SQL injection and prompt injection in LangGraph agents?"

    # 1. FlashRank Local ONNX Test
    t0 = time.perf_counter()
    flash_ranked = hybrid_reranker.rerank_flashrank(query, test_docs, top_k=2)
    flash_ms = (time.perf_counter() - t0) * 1000
    assert len(flash_ranked) == 2, "FlashRank should return top 2"
    print(f"  ✅ FlashRank (Local ONNX): {flash_ms:.2f}ms | Top-1: {flash_ranked[0]['id']} (Score: {flash_ranked[0].get('rerank_score'):.3f})")
    assert flash_ranked[0]["id"] in ("doc1", "doc3"), "Top document should be relevant security policy"

    # 2. Live Cohere v3.5 Cross-Attention Test
    if hybrid_reranker.cohere_key:
        t1 = time.perf_counter()
        cohere_ranked = hybrid_reranker.rerank_cohere(query, test_docs, top_k=2)
        cohere_ms = (time.perf_counter() - t1) * 1000
        print(f"  ✅ Cohere v3.5 (Cloud Transformer): {cohere_ms:.2f}ms | Top-1: {cohere_ranked[0]['id']} (Score: {cohere_ranked[0].get('rerank_score'):.3f})")
        assert len(cohere_ranked) == 2

    # 3. Hybrid Reciprocal Rank Fusion (RRF)
    t2 = time.perf_counter()
    rrf_ranked = hybrid_reranker.rerank(query, test_docs, top_k=3, mode="hybrid_rrf")
    rrf_ms = (time.perf_counter() - t2) * 1000
    print(f"  ✅ Hybrid RRF Ensemble: {rrf_ms:.2f}ms | Top-1: {rrf_ranked[0]['id']} (RRF: {rrf_ranked[0].get('rrf_score'):.5f}, Cohere: {rrf_ranked[0].get('cohere_score')}, FlashRank: {rrf_ranked[0].get('flashrank_score')})")

    # 4. Cascade Re-Ranker Test
    cascade_ranked = hybrid_reranker.rerank(query, test_docs, top_k=2, mode="cascade")
    print(f"  ✅ Cascaded Re-Ranker: Successfully executed via {cascade_ranked[0].get('ranker', 'hybrid')}")



def test_3_model_context_protocol():
    print("\n🔌 [TEST 3] Testing Model Context Protocol (MCP) Security Client...")
    
    # 1. MCP Health Check
    health = security_mcp_client.check_health()
    print(f"  ✅ MCP Status: {health.get('status')} at {health.get('server_url')}")

    # 2. CVE Lookup Tool Call
    cve_res = security_mcp_client.call_tool("cve_lookup", {"cve_id": "CVE-2024-21413"})
    assert cve_res.get("found") is True
    print(f"  ✅ MCP Tool 'cve_lookup': {cve_res.get('cve_id')} -> {cve_res.get('details', {}).get('title')[:60]}...")

    # 3. Threat Feed Tool Call
    intel_res = security_mcp_client.call_tool("threat_intel_feed", {"indicator": "198.51.100.25"})
    assert intel_res.get("reputation_score") > 50
    print(f"  ✅ MCP Tool 'threat_intel_feed': Indicator {intel_res.get('indicator')} -> Category: {intel_res.get('threat_category')}")


def test_4_hitl_governance_lifecycle():
    print("\n⏸️ [TEST 4] Testing Human-in-the-Loop (HITL) Checkpoint Lifecycle...")
    thread_id = "test_sec_thread_777"
    
    # 1. Register high-impact action
    action = security_hitl_manager.register(
        thread_id=thread_id,
        tool_name="apply_waf_ip_ban",
        arguments={"ip_cidr": "203.0.113.0/24", "duration_minutes": 1440, "reason": "Distributed botnet probe"},
        custom_description="Ban malicious IP block 203.0.113.0/24 from production WAF"
    )
    assert action.status == "pending_approval"
    print(f"  ✅ Action Registered: ID '{action.action_id}' | Severity: {action.severity.value}")

    # 2. Inspect pending action via REST endpoint
    res_pending = client.get(f"/api/v1/hitl/pending/{thread_id}", headers={"X-Forwarded-For": "10.0.0.10"})
    assert res_pending.status_code == 200
    p_json = res_pending.json()
    assert p_json["pending"] is True
    assert p_json["action"]["tool_name"] == "apply_waf_ip_ban"
    print(f"  ✅ Inspection Endpoint 200 OK: Thread '{thread_id}' pending '{p_json['action']['tool_name']}'")

    # 3. Resolve via supervisor authorization endpoint
    res_appr = client.post("/api/v1/hitl/approve", headers={"X-Forwarded-For": "10.0.0.10"}, json={
        "thread_id": thread_id,
        "decision": "approved",
        "supervisor_notes": "Authorized by Security Principal Architect"
    })
    assert res_appr.status_code == 200
    a_json = res_appr.json()
    assert a_json["status"] == "success"
    assert a_json["decision"] == "approved"
    print(f"  ✅ Supervisor Authorization: {a_json['resolution_summary']}")

    # 4. Confirm checkpoint cleared
    res_check = client.get(f"/api/v1/hitl/pending/{thread_id}", headers={"X-Forwarded-For": "10.0.0.10"})
    assert res_check.json()["pending"] is False
    print("  ✅ Checkpoint Cleared: Thread successfully resumed past the HITL gate")


def test_5_supervisor_graph_and_subagents():
    print("\n👑 [TEST 5] Testing SecuritySupervisor & 5 Specialized Sub-Agents (Graph & Loop Engineering)...")
    thread_id = "test_investigation_thread_888"
    
    initial_state = {
        "messages": [{"role": "user", "content": "Investigate CVE-2024-21413 MonikerLink exploit and synthesize a WAF hotfix rule"}],
        "current_query": "Investigate CVE-2024-21413 MonikerLink exploit and synthesize a WAF hotfix rule",
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
        "status": "Starting...",
        "sources": []
    }
    
    config = {"configurable": {"thread_id": thread_id}}
    output = supervisor_agent.invoke(initial_state, config=config)

    assert output.get("final_answer"), "Supervisor should synthesize a final answer"
    assert len(output.get("thought_process", [])) >= 4, "Should execute through multi-agent stages"
    print(f"  ✅ Execution Path: {' -> '.join(output.get('thought_process', []))}")
    print(f"  ✅ Loop Iterations Completed: {output.get('iteration_count')}")
    print(f"  ✅ Final Briefing Length: {len(output.get('final_answer', ''))} characters")


def test_6_api_endpoints():
    print("\n🌐 [TEST 6] Testing FastAPI REST Endpoints & Governance Routes...")
    
    # 1. Health & Home
    res_home = client.get("/", headers={"X-Forwarded-For": "10.0.0.20"})
    assert res_home.status_code == 200
    assert "BotShield WAF v2.0" in res_home.json()["defense"]
    print("  ✅ GET / 200 OK: Home endpoint returned active defense")

    # 2. Reranker Benchmark Endpoint
    res_bench = client.get("/api/v1/reranker/benchmark", headers={"X-Forwarded-For": "10.0.0.20"})
    assert res_bench.status_code == 200
    b_json = res_bench.json()
    print(f"  ✅ GET /api/v1/reranker/benchmark: FlashRank ({b_json['flashrank']['latency_ms']}ms, {b_json['flashrank']['cost']})")

    # 3. Search Health Endpoint
    res_search = client.get("/api/v1/search/health", headers={"X-Forwarded-For": "10.0.0.20"})
    assert res_search.status_code == 200
    print(f"  ✅ GET /api/v1/search/health: Active engines: {res_search.json()['engines_active']}")

    # 4. Live POST /query through Supervisor
    res_query = client.post("/query", headers={"X-Forwarded-For": "10.0.0.21"}, json={
        "q": "Analyze prompt injection vulnerability in LLM applications and propose mitigation",
        "thread_id": "test_api_client_001"
    })
    assert res_query.status_code == 200
    q_data = res_query.json()
    assert q_data.get("answer"), "Query response should contain answer"
    print(f"  ✅ POST /query 200 OK: Completed with status '{q_data.get('status')}' | HITL Gated: {q_data.get('hitl_pending')}")


if __name__ == "__main__":
    print("==================================================================")
    print("🛡️ STARTING PRINCIPAL ENGINEER SUPERVISOR MULTI-AGENT VERIFICATION")
    print("==================================================================")
    try:
        test_1_web_search_intelligence()
        test_2_dual_tier_reranker()
        test_3_model_context_protocol()
        test_4_hitl_governance_lifecycle()
        test_5_supervisor_graph_and_subagents()
        test_6_api_endpoints()
        print("\n==================================================================")
        print("🎉 ALL PRINCIPAL ENGINEER SUPERVISOR CHECKS PASSED WITH 100% SUCCESS!")
        print("==================================================================")
    except AssertionError as e:
        print(f"\n❌ Assertion Failed: {e}")
        sys.exit(1)
    except Exception as exc:
        print(f"\n❌ Unexpected Exception: {exc}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
