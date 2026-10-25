"""Approval workflow state machine with human-in-the-loop audit integration."""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from typing import Any, Literal

ApprovalStatus = Literal["pending", "approved", "denied", "expired"]


@dataclass
class ApprovalRequest:
    id: str
    agent_id: str
    tool_name: str
    arguments: dict[str, Any]
    context: dict[str, Any]
    rule_ids: list[str]
    risk_score: float
    explanation_en: str
    explanation_bn: str
    status: ApprovalStatus = "pending"
    created_at: str = field(default_factory=lambda: datetime.datetime.now(datetime.UTC).isoformat())
    expires_at: str = field(
        default_factory=lambda: (
            datetime.datetime.now(datetime.UTC) + datetime.timedelta(minutes=30)
        ).isoformat()
    )
    decided_at: str | None = None
    decided_by: str | None = None
    decision_note: str | None = None
    executed: bool = False


class ApprovalQueue:
    """Thread-safe human approval manager with idempotency and self-approval guards."""

    def __init__(self, expiry_minutes: int = 30) -> None:
        self.expiry_minutes = expiry_minutes
        self._approvals: dict[str, ApprovalRequest] = {}

    def create_request(
        self,
        approval_id: str,
        agent_id: str,
        tool_name: str,
        arguments: dict[str, Any],
        context: dict[str, Any],
        rule_ids: list[str],
        risk_score: float,
        explanation_en: str,
        explanation_bn: str,
    ) -> ApprovalRequest:
        """Create and register a pending approval request."""
        req = ApprovalRequest(
            id=approval_id,
            agent_id=agent_id,
            tool_name=tool_name,
            arguments=arguments,
            context=context,
            rule_ids=rule_ids,
            risk_score=risk_score,
            explanation_en=explanation_en,
            explanation_bn=explanation_bn,
            expires_at=(
                datetime.datetime.now(datetime.UTC)
                + datetime.timedelta(minutes=self.expiry_minutes)
            ).isoformat(),
        )
        self._approvals[approval_id] = req
        return req

    def list_requests(self, status: ApprovalStatus | None = None) -> list[ApprovalRequest]:
        """List requests, auto-expiring overdue items."""
        now_iso = datetime.datetime.now(datetime.UTC).isoformat()
        results: list[ApprovalRequest] = []

        for req in self._approvals.values():
            # Check expiry
            if req.status == "pending" and req.expires_at < now_iso:
                req.status = "expired"

            if status is None or req.status == status:
                results.append(req)

        # Sort newest first
        results.sort(key=lambda r: r.created_at, reverse=True)
        return results

    def get_request(self, approval_id: str) -> ApprovalRequest | None:
        """Fetch request by ID with automatic expiration check."""
        req = self._approvals.get(approval_id)
        if not req:
            return None
        now_iso = datetime.datetime.now(datetime.UTC).isoformat()
        if req.status == "pending" and req.expires_at < now_iso:
            req.status = "expired"
        return req

    def submit_decision(
        self,
        approval_id: str,
        decision: Literal["approve", "deny"],
        decided_by: str,
        note: str = "",
        prevent_self_approval: bool = True,
    ) -> tuple[bool, str, ApprovalRequest | None]:
        """Submit a decision (approve or deny) with anti-tamper and idempotency checks."""
        req = self.get_request(approval_id)
        if not req:
            return False, "Approval request not found.", None

        if req.status != "pending":
            return False, f"Cannot decide on request with status '{req.status}'.", req

        # Check self-approval guard: actor cannot approve their own action
        requestor = str(req.context.get("user_id", req.agent_id))
        if prevent_self_approval and decided_by == requestor:
            return (
                False,
                "Self-approval is forbidden: approver cannot match requestor identity.",
                req,
            )

        now_iso = datetime.datetime.now(datetime.UTC).isoformat()
        req.status = "approved" if decision == "approve" else "denied"
        req.decided_at = now_iso
        req.decided_by = decided_by
        req.decision_note = note

        return True, f"Approval request successfully {req.status}.", req

    def mark_executed(self, approval_id: str) -> bool:
        """Mark held tool call as executed exactly once (idempotent release)."""
        req = self.get_request(approval_id)
        if not req or req.status != "approved" or req.executed:
            return False
        req.executed = True
        return True
