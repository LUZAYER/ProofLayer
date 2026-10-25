"""Provenance boundary tagging, Spotlighting delimiters, and structural signal analysis."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

ProvenanceTag = Literal["SYSTEM", "USER", "TOOL_OUTPUT", "RETRIEVED_DOC", "WEB"]

UNTRUSTED_TAGS: set[ProvenanceTag] = {"TOOL_OUTPUT", "RETRIEVED_DOC", "WEB"}

# Common imperative and directive indicators across English, Bangla, and Banglish
IMPERATIVE_PATTERNS = [
    # English
    r"\b(?:must|shall|always|never|execute|run|send|forward|call|extract|ignore|override|delete|update)\b",
    # Bangla
    r"(?:করুন|করো|পাঠাও|মুছে\s+ফেলো|উপেক্ষা\s+করো|প্রকাশ\s+করো|অবিলম্বে|হবে|করবে)",
    # Banglish
    r"\b(?:koro|korun|pathao|delete\s+koro|send\s+koro|bhule\s+jao|dekhao)\b",
]


@dataclass
class SegmentAnalysis:
    """Analysis of a single provenance-tagged segment."""

    text: str
    provenance: ProvenanceTag
    is_untrusted: bool
    spotlighted_text: str
    instruction_density: float  # 0.0 to 1.0
    has_untrusted_instruction: bool


class ProvenanceAnalyzer:
    """Enforces provenance boundaries and analyzes instruction density in untrusted segments."""

    def __init__(self) -> None:
        self.compiled_imperatives = [re.compile(p, re.IGNORECASE) for p in IMPERATIVE_PATTERNS]

    def analyze_segment(self, text: str, provenance: ProvenanceTag) -> SegmentAnalysis:
        """Analyze a segment and apply cryptographic/structured spotlight delimiters."""
        is_untrusted = provenance in UNTRUSTED_TAGS

        # Calculate instruction density
        words = text.split()
        num_words = len(words)
        if num_words == 0:
            density = 0.0
        else:
            imperative_hits = 0
            for pat in self.compiled_imperatives:
                imperative_hits += len(pat.findall(text))
            density = min(1.0, imperative_hits / max(10, num_words))

        # Flag strong indicator if untrusted segment has high instruction density or imperative commands
        has_untrusted_instruction = is_untrusted and (density >= 0.10 or imperative_hits >= 1)

        # Apply Spotlighting delimiter wrapping for untrusted content
        if is_untrusted:
            spotlighted = (
                f'\n<<<PROOFLAYER_UNTRUSTED_DATA provenance="{provenance}">>>\n'
                f"{text}\n"
                f"<<</PROOFLAYER_UNTRUSTED_DATA>>>\n"
            )
        else:
            spotlighted = text

        return SegmentAnalysis(
            text=text,
            provenance=provenance,
            is_untrusted=is_untrusted,
            spotlighted_text=spotlighted,
            instruction_density=density,
            has_untrusted_instruction=has_untrusted_instruction,
        )

    def correlate_cross_segments(
        self, user_segments: list[str], untrusted_segments: list[str]
    ) -> bool:
        """Check if untrusted segment contains action directives not present in user query."""
        user_text = " ".join(user_segments).lower()
        for untrusted in untrusted_segments:
            analysis = self.analyze_segment(untrusted, "RETRIEVED_DOC")
            if analysis.has_untrusted_instruction:
                # If untrusted segment mentions refund or email and user never asked for it
                triggers = ["refund", "email", "transfer", "taka", "password", "canary"]
                for trig in triggers:
                    if trig in untrusted.lower() and trig not in user_text:
                        return True
        return False
