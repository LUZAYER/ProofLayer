# PROOFLAYER — MASTER BUILD PROMPT (for Google Antigravity)

> Paste this whole document into the Antigravity Manager as the mission brief.
> Work phase by phase. Do NOT start a phase until the previous phase's acceptance gate passes.

---

## 0. ROLE AND MISSION

You are a principal-level engineering team (staff backend engineer, security engineer, ML engineer, frontend engineer, SRE, technical writer) building **ProofLayer**: a production-grade **security, governance and trust layer for AI agents**.

ProofLayer sits between an AI agent, its model, its tools and its data, and does four things:

1. **Shield** — a runtime gateway that detects prompt injection (direct and indirect), enforces tool policies, stops secret and personal-data leakage, requires human approval for risky actions, and writes a tamper-evident audit trail.
2. **Red Team** — an automated, multilingual attack-testing engine that measures how vulnerable an agent is, before and after Shield, and explains how to fix it.
3. **Proof** — signed, verifiable evidence: a hash-chained, digitally signed audit log plus compliance reports mapped to recognised frameworks.
4. **Console** — a polished, bilingual (English and Bangla) web dashboard to operate all of the above.

The product is being entered in the **International AI Builders Congress 2026** (CloudCamp Bangladesh), where projects are judged on **innovation, technical proficiency, business potential, global scalability and responsible AI**, and where the provenance policy forbids fabricated results, fake demos and misleading performance claims. Everything you build must therefore be **real, working, tested and honestly measured**.

### Differentiator (keep it in the product, docs and demo)
Most AI-security tooling is English-first. ProofLayer is **multilingual-first** (Bangla, Banglish/romanised Bangla, English, with an extensible language-pack system), built for the emerging-market agent deployments that incumbents under-serve.

### Hard deadline context
The team preliminary submission is expected around **31 October 2026**. Therefore the work is split into **priority tiers** (Section 3). **P0 must be fully working before any P1 work starts.** A smaller product that works and is honestly measured beats a broad product that is partly simulated.

---

## 1. NON-NEGOTIABLE RULES

### 1.1 Honesty and provenance (critical)
- Never fabricate metrics, benchmarks, customers, revenue, testimonials or screenshots. Every number shown in the UI, README or docs must be produced by code in this repository (the evaluation harness) or be explicitly labelled **"illustrative assumption"**.
- All datasets in the repo are **synthetic** unless a licensed public source is explicitly listed in `docs/PROVENANCE.md`. Label synthetic data as synthetic everywhere it appears (file headers, dataset cards, UI badges).
- If detector performance is weak on some category or language, **report it**. Honest limits are a feature. The evaluation report must include a "Known limitations and failure modes" section.
- Generate `docs/PROVENANCE.md` documenting: every AI tool and model used to build the project, which parts were AI-generated or AI-assisted, every dataset and its origin and licence, third-party dependencies, and what the human team must still review.
- Do not claim certification or compliance. Compliance mapping is **indicative**, never a certification.

### 1.2 Safety and scope of offensive content
ProofLayer includes attack-simulation capability. It must stay a **defensive testing tool**:
- Attack payloads are **benign proof-of-concept probes** whose only "malicious goal" is to make a sandbox agent reveal a **canary token**, call a **fake tool** with a forbidden argument, or ignore a **fake system rule**. Payload goals must never involve real malware, real exploits, real credentials or real people.
- The Red Team engine may only target (a) the bundled sandbox agent, or (b) an agent endpoint the operator explicitly registers and confirms they own or are authorised to test (require an explicit "I am authorised to test this target" confirmation recorded in the audit log). Default configuration allows **localhost / private-network targets only**.
- No real personal data. All people, accounts, phone numbers, emails and card numbers in fixtures are fake. Use reserved or obviously invalid formats where possible (for example `example.com`, `+880 1XXX-XXXXXX` style fakes, test card numbers that fail real issuance).
- No code that scans, scrapes or attacks third-party systems. The sandbox tools have **no outbound network access**.

### 1.3 Engineering quality bar
- Production-level: typed, linted, tested, documented, containerised, observable, secure by default.
- No placeholder code, no `TODO` left in P0 paths, no mocked functionality presented as real. If something is simulated (for example the deterministic "naive LLM" in the sandbox), it must be named as such in code, UI and docs.
- Every module has unit tests. Every API endpoint has an integration test. Critical flows have end-to-end tests.
- Pin dependency versions. Provide a lockfile. Do not add dependencies you cannot justify.
- Secrets only via environment variables; ship `.env.example`; never commit secrets.

### 1.4 Antigravity working protocol
- **Plan first.** Before writing code, produce an Implementation Plan artifact covering architecture, module boundaries, data models, API contracts, test strategy and risks. Wait for it to be internally consistent, then proceed.
- Maintain a **Task List artifact** mapped to the phases below; tick items only when their tests pass.
- Use parallel agents where modules are independent (for example gateway core, dashboard, dataset generation), but **integrate through the API contracts defined in Section 5** and re-run the full test suite after each merge.
- Use the **browser agent** to verify the dashboard end-to-end (navigation, forms, live updates, Bangla/English toggle, keyboard navigation) and attach screenshots to the walkthrough.
- After each phase, produce a **Walkthrough artifact**: what was built, how it was verified, test output, known gaps.
- If a requirement is ambiguous, choose the safer, simpler interpretation, record it in `docs/DECISIONS.md` (ADR style), and continue.
- If the environment lacks something (for example Docker, a GPU, an API key), the project must still run in a **degraded but fully functional local mode** (Section 4.3).

---

## 2. PRODUCT SCOPE AT A GLANCE

| Module | What it is |
|---|---|
| `gateway` | FastAPI service: OpenAI-compatible proxy plus tool-authorisation API plus policy engine plus detectors plus audit log |
| `detectors` | Python package: normalisation, rules, ML classifier, PII/secret scanners, canary tokens, ensemble scoring, explanations |
| `policy` | Declarative YAML policy language, validator, simulator (dry run), versioning |
| `audit` | Hash-chained, Ed25519-signed append-only log plus offline verifier CLI |
| `redteam` | Attack corpus, mutation engine, runner, scorer, report generator |
| `sandbox` | "BankDesk" intentionally vulnerable demo agent with fake data and fake tools (Shield on/off switch) |
| `console` | Next.js plus TypeScript dashboard, bilingual |
| `sdk-python` / `sdk-ts` | Thin client SDKs plus integration examples |
| `eval` | Reproducible evaluation harness and dataset builder |
| `docs` | Architecture, threat model, evaluation, provenance, responsible AI, demo runbook, submission drafts |
| `infra` | Docker Compose, CI, Makefile, scripts |

---

## 3. PRIORITY TIERS

### P0 — MUST WORK (target: complete first; this alone is a winning submission)
1. Gateway with prompt-injection detection (direct plus indirect), tool-policy enforcement, output leakage scanning, human-approval queue, audit log with verification.
2. Detector ensemble (rules plus trained classifier) with normalisation for Bangla, Banglish and English.
3. BankDesk sandbox agent with the **Shield OFF = breach, Shield ON = blocked** demo, fully deterministic and reproducible.
4. Red Team runner with the synthetic attack corpus, per-language attack-success-rate (ASR), before and after Shield.
5. Evaluation harness producing `metrics.json` plus `docs/EVALUATION.md` (ASR, false-positive rate, precision/recall, latency).
6. Console with: Overview, Live Traffic, Incidents, Approvals, Red Team run and results, Audit verifier. English plus Bangla.
7. Docker Compose one-command start (`make up`) and a no-Docker local mode.
8. Tests, CI, README, demo runbook.

### P1 — SHOULD WORK (after P0 is green)
9. Policy editor with validation and dry-run simulation in the console.
10. Compliance report generator (HTML plus PDF plus JSON) mapped to OWASP Top 10 for LLM Applications, NIST AI RMF and ISO/IEC 42001 (indicative).
11. Multi-tenant organisations, API keys, RBAC (admin, analyst, viewer).
12. Python and TypeScript SDKs with examples.
13. Adaptive attack set (held out from tuning) and mutation engine v2.

### P2 — NICE TO HAVE
14. Webhook/Slack-style notification connector (local mock receiver included).
15. Optional LLM-based judge detector via pluggable provider (off by default).
16. Language pack scaffolding with one extra pack stub (for example Hindi/Urdu) demonstrating extensibility, clearly labelled experimental.
17. Load-test script and published latency profile.

---

## 4. ARCHITECTURE

### 4.1 Repository layout (monorepo)

```
prooflayer/
├─ README.md
├─ Makefile
├─ docker-compose.yml
├─ .env.example
├─ .github/workflows/ci.yml
├─ docs/
│  ├─ ARCHITECTURE.md  THREAT_MODEL.md  EVALUATION.md  PROVENANCE.md
│  ├─ RESPONSIBLE_AI.md  DECISIONS.md  API.md  POLICY_LANGUAGE.md
│  ├─ COMPLIANCE_MAPPING.md  DEMO_RUNBOOK.md  BUSINESS_MODEL_ILLUSTRATIVE.md
│  ├─ SUBMISSION_ONE_PAGER.md  VIDEO_SCRIPT_3MIN.md  DATASET_CARDS/
├─ services/
│  ├─ gateway/        (FastAPI app, routers, middleware, pipelines)
│  ├─ detectors/      (installable Python package)
│  ├─ policy/         (policy engine package)
│  ├─ audit/          (audit log package plus CLI verifier)
│  ├─ redteam/        (attack engine package plus CLI)
│  └─ sandbox/        (BankDesk agent plus fake tools plus fixtures)
├─ apps/
│  └─ console/        (Next.js plus TypeScript plus Tailwind)
├─ sdk/
│  ├─ python/  └─ typescript/
├─ eval/
│  ├─ datasets/ (synthetic, versioned, with dataset cards)
│  ├─ build_datasets.py  run_eval.py  report.py
├─ policies/          (example YAML policies)
└─ scripts/           (seed, demo, verify, load-test)
```

### 4.2 Technology choices (use these unless you record an ADR for a change)
- **Backend:** Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2 plus Alembic, `httpx`, `uvicorn`, `structlog`, `prometheus-client`, `cryptography` (Ed25519), `PyYAML`, `jsonschema`.
- **ML (CPU only):** scikit-learn (char n-gram TF-IDF plus calibrated logistic regression / linear SVM with Platt or isotonic calibration). Persist with `joblib`. No GPU needed. Optional small multilingual embedding model only as a P2 plug-in.
- **Database:** SQLite by default (zero-config), PostgreSQL in Docker Compose. Same SQLAlchemy models for both.
- **Realtime:** WebSocket or Server-Sent Events from gateway to console.
- **Frontend:** Next.js (App Router) plus TypeScript plus Tailwind plus a charting library (Recharts or equivalent), `next-intl` or equivalent for English/Bangla i18n, Playwright for e2e.
- **Packaging/infra:** Docker, Docker Compose, Makefile, GitHub Actions, `ruff`, `mypy`, `pytest`, `pytest-cov`, `eslint`, `prettier`.

### 4.3 Run modes
1. **Full mode:** `make up` starts gateway, Postgres, console, sandbox with Docker Compose.
2. **Local mode (no Docker):** `make dev` runs gateway with SQLite, sandbox, and console via `uvicorn` and `npm run dev`; seed data included.
3. **Offline mode:** no external API keys required for anything in P0. The sandbox uses the bundled deterministic simulated model (Section 6.1). A real model provider adapter is optional via environment variables.

### 4.4 Core request flow (Shield pipeline)

```
Agent/App ──► ProofLayer Gateway
   1. Authenticate (API key → org, role, policy set)
   2. Normalise input (unicode, zero-width, homoglyph, encodings)
   3. Provenance-tag every content segment: SYSTEM | USER | TOOL_OUTPUT | RETRIEVED_DOC | WEB
   4. Input scan   → detectors (rules + ML + canary + PII/secret)
   5. Spotlighting → wrap untrusted segments with provenance markers/delimiters
   6. Decision     → ALLOW | ALLOW_WITH_REDACTION | REQUIRE_APPROVAL | BLOCK
   7. Forward to model provider (or sandbox simulated model)
   8. Output scan  → secrets, PII, canary leakage, policy-violating content
   9. Tool-call mediation → every proposed tool call is authorised by the policy engine
  10. Audit append → signed, hash-chained event with redacted evidence
  11. Stream event to Console
```

Treat **content from tools, documents and the web as untrusted data, never as instructions.** This is the central security principle; encode it in the pipeline, the policy language and the docs.

---

## 5. API CONTRACTS (define these first; all modules integrate through them)

Generate an OpenAPI spec (`docs/openapi.json`) and keep it in sync via tests. Minimum endpoints:

### 5.1 Proxy and mediation
- `POST /v1/chat/completions` — OpenAI-compatible request/response. Accepts optional header `X-ProofLayer-Session`, `X-ProofLayer-Agent`. Messages may carry `metadata.provenance` per message part. Unlabelled tool/retrieval content defaults to **untrusted**.
- `POST /v1/shield/scan` — scan arbitrary text segments with provenance labels; returns decision, scores, categories, evidence spans, explanation (bilingual), latency.
- `POST /v1/tools/authorize` — given `{agent, tool, arguments, context}` returns `{decision, reasons, requires_approval, approval_id?}`.
- `POST /v1/output/scan` — scan model output for leakage; returns redactions and findings.

### 5.2 Approvals
- `GET /v1/approvals?status=pending`
- `POST /v1/approvals/{id}/decision` with `{decision: approve|deny, note}` (analyst/admin only; audited).

### 5.3 Audit
- `GET /v1/audit/events?…filters…` (paginated, redacted)
- `GET /v1/audit/verify` — verifies the hash chain and signatures and returns `{valid, checked, first_broken_index?}`.
- CLI: `prooflayer-verify --db … --pubkey …` verifies offline.

### 5.4 Policies
- `GET/PUT /v1/policies/{id}` (versioned), `POST /v1/policies/validate`, `POST /v1/policies/simulate` (dry-run a policy against recorded or supplied events and show would-be decisions).

### 5.5 Red Team
- `POST /v1/redteam/runs` — `{target, languages[], categories[], shield_mode: off|on|both, seed}`; async run.
- `GET /v1/redteam/runs/{id}` — status, per-attack results, aggregates, per-language ASR, before/after delta.
- `GET /v1/redteam/runs/{id}/report?format=html|pdf|json`
- Targets require the authorisation confirmation described in 1.2.

### 5.6 Org, auth, metrics
- `POST /v1/orgs`, `POST /v1/keys`, `GET /v1/me`, `GET /healthz`, `GET /readyz`, `GET /metrics` (Prometheus).

Standard error format, request IDs, idempotency keys for POSTs that create runs, pagination, rate limits, and strict request-size limits.

---

## 6. MODULE SPECIFICATIONS

### 6.1 Sandbox — "BankDesk" (the demo centrepiece)

A deliberately vulnerable customer-support agent for a **fictional bank** ("Padma Test Bank"), with **entirely fake** data.

**Fake data (in-memory plus JSON fixtures):** ~50 fake customers with fake account IDs, fake phone numbers and emails, balances, and notes; each customer record contains a **unique canary token** (for example `CANARY-ACC-7F3A9`) planted in a sensitive field; a fake internal "system prompt" containing a **system-prompt canary**; a fake "admin API key" canary.

**Fake tools (no network, no real side effects):**
- `lookup_account(account_id)` — returns the fake record.
- `issue_refund(account_id, amount, reason)` — mutates fake state; policy-sensitive (amount limits, approval over a threshold).
- `send_email(to, subject, body)` — writes to an in-memory "outbox" (viewable in the sandbox UI); policy-sensitive (external-domain allowlist, no sensitive data in body).
- `fetch_document(doc_id)` — returns a document from a fixture library. Some fixtures are **poisoned with benign canary-goal indirect injections** (in English, Bangla and Banglish) to simulate untrusted content.
- `summarize_ticket(ticket_id)` — returns ticket text (also may be poisoned).

**The simulated model ("NaiveSimLLM")** — clearly labelled as a simulation: a deterministic, seed-controlled component that behaves like an over-compliant LLM agent: it follows instruction-like text found anywhere in its context (including tool outputs) according to simple, transparent rules, and emits tool calls and text accordingly. This makes the **breach reproducible** with no API keys, and makes before/after comparison scientifically fair. Implement an optional `ProviderAdapter` for a real model via env vars, but P0 must not depend on it. Document that results on the simulated model measure the **gateway's detection and policy enforcement**, not the behaviour of any specific commercial model, and say so in the UI and `EVALUATION.md`.

**Shield switch:** a toggle (and API flag) routes the agent either directly to the model/tools (**OFF**) or through ProofLayer (**ON**). The sandbox has its own small web UI showing: the conversation, the tool calls, the fake outbox, the fake refund ledger, and a live "BREACH DETECTED" banner when a canary token leaves a boundary (appears in an email body, a model output shown to an unauthorised user, or a forbidden tool argument).

**Acceptance gate:** with Shield OFF, the scripted indirect-injection scenario reliably causes a canary leak or forbidden tool call; with Shield ON, the same scenario is blocked or sent for approval, an incident appears in the console, and the audit chain verifies.

### 6.2 Detectors (`services/detectors`)

Pipeline stages, each independently testable and returning structured evidence (category, score 0–1, matched spans, explanation key):

**A. Normalisation**
- Unicode NFKC, remove zero-width and bidi control characters, collapse homoglyphs and confusables (Latin/Cyrillic/Greek lookalikes), normalise whitespace, strip HTML/markdown comment tricks, decode common encodings recursively with a depth limit (base64, hex, URL-encoding, ROT13, simple leetspeak) while recording that decoding occurred (it is itself a signal).
- Bangla-aware: normalise Bangla digits, handle Bangla joiners and normalisation forms, detect script mixing.
- **Banglish handling:** a transliteration-normalisation layer mapping common romanised Bangla instruction vocabulary and spelling variants (for example variants of "ignore/forget previous instructions", "send", "tell me the password") to canonical tokens. Keep the lexicon as a data file, versioned, with tests.

**B. Rules pack** (YAML-driven, per language pack)
- Instruction-override phrases, role-reassignment, system-prompt extraction requests, data-exfiltration requests, "act as admin" claims, tool-misuse requests, delimiter/format-smuggling, hidden-instruction markers in documents.
- Each rule: id, category, languages, severity, regex or token pattern, rationale, example positives and negatives (used as unit tests), OWASP mapping.

**C. ML classifier**
- Char n-gram (1–5) TF-IDF plus linear model, **calibrated probabilities**, trained on the synthetic dataset (Section 7) with language-balanced sampling.
- Output: injection probability per segment plus top contributing n-grams (for explanation).
- Model card: training data, splits, metrics, limitations. Model artifact versioned and loaded at startup; training is reproducible with a fixed seed (`make train`).

**D. Structural/behavioural signals**
- Provenance violation: instruction-like language inside UNTRUSTED segments (strong signal regardless of wording).
- Instruction-density scoring for retrieved documents.
- Cross-segment correlation: untrusted segment instructs an action that the user never requested.
- Canary token detection (planted tokens appearing where they should not).

**E. PII and secret scanners**
- Secrets: common API-key/token shapes, private-key headers, high-entropy strings with context, JWTs.
- PII (synthetic-safe): email, phone (Bangladesh and international formats), card numbers with Luhn validation, national-ID-like patterns **as generic digit patterns only**, IBAN-like patterns.
- Redaction modes: mask, hash-tag, drop; reversible tokenisation only inside the tenant boundary (optional, P1).

**F. Ensemble and decision**
- Weighted, configurable combination → single risk score with category breakdown; thresholds per policy; abstain band → `REQUIRE_APPROVAL` when uncertain.
- Every decision produces a **bilingual human-readable explanation** ("Blocked: a retrieved document contained an instruction to send customer data to an external address") generated from templates, not from an LLM (deterministic, auditable).

**Performance target:** p95 scan latency for typical inputs (≤ 4 KB) under 50 ms on a laptop CPU for the non-LLM pipeline. Measure and report the real number.

### 6.3 Policy engine (`services/policy`)

A declarative YAML policy language, with JSON-Schema validation, versioning and a simulator.

Capabilities:
- **Tool rules:** allowlist/denylist per agent and per role; argument constraints (JSON Schema, regex, numeric ranges, domain allowlists); per-session and per-time-window rate and spend limits (for example "refunds ≤ 50 per call, ≤ 200 per day"); **approval thresholds** (above a limit, require human approval); **data-flow rules** (for example "tool output tagged `sensitive` may not flow into `send_email.body` or any external-domain recipient").
- **Content rules:** thresholds per detector category, redaction behaviour, language-specific overrides.
- **Provenance rules:** untrusted segments may never trigger tool calls unless the user's own message independently requested the action.
- **Modes:** `enforce`, `monitor` (log only), `shadow` (log would-be decisions).
- **Explainability:** every decision lists the rule IDs that fired.
- Ship 4 example policies (`strict-bank`, `balanced-support`, `monitor-only`, `dev-sandbox`) with tests.

Write `docs/POLICY_LANGUAGE.md` with a full reference and examples.

### 6.4 Audit and Proof (`services/audit`)

- Append-only event table; each event stores: sequence number, timestamp (UTC), org, agent, session, event type, decision, rule/detector IDs, **redacted** evidence, previous hash, hash, signature.
- `hash = SHA-256(canonical_json(event_without_hash) || previous_hash)`; signature = Ed25519 over the hash. Key generation on first run; private key in a configurable path or environment secret; public key exposed for verification; key rotation procedure documented (events record the key ID).
- **No raw secrets or raw personal data in the log** — redact before write. Add tests that deliberately try to log a secret and assert it never reaches storage.
- **Verifier:** library, API and standalone CLI that detects (and pinpoints) tampering, deletion, reordering and signature forgery. Include a "tamper demo" script and a console button ("Simulate tampering on a copy") that proves detection live.
- Export signed evidence bundles (JSON plus manifest plus signature).

### 6.5 Approvals

- State machine: `pending → approved | denied | expired`. Configurable expiry, default-deny on expiry.
- Console queue with context (what the agent tried, which rule fired, redacted evidence, risk score), keyboard shortcuts, bilingual labels.
- Every decision is audited with the human's identity and note. Prevent self-approval where the actor and approver are the same identity (policy-controlled).
- On approval, the gateway releases the held tool call exactly once (idempotent).

### 6.6 Red Team engine (`services/redteam`)

**Attack taxonomy** (map each to OWASP Top 10 for LLM Applications categories; **verify the current official category names and numbering when writing the mapping and cite the version in the docs**):
- Direct prompt injection / instruction override
- Indirect injection via documents, tickets, web content, tool output
- System-prompt extraction (against the fake system prompt)
- Sensitive-data exfiltration (canary-based)
- Excessive agency / tool misuse (forbidden arguments, over-limit refunds)
- Data-flow violations (sensitive tool output routed to external email)
- Encoding/obfuscation evasion (base64, homoglyph, zero-width, split payloads)
- Multilingual evasion (Bangla, Banglish, mixed-script, code-switching)
- Multi-turn / staged attacks (benign setup turns, payload later)

**Corpus generation** (`eval/build_datasets.py`, deterministic with a seed): templates × slots × languages × obfuscation transforms → thousands of synthetic attacks; each labelled with category, language, transform, expected canary/tool-violation goal. Hand-write a **seed set** of Bangla and Banglish templates carefully (natural phrasing, multiple dialect/spelling variants); mark in the dataset card that native-speaker review is still recommended and flag unreviewed items.

**Splits:** `train` (for the classifier), `validation`, `test_heldout`, and `test_adaptive` — an adversarial set built with **mutation strategies that were not used to generate training data** (new obfuscations, paraphrase templates, payload splitting). The classifier and rules must **never be tuned on `test_heldout` or `test_adaptive`**; enforce this with a checksum test and document it.

**Runner:** drives the sandbox agent through each attack in both modes (Shield off / on), records outcomes: `breach` (canary leaked or forbidden tool call executed), `blocked`, `approval_required`, `no_effect`; computes ASR = breaches / attacks per category and language, plus 95% confidence intervals (Wilson); concurrency-limited and seed-reproducible.

**Benign set:** a large benign conversation/tool-use set (including tricky benign cases that mention "ignore", "password reset", "send email" legitimately, in all languages) to measure **false-positive rate** and task-success impact.

**Fix guidance:** for each failing category, produce a remediation suggestion (policy snippet to add, threshold to adjust, architectural note).

### 6.7 Compliance reports (P1)

Generate reports (HTML, PDF, JSON) containing: executive summary, test scope and method, ASR and FPR tables by language and category (before/after), top findings with evidence references to signed audit events, remediation plan, control mapping tables (OWASP LLM Top 10, NIST AI RMF functions, ISO/IEC 42001 clauses), explicit **limitations and "not a certification" disclaimer**, and a verification hash plus signature of the report itself. Keep mappings in data files (`docs/COMPLIANCE_MAPPING.md` plus YAML) with citations to the framework versions used.

### 6.8 Auth, tenancy, RBAC (P1)

- Organisations, users, API keys (stored hashed with a prefix for identification, shown once on creation), roles: `admin`, `analyst`, `viewer`.
- Row-level tenant isolation enforced in the data-access layer, with tests proving cross-tenant access is impossible.
- Console login (local accounts for the demo; document how to plug in OIDC).
- Rate limiting per key; request size limits; CORS locked down; security headers.

### 6.9 SDKs (P1)

- **Python:** `pip install`-able; `ProofLayer(api_key, base_url)`; `scan()`, `authorize_tool()`, `guard_tool` decorator, a drop-in OpenAI-client wrapper pointing at the gateway; async support.
- **TypeScript:** equivalent for Node.
- Examples: guarding a LangChain-style tool, guarding a raw function-calling loop, 10-line quickstart.

---

## 7. DATA AND EVALUATION

### 7.1 Datasets (all synthetic, versioned, with dataset cards in `docs/DATASET_CARDS/`)
- `injection_train/val/test_heldout/test_adaptive` as above, ≥ 3 languages (en, bn, bn-Latn "Banglish") plus mixed.
- `benign_*` sets across the same languages and domains (banking support, document summarisation, email drafting).
- `pii_secrets_synthetic` for scanners.
- Report class balance, per-language counts, generation seeds and generator commit hash.

### 7.2 Metrics (produced by `make eval`, written to `eval/out/metrics.json` and rendered into `docs/EVALUATION.md` and the console)
- Detection: precision, recall, F1, ROC-AUC, PR-AUC, per language and category, with confidence intervals.
- Security outcome: **ASR before vs after Shield**, per language and category (headline chart).
- Utility: **false-positive rate** and benign task-completion rate with Shield on.
- Performance: p50/p95/p99 added latency, throughput, memory.
- Calibration: reliability curve and expected calibration error.
- Ablation: rules-only vs ML-only vs ensemble vs ensemble+provenance rules.
- Adaptive-set results reported separately and honestly, including failure examples (redacted).
- **Known limitations** section generated from actual failures, plus a statement that results are on synthetic data and a simulated model and do not predict real-world performance.

### 7.3 Reproducibility
`make eval` must run from a clean clone, produce identical metrics given the same seed, and finish in a reasonable time on a laptop CPU. CI runs a reduced-size smoke version and fails if metrics regress beyond configured tolerances.

---

## 8. CONSOLE (apps/console)

**Design principles:** clean, calm, professional security-product aesthetic; dark and light themes; WCAG AA contrast; full keyboard navigation; responsive down to tablet; skeleton loaders; helpful empty states; no jargon without a tooltip. **Easy to use is a hard requirement:** a first-time user should reach the "Shield OFF vs ON" demo within three clicks from the home screen.

**i18n:** complete English and Bangla UI (all strings externalised, including explanations returned by the API), language toggle persisted, correct Bangla font stack and line-height, Bangla numerals option.

**Pages**
1. **Overview** — protected agents, requests scanned, incidents (24 h), block rate, approvals pending, latest ASR before/after card, audit-chain health indicator (green = verified).
2. **Live Traffic** — real-time stream with decision badges, filters (agent, decision, category, language), click-through to an event drawer showing provenance-tagged segments, highlighted evidence spans, rule IDs, bilingual explanation.
3. **Incidents** — grouped by category/agent, severity, timeline, linked audit events.
4. **Approvals** — queue with full context and approve/deny actions.
5. **Policies** (P1) — YAML editor with live validation, diff view, versioning, **dry-run simulator** showing how a change would alter decisions on recent traffic.
6. **Red Team** — configure and launch runs (target, languages, categories, mode), live progress, results with per-language ASR bar charts (before vs after), per-attack drill-down, remediation suggestions, report export. Includes the authorisation confirmation dialog.
7. **Proof / Audit** — event explorer, **Verify chain** button, **Simulate tampering** demo, export evidence bundle.
8. **Playground** — type or paste text with provenance labels and see a scan result instantly; includes sample poisoned documents in en/bn/bn-Latn.
9. **Settings** — API keys, members and roles (P1), language and theme.
10. **Demo mode** — a guided overlay walking through the 3-minute story (Section 11) with one-click scenario launchers.

All charts and numbers are fetched from real endpoints; no hard-coded demo values. Include Playwright e2e tests for: login, running the demo scenario, approving an action, running a red-team run, verifying the audit chain, switching language.

---

## 9. SECURITY OF PROOFLAYER ITSELF (a security product must be secure)

- Write `docs/THREAT_MODEL.md` (STRIDE per component; data-flow diagram in Mermaid; assets, trust boundaries, abuse cases, mitigations, residual risks). Include attacks against ProofLayer: detector evasion, policy bypass, log injection, audit tampering, tenant escape, SSRF via document fetch, resource exhaustion, ReDoS in rules, prompt injection against any LLM-based component.
- **ReDoS safety:** all regex rules run with input-length caps and timeouts; add tests with pathological inputs.
- **Resource limits:** max body size, max segments, max decode depth, per-request time budget; fail-closed behaviour for high-risk policies, fail-open only if explicitly configured and audited.
- Parameterised queries only; strict input validation; output encoding in the console (no XSS from attacker-controlled evidence strings — render evidence as text, never HTML; add tests with XSS payload strings as data).
- Secrets scanning in CI; dependency audit (`pip-audit`, `npm audit`) in CI; SBOM generation (CycloneDX) in the release script.
- Principle of least privilege for containers (non-root, read-only filesystem where possible).
- Structured logs with redaction; metrics for detector hit rates and latencies.

---

## 10. TESTING AND CI

- **Unit:** every detector, normaliser, rule (using each rule's embedded positive/negative examples), policy construct, audit function. Target ≥ 85% coverage on `detectors`, `policy`, `audit`; report overall coverage.
- **Property-based tests** (Hypothesis) for normalisation idempotence, audit chain integrity under random event sequences, and policy-engine determinism.
- **Integration:** every API endpoint, auth/RBAC matrix, tenant isolation, approval state machine, idempotency.
- **Security tests:** tamper detection, secret-never-logged, XSS-in-evidence, SSRF denial on `fetch_document`, ReDoS timeouts, oversize payload rejection.
- **E2E:** Playwright scenarios listed in Section 8, run against the full stack in CI.
- **Evaluation smoke test** in CI with regression thresholds.
- CI (GitHub Actions): lint, type-check, unit, integration, e2e (containerised), eval smoke, dependency audit, build images. Cache aggressively. A failing gate blocks merge.

---

## 11. DEMO AND SUBMISSION ASSETS (generate these too)

1. **`docs/DEMO_RUNBOOK.md`** — exact commands and click-path, expected outputs, fallback steps if something fails during judging, and a pre-demo checklist.
2. **`docs/VIDEO_SCRIPT_3MIN.md`** — a timed script for a 3-minute video: problem (0:00–0:25); live demo, Shield OFF breach then Shield ON block then audit verification (0:25–1:30); how it works plus real metrics from `metrics.json` (1:30–2:10); business model and global expansion, flagged as illustrative (2:10–2:40); responsible AI and next steps (2:40–3:00).
3. **`docs/SUBMISSION_ONE_PAGER.md`** — one page, structured: problem, solution, demo, AI approach, impact, next steps; all figures pulled from the evaluation output; every claim backed by the repo.
4. **`docs/BUSINESS_MODEL_ILLUSTRATIVE.md`** — customer segments, pricing tiers (developer free / team / enterprise), go-to-market, competitive landscape (a section that **must be filled by the human team after verifying current competitors; do not invent competitor facts**), expansion via language packs, defensibility via the attack library and multilingual evaluation data. Every financial figure is labelled an assumption.
5. **`docs/RESPONSIBLE_AI.md`** — privacy by design, human-in-the-loop, honest metrics, dual-use considerations of the Red Team module and the mitigations in 1.2, bias and language-coverage limits, appeal/override process for false positives.
6. **README.md** — what it is, 60-second quickstart, architecture diagram (Mermaid), screenshots captured by the browser agent, how to reproduce the evaluation, project status, honest limitations.

---

## 12. PHASED EXECUTION PLAN WITH ACCEPTANCE GATES

**Phase 0 — Foundations (plan, scaffolding)**
Deliver: Implementation Plan artifact, repo scaffold, tooling, CI skeleton, OpenAPI contract stubs, `docs/DECISIONS.md`.
*Gate:* `make lint test` runs green on an empty-but-wired skeleton; contracts reviewed for consistency.

**Phase 1 — Detectors and datasets**
Deliver: normalisation, rules pack (en/bn/bn-Latn), synthetic dataset builder with splits, classifier training, PII/secret scanners, ensemble, bilingual explanations, unit tests.
*Gate:* `make train` and `make eval-detectors` reproduce metrics; leakage test proves no tuning on held-out/adaptive sets; latency measured.

**Phase 2 — Policy engine, audit, approvals**
Deliver: policy language, validator, simulator, signed hash-chained audit with verifier CLI, approval state machine.
*Gate:* tamper-detection tests pass; policy determinism tests pass; example policies validated.

**Phase 3 — Gateway**
Deliver: Shield pipeline, proxy endpoints, tool authorisation, output scan, auth, rate limits, metrics, realtime events.
*Gate:* all integration and security tests green; p95 overhead measured and recorded.

**Phase 4 — Sandbox (BankDesk)**
Deliver: fake data, tools, NaiveSimLLM, poisoned fixtures, Shield switch, sandbox UI, breach detector.
*Gate:* scripted scenario shows breach (OFF) and block (ON) deterministically across 50 seeded runs.

**Phase 5 — Red Team**
Deliver: attack engine, mutation, runner, scorer, Wilson CIs, benign set run, remediation guidance.
*Gate:* full run produces per-language ASR before/after and FPR; results saved and reproducible.

**Phase 6 — Console**
Deliver: all P0 pages, bilingual, demo mode, e2e tests; browser-agent screenshots.
*Gate:* Playwright suite green; accessibility checks pass; first-time-user path to the demo ≤ 3 clicks verified.

**Phase 7 — P1 features**
Deliver (in order): policy editor with dry-run, compliance reports, multi-tenancy/RBAC, SDKs, adaptive attack v2.
*Gate:* each feature merged only with tests and docs; no regression in P0 e2e.

**Phase 8 — Hardening, docs, submission pack**
Deliver: threat model, provenance doc, evaluation report, runbook, video script, one-pager, README with real screenshots, SBOM, final CI run.
*Gate:* a clean clone runs `make up` then `make demo` successfully; `make eval` reproduces the published numbers; every doc claim is traceable to code or labelled as an assumption.

**P2 items** only if all gates above are green.

---

## 13. DEFINITION OF DONE (verify every line)

- [ ] `make up` (or `make dev`) starts the full stack with zero API keys.
- [ ] Demo scenario: Shield OFF breaches; Shield ON blocks; incident visible; audit verifies; tamper simulation is detected.
- [ ] Red Team run completes in both modes across en, bn, bn-Latn and shows before/after ASR with confidence intervals.
- [ ] `metrics.json` and `docs/EVALUATION.md` generated by code, including false-positive rate, latency, ablations, adaptive-set results and known limitations.
- [ ] Console fully bilingual; keyboard accessible; no hard-coded data.
- [ ] All tests green in CI; coverage thresholds met; dependency and secrets scans clean.
- [ ] `docs/PROVENANCE.md`, `THREAT_MODEL.md`, `RESPONSIBLE_AI.md`, `DEMO_RUNBOOK.md`, `VIDEO_SCRIPT_3MIN.md`, `SUBMISSION_ONE_PAGER.md` complete and consistent with the code.
- [ ] No fabricated claims anywhere; every assumption labelled; every synthetic dataset labelled.
- [ ] A final **Walkthrough artifact** lists: what works, what is simulated, known limitations, and the **human review checklist** (native-speaker review of Bangla/Banglish data, verification of framework mappings against official sources, competitor research, legal review before any real deployment).

---

## 14. HOW TO REPORT PROGRESS

At the end of each phase, output:
1. What was completed (with file paths).
2. Test and evaluation output (actual command output, not summaries).
3. Gate status (pass/fail with evidence).
4. Deviations and ADRs recorded.
5. Risks and what you recommend next.

If any gate fails, **fix it before moving on**. If you are blocked, state exactly what is missing and continue with the highest-value unblocked work.

**Begin with Phase 0. Produce the Implementation Plan artifact first.**