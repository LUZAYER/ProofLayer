"""FastAPI web server for BankDesk sandbox with live state inspection."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from services.sandbox.agent import BankDeskAgent
from services.sandbox.fixtures import DOCUMENT_FIXTURES, TICKET_FIXTURES

sandbox_app = FastAPI(
    title="Padma Test Bank — BankDesk Sandbox API",
    version="1.0.0",
)

sandbox_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared agent instance
agent = BankDeskAgent(shield_enabled=False)


class ChatRequest(BaseModel):
    message: str
    shield_enabled: bool = False
    session_id: str = "sandbox-session"


@sandbox_app.post("/api/sandbox/chat")
def chat(req: ChatRequest) -> dict[str, Any]:
    """Execute a chat turn through BankDesk."""
    agent.shield_enabled = req.shield_enabled
    result = agent.process_turn(req.message, session_id=req.session_id)
    return {
        "user_input": result.user_input,
        "assistant_reply": result.assistant_reply,
        "shield_enabled": result.shield_enabled,
        "breach_occurred": result.breach_occurred,
        "shield_blocked": result.shield_blocked,
        "executed_tools": result.executed_tools,
        "blocked_tools": result.blocked_tools,
        "audit_sequence": result.audit_sequence,
        "explanation": result.explanation,
        "summary": agent.state.get_summary(),
    }


@sandbox_app.get("/api/sandbox/state")
def get_state() -> dict[str, Any]:
    """Inspect in-memory state: outbox, refunds, breaches."""
    return {
        "summary": agent.state.get_summary(),
        "email_outbox": [
            {
                "to": e.to,
                "subject": e.subject,
                "body": e.body,
                "timestamp": e.timestamp,
                "is_external": e.is_external,
                "leaked_canary": e.leaked_canary,
            }
            for e in reversed(agent.state.email_outbox)
        ],
        "refund_ledger": [
            {
                "account_id": r.account_id,
                "amount": r.amount,
                "reason": r.reason,
                "timestamp": r.timestamp,
            }
            for r in reversed(agent.state.refund_ledger)
        ],
        "breach_alerts": [
            {
                "breach_type": b.breach_type,
                "severity": b.severity,
                "details": b.details,
                "canary_token": b.canary_token,
                "timestamp": b.timestamp,
            }
            for b in reversed(agent.state.breach_alerts)
        ],
    }


@sandbox_app.post("/api/sandbox/reset")
def reset_state() -> dict[str, str]:
    """Reset sandbox state back to clean initial data."""
    agent.reset()
    return {"status": "reset_successful"}


@sandbox_app.get("/api/sandbox/fixtures")
def get_fixtures() -> dict[str, Any]:
    """List sample test documents and tickets for interactive testing."""
    return {
        "documents": [
            {
                "id": k,
                "title": v["title"],
                "language": v["language"],
                "is_poisoned": v.get("is_poisoned", False),
            }
            for k, v in DOCUMENT_FIXTURES.items()
        ],
        "tickets": [
            {"id": k, "subject": v["subject"], "is_poisoned": v.get("is_poisoned", False)}
            for k, v in TICKET_FIXTURES.items()
        ],
    }
