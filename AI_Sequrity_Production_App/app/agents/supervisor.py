import logging
from typing import Dict, Any, List
from app.agents.state import SupervisorState
from app.hitl.manager import security_hitl_manager

logger = logging.getLogger("SecuritySupervisor")


def supervisor_planner_node(state: SupervisorState) -> Dict[str, Any]:
    """
    Supervisor Agent: Master Planning & Triage Node.
    - Inspects incoming query and context.
    - Decomposes problem into subtasks across the 5 specialized sub-agents:
        1. ThreatResearcher (Tavily/Serper web intelligence + MCP CVE lookup)
        2. ExploitAnalyst (Red-teaming & attack vector analysis)
        3. SecurityRetrieval (Dual-Tier RAG: FlashRank + Cohere)
        4. ComplianceAuditor (NIST/ISO risk rating & reflection loop critic)
        5. RemediationPatcher (Active defense code & WAF rule synthesis)
    """
    query = state.get("current_query", "").strip()
    logger.info(f"👑 [SecuritySupervisor] Triage & planning for query: '{query[:60]}'")

    lower_q = query.lower()
    plan = ["supervisor_triage"]

    # Dynamic Subtask Scheduling
    is_exploit = any(k in lower_q for k in ["exploit", "injection", "jailbreak", "bypass", "attack", "dan", "override"])
    is_live_cve = any(k in lower_q for k in ["cve", "zero-day", "0-day", "advisory", "vulnerability", "threat"])
    is_policy = any(k in lower_q for k in ["policy", "compliance", "standard", "guideline", "runbook", "nist", "iso", "soc"])
    is_remediation = any(k in lower_q for k in ["patch", "fix", "mitigate", "remediate", "rule", "waf", "hotfix", "ban"])

    # Build plan
    if is_live_cve or is_exploit or not (is_policy or is_remediation):
        plan.append("threat_research")
    if is_exploit or is_live_cve:
        plan.append("exploit_analysis")
    plan.append("policy_retrieval")
    if is_remediation or is_exploit or is_live_cve:
        plan.append("remediation_patch")
        plan.append("compliance_audit")
    else:
        plan.append("compliance_audit")

    plan.append("final_synthesis")

    logger.info(f"📋 [SecuritySupervisor] Formulated execution plan: {plan}")

    return {
        "task_plan": plan,
        "completed_steps": ["supervisor_triage"],
        "status": f"Supervisor plan created with {len(plan)} stages."
    }


def supervisor_synthesizer_node(state: SupervisorState) -> Dict[str, Any]:
    """
    Supervisor Agent: Final Intelligence & Remediation Synthesis.
    Aggregates findings from all 5 agents into a master incident report.
    """
    query = state.get("current_query", "")
    threat = state.get("threat_intel", {})
    exploit = state.get("exploit_analysis", {})
    docs = state.get("retrieved_documents", [])
    compliance = state.get("compliance_audit", {})
    remediation = state.get("remediation_proposal", {})
    iteration = state.get("iteration_count", 0)

    logger.info("👑 [SecuritySupervisor] Synthesizing comprehensive intelligence briefing...")

    report_sections = [
        "# 🛡️ Enterprise AI Security & Threat Intelligence Briefing",
        f"**Query Under Investigation**: `{query}`",
        f"**Analysis Mode**: Multi-Agent Supervisor Hierarchy (5 Specialist Agents | Cycle {iteration})",
        "",
        "## 1. 🔍 Live Threat Reconnaissance (ThreatResearcher)",
        threat.get("intelligence_summary", "No external zero-day disclosures active for this vector."),
        "",
        "## 2. 💥 Exploit & Red-Teaming Analysis (ExploitAnalyst)",
        f"• **Exploitability Level**: `{exploit.get('overall_severity', 'LOW')}`",
        f"• **Blast Radius**: `{exploit.get('blast_radius', 'CONTAINED')}`",
        f"• **Technical Assessment**: {exploit.get('analysis_summary', 'No active exploit payload detected.')}",
        "",
        "## 3. 📚 Enterprise Knowledge & Dual-Tier RAG (SecurityRetrieval)",
        "• **Re-Ranking Engine**: Dual-Tier Cascade (FlashRank local ONNX + Cohere cross-attention)",
    ]

    for d in docs[:3]:
        report_sections.append(f"  - **[{d.get('id', 'POL')}] {d.get('title')}**: {d.get('content')[:140]}... *(Score: {d.get('rerank_score'):.3f})*")

    report_sections.extend([
        "",
        "## 4. ⚖️ Governance & Risk Audit (ComplianceAuditor)",
        f"• **Dynamic CVSS v3.1 Base Score**: `{compliance.get('cvss_v3_score', 'N/A')}` ({compliance.get('risk_tier', 'LOW')})",
        f"• **Control Frameworks**: NIST AI RMF, ISO 27001 (A.12.6.1), SOC 2 Type II",
        f"• **Audit Verification**: `{compliance.get('audit_decision', 'APPROVED')}`",
        "",
        "## 5. 🛠️ Active Defense & Remediation Runbook (RemediationPatcher)",
    ])

    if remediation:
        report_sections.extend([
            f"• **Refinement Iterations**: Applied {iteration} self-correction reflection cycle(s).",
            "```python",
            remediation.get("patch_content", "# No patch code generated"),
            "```",
        ])
    else:
        report_sections.append("• Standard baseline controls sufficient; no custom hotfix required.")

    # Check if a pending HITL action was flagged
    hitl_action = None
    if remediation and remediation.get("requires_hitl"):
        prop = remediation.get("proposed_hitl_action", {})
        action_obj = security_hitl_manager.register(
            thread_id=state.get("thread_id", "default_thread"),
            tool_name=prop.get("tool_name", "deploy_security_patch"),
            arguments=prop.get("arguments", {}),
            custom_description=prop.get("description")
        )
        hitl_action = action_obj.dict()
        report_sections.extend([
            "",
            "> [!WARNING]",
            f"> **Human-in-the-Loop Gate Active**: Action `{action_obj.tool_name}` has a high blast radius. "
            f"Execution paused. Action ID `{action_obj.action_id}` awaiting supervisor authorization."
        ])

    final_markdown = "\n".join(report_sections)

    return {
        "final_answer": final_markdown,
        "hitl_pending": bool(hitl_action),
        "hitl_action": hitl_action,
        "thought_process": state.get("completed_steps", []),
        "status": "Investigation and synthesis complete."
    }
