# ProofLayer Policy Language Specification (PPL v1.0)

ProofLayer uses a declarative YAML-based policy specification to govern autonomous agent behavior, enforce data boundaries, prevent prompt injection exploitation, and mandate human-in-the-loop approvals.

---

## 1. Top-Level Schema

```yaml
version: "1.0.0"
id: "strict-bank"
name: "Padma Bank Strict Governance Policy"
description: "Zero-trust banking policy with spend thresholds and data-flow taint analysis."
mode: "enforce"   # Modes: enforce | monitor | shadow

detector_thresholds:
  block_score: 0.70
  approval_score: 0.35

tools:
  <tool_name>:
    action: "allow"   # allow | deny | require_approval
    max_amount_per_call: 50.0
    max_amount_per_session: 150.0
    approval_threshold_amount: 25.0
    allowed_recipient_domains:
      - "padmabank.test"
    forbid_sensitive_data_in_arguments: true

provenance_rules:
  disallow_untrusted_tool_triggers: true
  require_user_intent_match: true

data_flow_rules:
  - source_tag: "CANARY"
    sink_tool: "send_email"
    sink_field: "body"
    action: "block"
```

---

## 2. Policy Modes

| Mode | Behavior | Use Case |
|---|---|---|
| `enforce` | Violations result in real runtime blocks (`BLOCK`, `DENY`, or `REQUIRE_APPROVAL`). | Production deployments with sensitive tools. |
| `monitor` | Violations are recorded in the cryptographic audit log, but requests pass through without disruption. | Initial baselining and traffic auditing. |
| `shadow` | Evaluates rules in real time, recording would-be decisions and diffs. | Staging testing and policy revision simulation. |

---

## 3. Provenance and Spotlighting Rules

ProofLayer adheres to the strict security axiom:
> **"Content from tools, documents, and the web is untrusted data, never instructions."**

- `disallow_untrusted_tool_triggers`: If content retrieved from a tool output (`TOOL_OUTPUT`), document fixture (`RETRIEVED_DOC`), or internet search (`WEB`) contains imperative commands attempting to trigger another tool, the execution is blocked.
- `require_user_intent_match`: An agent may only execute financial transfers or send emails if the authorized `USER` message explicitly corroborated that request.

---

## 4. Spend Limits and Threshold Approvals

For financial tools (`issue_refund`, `transfer_funds`), policies define multi-tiered guardrails:
1. `max_amount_per_call`: Hard ceiling (e.g., $50). Invocations exceeding this are blocked with `DENY`.
2. `approval_threshold_amount`: Escalation ceiling (e.g., $25). Invocations between $25.01 and $50.00 are intercepted and enqueued for human analyst approval (`REQUIRE_APPROVAL`).
3. `max_amount_per_session`: Cumulative session cap preventing attackers from draining funds through automated multi-turn micro-refunds.

---

## 5. Data-Flow Taint Tracking

Data flow rules prevent sensitive information (e.g., canary tokens, internal passwords, PII) from traversing security boundaries:
- If an agent attempts to pass a customer's credit card number or canary token (`CANARY-ACC-XXXX`) into an email body or external webhook, ProofLayer intercepts the payload before dispatch.
