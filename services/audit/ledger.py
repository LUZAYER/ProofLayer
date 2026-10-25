"""Append-only cryptographic audit ledger with SHA-256 hash chaining and Ed25519 signatures."""

from __future__ import annotations

import datetime
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

from services.detectors.pii import PIIScanner

GENESIS_PREVIOUS_HASH = "0" * 64


@dataclass
class AuditEvent:
    sequence: int
    timestamp: str
    org_id: str
    agent_id: str
    session_id: str
    event_type: str
    decision: str
    rule_ids: list[str]
    risk_score: float
    evidence: dict[str, Any]
    previous_hash: str
    key_id: str
    hash: str = ""
    signature: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class VerificationResult:
    valid: bool
    checked_count: int
    first_broken_index: int | None = None
    reason: str | None = None


def canonical_json(data: dict[str, Any]) -> bytes:
    """Deterministic JSON serialization (RFC 8785 style) for consistent hashing."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )


class AuditLedger:
    """Cryptographically verifiable, tamper-evident audit ledger with strict PII sanitization."""

    def __init__(
        self,
        key_id: str = "prooflayer-ed25519-v1",
        private_key: ed25519.Ed25519PrivateKey | None = None,
        db_path: Path | str | None = None,
    ) -> None:
        self.key_id = key_id
        if private_key is not None:
            self._private_key = private_key
        else:
            self._private_key = ed25519.Ed25519PrivateKey.generate()
        self._public_key = self._private_key.public_key()

        self.pii_scanner = PIIScanner(redaction_mode="mask")
        self.events: list[AuditEvent] = []
        self.db_path = Path(db_path) if db_path else None

    @property
    def public_key_hex(self) -> str:
        """Export raw 32-byte public key as hex."""
        raw_bytes = self._public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        return raw_bytes.hex()

    @property
    def public_key_pem(self) -> str:
        """Export public key in PEM format."""
        pem_bytes = self._public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        return pem_bytes.decode("ascii")

    def append_event(
        self,
        event_type: str,
        decision: str,
        org_id: str = "org-default",
        agent_id: str = "agent-bankdesk",
        session_id: str = "sess-001",
        rule_ids: list[str] | None = None,
        risk_score: float = 0.0,
        evidence: dict[str, Any] | None = None,
    ) -> AuditEvent:
        """Sanitize payload, calculate SHA-256 hash chain, sign with Ed25519, and append."""
        sequence = len(self.events) + 1
        timestamp = datetime.datetime.now(datetime.UTC).isoformat()
        rules = rule_ids or []
        raw_evidence = evidence or {}

        # STRICT PRIVACY & ZERO-SECRET GUARANTEE:
        # Sanitize all strings in evidence before storing or hashing
        sanitized_evidence = self._sanitize_evidence(raw_evidence)

        # Previous hash
        previous_hash = self.events[-1].hash if self.events else GENESIS_PREVIOUS_HASH

        # Construct unhashed payload
        event_core = {
            "sequence": sequence,
            "timestamp": timestamp,
            "org_id": org_id,
            "agent_id": agent_id,
            "session_id": session_id,
            "event_type": event_type,
            "decision": decision,
            "rule_ids": sorted(rules),
            "risk_score": round(risk_score, 4),
            "evidence": sanitized_evidence,
            "previous_hash": previous_hash,
            "key_id": self.key_id,
        }

        # SHA-256(canonical_json(event_without_hash) || previous_hash)
        payload_bytes = canonical_json(event_core) + previous_hash.encode("ascii")
        event_hash = hashlib.sha256(payload_bytes).hexdigest()

        # Sign hash with Ed25519
        signature = self._private_key.sign(event_hash.encode("ascii")).hex()

        event = AuditEvent(
            sequence=sequence,
            timestamp=timestamp,
            org_id=org_id,
            agent_id=agent_id,
            session_id=session_id,
            event_type=event_type,
            decision=decision,
            rule_ids=sorted(rules),
            risk_score=round(risk_score, 4),
            evidence=sanitized_evidence,
            previous_hash=previous_hash,
            key_id=self.key_id,
            hash=event_hash,
            signature=signature,
        )

        self.events.append(event)
        return event

    def _sanitize_evidence(self, data: Any) -> Any:
        """Recursively scan and mask secrets and PII in evidence structures."""
        if isinstance(data, str):
            scan_res = self.pii_scanner.scan(data)
            return scan_res.sanitized_text
        elif isinstance(data, dict):
            return {k: self._sanitize_evidence(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._sanitize_evidence(v) for v in data]
        return data

    def verify(self, events: list[AuditEvent] | None = None) -> VerificationResult:
        """Verify the integrity of the hash chain and Ed25519 digital signatures."""
        chain = events if events is not None else self.events
        if not chain:
            return VerificationResult(valid=True, checked_count=0)

        expected_prev = GENESIS_PREVIOUS_HASH

        for i, ev in enumerate(chain):
            idx = ev.sequence

            # 1. Check sequence ordering
            if ev.sequence != (i + 1):
                return VerificationResult(
                    valid=False,
                    checked_count=i,
                    first_broken_index=idx,
                    reason=f"Sequence anomaly at index {idx}: expected {i + 1}",
                )

            # 2. Check previous hash linkage
            if ev.previous_hash != expected_prev:
                return VerificationResult(
                    valid=False,
                    checked_count=i,
                    first_broken_index=idx,
                    reason=f"Broken hash chain at sequence {idx}: previous_hash does not match preceding event hash",
                )

            # 3. Recalculate SHA-256 hash
            event_core = {
                "sequence": ev.sequence,
                "timestamp": ev.timestamp,
                "org_id": ev.org_id,
                "agent_id": ev.agent_id,
                "session_id": ev.session_id,
                "event_type": ev.event_type,
                "decision": ev.decision,
                "rule_ids": sorted(ev.rule_ids),
                "risk_score": round(ev.risk_score, 4),
                "evidence": ev.evidence,
                "previous_hash": ev.previous_hash,
                "key_id": ev.key_id,
            }
            payload_bytes = canonical_json(event_core) + ev.previous_hash.encode("ascii")
            recalc_hash = hashlib.sha256(payload_bytes).hexdigest()

            if recalc_hash != ev.hash:
                return VerificationResult(
                    valid=False,
                    checked_count=i,
                    first_broken_index=idx,
                    reason=f"Hash mismatch at sequence {idx}: event content was modified",
                )

            # 4. Verify Ed25519 signature
            try:
                sig_bytes = bytes.fromhex(ev.signature)
                self._public_key.verify(sig_bytes, ev.hash.encode("ascii"))
            except (ValueError, InvalidSignature) as e:
                return VerificationResult(
                    valid=False,
                    checked_count=i,
                    first_broken_index=idx,
                    reason=f"Cryptographic signature verification failed at sequence {idx}: {e}",
                )

            expected_prev = ev.hash

        return VerificationResult(valid=True, checked_count=len(chain))

    def simulate_tampering(
        self, target_index: int = 1
    ) -> tuple[VerificationResult, dict[str, Any]]:
        """Create a detached copy of the ledger, tamper with target_index, and demonstrate detection."""
        if not self.events:
            raise ValueError("Cannot simulate tampering on empty ledger")

        idx = max(0, min(target_index - 1, len(self.events) - 1))
        # Deep copy events
        copied_events = [AuditEvent(**ev.to_dict()) for ev in self.events]

        # Tamper: modify decision in copied event
        original_decision = copied_events[idx].decision
        copied_events[idx].decision = "ALLOW" if original_decision != "ALLOW" else "BLOCK"

        # Run verification against tampered chain
        result = self.verify(copied_events)
        details = {
            "tampered_sequence": copied_events[idx].sequence,
            "original_decision": original_decision,
            "tampered_decision": copied_events[idx].decision,
            "detected": not result.valid,
            "first_broken_index": result.first_broken_index,
            "reason": result.reason,
        }
        return result, details

    def export_evidence_bundle(self) -> dict[str, Any]:
        """Export signed evidence bundle with manifest and public key for external compliance verification."""
        events_dicts = [ev.to_dict() for ev in self.events]
        bundle_hash = hashlib.sha256(canonical_json({"events": events_dicts})).hexdigest()
        bundle_sig = self._private_key.sign(bundle_hash.encode("ascii")).hex()

        return {
            "version": "1.0.0",
            "exported_at": datetime.datetime.now(datetime.UTC).isoformat(),
            "key_id": self.key_id,
            "public_key_hex": self.public_key_hex,
            "events_count": len(events_dicts),
            "manifest_hash": bundle_hash,
            "manifest_signature": bundle_sig,
            "events": events_dicts,
        }
