from __future__ import annotations

import hashlib
import re

PII_PATTERNS: dict[str, str] = {
    "email": r"[\w\.-]+@[\w\.-]+\.\w+",
    # Long identifiers first, so phone matching cannot partially redact a card.
    "credit_card": r"(?<!\w)(?:\d[ -]?){12,18}\d(?!\w)",
    "cccd": r"(?<!\w)\d{12}(?!\w)",
    "phone_vn": r"(?<!\w)(?:\+84|0)(?:[ .-]?\d){9}(?!\w)",
}


def scrub_text(text: str) -> str:
    safe = text
    for name, pattern in PII_PATTERNS.items():
        safe = re.sub(pattern, f"[REDACTED_{name.upper()}]", safe)
    return safe


def summarize_text(text: str, max_len: int = 80) -> str:
    safe = scrub_text(text).strip().replace("\n", " ")
    return safe[:max_len] + ("..." if len(safe) > max_len else "")


def hash_user_id(user_id: str) -> str:
    return hashlib.sha256(user_id.encode("utf-8")).hexdigest()[:12]
