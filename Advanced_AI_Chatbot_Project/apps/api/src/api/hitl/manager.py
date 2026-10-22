import time
import uuid
import logging
from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("HITLManager")


class ActionSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class PendingAction(BaseModel):
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


# Tools that CANNOT be executed autonomously by LLM without explicit human supervisor sign-off
SENSITIVE_TOOLS = {
    "request_refund": {
        "severity": ActionSeverity.CRITICAL,
        "description": "Financial mutation: Process an automated refund to customer's payment method.",
    },
    "apply_manager_discount": {
        "severity": ActionSeverity.HIGH,
        "description": "Promotional override: Issue a custom discount code > 15%.",
    },
    "cancel_order": {
        "severity": ActionSeverity.HIGH,
        "description": "Fulfillment mutation: Terminate order processing and issue restocking order.",
    },
    "escalate_human_agent": {
        "severity": ActionSeverity.MEDIUM,
        "description": "Routing mutation: Transfer session to Tier-2 human customer representative.",
    },
}


class HITLManager:
    """
    Principal Engineer grade Human-in-the-Loop (HITL) Governance Manager.
    Interprets intent and proposed agent tools. When a sensitive financial or
    customer-impacting action is planned, pauses execution, stores pending state,
    and awaits asynchronous supervisor resolution.
    """

    def __init__(self):
        # thread_id -> PendingAction
        self._pending_actions: Dict[str, PendingAction] = {}
        # action_id -> PendingAction history
        self._action_history: Dict[str, PendingAction] = {}

    def is_sensitive(self, tool_name: str) -> bool:
        return tool_name in SENSITIVE_TOOLS

    def register_action(
        self,
        thread_id: str,
        tool_name: str,
        arguments: Dict[str, Any],
        custom_description: Optional[str] = None,
    ) -> PendingAction:
        tool_meta = SENSITIVE_TOOLS.get(tool_name, {})
        severity = tool_meta.get("severity", ActionSeverity.HIGH)
        description = custom_description or tool_meta.get("description", f"Sensitive action: {tool_name}")

        action = PendingAction(
            thread_id=thread_id,
            tool_name=tool_name,
            arguments=arguments,
            description=description,
            severity=severity,
        )

        self._pending_actions[thread_id] = action
        self._action_history[action.action_id] = action

        logger.warning(
            f"⏸️ [HITL INTERRUPT] Thread {thread_id} requested high-stakes tool '{tool_name}'. "
            f"Action ID {action.action_id} awaiting supervisor sign-off."
        )
        return action

    def get_pending(self, thread_id: str) -> Optional[PendingAction]:
        return self._pending_actions.get(thread_id)

    def resolve(
        self,
        thread_id: str,
        decision: str,  # 'approved' | 'rejected'
        supervisor_notes: str = "",
    ) -> Optional[PendingAction]:
        action = self._pending_actions.get(thread_id)
        if not action:
            logger.warning(f"No pending HITL action found for thread {thread_id}")
            return None

        action.status = decision
        action.resolved_at = time.time()
        action.supervisor_notes = supervisor_notes

        if decision == "approved":
            action.resolution_summary = (
                f"✅ Action '{action.tool_name}' APPROVED by supervisor. "
                f"Transaction authorized with parameters: {action.arguments}."
            )
        else:
            action.resolution_summary = (
                f"❌ Action '{action.tool_name}' REJECTED by supervisor. "
                f"Reason: {supervisor_notes or 'Declined by human authority'}."
            )

        # Clear from pending
        del self._pending_actions[thread_id]
        logger.info(f"▶️ [HITL RESUMED] Thread {thread_id} resolved with status '{decision}'.")
        return action


hitl_manager = HITLManager()
