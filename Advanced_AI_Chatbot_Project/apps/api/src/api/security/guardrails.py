import re
import logging
from typing import NamedTuple, Optional

logger = logging.getLogger("PromptSecurityGuardrail")


class ThreatAssessment(NamedTuple):
    is_safe: bool
    threat_type: Optional[str]
    safe_query: str
    reason: Optional[str]


# Direct jailbreak phrases and adversarial instruction overrides
JAILBREAK_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior)\s+(instructions|prompts|directions)", re.IGNORECASE),
    re.compile(r"disregard\s+(all\s+)?(previous|prior)\s+(instructions|prompts)", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(in\s+)?(DAN|developer|unfiltered|jailbroken)\s+mode", re.IGNORECASE),
    re.compile(r"act\s+as\s+(an\s+)?unrestricted\s+ai", re.IGNORECASE),
    re.compile(r"bypass\s+(safety|content|policy)\s+(filter|filters|guidelines)", re.IGNORECASE),
    re.compile(r"system\s*:\s*override", re.IGNORECASE),
    re.compile(r"###\s*instruction\s*:\s*override", re.IGNORECASE),
    re.compile(r"reveal\s+(your\s+)?(secret|hidden|internal)\s+(prompt|api\s*key|token|instructions)", re.IGNORECASE),
    re.compile(r"print\s+(your\s+)?system\s+prompt", re.IGNORECASE),
    re.compile(r"what\s+is\s+your\s+system\s+prompt", re.IGNORECASE),
]

# Sensitive PII patterns
PII_PATTERNS = [
    (re.compile(r"\b(?:\d{4}[- ]?){3}\d{4}\b"), "[REDACTED_CREDIT_CARD]"),
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[REDACTED_SSN]"),
    (re.compile(r"sk-[a-zA-Z0-9]{20,}"), "[REDACTED_API_KEY]"),
]


class PromptSecurityGuardrail:
    """
    Evaluates inbound queries for prompt injections, system extraction attempts,
    and PII leaks before dispatching to the LLM agent.
    """

    @classmethod
    def evaluate(cls, query: str) -> ThreatAssessment:
        if not query or not query.strip():
            return ThreatAssessment(
                is_safe=False,
                threat_type="EMPTY_INPUT",
                safe_query="",
                reason="Query cannot be empty.",
            )

        # 1. JAILBREAK & PROMPT INJECTION DETECTION
        for pattern in JAILBREAK_PATTERNS:
            if pattern.search(query):
                logger.warning(f"🚨 Prompt injection threat detected in query: '{query[:80]}...'")
                return ThreatAssessment(
                    is_safe=False,
                    threat_type="PROMPT_INJECTION",
                    safe_query="",
                    reason="Malicious instruction override or system prompt exfiltration attempt blocked.",
                )

        # 2. SANITIZE PII & SECRETS
        sanitized = query
        for pattern, replacement in PII_PATTERNS:
            sanitized = pattern.sub(replacement, sanitized)

        return ThreatAssessment(
            is_safe=True,
            threat_type=None,
            safe_query=sanitized,
            reason=None,
        )

    @classmethod
    def sanitize_output(cls, text: str) -> str:
        """Sanitizes outgoing LLM responses to prevent secret/PII leaks."""
        if not text:
            return ""
        cleaned = text
        for pattern, replacement in PII_PATTERNS:
            cleaned = pattern.sub(replacement, cleaned)
        return cleaned
