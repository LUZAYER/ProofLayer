"""ProofLayer Python Client SDK with tool guard decorator and OpenAI client wrapper."""

from __future__ import annotations

import functools
import inspect
from collections.abc import Callable
from typing import Any

import httpx


class ProofLayerSecurityError(Exception):
    """Raised when ProofLayer Shield blocks a prompt or tool execution."""

    def __init__(self, decision: str, reasons: list[str], explanation: dict[str, str]) -> None:
        self.decision = decision
        self.reasons = reasons
        self.explanation = explanation
        super().__init__(f"ProofLayer Security Block ({decision}): {'; '.join(reasons)}")


class ProofLayer:
    """Official Python Client for ProofLayer AI Trust & Governance Gateway."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "http://localhost:8000",
        agent_id: str = "default-agent",
        timeout: float = 10.0,
    ) -> None:
        self.api_key = api_key or ""
        self.base_url = base_url.rstrip("/")
        self.agent_id = agent_id
        self.timeout = timeout
        self._headers = {
            "Content-Type": "application/json",
            "X-ProofLayer-Agent": self.agent_id,
        }
        if self.api_key:
            self._headers["Authorization"] = f"Bearer {self.api_key}"

    def scan(self, text: str, provenance: str = "USER") -> dict[str, Any]:
        """Directly scan a content segment for prompt injection, secrets, and policy violations."""
        url = f"{self.base_url}/v1/shield/scan"
        payload = {"segments": [{"text": text, "provenance": provenance}]}
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(url, json=payload, headers=self._headers)
            resp.raise_for_status()
            data: dict[str, Any] = resp.json()
            return data

    def authorize_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Authorize a proposed tool invocation against active policies."""
        url = f"{self.base_url}/v1/tools/authorize"
        payload = {
            "agent_id": self.agent_id,
            "tool_name": tool_name,
            "arguments": arguments,
            "context": context or {},
        }
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(url, json=payload, headers=self._headers)
            resp.raise_for_status()
            data: dict[str, Any] = resp.json()
            return data

    def guard_tool(self, tool_name: str | None = None) -> Callable[..., Any]:
        """Decorator to wrap and protect python agent tools with automatic policy mediation."""

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            name = tool_name or func.__name__

            @functools.wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                # Bind function arguments to parameter names
                sig = inspect.signature(func)
                bound = sig.bind(*args, **kwargs)
                bound.apply_defaults()
                arguments = bound.arguments

                # Mediate with ProofLayer
                res = self.authorize_tool(tool_name=name, arguments=arguments)
                if res.get("decision") != "ALLOW":
                    raise ProofLayerSecurityError(
                        decision=res.get("decision", "DENY"),
                        reasons=res.get("reasons", []),
                        explanation={"en": f"Tool '{name}' execution was blocked by policy."},
                    )
                return func(*args, **kwargs)

            return wrapper

        return decorator

    def wrap_openai(self, openai_client: Any) -> Any:
        """Configure OpenAI client to route chat completions through ProofLayer proxy."""
        openai_client.base_url = f"{self.base_url}/v1"
        return openai_client
