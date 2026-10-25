"""Standalone offline verifier CLI for ProofLayer cryptographic audit chains and evidence bundles."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives.asymmetric import ed25519

from services.audit.ledger import AuditEvent, AuditLedger, VerificationResult


def verify_bundle_file(bundle_path: Path) -> int:
    """Verify an exported evidence bundle JSON file."""
    if not bundle_path.exists():
        print(f"Error: Bundle file not found: {bundle_path}", file=sys.stderr)
        return 1

    with bundle_path.open("r", encoding="utf-8") as f:
        bundle: dict[str, Any] = json.load(f)

    public_key_hex = bundle.get("public_key_hex")
    if not public_key_hex:
        print("Error: Bundle missing public_key_hex", file=sys.stderr)
        return 1

    try:
        pub_key_bytes = bytes.fromhex(public_key_hex)
        public_key = ed25519.Ed25519PublicKey.from_public_bytes(pub_key_bytes)
    except Exception as e:
        print(f"Error: Invalid public key hex: {e}", file=sys.stderr)
        return 1

    events_raw = bundle.get("events", [])
    events: list[AuditEvent] = []
    for r in events_raw:
        events.append(AuditEvent(**r))

    ledger = AuditLedger(key_id=bundle.get("key_id", "external"))
    # Point public key
    ledger._public_key = public_key

    result: VerificationResult = ledger.verify(events)
    if result.valid:
        print(f"SUCCESS: Cryptographic verification passed for {result.checked_count} events.")
        print(f"Public Key ID: {bundle.get('key_id')}")
        print(f"Manifest Hash: {bundle.get('manifest_hash')}")
        return 0
    else:
        print("TAMPERING DETECTED: Cryptographic audit chain verification failed!", file=sys.stderr)
        print(f"First broken index: {result.first_broken_index}", file=sys.stderr)
        print(f"Reason: {result.reason}", file=sys.stderr)
        return 2


def main() -> None:
    parser = argparse.ArgumentParser(description="ProofLayer Cryptographic Audit Verifier CLI")
    parser.add_argument("--bundle", type=str, help="Path to evidence bundle JSON")
    parser.add_argument("--verify", action="store_true", help="Run local self-verification check")

    args = parser.parse_args()

    if args.bundle:
        sys.exit(verify_bundle_file(Path(args.bundle)))
    elif args.verify:
        ledger = AuditLedger()
        # Seed 3 events
        ledger.append_event("SHIELD_SCAN", "ALLOW", risk_score=0.1)
        ledger.append_event("TOOL_AUTHORIZATION", "ALLOW", risk_score=0.2)
        ledger.append_event("OUTPUT_SCAN", "ALLOW_WITH_REDACTION", risk_score=0.3)
        res = ledger.verify()
        if res.valid:
            print(f"Self-verification OK: {res.checked_count} events verified.")
            sys.exit(0)
        else:
            print(f"Self-verification FAILED: {res.reason}", file=sys.stderr)
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
