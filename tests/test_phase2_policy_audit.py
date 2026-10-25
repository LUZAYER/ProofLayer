"""Unit, security, and property-based tests for Phase 2: Policy, Audit, and Approvals."""

from __future__ import annotations

from pathlib import Path

from services.audit.ledger import AuditLedger
from services.audit.verifier import verify_bundle_file
from services.gateway.approvals import ApprovalQueue
from services.policy.engine import PolicyEngine
from services.policy.schema import PolicyDefinition
from services.policy.simulator import PolicySimulator


def test_example_policies_validity() -> None:
    """Verify all 4 production YAML policies validate successfully against JSONSchema."""
    policies_dir = Path("policies")
    assert policies_dir.exists()

    expected_policies = ["strict-bank", "balanced-support", "monitor-only", "dev-sandbox"]
    for pol_name in expected_policies:
        yaml_path = policies_dir / f"{pol_name}.yaml"
        assert yaml_path.exists(), f"Policy file {yaml_path} must exist"
        content = yaml_path.read_text(encoding="utf-8")
        policy = PolicyDefinition.from_yaml(content)
        assert policy.id == pol_name
        assert policy.mode in ("enforce", "monitor", "shadow")


def test_policy_engine_spend_and_approval_thresholds() -> None:
    strict_policy = PolicyDefinition.from_yaml(
        Path("policies/strict-bank.yaml").read_text(encoding="utf-8")
    )
    engine = PolicyEngine(default_policy=strict_policy)

    # 1. Under approval threshold ($20 <= $25 threshold) -> ALLOW
    res1 = engine.authorize_tool("agent-1", "issue_refund", {"amount": 20.0}, {"session_id": "s1"})
    assert res1.decision == "ALLOW"
    assert res1.requires_approval is False

    # 2. Over approval threshold ($35 > $25 threshold) -> REQUIRE_APPROVAL
    res2 = engine.authorize_tool("agent-1", "issue_refund", {"amount": 35.0}, {"session_id": "s1"})
    assert res2.decision == "REQUIRE_APPROVAL"
    assert res2.requires_approval is True
    assert res2.approval_id is not None

    # 3. Over per-call maximum ($60 > $50 max) -> DENY
    res3 = engine.authorize_tool("agent-1", "issue_refund", {"amount": 60.0}, {"session_id": "s1"})
    assert res3.decision == "DENY"


def test_policy_engine_email_domain_allowlist() -> None:
    strict_policy = PolicyDefinition.from_yaml(
        Path("policies/strict-bank.yaml").read_text(encoding="utf-8")
    )
    engine = PolicyEngine(default_policy=strict_policy)

    # Allowed domain
    res_ok = engine.authorize_tool(
        "agent-1", "send_email", {"to": "support@padmabank.test", "body": "Hello"}
    )
    assert res_ok.decision == "ALLOW"

    # Disallowed external domain
    res_deny = engine.authorize_tool(
        "agent-1", "send_email", {"to": "attacker@evil.com", "body": "Hello"}
    )
    assert res_deny.decision == "DENY"
    assert any("not in policy allowlist" in r for r in res_deny.reasons)


def test_policy_engine_canary_leakage_in_arguments() -> None:
    strict_policy = PolicyDefinition.from_yaml(
        Path("policies/strict-bank.yaml").read_text(encoding="utf-8")
    )
    engine = PolicyEngine(default_policy=strict_policy)

    # Attempt to pass a canary token inside arguments
    res = engine.authorize_tool(
        "agent-1",
        "send_email",
        {"to": "customer@padmabank.test", "body": "Leaked token: CANARY-ACC-7F3A9"},
    )
    assert res.decision == "DENY"
    assert any("Canary token or secret" in r for r in res.reasons)


def test_policy_simulator() -> None:
    strict_yaml = Path("policies/strict-bank.yaml").read_text(encoding="utf-8")
    simulator = PolicySimulator()

    sample_events = [
        {
            "id": "e1",
            "tool_name": "lookup_account",
            "arguments": {"account_id": "ACC-101"},
            "decision": "ALLOW",
        },
        {
            "id": "e2",
            "tool_name": "issue_refund",
            "arguments": {"amount": 40.0},
            "decision": "ALLOW",
        },
        {
            "id": "e3",
            "tool_name": "send_email",
            "arguments": {"to": "hacker@external.org"},
            "decision": "ALLOW",
        },
    ]

    summary = simulator.simulate(strict_yaml, sample_events)
    assert summary.total_events == 3
    # e2 requires approval, e3 is denied
    assert summary.approval_count == 1
    assert summary.denied_count == 1
    assert summary.allowed_count == 1
    assert summary.decisions_changed == 2


def test_audit_ledger_hash_chain_and_signature_integrity() -> None:
    ledger = AuditLedger()

    ev1 = ledger.append_event("SHIELD_SCAN", "ALLOW", risk_score=0.1)
    ev2 = ledger.append_event("TOOL_AUTHORIZATION", "ALLOW", risk_score=0.2)
    ev3 = ledger.append_event("OUTPUT_SCAN", "BLOCK", risk_score=0.95)

    assert ev1.sequence == 1
    assert ev2.sequence == 2
    assert ev3.sequence == 3
    assert ev2.previous_hash == ev1.hash
    assert ev3.previous_hash == ev2.hash

    res = ledger.verify()
    assert res.valid is True
    assert res.checked_count == 3


def test_audit_zero_secret_guarantee() -> None:
    """Security test: assert raw secrets NEVER reach the audit ledger storage."""
    ledger = AuditLedger()
    raw_secret = "sk-test1234567890abcdef1234567890abcdef"
    canary = "CANARY-ACC-99999"

    ev = ledger.append_event(
        "SHIELD_SCAN",
        "BLOCK",
        evidence={"query": f"My secret is {raw_secret} and token {canary}"},
    )

    ev_json = str(ev.to_dict())
    assert raw_secret not in ev_json, "Raw API key found in audit log!"
    assert "[REDACTED]" in ev_json or "..." in ev_json


def test_audit_tamper_detection_pinpoints_index() -> None:
    ledger = AuditLedger()
    for i in range(5):
        ledger.append_event("SHIELD_SCAN", "ALLOW", risk_score=i * 0.1)

    # Tamper with event at sequence 3
    verify_res, details = ledger.simulate_tampering(target_index=3)
    assert verify_res.valid is False
    assert details["detected"] is True
    assert details["first_broken_index"] == 3
    assert "Hash mismatch" in str(verify_res.reason)


def test_audit_evidence_bundle_export_and_cli_verifier(tmp_path: Path) -> None:
    ledger = AuditLedger()
    ledger.append_event("SHIELD_SCAN", "ALLOW", risk_score=0.05)
    ledger.append_event("TOOL_AUTHORIZATION", "ALLOW", risk_score=0.10)

    bundle = ledger.export_evidence_bundle()
    bundle_file = tmp_path / "evidence_bundle.json"
    import json

    bundle_file.write_text(json.dumps(bundle), encoding="utf-8")

    # Verify via CLI logic
    exit_code = verify_bundle_file(bundle_file)
    assert exit_code == 0


def test_approval_queue_state_machine() -> None:
    queue = ApprovalQueue(expiry_minutes=30)
    req = queue.create_request(
        approval_id="appr-101",
        agent_id="agent-support",
        tool_name="issue_refund",
        arguments={"amount": 45.0},
        context={"user_id": "customer-1"},
        rule_ids=["REFUND_THRESHOLD"],
        risk_score=0.45,
        explanation_en="Refund exceeds $25",
        explanation_bn="রিফান্ড ২৫ ডলারের বেশি",
    )
    assert req.status == "pending"

    # Self-approval prevented
    ok, msg, _ = queue.submit_decision("appr-101", "approve", decided_by="customer-1")
    assert ok is False
    assert "Self-approval is forbidden" in msg

    # Authorized analyst approves
    ok, msg, req_updated = queue.submit_decision("appr-101", "approve", decided_by="analyst-john")
    assert ok is True
    assert req_updated is not None
    assert req_updated.status == "approved"

    # Exactly-once execution release
    first_exec = queue.mark_executed("appr-101")
    assert first_exec is True
    second_exec = queue.mark_executed("appr-101")
    assert second_exec is False  # Idempotent
