"""PII and secret scanning engine with entropy checks and safe redaction."""

from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass, field
from typing import Literal


@dataclass
class Finding:
    """Represents a discovered secret or PII entity."""

    entity_type: str
    category: Literal["SECRET", "PII"]
    value: str
    redacted_value: str
    start: int
    end: int
    confidence: float = 1.0


@dataclass
class ScanOutputResult:
    """Result of scanning text for sensitive leakage."""

    has_leakage: bool
    findings: list[Finding] = field(default_factory=list)
    sanitized_text: str = ""


# Precompiled regex patterns
EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")

# Bangladesh phone numbers: +8801[3-9]XXXXXXXX or 01[3-9]XXXXXXXX (with optional hyphens/spaces)
BD_PHONE_PATTERN = re.compile(r"(?:\+880\s?1|01)[3-9](?:[0-9][\s-]?){7}[0-9]\b")

# Generic international E.164 phone numbers
INTL_PHONE_PATTERN = re.compile(r"\+(?:[0-9][\s-]?){8,14}[0-9]\b")

# Generic credit card candidates (13-19 digits, optionally spaced or hyphenated)
CREDIT_CARD_CANDIDATE = re.compile(r"\b(?:\d{4}[ -]?){3}\d{1,4}\b|\b\d{13,19}\b")

# Bangladesh National ID patterns (10 digits smart NID, or 13/17 digits old NID)
BD_NID_PATTERN = re.compile(r"\b(?:19\d{2}|20\d{2})?\d{10}\b|\b\d{10}\b")

# Secrets: JWT tokens
JWT_PATTERN = re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b")

# Secrets: Common API keys (OpenAI, GitHub, AWS, Generic)
API_KEY_PATTERNS = [
    ("OPENAI_KEY", re.compile(r"\bsk-[A-Za-z0-9]{32,}\b")),
    ("GITHUB_TOKEN", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36}\b")),
    ("AWS_ACCESS_KEY", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("GENERIC_BEARER", re.compile(r"(?i)\bbearer\s+([A-Za-z0-9_\-\.]{24,})\b")),
    ("CANARY_TOKEN", re.compile(r"\bCANARY-[A-Z0-9_\-]{5,}\b")),
]

# Private Key Headers
PRIVATE_KEY_HEADER = re.compile(
    r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----[\s\S]+?-----END (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"
)


def calculate_shannon_entropy(data: str) -> float:
    """Calculate the Shannon entropy of a string."""
    if not data:
        return 0.0
    entropy = 0.0
    length = len(data)
    for x in set(data):
        p_x = float(data.count(x)) / length
        entropy += -p_x * math.log(p_x, 2)
    return entropy


def luhn_checksum_valid(number_str: str) -> bool:
    """Validate numeric string using Luhn algorithm."""
    digits = [int(c) for c in number_str if c.isdigit()]
    if len(digits) < 13 or len(digits) > 19:
        return False
    # Reverse digits
    rev = digits[::-1]
    total = 0
    for i, d in enumerate(rev):
        if i % 2 == 1:
            d2 = d * 2
            total += d2 - 9 if d2 > 9 else d2
        else:
            total += d
    return total % 10 == 0


class PIIScanner:
    """High-performance PII and secret scanner with multiple redaction strategies."""

    def __init__(self, redaction_mode: Literal["mask", "drop", "hash"] = "mask") -> None:
        self.redaction_mode = redaction_mode

    def scan(self, text: str) -> ScanOutputResult:
        """Scan text and return findings with sanitized output."""
        if not text:
            return ScanOutputResult(has_leakage=False, sanitized_text="")

        findings: list[Finding] = []

        # 1. Private key blocks
        for m in PRIVATE_KEY_HEADER.finditer(text):
            val = m.group(0)
            redacted = self._redact(val, "PRIVATE_KEY")
            findings.append(
                Finding(
                    entity_type="PRIVATE_KEY",
                    category="SECRET",
                    value=val,
                    redacted_value=redacted,
                    start=m.start(),
                    end=m.end(),
                    confidence=1.0,
                )
            )

        # 2. JWTs
        for m in JWT_PATTERN.finditer(text):
            val = m.group(0)
            redacted = self._redact(val, "JWT")
            findings.append(
                Finding(
                    entity_type="JWT_TOKEN",
                    category="SECRET",
                    value=val,
                    redacted_value=redacted,
                    start=m.start(),
                    end=m.end(),
                    confidence=1.0,
                )
            )

        # 3. API Keys & Canary Tokens
        for key_type, pattern in API_KEY_PATTERNS:
            for m in pattern.finditer(text):
                val = m.group(0)
                redacted = self._redact(val, key_type)
                findings.append(
                    Finding(
                        entity_type=key_type,
                        category="SECRET",
                        value=val,
                        redacted_value=redacted,
                        start=m.start(),
                        end=m.end(),
                        confidence=1.0,
                    )
                )

        # 4. Email addresses
        for m in EMAIL_PATTERN.finditer(text):
            val = m.group(0)
            redacted = self._redact_email(val)
            findings.append(
                Finding(
                    entity_type="EMAIL_ADDRESS",
                    category="PII",
                    value=val,
                    redacted_value=redacted,
                    start=m.start(),
                    end=m.end(),
                    confidence=0.99,
                )
            )

        # 5. Bangladesh phone numbers
        for m in BD_PHONE_PATTERN.finditer(text):
            val = m.group(0)
            redacted = self._redact_phone(val)
            findings.append(
                Finding(
                    entity_type="PHONE_NUMBER_BD",
                    category="PII",
                    value=val,
                    redacted_value=redacted,
                    start=m.start(),
                    end=m.end(),
                    confidence=0.95,
                )
            )

        # 6. Credit cards (with Luhn validation)
        for m in CREDIT_CARD_CANDIDATE.finditer(text):
            raw_digits = re.sub(r"\D", "", m.group(0))
            if luhn_checksum_valid(raw_digits):
                val = m.group(0)
                redacted = self._redact_card(raw_digits)
                findings.append(
                    Finding(
                        entity_type="CREDIT_CARD",
                        category="PII",
                        value=val,
                        redacted_value=redacted,
                        start=m.start(),
                        end=m.end(),
                        confidence=1.0,
                    )
                )

        # 7. High-entropy candidate strings (length >= 24, entropy >= 4.5)
        words = re.findall(r"\b[A-Za-z0-9+/=_-]{24,}\b", text)
        for w in words:
            # Skip if already captured
            if any(w in f.value for f in findings):
                continue
            entropy = calculate_shannon_entropy(w)
            if entropy >= 4.5:
                start_pos = text.find(w)
                redacted = self._redact(w, "HIGH_ENTROPY_SECRET")
                findings.append(
                    Finding(
                        entity_type="HIGH_ENTROPY_SECRET",
                        category="SECRET",
                        value=w,
                        redacted_value=redacted,
                        start=start_pos,
                        end=start_pos + len(w),
                        confidence=0.85,
                    )
                )

        # Sort findings by start position ascending
        findings.sort(key=lambda x: x.start)

        # Build sanitized text by replacing findings from end to start to preserve indices
        sanitized = text
        for f in reversed(findings):
            sanitized = sanitized[: f.start] + f.redacted_value + sanitized[f.end :]

        return ScanOutputResult(
            has_leakage=len(findings) > 0,
            findings=findings,
            sanitized_text=sanitized,
        )

    def _redact(self, val: str, tag: str) -> str:
        if self.redaction_mode == "drop":
            return ""
        if self.redaction_mode == "hash":
            digest = hashlib.sha256(val.encode("utf-8")).hexdigest()[:8]
            return f"[{tag}:SHA256:{digest}]"
        # Mask mode
        if len(val) <= 8:
            return "[REDACTED]"
        return f"{val[:3]}...{val[-3:]}"

    def _redact_email(self, email: str) -> str:
        if self.redaction_mode == "drop":
            return ""
        if self.redaction_mode == "hash":
            digest = hashlib.sha256(email.encode("utf-8")).hexdigest()[:8]
            return f"[EMAIL:SHA256:{digest}]"
        parts = email.split("@", 1)
        user = parts[0]
        domain = parts[1] if len(parts) > 1 else ""
        masked_user = user[0] + "***" if user else "***"
        return f"{masked_user}@{domain}"

    def _redact_phone(self, phone: str) -> str:
        if self.redaction_mode == "drop":
            return ""
        if self.redaction_mode == "hash":
            digest = hashlib.sha256(phone.encode("utf-8")).hexdigest()[:8]
            return f"[PHONE:SHA256:{digest}]"
        digits = re.sub(r"\D", "", phone)
        if len(digits) >= 10:
            return f"{digits[:3]}****{digits[-4:]}"
        return "[PHONE_REDACTED]"

    def _redact_card(self, digits: str) -> str:
        if self.redaction_mode == "drop":
            return ""
        if self.redaction_mode == "hash":
            digest = hashlib.sha256(digits.encode("utf-8")).hexdigest()[:8]
            return f"[CARD:SHA256:{digest}]"
        return f"{digits[:4]}-****-****-{digits[-4:]}"
