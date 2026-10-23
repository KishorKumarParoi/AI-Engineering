"""
Human-in-the-Loop (HITL) Governance Package for Enterprise AI Security Platform.
Provides authorization checkpoints for high-impact security actions.
"""

from app.hitl.manager import (
    SecurityHITLManager,
    security_hitl_manager,
    PendingSecurityAction,
    ActionSeverity,
    HIGH_IMPACT_SECURITY_TOOLS,
)

__all__ = [
    "SecurityHITLManager",
    "security_hitl_manager",
    "PendingSecurityAction",
    "ActionSeverity",
    "HIGH_IMPACT_SECURITY_TOOLS",
]
