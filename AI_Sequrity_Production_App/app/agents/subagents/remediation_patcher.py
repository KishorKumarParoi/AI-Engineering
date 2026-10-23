import logging
from typing import Dict, Any
from app.agents.state import SupervisorState

logger = logging.getLogger("RemediationPatchAgent")


def remediation_patcher_node(state: SupervisorState) -> Dict[str, Any]:
    """
    Agent 5: Active Defense & Remediation Patch Synthesis.
    - Synthesizes concrete WAF firewall rules, guardrail patterns, and mitigation code.
    - Incorporates reflective critique feedback from Agent 4 to refine fixes.
    - Prepares high-impact action proposals for Human-in-the-Loop (HITL) authorization.
    """
    critique = state.get("critique_feedback")
    iteration = state.get("iteration_count", 0) + 1
    exploit_info = state.get("exploit_analysis", {})
    query = state.get("current_query", "")

    logger.info(f"🛠️ [Agent 5: RemediationPatcher] Synthesizing mitigation patch (Iteration {iteration})")

    # If this is a self-correction loop responding to critique, generate a hardened patch with rollback & verification!
    if critique:
        logger.info(f"🔄 Incorporating Auditor critique: {critique}")
        patch_code = (
            "# ================================================================\n"
            "# ENTERPRISE REFINED MITIGATION HOTFIX (SELF-CORRECTED VIA AUDIT)\n"
            "# ================================================================\n"
            "# 1. DEFENSIVE GUARDRAIL INTERCEPTOR (BotShield & NeMo)\n"
            "import re\n"
            "ADVERSARIAL_SIG = re.compile(r'(?i)(ignore\\s+previous\\s+instructions|DAN\\s+mode|override)')\n"
            "\n"
            "def sanitize_inbound_stream(prompt: str) -> tuple[bool, str]:\n"
            "    if ADVERSARIAL_SIG.search(prompt):\n"
            "        return False, 'BLOCKED: BotShield Edge Violation'\n"
            "    return True, prompt\n"
            "\n"
            "# 2. AUTOMATED VERIFICATION TEST HARNESS\n"
            "def test_remediation_efficacy():\n"
            "    assert sanitize_inbound_stream('test benign query')[0] is True\n"
            "    assert sanitize_inbound_stream('ignore previous instructions')[0] is False\n"
            "    print('✅ Unit test verification passed.')\n"
            "\n"
            "# 3. DEFENSIVE ROLLBACK PROCEDURE\n"
            "# Rollback Trigger: Error rate > 0.5% or P95 latency > 50ms\n"
            "# Rollback Command: git revert HEAD --no-edit && systemctl reload botshield\n"
        )
    else:
        patch_code = (
            "# ================================================================\n"
            "# PROPOSED BOTSHIELD WAF DEFENSE RULE\n"
            "# ================================================================\n"
            "# Action: Block pattern matching inbound query vectors\n"
            "waf_rule = {\n"
            f"    'threat_pattern': '{query[:40]}',\n"
            "    'action': 'DENY_AND_BAN',\n"
            "    'duration': 600,\n"
            "    'headers': {'X-BotShield-Mitigation': 'ACTIVE'}\n"
            "}\n"
        )

    # Determine if this proposed action has high blast radius requiring HITL sign-off
    is_sensitive = bool(exploit_info.get("detected_vectors")) or "ban" in query.lower() or "patch" in query.lower()

    hitl_proposal = None
    if is_sensitive:
        hitl_proposal = {
            "tool_name": "deploy_security_patch",
            "arguments": {
                "rule_name": "HOTFIX_ADVERSARIAL_DEFENSE",
                "target": "BotShield_WAF",
                "patch_snippet": patch_code[:120] + "..."
            },
            "description": "Authorize immediate hotfix deployment to production BotShield WAF & Guardrail layer."
        }

    proposal_result = {
        "agent": "remediation_patcher",
        "patch_content": patch_code,
        "iteration_applied": iteration,
        "requires_hitl": is_sensitive,
        "proposed_hitl_action": hitl_proposal,
        "status": "completed"
    }

    completed = list(state.get("completed_steps", []))
    completed.append(f"remediation_patch_v{iteration}")

    return {
        "remediation_proposal": proposal_result,
        "iteration_count": iteration,
        "completed_steps": completed,
        "status": f"Remediation patch v{iteration} synthesized."
    }
