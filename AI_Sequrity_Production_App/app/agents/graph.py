import logging
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from app.agents.state import SupervisorState
from app.agents.supervisor import supervisor_planner_node, supervisor_synthesizer_node
from app.agents.subagents import (
    threat_researcher_node,
    exploit_analyst_node,
    retrieval_agent_node,
    compliance_auditor_node,
    remediation_patcher_node,
)

logger = logging.getLogger("SupervisorGraph")


def route_after_planner(state: SupervisorState) -> str:
    """Routes from master planner to initial investigation sub-agent."""
    plan = state.get("task_plan", [])
    if "threat_research" in plan:
        return "threat_researcher"
    elif "exploit_analysis" in plan:
        return "exploit_analyst"
    return "retrieval_agent"


def route_after_audit(state: SupervisorState) -> str:
    """
    Loop Engineering: Reflective Self-Correction Gateway.
    - If the compliance audit detected gaps and iteration < max_iterations,
      loops back to remediation_patcher to refine the defensive fix.
    - Otherwise, proceeds to final supervisor synthesis.
    """
    status = state.get("loop_status", "APPROVED")
    iteration = state.get("iteration_count", 0)
    max_iter = state.get("max_iterations", 3)

    if status == "NEEDS_REFINEMENT" and iteration < max_iter:
        logger.info(f"🔁 [Loop Engineering: Self-Correction] Auditor requested refinement. Looping back (Iteration {iteration}/{max_iter}).")
        return "remediation_patcher"
    
    logger.info("✅ [Loop Engineering] Reflection cycle satisfied. Routing to final supervisor synthesis.")
    return "supervisor_synthesizer"


# 1. INITIALIZE HIERARCHICAL STATE GRAPH
workflow = StateGraph(SupervisorState)

# 2. REGISTER NODES (Supervisor + 5 Specialized Agents)
workflow.add_node("supervisor_planner", supervisor_planner_node)
workflow.add_node("threat_researcher", threat_researcher_node)     # Agent 1 (Tavily/Serper + MCP)
workflow.add_node("exploit_analyst", exploit_analyst_node)           # Agent 2 (Red-Teaming)
workflow.add_node("retrieval_agent", retrieval_agent_node)           # Agent 3 (Dual-Tier RAG)
workflow.add_node("remediation_patcher", remediation_patcher_node)   # Agent 5 (Active Defense Hotfix)
workflow.add_node("compliance_auditor", compliance_auditor_node)     # Agent 4 (NIST/ISO Audit & Reflection Critic)
workflow.add_node("supervisor_synthesizer", supervisor_synthesizer_node)

# 3. CONFIGURE GRAPH EDGES & SEQUENCING
workflow.set_entry_point("supervisor_planner")

workflow.add_conditional_edges(
    "supervisor_planner",
    route_after_planner,
    {
        "threat_researcher": "threat_researcher",
        "exploit_analyst": "exploit_analyst",
        "retrieval_agent": "retrieval_agent",
    }
)

# Linear / Cascaded transitions between investigation agents
workflow.add_edge("threat_researcher", "exploit_analyst")
workflow.add_edge("exploit_analyst", "retrieval_agent")
workflow.add_edge("retrieval_agent", "remediation_patcher")
workflow.add_edge("remediation_patcher", "compliance_auditor")

# 4. LOOP ENGINEERING: REFLECTION & SELF-CORRECTION EDGE
workflow.add_conditional_edges(
    "compliance_auditor",
    route_after_audit,
    {
        "remediation_patcher": "remediation_patcher",   # Cyclic Reflection Loop
        "supervisor_synthesizer": "supervisor_synthesizer", # Terminal Synthesis
    }
)

workflow.add_edge("supervisor_synthesizer", END)

# 5. STATEFUL CHECKPOINTER (Supports Thread History & HITL State Resumption)
checkpointer = MemorySaver()

# 6. COMPILE PRINCIPAL SUPERVISOR AGENT
supervisor_agent = workflow.compile(checkpointer=checkpointer)

# Backward compatibility alias
rag_agent = supervisor_agent
