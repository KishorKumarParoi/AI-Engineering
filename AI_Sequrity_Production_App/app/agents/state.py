from typing import TypedDict, List, Dict, Any, Optional, Annotated
import operator


class SupervisorState(TypedDict):
    """
    Principal Engineer Grade Hierarchical Multi-Agent State.
    Maintains task planning, sub-agent findings, reflection loops,
    and Human-in-the-Loop (HITL) checkpoints.
    """
    # Conversation & Planning
    messages: Annotated[List[dict], operator.add]
    current_query: str
    thread_id: str
    task_plan: List[str]
    active_agent: str
    completed_steps: List[str]
    
    # Specialist Sub-Agent Findings
    threat_intel: Dict[str, Any]             # Agent 1: Live Web & CVE Recon (Tavily/Serper)
    exploit_analysis: Dict[str, Any]         # Agent 2: Red-Teaming & Exploit Vector Analysis
    retrieved_documents: List[Dict[str, Any]]# Agent 3: Dual-Tier RAG (FlashRank + Cohere)
    compliance_audit: Dict[str, Any]         # Agent 4: NIST/SOC2/CVSS Risk Evaluation
    remediation_proposal: Dict[str, Any]     # Agent 5: Patch & WAF Rule Synthesis
    
    # Loop Engineering (Self-Correction & Critique)
    critique_feedback: Optional[str]
    iteration_count: int
    max_iterations: int
    loop_status: str
    
    # Human-in-the-Loop (HITL) Governance
    hitl_pending: bool
    hitl_action: Optional[Dict[str, Any]]
    
    # Final Synthesis & Telemetry
    final_answer: str
    thought_process: List[str]
    status: str
    sources: List[Dict[str, Any]]


# Backward compatibility alias
AgentState = SupervisorState
