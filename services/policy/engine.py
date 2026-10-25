"""Policy evaluation engine enforcing tool, data-flow, spend, and provenance constraints."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Literal

from services.policy.schema import PolicyDefinition

DecisionResult = Literal["ALLOW", "DENY", "REQUIRE_APPROVAL"]


@dataclass
class ToolAuthorizationResult:
    """Result of evaluating a proposed tool invocation against active policy."""

    decision: DecisionResult
    reasons: list[str] = field(default_factory=list)
    requires_approval: bool = False
    approval_id: str | None = None
    shadow_mode: bool = False
    effective_decision: DecisionResult = "ALLOW"


class PolicyEngine:
    """Evaluates proposed agent tool calls and data flows against declarative policies."""

    def __init__(self, default_policy: PolicyDefinition | None = None) -> None:
        self.default_policy = default_policy
        # In-memory cumulative spend per session: {session_id: cumulative_amount}
        self._session_spend: dict[str, float] = {}

    def authorize_tool(
        self,
        agent_id: str,
        tool_name: str,
        arguments: dict[str, Any],
        context: dict[str, Any] | None = None,
        policy: PolicyDefinition | None = None,
    ) -> ToolAuthorizationResult:
        """Evaluate a tool invocation against active policy."""
        active_policy = policy or self.default_policy
        if not active_policy:
            return ToolAuthorizationResult(decision="ALLOW", effective_decision="ALLOW")

        ctx = context or {}
        reasons: list[str] = []
        requires_approval = False
        decision: DecisionResult = "ALLOW"
        session_id = str(ctx.get("session_id", "default-session"))

        tool_cfg = active_policy.tools.get(tool_name)
        if not tool_cfg:
            # If tool is not recognized in strict mode, deny; otherwise allow
            if active_policy.mode == "enforce":
                decision = "DENY"
                reasons.append(
                    f"Tool '{tool_name}' is not configured in policy '{active_policy.id}'."
                )
            return self._finalize_decision(decision, reasons, active_policy.mode)

        # 1. Base Tool Action
        if tool_cfg.action == "deny":
            decision = "DENY"
            reasons.append(f"Tool '{tool_name}' is explicitly denied by policy.")
            return self._finalize_decision(decision, reasons, active_policy.mode)

        if tool_cfg.action == "require_approval":
            requires_approval = True
            decision = "REQUIRE_APPROVAL"
            reasons.append(f"Tool '{tool_name}' requires human authorization by default.")

        # 2. Spend & Amount Constraints (e.g., issue_refund)
        if "amount" in arguments:
            try:
                amt = float(arguments["amount"])
                # Per-call limit
                if tool_cfg.max_amount_per_call is not None and amt > tool_cfg.max_amount_per_call:
                    decision = "DENY"
                    reasons.append(
                        f"Amount ${amt:.2f} exceeds max per-call limit (${tool_cfg.max_amount_per_call:.2f})."
                    )
                # Approval threshold (only if not already denied)
                elif (
                    tool_cfg.approval_threshold_amount is not None
                    and amt > tool_cfg.approval_threshold_amount
                ):
                    requires_approval = True
                    decision = "REQUIRE_APPROVAL"
                    reasons.append(
                        f"Amount ${amt:.2f} exceeds human approval threshold (${tool_cfg.approval_threshold_amount:.2f})."
                    )

                # Session spend limit
                curr_spend = self._session_spend.get(session_id, 0.0)
                if (
                    tool_cfg.max_amount_per_session is not None
                    and (curr_spend + amt) > tool_cfg.max_amount_per_session
                ):
                    decision = "DENY"
                    requires_approval = False
                    reasons.append(
                        f"Cumulative session spend (${curr_spend + amt:.2f}) exceeds session limit (${tool_cfg.max_amount_per_session:.2f})."
                    )

            except (ValueError, TypeError):
                decision = "DENY"
                reasons.append(
                    f"Invalid numeric amount supplied in tool arguments: {arguments.get('amount')}"
                )

        # 3. Recipient Domain Constraints (e.g., send_email)
        if tool_name == "send_email" and "to" in arguments:
            to_addr = str(arguments["to"]).strip().lower()
            if tool_cfg.allowed_recipient_domains:
                domain = to_addr.split("@")[-1] if "@" in to_addr else ""
                if domain not in [d.lower() for d in tool_cfg.allowed_recipient_domains]:
                    decision = "DENY"
                    reasons.append(
                        f"Recipient '{to_addr}' domain '{domain}' is not in policy allowlist: {tool_cfg.allowed_recipient_domains}."
                    )

        # 4. Data-Flow Taint & Canary Leakage in Arguments
        arg_str = str(arguments)
        if "CANARY-" in arg_str or "admin_api_key" in arg_str:
            decision = "DENY"
            reasons.append(
                "CRITICAL: Canary token or secret credential detected inside tool arguments."
            )

        # 5. Provenance Constraints
        trigger_provenance = ctx.get("provenance")
        user_intent_matched = ctx.get("user_intent_matched", True)
        if active_policy.provenance_rules.disallow_untrusted_tool_triggers:
            if (
                trigger_provenance in ("TOOL_OUTPUT", "RETRIEVED_DOC", "WEB")
                and not user_intent_matched
            ):
                decision = "DENY"
                reasons.append(
                    f"Untrusted provenance '{trigger_provenance}' attempted to trigger tool without user intent confirmation."
                )

        # If approved or allowed, track cumulative spend
        if decision == "ALLOW" and "amount" in arguments:
            try:
                amt = float(arguments["amount"])
                self._session_spend[session_id] = self._session_spend.get(session_id, 0.0) + amt
            except (ValueError, TypeError):
                pass

        return self._finalize_decision(decision, reasons, active_policy.mode, requires_approval)

    def _finalize_decision(
        self,
        decision: DecisionResult,
        reasons: list[str],
        mode: str,
        requires_approval: bool = False,
    ) -> ToolAuthorizationResult:
        shadow_mode = mode in ("monitor", "shadow")
        effective_decision = "ALLOW" if shadow_mode else decision
        approval_id = (
            str(uuid.uuid4()) if requires_approval or decision == "REQUIRE_APPROVAL" else None
        )

        return ToolAuthorizationResult(
            decision=decision,
            reasons=reasons,
            requires_approval=requires_approval or (decision == "REQUIRE_APPROVAL"),
            approval_id=approval_id,
            shadow_mode=shadow_mode,
            effective_decision=effective_decision,
        )

    def reset_session_spend(self, session_id: str | None = None) -> None:
        """Reset spend tracking for testing or session cleanup."""
        if session_id:
            self._session_spend.pop(session_id, None)
        else:
            self._session_spend.clear()
