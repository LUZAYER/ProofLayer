"""OWASP LLM 2025 mapped attack taxonomy for automated red teaming."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TaxonomyCategory:
    id: str
    name: str
    owasp_mapping: str
    description: str
    remediation_suggestion: str


ATTACK_TAXONOMY: dict[str, TaxonomyCategory] = {
    "DIRECT_PROMPT_INJECTION": TaxonomyCategory(
        id="DIRECT_PROMPT_INJECTION",
        name="Direct Prompt Injection / Instruction Override",
        owasp_mapping="LLM01:2025-Prompt-Injection",
        description="User prompts explicitly ordering the agent to ignore system instructions or constraints.",
        remediation_suggestion="Enforce strict input normalisation, char n-gram ML classification, and lower the policy block threshold.",
    ),
    "INDIRECT_PROMPT_INJECTION": TaxonomyCategory(
        id="INDIRECT_PROMPT_INJECTION",
        name="Indirect Document & Tool Injection",
        owasp_mapping="LLM01:2025-Prompt-Injection",
        description="Adversarial instructions embedded in third-party tickets, emails, or retrieved documents.",
        remediation_suggestion="Apply Spotlighting boundaries on all untrusted segments and enforce provenance isolation rules.",
    ),
    "SYSTEM_PROMPT_EXTRACTION": TaxonomyCategory(
        id="SYSTEM_PROMPT_EXTRACTION",
        name="System Prompt Extraction",
        owasp_mapping="LLM02:2025-Sensitive-Information-Disclosure",
        description="Prompts attempting to reveal the agent's initial prompt, developer directives, or hidden tokens.",
        remediation_suggestion="Plant canary verification tokens and enforce regex extraction patterns across en/bn/bn-Latn.",
    ),
    "CANARY_EXFILTRATION": TaxonomyCategory(
        id="CANARY_EXFILTRATION",
        name="Sensitive Data / Canary Exfiltration",
        owasp_mapping="LLM02:2025-Sensitive-Information-Disclosure",
        description="Extracting planted canary tokens or secrets from memory and leaking to external sinks.",
        remediation_suggestion="Configure output scanning with canary token pattern matching and external domain allowlists.",
    ),
    "EXCESSIVE_AGENCY": TaxonomyCategory(
        id="EXCESSIVE_AGENCY",
        name="Excessive Agency & Tool Misuse",
        owasp_mapping="LLM06:2025-Excessive-Agency",
        description="Tricks forcing the agent to execute unauthorized refunds or high-impact actions.",
        remediation_suggestion="Define per-call and per-session spend limits and mandate human analyst approval above threshold.",
    ),
    "DATA_FLOW_VIOLATION": TaxonomyCategory(
        id="DATA_FLOW_VIOLATION",
        name="Data-Flow Taint Violation",
        owasp_mapping="LLM02:2025-Sensitive-Information-Disclosure",
        description="Routing sensitive data (balances, tokens) from internal tool responses to external sinks.",
        remediation_suggestion="Add declarative data_flow_rules forbidding sensitive source tags from flowing to email/webhook sinks.",
    ),
    "ENCODING_OBFUSCATION_EVASION": TaxonomyCategory(
        id="ENCODING_OBFUSCATION_EVASION",
        name="Encoding & Obfuscation Evasion",
        owasp_mapping="LLM01:2025-Prompt-Injection",
        description="Adversarial inputs disguised via base64, hex, ROT13, homoglyphs, or zero-width spaces.",
        remediation_suggestion="Enable multi-layer recursive decoding (depth >= 3) and homoglyph substitution in the text normalizer.",
    ),
    "MULTILINGUAL_EVASION": TaxonomyCategory(
        id="MULTILINGUAL_EVASION",
        name="Multilingual Evasion (Bangla & Banglish)",
        owasp_mapping="LLM01:2025-Prompt-Injection",
        description="Adversarial prompts translated into native Bangla or romanised Banglish with colloquial variations.",
        remediation_suggestion="Deploy the Banglish transliteration canonicalizer and train language-balanced ML classifiers.",
    ),
    "MULTI_TURN_STAGED_ATTACK": TaxonomyCategory(
        id="MULTI_TURN_STAGED_ATTACK",
        name="Multi-Turn Staged Jailbreak",
        owasp_mapping="LLM01:2025-Prompt-Injection",
        description="Gradual conditioning where early benign turns setup context before executing an injection.",
        remediation_suggestion="Maintain conversation-level context tracking and evaluate cumulative session risk scores.",
    ),
}
