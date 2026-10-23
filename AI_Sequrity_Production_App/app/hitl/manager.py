import time
import uuid
import logging
from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("SecurityHITLManager")


class ActionSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class PendingSecurityAction(BaseModel):
    action_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    thread_id: str
    tool_name: str
    arguments: Dict[str, Any]
    description: str
    severity: ActionSeverity = ActionSeverity.HIGH
    status: str = "pending_approval"  # pending_approval | approved | rejected
    created_at: float = Field(default_factory=time.time)
    resolved_at: Optional[float] = None
    supervisor_notes: Optional[str] = None
    resolution_summary: Optional[str] = None


# High-impact operational tools requiring explicit human supervisor authorization
HIGH_IMPACT_SECURITY_TOOLS = {
    "apply_waf_ip_ban": {
        "severity": ActionSeverity.CRITICAL,
        "description": "Network Defense Mutation: Enact immediate firewall IP block on production WAF gateway.",
    },
    "deploy_security_patch": {
        "severity": ActionSeverity.CRITICAL,
        "description": "System Mutation: Deploy updated input sanitization rules or live guardrail hotfix.",
    },
    "publish_incident_advisory": {
        "severity": ActionSeverity.HIGH,
        "description": "Governance Disclosure: Broadcast internal and regulatory incident breach alert.",
    },
    "quarantine_compromised_endpoint": {
        "severity": ActionSeverity.CRITICAL,
        "description": "Infrastructure Isolation: Disconnect infected host or container from enterprise VPC.",
    },
}


class SecurityHITLManager:
    """
    Enterprise Security Human-in-the-Loop (HITL) Governance Engine.
    When an autonomous agent plans an action with high blast radius
    (e.g., blocking network subnets, modifying production WAF rules, isolating containers),
    this manager pauses graph execution and gates execution on human sign-off.
    """

    def __init__(self):
        self._pending_actions: Dict[str, PendingSecurityAction] = {}
        self._history: Dict[str, PendingSecurityAction] = {}

    def is_high_impact(self, tool_name: str) -> bool:
        return tool_name in HIGH_IMPACT_SECURITY_TOOLS

    def register(
        self,
        thread_id: str,
        tool_name: str,
        arguments: Dict[str, Any],
        custom_description: Optional[str] = None,
    ) -> PendingSecurityAction:
        tool_meta = HIGH_IMPACT_SECURITY_TOOLS.get(tool_name, {})
        severity = tool_meta.get("severity", ActionSeverity.HIGH)
        description = custom_description or tool_meta.get("description", f"Security mutation: {tool_name}")

        action = PendingSecurityAction(
            thread_id=thread_id,
            tool_name=tool_name,
            arguments=arguments,
            description=description,
            severity=severity,
        )

        self._pending_actions[thread_id] = action
        self._history[action.action_id] = action

        logger.warning(
            f"⏸️ [HITL GATE] Thread '{thread_id}' requested high-impact tool '{tool_name}'. "
            f"Execution halted. Action ID '{action.action_id}' awaiting supervisor authorization."
        )
        return action

    def get_pending(self, thread_id: str) -> Optional[PendingSecurityAction]:
        return self._pending_actions.get(thread_id)

    def resolve(
        self,
        thread_id: str,
        decision: str,  # 'approved' | 'rejected'
        supervisor_notes: str = "",
    ) -> Optional[PendingSecurityAction]:
        action = self._pending_actions.get(thread_id)
        if not action:
            logger.warning(f"No pending action found for thread '{thread_id}'.")
            return None

        action.status = decision
        action.resolved_at = time.time()
        action.supervisor_notes = supervisor_notes

        if decision == "approved":
            action.resolution_summary = (
                f"✅ Action '{action.tool_name}' APPROVED by Security Supervisor. "
                f"Payload authorized: {action.arguments}."
            )
        else:
            action.resolution_summary = (
                f"❌ Action '{action.tool_name}' REJECTED by Security Supervisor. "
                f"Rationale: {supervisor_notes or 'Declined by human authority'}."
            )

        del self._pending_actions[thread_id]
        logger.info(f"▶️ [HITL RESUMED] Thread '{thread_id}' resolved with status '{decision}'.")
        return action


security_hitl_manager = SecurityHITLManager()
