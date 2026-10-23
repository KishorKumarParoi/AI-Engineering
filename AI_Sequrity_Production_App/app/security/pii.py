"""
Enterprise PII & Secrets Detection, Redaction, and Tokenization Engine.
Compliant with ISO 27001 (A.8.11 Data Masking) and GDPR Article 32/35.

Features:
- Algorithmic Luhn verification for credit card numbers.
- High-recall detection for SSNs, emails, phone numbers, and IP addresses.
- Strict heuristic signatures for cloud credentials (AWS, Groq, OpenAI, JWTs, Private Keys).
- Reversible tokenization preserving semantic intent during LLM inference.
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


class MaskingMode(str, Enum):
    REDACT = "redact"          # Replace with [REDACTED_ENTITY]
    TOKENIZE = "tokenize"      # Replace with <PII:ENTITY_1> (reversible)
    PARTIAL = "partial"        # e.g., ****-****-****-1234


@dataclass
class PIIEntity:
    entity_type: str
    original_value: str
    start_pos: int
    end_pos: int
    token: Optional[str] = None
    masked_value: Optional[str] = None
    confidence: float = 1.0


@dataclass
class PIIScanResult:
    has_pii: bool
    sanitized_text: str
    detected_entities: List[PIIEntity] = field(default_factory=list)
    token_map: Dict[str, str] = field(default_factory=dict)  # token -> original_value
    summary_by_type: Dict[str, int] = field(default_factory=dict)


def _luhn_checksum_valid(card_number: str) -> bool:
    """Validates a credit card string using the standard Luhn algorithm (Mod 10)."""
    digits = [int(c) for c in card_number if c.isdigit()]
    if len(digits) < 13 or len(digits) > 19:
        return False
    checksum = 0
    reverse_digits = digits[::-1]
    for i, digit in enumerate(reverse_digits):
        if i % 2 == 1:
            doubled = digit * 2
            checksum += doubled - 9 if doubled > 9 else doubled
        else:
            checksum += digit
    return checksum % 10 == 0


class PIIFilterEngine:
    """
    Enterprise-grade bidirectional PII & Secrets Filter.
    Applies regex heuristics, algorithmic validation, and semantic tokenization.
    """

    # Secret & Credential Regex Signatures
    PATTERNS_SECRETS = {
        "AWS_ACCESS_KEY": re.compile(r"\b(AKIA[0-9A-Z]{16})\b"),
        "AWS_SECRET_KEY": re.compile(r"\b([a-zA-Z0-9/+=]{40})\b"),
        "GROQ_API_KEY": re.compile(r"\b(gsk_[a-zA-Z0-9]{48,64})\b"),
        "OPENAI_API_KEY": re.compile(r"\b(sk-[a-zA-Z0-9-_]{20,64})\b"),
        "JWT_TOKEN": re.compile(r"\b(eyJ[a-zA-Z0-9-_]{10,}\.eyJ[a-zA-Z0-9-_]{10,}\.[a-zA-Z0-9-_]{10,})\b"),
        "PRIVATE_KEY": re.compile(r"-----BEGIN\s+(?:RSA|EC|DSA|OPENSSH|PGP)?\s*PRIVATE KEY-----[\s\S]+?-----END\s+(?:RSA|EC|DSA|OPENSSH|PGP)?\s*PRIVATE KEY-----"),
    }

    # Standard PII Signatures
    PATTERNS_PII = {
        "EMAIL": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"),
        "PHONE_NUMBER": re.compile(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
        "US_SSN": re.compile(r"\b(?!000|666|9\d{2})\d{3}[- ]?(?!00)\d{2}[- ]?(?!0000)\d{4}\b"),
        "IPV4_ADDRESS": re.compile(r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b"),
        "CREDIT_CARD": re.compile(r"\b(?:\d{4}[- ]?){3}\d{4}\b|\b\d{13,19}\b"),
    }

    def __init__(self, default_mode: MaskingMode = MaskingMode.TOKENIZE):
        self.default_mode = default_mode

    def scan_and_mask(self, text: str, mode: Optional[MaskingMode] = None) -> PIIScanResult:
        """
        Scans inbound or outbound text for PII & secret tokens, applying the specified masking mode.
        """
        if not text:
            return PIIScanResult(has_pii=False, sanitized_text="", detected_entities=[], token_map={})

        active_mode = mode or self.default_mode
        detected: List[PIIEntity] = []
        token_map: Dict[str, str] = {}
        type_counts: Dict[str, int] = {}

        # 1. Scan Secrets first (highest criticality)
        for sec_type, regex in self.PATTERNS_SECRETS.items():
            for match in regex.finditer(text):
                val = match.group(0)
                # Filter false positives for short secret patterns
                if sec_type == "AWS_SECRET_KEY" and (len(val) != 40 or " " in val):
                    continue
                detected.append(PIIEntity(
                    entity_type=sec_type,
                    original_value=val,
                    start_pos=match.start(),
                    end_pos=match.end(),
                    confidence=0.98,
                ))

        # 2. Scan Standard PII
        for pii_type, regex in self.PATTERNS_PII.items():
            for match in regex.finditer(text):
                val = match.group(0)
                # Specialized verification for Credit Cards (Luhn check)
                if pii_type == "CREDIT_CARD":
                    clean_digits = re.sub(r"\D", "", val)
                    if not _luhn_checksum_valid(clean_digits):
                        continue
                detected.append(PIIEntity(
                    entity_type=pii_type,
                    original_value=val,
                    start_pos=match.start(),
                    end_pos=match.end(),
                    confidence=0.95,
                ))

        if not detected:
            return PIIScanResult(
                has_pii=False,
                sanitized_text=text,
                detected_entities=[],
                token_map={},
                summary_by_type={},
            )

        # Sort matches by start position descending to allow safe in-place replacement
        detected.sort(key=lambda e: e.start_pos, reverse=True)

        sanitized_chars = list(text)
        
        # Deduplicate overlapping matches
        filtered_detected: List[PIIEntity] = []
        last_start = len(text) + 1

        for ent in detected:
            if ent.end_pos <= last_start:
                filtered_detected.append(ent)
                last_start = ent.start_pos

        # Re-sort descending
        filtered_detected.sort(key=lambda e: e.start_pos, reverse=True)

        for ent in filtered_detected:
            type_counts[ent.entity_type] = type_counts.get(ent.entity_type, 0) + 1
            idx = type_counts[ent.entity_type]
            
            token = f"<{ent.entity_type}_{idx}>"
            ent.token = token
            token_map[token] = ent.original_value

            if active_mode == MaskingMode.TOKENIZE:
                replacement = token
            elif active_mode == MaskingMode.REDACT:
                replacement = f"[REDACTED_{ent.entity_type}]"
            elif active_mode == MaskingMode.PARTIAL:
                orig = ent.original_value
                if len(orig) > 4:
                    replacement = f"***{orig[-4:]}"
                else:
                    replacement = "***"
            else:
                replacement = token

            ent.masked_value = replacement
            sanitized_chars[ent.start_pos:ent.end_pos] = list(replacement)

        final_text = "".join(sanitized_chars)

        return PIIScanResult(
            has_pii=True,
            sanitized_text=final_text,
            detected_entities=list(reversed(filtered_detected)),
            token_map=token_map,
            summary_by_type=type_counts,
        )

    def detokenize(self, text: str, token_map: Dict[str, str]) -> str:
        """
        Reverses tokenization by replacing <ENTITY_ID> back with the original value.
        Restricted to post-inference output when authorized.
        """
        if not text or not token_map:
            return text

        result = text
        for token, original in token_map.items():
            result = result.replace(token, original)
        return result


# Global Singleton Filter
pii_engine = PIIFilterEngine(default_mode=MaskingMode.TOKENIZE)
