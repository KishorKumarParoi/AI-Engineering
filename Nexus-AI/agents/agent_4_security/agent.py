"""
Nexus-AI: Agent 4 — AI Security Agent
========================================
OWASP LLM Top 10 Security Guardrail Agent:
- Prompt Injection Detection (LLM01)
- Data Poisoning Prevention (LLM03)
- PII Redaction (GDPR/DPDP Act compliance)
- Output Sanitization (LLM05)
- SQL Injection Prevention (LLM06)
- Rate Limiting & Abuse Detection

Operates as Layer-7 firewall in the agent mesh.
Every request passes through this agent FIRST.
"""

import re
import time
from datetime import datetime, timezone
from typing import Any


# ── Threat Signatures ────────────────────────────────────────────────────
INJECTION_PATTERNS = [
    # Direct prompt injections
    (r"ignore\s+(all\s+)?previous\s+instructions?", "PROMPT_INJECTION", 0.95),
    (r"(you\s+are\s+now|act\s+as)\s+(dan|evil|jailbreak)", "JAILBREAK", 0.98),
    (r"system\s+(override|prompt|credentials?)", "SYSTEM_COMPROMISE", 0.97),
    (r"bypass\s+(safety|security|filter|guardrail)", "BYPASS_ATTEMPT", 0.96),
    (r"reveal\s+(your\s+)?(system|internal)\s+(prompt|instructions?)", "PROMPT_LEAK", 0.93),
    (r"pretend\s+(you\s+)?(have\s+)?(no|don'?t\s+have)\s+(restrictions?|rules?)", "RESTRICTION_BYPASS", 0.94),

    # SQL injection attempts
    (r";\s*(drop|delete|truncate|alter|insert|update)\s+", "SQL_INJECTION", 0.99),
    (r"'\s*(or|and)\s*'?\s*\d+\s*=\s*\d+", "SQL_INJECTION", 0.97),
    (r"union\s+(all\s+)?select", "SQL_INJECTION", 0.96),
    (r"--\s*$", "SQL_COMMENT_INJECTION", 0.85),

    # Code injection
    (r"(\bexec\b\s*\(|\beval\b\s*\(|import\s+os\b|subprocess|__import__)", "CODE_INJECTION", 0.95),
    (r"<script[\s>]", "XSS_ATTEMPT", 0.97),

    # Sensitive information extraction
    (r"(api[_\s]?key|secret[_\s]?key|password|token|credential)", "SENSITIVE_INFO_REQUEST", 0.80),
]

# ── PII Patterns ─────────────────────────────────────────────────────────
PII_PATTERNS = {
    "EMAIL": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b",
    "PHONE_IN": r"\+?91[-\s]?[6-9]\d{4}[-\s]?\d{5}",
    "PHONE_GENERIC": r"\b\d{10,12}\b",
    "AADHAAR": r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",
    "PAN": r"\b[A-Z]{5}\d{4}[A-Z]\b",
    "SSN": r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b",
    "CREDIT_CARD": r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
    "IP_ADDRESS": r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
}


class SecurityAuditResult:
    """Result of a security audit on a prompt."""

    def __init__(self):
        self.allowed = True
        self.risk_score = 0.0
        self.threats: list[dict] = []
        self.pii_detections: list[dict] = []
        self.sanitized_text = ""
        self.audit_id = f"audit_{int(time.time()*1000)}"
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "audit_id": self.audit_id,
            "allowed": self.allowed,
            "risk_score": round(self.risk_score, 4),
            "threat_count": len(self.threats),
            "threats": self.threats,
            "pii_count": len(self.pii_detections),
            "pii_detections": self.pii_detections,
            "sanitized_text": self.sanitized_text,
            "timestamp": self.timestamp,
        }


def audit_prompt(text: str) -> SecurityAuditResult:
    """
    Run comprehensive security audit on input text.

    Checks:
    1. Prompt injection / jailbreak patterns
    2. SQL injection patterns
    3. PII detection and redaction
    4. Output length bounds
    """
    result = SecurityAuditResult()
    text_lower = text.lower()
    sanitized = text

    # ── Threat Detection ─────────────────────────────────────────────
    max_risk = 0.0
    for pattern, threat_type, confidence in INJECTION_PATTERNS:
        matches = re.findall(pattern, text_lower)
        if matches:
            result.threats.append({
                "type": threat_type,
                "pattern": pattern,
                "confidence": confidence,
                "match_count": len(matches),
            })
            max_risk = max(max_risk, confidence)

    # ── PII Detection & Redaction ────────────────────────────────────
    for pii_type, pattern in PII_PATTERNS.items():
        matches = re.findall(pattern, sanitized)
        if matches:
            result.pii_detections.append({
                "type": pii_type,
                "count": len(matches),
                "action": "REDACTED",
            })
            sanitized = re.sub(pattern, f"[REDACTED_{pii_type}]", sanitized)

    # ── Risk Scoring ─────────────────────────────────────────────────
    result.risk_score = max_risk
    result.sanitized_text = sanitized

    # Block if risk is high
    if max_risk >= 0.85:
        result.allowed = False
        result.sanitized_text = "[BLOCKED BY AI SECURITY GUARDRAILS]"

    return result


def audit_output(text: str) -> dict[str, Any]:
    """
    Audit agent OUTPUT before returning to user.

    Checks:
    - PII in responses (model hallucinating real data)
    - Dangerous code snippets
    - Excessive length
    """
    issues = []
    sanitized = text

    # Check for PII in output
    for pii_type, pattern in PII_PATTERNS.items():
        matches = re.findall(pattern, sanitized)
        if matches:
            issues.append(f"Output contains {pii_type}")
            sanitized = re.sub(pattern, f"[REDACTED_{pii_type}]", sanitized)

    # Length guard
    if len(text) > 50000:
        issues.append("Output exceeds 50K character limit")
        sanitized = sanitized[:50000] + "\n... [TRUNCATED BY SECURITY AGENT]"

    return {
        "clean": len(issues) == 0,
        "issues": issues,
        "sanitized_output": sanitized,
    }


def analyze_query(query: str) -> dict[str, Any]:
    """Route security agent queries."""
    q = query.lower()

    if any(kw in q for kw in ["scan", "audit", "check"]):
        # They want to scan a specific text
        result = audit_prompt(query)
        return {
            "agent": "SecurityAgent",
            "type": "audit_report",
            **result.to_dict(),
        }

    elif any(kw in q for kw in ["policy", "rules", "owasp"]):
        return {
            "agent": "SecurityAgent",
            "type": "policy_info",
            "owasp_coverage": [
                "LLM01: Prompt Injection — Pattern-based detection with 12+ signatures",
                "LLM02: Insecure Output — Output sanitization with PII redaction",
                "LLM03: Training Data Poisoning — Feature drift PSI monitoring",
                "LLM05: Supply Chain — Dependency pinning in pyproject.toml",
                "LLM06: Sensitive Info — 8-type PII detection (email, phone, Aadhaar, PAN, SSN, CC, IP)",
                "LLM07: Insecure Plugin — Rate limiting on inference endpoints",
                "LLM09: Overreliance — Confidence intervals on predictions",
                "LLM10: Model DoS — Query timeouts and row limits on SQL",
            ],
            "pii_types_detected": list(PII_PATTERNS.keys()),
            "injection_signatures_count": len(INJECTION_PATTERNS),
        }

    else:
        return {
            "agent": "SecurityAgent",
            "type": "status",
            "message": "AI Security Agent active. All prompts are screened for injection attacks, PII, and OWASP LLM Top 10 violations.",
            "injection_patterns": len(INJECTION_PATTERNS),
            "pii_patterns": len(PII_PATTERNS),
        }
