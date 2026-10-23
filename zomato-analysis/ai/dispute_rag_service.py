"""
Production-Grade Dispute Resolution & Customer RAG Service for Zomato.
Includes PII tokenization, prompt injection defenses, policy retrieval, and automated fraud gating.
"""

import re
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

# Indian Mobile Number & PII Signatures
MOBILE_REGEX = re.compile(r"(?:\+?91[-.\s]?)?[6-9]\d{9}\b")
CARD_REGEX = re.compile(r"\b(?:\d{4}[- ]?){3}\d{4}\b")
INJECTION_SIGNATURES = [
    re.compile(r"(?i)\bignore\s+(all\s+)?(previous\s+)?(instructions|refund\s+rules|policies)\b"),
    re.compile(r"(?i)\byou\s+are\s+now\s+in\s+unrestricted\s+mode\b"),
    re.compile(r"(?i)\bgrant\s+(me\s+)?(full\s+)?refund\s+unconditionally\b"),
]

# Internal Zomato Customer Support Policies
ZOMATO_POLICIES = [
    {
        "id": "REF-POL-01",
        "title": "Missing Item Refund Policy",
        "content": "If a customer reports a missing item with photographic proof of the receipt and delivered bag, credit full item value + 20% convenience coupon within 5 minutes.",
        "max_refund_inr": 1500.0
    },
    {
        "id": "REF-POL-02",
        "title": "Spilled or Cold Food Policy",
        "content": "For food delivered spilt or excessively cold (>45 mins beyond ETA), offer 100% refund to original payment source or instant Zomato Money wallet credit.",
        "max_refund_inr": 2000.0
    },
    {
        "id": "REF-POL-03",
        "title": "Delivery Delay Compensation",
        "content": "Deliveries delayed > 30 minutes due to rider or kitchen fault are eligible for delivery fee refund + 50 INR apology voucher.",
        "max_refund_inr": 200.0
    }
]


@dataclass
class DisputeResolutionResult:
    dispute_id: str
    original_prompt: str
    sanitized_prompt: str
    pii_filtered: bool
    injection_detected: bool
    policy_applied: str
    decision: str              # "AUTO_REFUND_APPROVED", "MANUAL_REVIEW_REQUIRED", "REJECTED"
    refund_amount_inr: float
    justification: str
    latency_ms: float


class ZomatoDisputeRAGService:
    """
    RAG & Guardrail service managing automated refund decisions under strict enterprise constraints.
    """

    def process_dispute(self, dispute_id: str, customer_prompt: str, claimed_amount_inr: float) -> DisputeResolutionResult:
        t0 = time.perf_counter()

        # 1. PII Tokenization (Sanitize Indian mobile numbers & card details)
        sanitized = MOBILE_REGEX.sub("<PII:MOBILE_REDACTED>", customer_prompt)
        sanitized = CARD_REGEX.sub("<PII:CARD_REDACTED>", sanitized)
        pii_found = sanitized != customer_prompt

        # 2. Prompt Injection Defense
        injection_found = any(pat.search(sanitized) for pat in INJECTION_SIGNATURES)
        if injection_found:
            elapsed = (time.perf_counter() - t0) * 1000
            return DisputeResolutionResult(
                dispute_id=dispute_id,
                original_prompt=customer_prompt,
                sanitized_prompt=sanitized,
                pii_filtered=pii_found,
                injection_detected=True,
                policy_applied="SECURITY-SHIELD-01",
                decision="REJECTED",
                refund_amount_inr=0.0,
                justification="Dispute rejected: Inbound request triggered adversarial prompt injection signature.",
                latency_ms=round(elapsed, 1)
            )

        # 3. Policy Retrieval & Resolution
        matched_policy = ZOMATO_POLICIES[0]
        if "cold" in sanitized.lower() or "spill" in sanitized.lower() or "late" in sanitized.lower():
            matched_policy = ZOMATO_POLICIES[1]
        elif "delay" in sanitized.lower():
            matched_policy = ZOMATO_POLICIES[2]

        # 4. Financial Bound Verification
        if claimed_amount_inr <= matched_policy["max_refund_inr"]:
            decision = "AUTO_REFUND_APPROVED"
            approved_amount = claimed_amount_inr
            justification = f"Claim of ₹{claimed_amount_inr} approved under policy '{matched_policy['title']}'."
        else:
            decision = "MANUAL_REVIEW_REQUIRED"
            approved_amount = 0.0
            justification = f"Claim of ₹{claimed_amount_inr} exceeds auto-approval threshold (₹{matched_policy['max_refund_inr']}). Routed to Senior Fraud Ops."

        elapsed = (time.perf_counter() - t0) * 1000
        return DisputeResolutionResult(
            dispute_id=dispute_id,
            original_prompt=customer_prompt,
            sanitized_prompt=sanitized,
            pii_filtered=pii_found,
            injection_detected=False,
            policy_applied=matched_policy["id"],
            decision=decision,
            refund_amount_inr=approved_amount,
            justification=justification,
            latency_ms=round(elapsed, 1)
        )


# Global Singleton Dispute Service
dispute_service = ZomatoDisputeRAGService()
