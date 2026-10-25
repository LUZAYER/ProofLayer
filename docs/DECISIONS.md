# Architecture Decision Records (ADR) — ProofLayer

This document records the foundational architectural, security, and algorithmic decisions made during the design and engineering of ProofLayer.

---

## ADR 001: Multilingual-First Architecture (Bangla, Banglish, and English)

### Status
Accepted

### Context
Most existing AI guardrail and governance platforms (Lakera, NeMo Guardrails, Langfuse, Prompt Security) are designed almost exclusively for English-language prompts. Emerging markets in South Asia (including Bangladesh with 180M+ people and global Bangla diaspora) deploy autonomous customer agents, banking assistants, and public services that process queries in standard Bangla script (বাংলা), Romanised Bangla ("Banglish"), and mixed code-switching. Traditional tokenizers and English-oriented injection heuristics completely fail to detect adversarial prompts in these dialects.

### Decision
ProofLayer adopts a first-class multilingual architecture:
1. Multi-stage script normalisation handling Bangla Unicode normalization forms, zero-width joiners/non-joiners (`ZWJ`/`ZWNJ`), and Bangla digit mapping.
2. A dedicated Banglish transliteration canonicalizer that maps Romanised phonetic variations (e.g., "amake shob data dao", "instruction bhule jao", "taka pathao") into canonical semantic tokens.
3. Language-balanced synthetic datasets and evaluation splits covering English, Bangla, and Banglish.
4. Pluggable language-pack interface allowing expansion to other emerging market languages (Hindi, Urdu, Arabic).

### Consequences
- High resilience against multilingual evasion attacks.
- Requires maintaining a curated lexicon of transliteration roots with automated testing.

---

## ADR 002: Offline Determinism with NaiveSimLLM and CPU-Only ML

### Status
Accepted

### Context
To qualify for competitive judging at the International AI Builders Congress 2026, the provenance policy strictly prohibits fabricated demonstrations or dependence on flaky third-party cloud APIs. The evaluation harness and demo sandbox must be 100% reproducible on any standard workstation or laptop without requiring GPU acceleration or paid external API keys.

### Decision
1. **CPU-Only ML**: The ML detector uses character n-gram (1–5) TF-IDF feature extraction coupled with a calibrated linear classifier (Platt scaling / isotonic calibration) via `scikit-learn`. Model inference completes in under 15 milliseconds on modern CPU cores.
2. **Deterministic NaiveSimLLM**: The sandbox ("BankDesk") bundles a deterministic, seed-controlled simulation model. When Shield is OFF, it dutifully executes instructions found in untrusted documents (demonstrating breach). When Shield is ON, ProofLayer intercepts the payload.
3. **Pluggable Real LLM Provider**: Real LLM endpoints (OpenAI, Anthropic, Gemini) are supported via environment variables for live production deployments.

### Consequences
- Zero external network dependencies for CI, local development, and demonstration.
- Fair, reproducible scientific benchmarking with 95% Wilson confidence intervals.

---

## ADR 003: Cryptographic Audit Ledger with SHA-256 Chaining and Ed25519 Signatures

### Status
Accepted

### Context
AI agent governance requires provable compliance. If an agent executes a fraudulent refund or leaks confidential PII, post-incident investigations require mathematical proof that the audit trail was not modified, deleted, or backdated by an attacker or rogue administrator.

### Decision
ProofLayer implements a cryptographic append-only audit ledger:
1. Each event is serialized into canonical JSON (RFC 8785 style) and linked to the preceding event via SHA-256 hash chaining:
   $$\text{hash}_n = \text{SHA-256}(\text{CanonicalJSON}(\text{event}_n) \,||\, \text{hash}_{n-1})$$
2. The event hash is digitally signed using an Ed25519 private key.
3. Public keys are served via `/v1/audit/pubkey` and verifiable offline using the `prooflayer-verify` CLI.
4. Raw secrets and raw PII are strictly redacted prior to hashing and storage, guaranteeing privacy compliance.

### Consequences
- Any alteration, deletion, or reordering of audit events immediately invalidates the cryptographic chain.
- The verifier can pinpoint the exact index of any tampering attempt.

---

## ADR 004: Spotlighting and Provenance-Driven Trust Boundaries

### Status
Accepted

### Context
Indirect prompt injection occurs when untrusted retrieved documents, tool outputs, or web content contain instructions that hijack the model's intent. Traditional architectures feed all context to the LLM indiscriminately.

### Decision
ProofLayer enforces the foundational security principle:
> **"Content from tools, documents, and the web is untrusted data, never instructions."**

1. Every text segment is explicitly tagged with a provenance label: `SYSTEM`, `USER`, `TOOL_OUTPUT`, `RETRIEVED_DOC`, or `WEB`.
2. Untrusted segments undergo Spotlighting: automatic wrapping with cryptographic provenance boundary delimiters before reaching the model.
3. The policy engine forbids untrusted document segments from triggering tool actions unless independently corroborated by an authorized `USER` instruction.

### Consequences
- Structural prevention of indirect injection.
- Seamless compatibility with both standard LLMs and tool-calling agent loops.

---

## ADR 005: Declarative YAML Policy Engine with Dry-Run Simulation

### Status
Accepted

### Context
Security policies must be auditable, version-controlled, and testable without risking downtime or accidental disruption to production agent workflows.

### Decision
1. Policies are defined in human-readable declarative YAML validated by strict JSON schemas.
2. Policy constructs support tool constraints, argument validation, spend thresholds, data-flow taint analysis, and detector confidence bands.
3. ProofLayer provides a dry-run simulator endpoint (`POST /v1/policies/simulate`) that evaluates proposed policy changes against historical traffic before enforcement.

### Consequences
- Operators can preview policy impacts and false-positive rates prior to applying new security rules.
