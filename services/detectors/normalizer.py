"""Multilingual text normalisation, script handling, and multi-layer decoding."""

from __future__ import annotations

import base64
import binascii
import codecs
import re
import unicodedata
from dataclasses import dataclass, field
from urllib.parse import unquote

# Zero-width and BiDi control characters
ZERO_WIDTH_AND_BIDI_CHARS = {
    "\u200b",  # Zero-width space
    "\u200c",  # Zero-width non-joiner (ZWNJ) - handled specially for Bangla if needed
    "\u200d",  # Zero-width joiner (ZWJ)
    "\u200e",  # Left-to-right mark
    "\u200f",  # Right-to-left mark
    "\u202a",  # Left-to-right embedding
    "\u202b",  # Right-to-left embedding
    "\u202c",  # Pop directional formatting
    "\u202d",  # Left-to-right override
    "\u202e",  # Right-to-left override
    "\u2060",  # Word joiner
    "\ufeff",  # Byte order mark / zero-width no-break space
}

# Common Latin confusables / homoglyphs from Cyrillic & Greek
HOMOGLYPH_MAP = {
    # Cyrillic lookalikes to Latin
    "а": "a",
    "А": "A",
    "в": "b",
    "В": "B",
    "с": "c",
    "С": "C",
    "е": "e",
    "Е": "E",
    "н": "h",
    "Н": "H",
    "і": "i",
    "І": "I",
    "ј": "j",
    "Ј": "J",
    "к": "k",
    "К": "K",
    "м": "m",
    "М": "M",
    "о": "o",
    "О": "O",
    "р": "p",
    "Р": "P",
    "ѕ": "s",
    "Ѕ": "S",
    "т": "t",
    "Т": "T",
    "у": "y",
    "У": "Y",
    "х": "x",
    "Х": "X",
    # Greek lookalikes to Latin
    "α": "a",
    "Α": "A",
    "β": "b",
    "Β": "B",
    "γ": "y",
    "Γ": "F",
    "ε": "e",
    "Ε": "E",
    "η": "n",
    "Η": "H",
    "ι": "i",
    "Ι": "I",
    "κ": "k",
    "Κ": "K",
    "ο": "o",
    "Ο": "O",
    "ρ": "p",
    "Ρ": "P",
    "τ": "t",
    "Τ": "T",
    "υ": "u",
    "Υ": "Y",
    "χ": "x",
    "Χ": "X",
}

# Bangla numeral to Arabic digit mapping
BANGLA_DIGIT_MAP = {
    "০": "0",
    "১": "1",
    "২": "2",
    "৩": "3",
    "৪": "4",
    "৫": "5",
    "৬": "6",
    "৭": "7",
    "৮": "8",
    "৯": "9",
}

# Simple Leetspeak map for evasion detection
LEET_MAP = {
    "@": "a",
    "4": "a",
    "8": "b",
    "3": "e",
    "1": "i",
    "!": "i",
    "0": "o",
    "5": "s",
    "$": "s",
    "7": "t",
    "+": "t",
}


@dataclass
class NormalizationResult:
    """Encapsulates the result of multi-stage text normalisation."""

    original_text: str
    normalized_text: str
    decoded_layers: list[str] = field(default_factory=list)
    has_script_mixing: bool = False
    has_zero_width_chars: bool = False
    has_homoglyphs: bool = False
    has_bangla_script: bool = False
    detected_encodings: list[str] = field(default_factory=list)


class TextNormalizer:
    """Production-grade text normalizer resilient to adversarial evasion."""

    def __init__(self, max_decode_depth: int = 3, max_text_length: int = 65536) -> None:
        self.max_decode_depth = max_decode_depth
        self.max_text_length = max_text_length

    def normalize(self, text: str) -> NormalizationResult:
        """Run full normalization pipeline on input text."""
        if not text:
            return NormalizationResult(original_text="", normalized_text="")

        # Enforce input length bound against ReDoS / resource exhaustion
        if len(text) > self.max_text_length:
            text = text[: self.max_text_length]

        original = text
        detected_encodings: list[str] = []
        decoded_layers: list[str] = []

        # Check for zero-width characters before stripping
        has_zero_width = any(c in text for c in ZERO_WIDTH_AND_BIDI_CHARS)

        # Step 1: Strip zero-width & BiDi controls
        text = "".join(c for c in text if c not in ZERO_WIDTH_AND_BIDI_CHARS)

        # Step 2: Unicode NFKC normalization
        text = unicodedata.normalize("NFKC", text)

        # Step 3: Recursive multi-layer decoding (base64, URL, hex, rot13)
        curr = text
        for _ in range(self.max_decode_depth):
            decoded, enc_type = self._attempt_decode_layer(curr)
            if decoded is not None and decoded != curr:
                detected_encodings.append(enc_type)
                decoded_layers.append(decoded)
                curr = unicodedata.normalize("NFKC", decoded)
            else:
                break
        text = curr

        # Step 4: Bangla script analysis & digit normalization
        has_bangla = bool(re.search(r"[\u0980-\u09FF]", text))
        text = "".join(BANGLA_DIGIT_MAP.get(c, c) for c in text)

        # Normalize Bangla Dari (Bengali full stop) to period for sentence splitting
        text = text.replace("।", ".")

        # Step 5: Check for homoglyphs and replace
        has_homoglyphs = any(c in text for c in HOMOGLYPH_MAP)
        if has_homoglyphs:
            text = "".join(HOMOGLYPH_MAP.get(c, c) for c in text)

        # Step 6: Script mixing detection (Latin + Cyrillic / Greek / Bangla within single words)
        has_mixing = self._detect_script_mixing(original)

        # Step 7: Collapse whitespace and strip comments
        # Strip HTML comments: <!-- ... -->
        text = re.sub(r"<!--.*?-->", " ", text, flags=re.DOTALL)
        # Strip Markdown block comments or hidden delimiters
        text = re.sub(r"\[\/\/\]:\s*#\s*\(.*?\)", " ", text)
        # Collapse multiple spaces and newlines
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n\s*\n+", "\n\n", text).strip()

        return NormalizationResult(
            original_text=original,
            normalized_text=text,
            decoded_layers=decoded_layers,
            has_script_mixing=has_mixing,
            has_zero_width_chars=has_zero_width,
            has_homoglyphs=has_homoglyphs,
            has_bangla_script=has_bangla,
            detected_encodings=detected_encodings,
        )

    def _attempt_decode_layer(self, text: str) -> tuple[str | None, str]:
        """Attempt to decode common single-layer obfuscations."""
        trimmed = text.strip()

        # 1. URL encoding (e.g., %20, %2F, %3C)
        if "%" in trimmed:
            unquoted = unquote(trimmed)
            if unquoted != trimmed:
                return unquoted, "url_encoding"

        # 2. Base64 encoding check (must be valid base64, len >= 16, printable ascii)
        # Match standard base64 strings or prefixed (base64:...)
        b64_candidate = trimmed
        if trimmed.lower().startswith("base64:"):
            b64_candidate = trimmed[7:].strip()

        if len(b64_candidate) >= 16 and len(b64_candidate) % 4 == 0:
            if re.fullmatch(r"[A-Za-z0-9+/]+={0,2}", b64_candidate):
                try:
                    raw = base64.b64decode(b64_candidate, validate=True)
                    decoded_str = raw.decode("utf-8")
                    if decoded_str.isprintable() and len(decoded_str) > 3:
                        return decoded_str, "base64"
                except (binascii.Error, UnicodeDecodeError):
                    pass

        # 3. Hex encoding (e.g. 0x69676e6f7265 or sequence of \x69)
        hex_match = re.fullmatch(r"(?:0x|\\x)?([0-9a-fA-F]{2}){4,}", trimmed)
        if hex_match:
            try:
                cleaned_hex = re.sub(r"0x|\\x", "", trimmed)
                decoded_str = bytes.fromhex(cleaned_hex).decode("utf-8")
                if decoded_str.isprintable() and len(decoded_str) > 3:
                    return decoded_str, "hex"
            except (ValueError, UnicodeDecodeError):
                pass

        # 4. ROT13 check for obvious instruction keywords
        try:
            rot = codecs.decode(trimmed, "rot_13")
            # Only trigger if ROT13 reveals explicit injection commands
            keywords = [
                "ignore",
                "forget",
                "system",
                "override",
                "instruction",
                "password",
                "canary",
            ]
            if any(kw in rot.lower() for kw in keywords) and not any(
                kw in trimmed.lower() for kw in keywords
            ):
                return rot, "rot13"
        except Exception:
            pass

        return None, ""

    def _detect_script_mixing(self, text: str) -> bool:
        """Detect mixed scripts within single word tokens."""
        words = re.findall(r"\b\w+\b", text)
        for w in words:
            has_latin = bool(re.search(r"[a-zA-Z]", w))
            has_cyrillic = bool(re.search(r"[\u0400-\u04FF]", w))
            has_bangla = bool(re.search(r"[\u0980-\u09FF]", w))
            # Flag if Latin is mixed with Cyrillic or Bangla in the exact same word
            if has_latin and (has_cyrillic or has_bangla):
                return True
        return False
