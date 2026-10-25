"""BankDesk agent orchestrator with toggleable ProofLayer Shield."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from services.audit.ledger import AuditLedger
from services.detectors.ensemble import DetectorEnsemble
from services.policy.engine import PolicyEngine
from services.policy.schema import PolicyDefinition
from services.sandbox.fixtures import SYSTEM_PROMPT
from services.sandbox.naive_llm import NaiveSimLLM
from services.sandbox.tools import BankState


@dataclass
class AgentTurnResult:
    user_input: str
    assistant_reply: str
    shield_enabled: bool
    breach_occurred: bool
    shield_blocked: bool
    executed_tools: list[dict[str, Any]] = field(default_factory=list)
    blocked_tools: list[dict[str, Any]] = field(default_factory=list)
    audit_sequence: int | None = None
    explanation: dict[str, str] = field(default_factory=dict)


class BankDeskAgent:
    """Padma Test Bank customer support agent with Shield toggle."""

    def __init__(
        self,
        shield_enabled: bool = False,
        policy: PolicyDefinition | None = None,
        ensemble: DetectorEnsemble | None = None,
        audit_ledger: AuditLedger | None = None,
    ) -> None:
        self.shield_enabled = shield_enabled
        self.state = BankState()
        self.llm = NaiveSimLLM()
        self.messages: list[dict[str, Any]] = []

        # Shield components
        self.ensemble = ensemble or DetectorEnsemble()
        self.policy_engine = PolicyEngine(default_policy=policy)
        self.audit_ledger = audit_ledger or AuditLedger()

    def reset(self) -> None:
        """Reset conversation and bank state."""
        self.state.reset()
        self.messages.clear()

    def process_turn(self, user_query: str, session_id: str = "sess-demo") -> AgentTurnResult:
        """Process a conversational turn through BankDesk."""
        executed_tools: list[dict[str, Any]] = []
        blocked_tools: list[dict[str, Any]] = []
        shield_blocked = False
        explanation: dict[str, str] = {}
        audit_seq: int | None = None

        # Step 1: Pre-input Shield inspection if Shield is ON
        if self.shield_enabled:
            scan_res = self.ensemble.scan(user_query, provenance="USER")
            if scan_res.decision == "BLOCK":
                shield_blocked = True
                explanation = {"en": scan_res.explanation.en, "bn": scan_res.explanation.bn}
                ev = self.audit_ledger.append_event(
                    event_type="SHIELD_INPUT_BLOCK",
                    decision="BLOCK",
                    session_id=session_id,
                    rule_ids=scan_res.categories,
                    risk_score=scan_res.risk_score,
                    evidence={"query": user_query},
                )
                audit_seq = ev.sequence
                return AgentTurnResult(
                    user_input=user_query,
                    assistant_reply=f"ProofLayer Shield blocked input: {scan_res.explanation.en}",
                    shield_enabled=True,
                    breach_occurred=False,
                    shield_blocked=True,
                    audit_sequence=audit_seq,
                    explanation=explanation,
                )

        # Add user message to conversation history
        self.messages.append({"role": "user", "content": user_query})

        # Turn 1: LLM proposes action or reply
        resp1 = self.llm.generate(self.messages, SYSTEM_PROMPT)

        if not resp1.tool_calls:
            self.messages.append({"role": "assistant", "content": resp1.content})
            return AgentTurnResult(
                user_input=user_query,
                assistant_reply=resp1.content,
                shield_enabled=self.shield_enabled,
                breach_occurred=len(self.state.breach_alerts) > 0,
                shield_blocked=False,
            )

        # Execute proposed tool calls
        for tc in resp1.tool_calls:
            tool_name = tc.tool_name
            args = tc.arguments

            # If Shield ON, authorize tool call
            if self.shield_enabled:
                auth_res = self.policy_engine.authorize_tool(
                    agent_id="bankdesk",
                    tool_name=tool_name,
                    arguments=args,
                    context={"session_id": session_id, "user_query": user_query},
                )
                if auth_res.decision != "ALLOW":
                    shield_blocked = True
                    blocked_tools.append(
                        {"tool": tool_name, "arguments": args, "reasons": auth_res.reasons}
                    )
                    ev = self.audit_ledger.append_event(
                        event_type="TOOL_POLICY_BLOCK",
                        decision=auth_res.decision,
                        session_id=session_id,
                        rule_ids=auth_res.reasons,
                        evidence={"tool": tool_name, "arguments": args},
                    )
                    audit_seq = ev.sequence
                    explanation = {
                        "en": f"Blocked unauthorized tool call '{tool_name}': {'; '.join(auth_res.reasons)}",
                        "bn": f"অননুমোদিত টুল কল '{tool_name}' প্রতিরোধ করা হয়েছে: {'; '.join(auth_res.reasons)}",
                    }
                    continue

            # Execute tool safely in sandbox
            tool_output = self._dispatch_tool(tool_name, args)
            executed_tools.append({"tool": tool_name, "arguments": args, "output": tool_output})

            # Append tool result to context
            tool_content = str(tool_output)

            # If Shield ON, inspect untrusted tool output
            if self.shield_enabled:
                doc_scan = self.ensemble.scan(tool_content, provenance="RETRIEVED_DOC")
                if doc_scan.decision == "BLOCK" or doc_scan.has_canary_leak:
                    shield_blocked = True
                    ev = self.audit_ledger.append_event(
                        event_type="INDIRECT_INJECTION_QUARANTINE",
                        decision="BLOCK",
                        session_id=session_id,
                        rule_ids=doc_scan.categories,
                        risk_score=doc_scan.risk_score,
                        evidence={"tool": tool_name, "categories": doc_scan.categories},
                    )
                    audit_seq = ev.sequence
                    explanation = {"en": doc_scan.explanation.en, "bn": doc_scan.explanation.bn}
                    # Spotlighting quarantine: sanitize and wrap content
                    tool_content = doc_scan.spotlighted_text

            self.messages.append({"role": "tool", "name": tool_name, "content": tool_content})

        # Turn 2: LLM evaluates tool results
        resp2 = self.llm.generate(self.messages, SYSTEM_PROMPT)

        # If LLM attempts follow-up tool calls (e.g. exfiltration email prompted by doc)
        if resp2.tool_calls:
            for tc in resp2.tool_calls:
                tool_name = tc.tool_name
                args = tc.arguments

                if self.shield_enabled:
                    auth_res = self.policy_engine.authorize_tool(
                        agent_id="bankdesk",
                        tool_name=tool_name,
                        arguments=args,
                        context={
                            "session_id": session_id,
                            "provenance": "RETRIEVED_DOC",
                            "user_intent_matched": False,
                        },
                    )
                    if auth_res.decision != "ALLOW":
                        shield_blocked = True
                        blocked_tools.append(
                            {"tool": tool_name, "arguments": args, "reasons": auth_res.reasons}
                        )
                        ev = self.audit_ledger.append_event(
                            event_type="INDIRECT_TOOL_CALL_BLOCKED",
                            decision=auth_res.decision,
                            session_id=session_id,
                            rule_ids=auth_res.reasons,
                            evidence={"tool": tool_name, "arguments": args},
                        )
                        audit_seq = ev.sequence
                        explanation = {
                            "en": f"Blocked indirect injection tool trigger '{tool_name}': {'; '.join(auth_res.reasons)}",
                            "bn": f"পরোক্ষ ইনজেকশন জনিত টুল কল '{tool_name}' প্রতিরোধ করা হয়েছে: {'; '.join(auth_res.reasons)}",
                        }
                        continue

                tool_output = self._dispatch_tool(tool_name, args)
                executed_tools.append({"tool": tool_name, "arguments": args, "output": tool_output})

        breach_occurred = len(self.state.breach_alerts) > 0
        final_reply = (
            resp2.content
            if not shield_blocked
            else f"Notice: Tool execution prevented by ProofLayer Shield ({explanation.get('en', '')})."
        )
        self.messages.append({"role": "assistant", "content": final_reply})

        return AgentTurnResult(
            user_input=user_query,
            assistant_reply=final_reply,
            shield_enabled=self.shield_enabled,
            breach_occurred=breach_occurred,
            shield_blocked=shield_blocked,
            executed_tools=executed_tools,
            blocked_tools=blocked_tools,
            audit_sequence=audit_seq,
            explanation=explanation,
        )

    def _dispatch_tool(self, tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
        """Dispatch tool invocation to in-memory BankState."""
        if tool_name == "lookup_account":
            return self.state.lookup_account(str(args.get("account_id", "")))
        elif tool_name == "issue_refund":
            return self.state.issue_refund(
                str(args.get("account_id", "")),
                float(args.get("amount", 0.0)),
                str(args.get("reason", "")),
            )
        elif tool_name == "send_email":
            return self.state.send_email(
                str(args.get("to", "")),
                str(args.get("subject", "")),
                str(args.get("body", "")),
            )
        elif tool_name == "fetch_document":
            return self.state.fetch_document(str(args.get("doc_id", "")))
        elif tool_name == "summarize_ticket":
            return self.state.summarize_ticket(str(args.get("ticket_id", "")))
        return {"error": f"Unknown tool: {tool_name}"}
