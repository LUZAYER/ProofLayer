"""Unit tests for Phase 7: SDKs and Compliance Report Generator."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sdk.python.prooflayer import ProofLayer, ProofLayerSecurityError
from services.compliance.report import ComplianceReportGenerator


def test_compliance_report_generation(tmp_path: Path) -> None:
    gen = ComplianceReportGenerator()
    report = gen.generate(org_name="Padma Test Bank", output_dir=tmp_path)

    assert report.report_id.startswith("COMP-REP-")
    assert len(report.control_mappings) >= 6
    assert len(report.report_hash) == 64
    assert "not constitute a formal" in report.disclaimer

    # Check generated files
    json_path = tmp_path / "compliance_report.json"
    html_path = tmp_path / "compliance_report.html"
    assert json_path.exists()
    assert html_path.exists()

    with json_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["report_id"] == report.report_id
    assert "OWASP Top 10 for LLM Applications (2025)" in [
        c["framework"] for c in data["control_mappings"]
    ]


def test_python_sdk_scan_and_guard_tool(monkeypatch: pytest.MonkeyPatch) -> None:
    sdk = ProofLayer(base_url="http://localhost:8000")

    # Mock authorize_tool to test guard_tool decorator
    def mock_auth_allow(tool_name: str, arguments: dict, context: dict | None = None) -> dict:
        return {"decision": "ALLOW", "reasons": []}

    def mock_auth_deny(tool_name: str, arguments: dict, context: dict | None = None) -> dict:
        return {"decision": "DENY", "reasons": ["Spend limit exceeded"]}

    # Case 1: Allowed execution
    monkeypatch.setattr(sdk, "authorize_tool", mock_auth_allow)

    @sdk.guard_tool("issue_refund")
    def refund_fn(account_id: str, amount: float) -> str:
        return f"Refunded ${amount} to {account_id}"

    res = refund_fn("ACC-1001", 20.0)
    assert "Refunded $20.0" in res

    # Case 2: Blocked execution raises ProofLayerSecurityError
    monkeypatch.setattr(sdk, "authorize_tool", mock_auth_deny)

    with pytest.raises(ProofLayerSecurityError) as exc_info:
        refund_fn("ACC-1001", 500.0)

    assert exc_info.value.decision == "DENY"
    assert "Spend limit exceeded" in exc_info.value.reasons


def test_auth_manager_rbac() -> None:
    from fastapi import HTTPException

    from services.gateway.auth import AuthManager

    auth = AuthManager()
    # Test dev mode fallback when disabled
    auth.auth_enabled = False
    user = auth.authenticate(None)
    assert user.role == "admin"
    assert user.can_access(["admin"])
    assert user.can_access(["analyst", "viewer"])

    # Test explicit key lookup
    admin_user = auth.authenticate("pl-admin-demo-key-2026")
    assert admin_user.role == "admin"
    assert admin_user.can_access(["admin"])

    analyst_user = auth.authenticate("pl-analyst-demo-key-2026")
    assert analyst_user.role == "analyst"
    assert not analyst_user.can_access(["admin"])
    assert analyst_user.can_access(["analyst"])
    assert analyst_user.can_access(["analyst", "viewer"])

    viewer_user = auth.authenticate("pl-viewer-demo-key-2026")
    assert viewer_user.role == "viewer"
    assert not viewer_user.can_access(["admin"])
    assert not viewer_user.can_access(["analyst"])
    assert viewer_user.can_access(["viewer"])

    # Test strict mode when enabled
    auth.auth_enabled = True
    with pytest.raises(HTTPException) as exc_info:
        auth.authenticate(None)
    assert exc_info.value.status_code == 401

    with pytest.raises(HTTPException) as exc_info:
        auth.authenticate("invalid-bogus-key")
    assert exc_info.value.status_code == 403

    valid_user = auth.authenticate("Bearer pl-analyst-demo-key-2026")
    assert valid_user.role == "analyst"
