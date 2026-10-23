"""Sub-millisecond heuristic safety filters before executing LLM guardrails."""

import re

BLOCKED_PATTERNS = [
    r"\bignore\s+all\s+previous\s+instructions\b",
    r"\byou\s+are\s+now\s+dan\b",
    r"\bdeveloper\s+mode\s+enabled\b",
    r"\bdisregard\s+all\s+rules\b",
    r"\bact\s+as\s+an\s+unrestricted\b",
]

COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in BLOCKED_PATTERNS]


def fast_adversarial_check(query: str) -> tuple[bool, str | None]:
    """Quickly detect blatant jailbreaks without invoking LLM tokens."""
    for pat in COMPILED_PATTERNS:
        if pat.search(query):
            return True, "Security filter triggered: Adversarial instruction override detected."
    return False, None
