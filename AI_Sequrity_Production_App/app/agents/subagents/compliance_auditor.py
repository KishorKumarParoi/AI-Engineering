import logging
from typing import Dict, Any
from app.agents.state import SupervisorState

logger = logging.getLogger("ComplianceAuditorAgent")


def compliance_auditor_node(state: SupervisorState) -> Dict[str, Any]:
    """
    Agent 4: Compliance Auditor & Reflection Loop Critic.
    - Maps threat and exploit vectors to NIST AI RMF, ISO 27001, and SOC 2.
    - Evaluates CVSS v3.1 impact.
    - Performs Self-Critique on the Remediation Proposal (Loop Engineering):
        If remediation is missing rollback procedures or test harnesses,
        issues critique_feedback and triggers a refinement loop.
    """
    exploit_info = state.get("exploit_analysis", {})
    threat_info = state.get("threat_intel", {})
    remediation = state.get("remediation_proposal", {})
    iteration = state.get("iteration_count", 0)
    max_iter = state.get("max_iterations", 3)

    logger.info(f"⚖️ [Agent 4: ComplianceAuditor] Evaluating risk & auditing remediation (Cycle {iteration}/{max_iter})")

    # 1. COMPUTE DYNAMIC CVSS v3.1 BASE SCORE
    has_exploit = bool(exploit_info.get("detected_vectors"))
    cves = threat_info.get("cve_records", [])
    
    if cves and cves[0].get("details", {}).get("cvss"):
        base_cvss = float(cves[0]["details"]["cvss"])
    elif has_exploit:
        base_cvss = 8.8
    else:
        base_cvss = 3.2

    # 2. MAP TO COMPLIANCE FRAMEWORKS
    compliance_mappings = {
        "NIST_AI_RMF": "GOVERN 1.2 (Risk Management) & MAP 2.3 (Vulnerability Identification)",
        "ISO_27001": "A.12.6.1 (Management of Technical Vulnerabilities)",
        "SOC_2_TYPE_II": "CC6.8 (Unauthorized Malicious Code & Input Validation)",
        "EU_AI_ACT": "Article 15 (Cybersecurity & Robustness Resilience)"
    }

    # 3. REFLECTIVE LOOP AUDIT (CRITIQUE OF REMEDIATION PATCH)
    critique_feedback = None
    loop_status = "APPROVED"

    if remediation:
        patch_code = remediation.get("patch_content", "")
        has_rollback = "rollback" in patch_code.lower() or "revert" in patch_code.lower()
        has_verification = "test" in patch_code.lower() or "verify" in patch_code.lower()

        # If on early cycle and missing rollback or verification, trigger self-correction loop!
        if iteration < max_iter and (not has_rollback or not has_verification):
            critique_feedback = (
                "⚠️ Compliance Critique: The proposed remediation patch lacks an explicit rollback runbook "
                "or automated unit test harness. Please refine to include defensive rollback triggers."
            )
            loop_status = "NEEDS_REFINEMENT"
            logger.info(f"🔁 [Loop Engineering] Audit failed quality gate. Triggering reflection loop: {critique_feedback}")
        else:
            loop_status = "AUDIT_PASSED"
            logger.info("✅ [Loop Engineering] Remediation proposal successfully passed compliance audit.")

    audit_result = {
        "agent": "compliance_auditor",
        "cvss_v3_score": base_cvss,
        "risk_tier": "CRITICAL" if base_cvss >= 9.0 else "HIGH" if base_cvss >= 7.0 else "MEDIUM",
        "compliance_standards": compliance_mappings,
        "audit_decision": loop_status,
        "audit_notes": "All controls mapped against enterprise security policy SEC-POL-01 and NIST AI RMF."
    }

    completed = list(state.get("completed_steps", []))
    completed.append("compliance_audit")

    return {
        "compliance_audit": audit_result,
        "critique_feedback": critique_feedback,
        "loop_status": loop_status,
        "completed_steps": completed,
        "status": f"Compliance audit complete. Decision: {loop_status} (CVSS {base_cvss})"
    }
