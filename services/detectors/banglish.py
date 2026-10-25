"""Banglish (Romanised Bangla) transliteration canonicalizer and lexicon engine."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

LEXICON_VERSION = "1.0.0"

# Phonetic normalization patterns for common Banglish spelling variations
BANGLISH_PHONETIC_REPLACEMENTS = [
    # v -> bh (e.g., vule -> bhule)
    (r"\bvule\b", "bhule"),
    (r"\bvul\b", "bhul"),
    (r"\bvalo\b", "bhalo"),
    # sob -> shob
    (r"\bsob\b", "shob"),
    # kota -> kotha
    (r"\bkota\b", "kotha"),
    # pathaw -> pathao
    (r"\bpathaw\b", "pathao"),
    # transfer koro / patan
    (r"\bpathan\b", "pathao"),
    # den -> dao (polite vs imperative normalization)
    (r"\bden\b", "dao"),
    (r"\bbolun\b", "bolo"),
    (r"\bjan\b", "jao"),
]

# Canonical trigger concepts for adversarial prompts in Banglish
BANGLISH_CANONICAL_PATTERNS: dict[str, list[str]] = {
    "BANGLISH_INSTRUCTION_OVERRIDE": [
        r"(?:age|ager|purber|shob)\s+(?:shob|kotha|nirdesh|instruction)\s+(?:bhule|vule|bad|cancel)\s*(?:jao|dao|koro)?",
        r"(?:ager|purbo)\s+(?:rules|niyom)\s+(?:ignore|bad|cancel)\s*(?:koro)?",
        r"shob\s+(?:instruction|niyom)\s+(?:bhule|vule)\s*jao",
    ],
    "BANGLISH_SECRET_EXFILTRATION": [
        r"(?:amake|amare)?\s*(?:password|secret|gopon\s+kotha|canary|admin\s+key)\s*(?:dao|bolo|dekhao|pathao)",
        r"(?:system\s+prompt|admin\s+pass)\s*(?:ki|bolo|dao|dekhao)",
        r"(?:shob\s+data|customer\s+data)\s*(?:export|leak|pathao|send)\s*koro",
    ],
    "BANGLISH_FINANCIAL_ACTION": [
        r"(?:taka|balance|fund|ortho)\s*(?:pathao|transfer\s+koro|send\s+koro|ferot\s+dao|refund\s+dao)",
        r"(?:taka|refund)\s*(?:dao|koro)\s*(?:account\s+e)?",
    ],
    "BANGLISH_ROLE_HIJACK": [
        r"tumi\s+ekhon\s+(?:theke\s+)?(?:admin|boss|developer|unrestricted|god\s+mode)",
        r"ekhon\s+theke\s+tumi\s+ja\s+iccha\s+tai\s+korba",
    ],
}


@dataclass
class BanglishAnalysis:
    """Encapsulates Banglish transliteration analysis."""

    canonical_text: str
    detected_triggers: list[str] = field(default_factory=list)
    has_banglish_intent: bool = False
    lexicon_version: str = LEXICON_VERSION


class BanglishCanonicalizer:
    """Canonicalizes romanised Bangla text to eliminate spelling variations."""

    def __init__(self) -> None:
        self.phonetic_rules = [
            (re.compile(pattern, re.IGNORECASE), replacement)
            for pattern, replacement in BANGLISH_PHONETIC_REPLACEMENTS
        ]
        self.trigger_patterns = {
            category: [re.compile(p, re.IGNORECASE) for p in patterns]
            for category, patterns in BANGLISH_CANONICAL_PATTERNS.items()
        }

    def process(self, text: str) -> BanglishAnalysis:
        """Apply phonetic normalization and detect canonical Banglish adversarial patterns."""
        normalized = text.lower()

        # Step 1: Apply phonetic spelling normalizations
        for pattern_re, replacement in self.phonetic_rules:
            normalized = pattern_re.sub(replacement, normalized)

        # Step 2: Check for canonical trigger patterns
        detected: list[str] = []
        for category, patterns in self.trigger_patterns.items():
            for pat in patterns:
                if pat.search(normalized):
                    detected.append(category)
                    break

        return BanglishAnalysis(
            canonical_text=normalized,
            detected_triggers=detected,
            has_banglish_intent=len(detected) > 0,
            lexicon_version=LEXICON_VERSION,
        )
