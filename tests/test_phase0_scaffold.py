"""Phase 0 scaffold verification tests."""

import json
from pathlib import Path

import services
import services.audit
import services.detectors
import services.gateway
import services.policy
import services.redteam
import services.sandbox


def test_packages_importable() -> None:
    """Verify all monorepo service packages are importable."""
    assert services.__version__ == "0.1.0"
    assert services.detectors is not None
    assert services.policy is not None
    assert services.audit is not None
    assert services.gateway is not None
    assert services.sandbox is not None
    assert services.redteam is not None


def test_openapi_specification_validity() -> None:
    """Verify that docs/openapi.json exists, is valid JSON, and specifies required endpoints."""
    spec_path = Path("docs/openapi.json")
    assert spec_path.exists(), "docs/openapi.json must exist"

    with spec_path.open("r", encoding="utf-8") as f:
        spec = json.load(f)

    assert spec["openapi"] == "3.1.0"
    paths = spec.get("paths", {})
    required_paths = [
        "/healthz",
        "/readyz",
        "/v1/chat/completions",
        "/v1/shield/scan",
        "/v1/tools/authorize",
        "/v1/output/scan",
        "/v1/approvals",
        "/v1/audit/events",
        "/v1/audit/verify",
        "/v1/policies/simulate",
        "/v1/redteam/runs",
    ]
    for p in required_paths:
        assert p in paths, f"Path {p} missing from openapi.json"


def test_decisions_file_exists() -> None:
    """Verify docs/DECISIONS.md records initial architectural decisions."""
    decisions_path = Path("docs/DECISIONS.md")
    assert decisions_path.exists()
    content = decisions_path.read_text(encoding="utf-8")
    assert "ADR 001" in content
    assert "ADR 002" in content
    assert "ADR 003" in content
    assert "ADR 004" in content
    assert "ADR 005" in content


def test_env_example_contains_required_keys() -> None:
    """Verify .env.example contains essential configuration keys."""
    env_example = Path(".env.example")
    assert env_example.exists()
    content = env_example.read_text(encoding="utf-8")
    assert "PROOFLAYER_AUDIT_KEY_ID" in content
    assert "PROOFLAYER_ALLOWED_TARGET_HOSTS" in content
