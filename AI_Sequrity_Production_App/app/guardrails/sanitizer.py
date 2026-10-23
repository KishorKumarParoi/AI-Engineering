"""Input sanitization and prompt injection delimiter security filters."""

import re
import unicodedata


def sanitize_input(text: str) -> tuple[str, bool]:
    """Sanitize user input, stripping dangerous control characters and homoglyphs.

    Returns:
        (sanitized_text, contains_suspicious_patterns)
    """
    # Normalize unicode to NFKC to defeat homoglyph obfuscation
    normalized = unicodedata.normalize("NFKC", text)

    # Strip null bytes and non-printable control characters
    stripped = "".join(ch for ch in normalized if ch == "\n" or ch == "\t" or not unicodedata.category(ch).startswith("C"))

    suspicious = False
    # Check for prompt injection delimiters like triple backtick system injections
    injection_patterns = [
        r"```\s*system",
        r"<\|im_start\|>",
        r"<\|im_end\|>",
        r"\[INST\]",
        r"\[/INST\]",
        r"\{\{.*?system.*?\}\}",
    ]

    for pat in injection_patterns:
        if re.search(pat, stripped, flags=re.IGNORECASE):
            suspicious = True
            stripped = re.sub(pat, "[FILTERED_DELIMITER]", stripped, flags=re.IGNORECASE)

    return stripped.strip(), suspicious
