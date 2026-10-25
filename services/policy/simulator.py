"""Policy simulator for dry-running policy versions against historical event logs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from services.policy.engine import PolicyEngine
from services.policy.schema import PolicyDefinition


@dataclass
class SimulatedEventResult:
    event_id: str
    tool_name: str
    original_decision: str
    simulated_decision: str
    changed: bool
    reasons: list[str] = field(default_factory=list)


@dataclass
class SimulationSummary:
    total_events: int
    allowed_count: int
    denied_count: int
    approval_count: int
    decisions_changed: int
    events: list[SimulatedEventResult] = field(default_factory=list)


class PolicySimulator:
    """Dry-run candidate policies against recorded event logs."""

    def __init__(self) -> None:
        self.engine = PolicyEngine()

    def simulate(
        self, candidate_policy_yaml: str, events: list[dict[str, Any]]
    ) -> SimulationSummary:
        """Evaluate candidate policy against a sequence of events without side effects."""
        policy = PolicyDefinition.from_yaml(candidate_policy_yaml)
        sim_results: list[SimulatedEventResult] = []

        allowed = 0
        denied = 0
        approvals = 0
        changed_count = 0

        # Isolated engine instance for clean spend calculation
        sim_engine = PolicyEngine(default_policy=policy)

        for ev in events:
            ev_id = str(ev.get("id", ev.get("session_id", "evt-sim")))
            tool_name = str(ev.get("tool_name", "unknown_tool"))
            arguments = ev.get("arguments", {})
            context = ev.get("context", {})
            orig_decision = str(ev.get("decision", "ALLOW")).upper()

            res = sim_engine.authorize_tool(
                agent_id=str(ev.get("agent_id", "agent-sim")),
                tool_name=tool_name,
                arguments=arguments,
                context=context,
                policy=policy,
            )

            sim_dec = res.decision
            if sim_dec == "ALLOW":
                allowed += 1
            elif sim_dec == "DENY":
                denied += 1
            elif sim_dec == "REQUIRE_APPROVAL":
                approvals += 1

            is_changed = sim_dec != orig_decision
            if is_changed:
                changed_count += 1

            sim_results.append(
                SimulatedEventResult(
                    event_id=ev_id,
                    tool_name=tool_name,
                    original_decision=orig_decision,
                    simulated_decision=sim_dec,
                    changed=is_changed,
                    reasons=res.reasons,
                )
            )

        return SimulationSummary(
            total_events=len(events),
            allowed_count=allowed,
            denied_count=denied,
            approval_count=approvals,
            decisions_changed=changed_count,
            events=sim_results,
        )
