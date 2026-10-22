"""
Human-in-the-Loop (HITL) Governance Package for Advanced AI Production Chatbot.
Provides approval gating, sensitive transaction interception, and supervisor authorization.
"""

from api.hitl.manager import (
    HITLManager,
    hitl_manager,
    PendingAction,
    ActionSeverity,
    SENSITIVE_TOOLS,
)

__all__ = [
    "HITLManager",
    "hitl_manager",
    "PendingAction",
    "ActionSeverity",
    "SENSITIVE_TOOLS",
]
