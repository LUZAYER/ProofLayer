"""ProofLayer Gateway Service — FastAPI application with real-time SSE telemetry."""

from __future__ import annotations

import asyncio
import json
import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from services.audit.ledger import AuditLedger
from services.detectors.ensemble import DetectorEnsemble
from services.gateway.approvals import ApprovalQueue
from services.gateway.auth import TenantUser, auth_manager, get_current_user
from services.policy.engine import PolicyEngine
from services.policy.schema import PolicyDefinition
from services.policy.simulator import PolicySimulator


# In-memory pub-sub for SSE real-time console streaming
class RealtimeBroadcaster:
    def __init__(self) -> None:
        self.subscribers: set[asyncio.Queue[str]] = set()

    async def broadcast(self, event_type: str, data: dict[str, Any]) -> None:
        payload = json.dumps({"event": event_type, "data": data, "timestamp": time.time()})
        for q in list(self.subscribers):
            try:
                q.put_nowait(payload)
            except asyncio.QueueFull:
                self.subscribers.remove(q)

    def subscribe(self) -> asyncio.Queue[str]:
        q: asyncio.Queue[str] = asyncio.Queue(maxsize=100)
        self.subscribers.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue[str]) -> None:
        self.subscribers.discard(q)


broadcaster = RealtimeBroadcaster()

# Global service singletons
ensemble = DetectorEnsemble(
    rules_dir=Path("services/detectors/rules"),
    model_dir=Path("services/detectors/model"),
)
audit_ledger = AuditLedger()
approval_queue = ApprovalQueue()
policy_simulator = PolicySimulator()

# Load default policy
policies_dir = Path("policies")
default_policy_file = policies_dir / "strict-bank.yaml"
if default_policy_file.exists():
    default_policy = PolicyDefinition.from_yaml(default_policy_file.read_text(encoding="utf-8"))
else:
    default_policy = PolicyDefinition(id="default", name="Default Strict Policy")

policy_engine = PolicyEngine(default_policy=default_policy)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup: Ensure classifier is loaded
    ensemble.classifier.load(Path("services/detectors/model"))
    yield
    # Teardown logic if needed


app = FastAPI(
    title="ProofLayer Trust Gateway",
    version="1.0.0",
    description="Multilingual AI Agent Governance, Runtime Shield, and Audit Ledger",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Rate limit tracking (token bucket per IP/Key)
REQUEST_COUNTS: dict[str, list[float]] = {}
RATE_LIMIT_WINDOW = 60.0  # seconds
RATE_LIMIT_MAX = 600  # requests per minute


@app.middleware("http")
async def security_and_rate_limit_middleware(request: Request, call_next: Any) -> Response:
    # 1. Enforce payload size limit (max 2 MB)
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > 2 * 1024 * 1024:
        return JSONResponse(
            status_code=413, content={"error": "Payload too large. Max limit is 2MB."}
        )

    # 2. Rate limiting
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    timestamps = [t for t in REQUEST_COUNTS.get(client_ip, []) if now - t < RATE_LIMIT_WINDOW]
    timestamps.append(now)
    REQUEST_COUNTS[client_ip] = timestamps
    if len(timestamps) > RATE_LIMIT_MAX:
        return JSONResponse(
            status_code=429, content={"error": "Rate limit exceeded. Max 600 req/min."}
        )

    # 3. Add security headers
    response: Response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response


# --- Pydantic Request / Response Models ---


class SegmentInput(BaseModel):
    text: str
    provenance: str = "USER"
    language_hint: str | None = None


class ShieldScanRequest(BaseModel):
    segments: list[SegmentInput]
    policy_id: str | None = None


class ToolAuthorizeRequest(BaseModel):
    agent_id: str
    tool_name: str
    arguments: dict[str, Any]
    context: dict[str, Any] = Field(default_factory=dict)
    policy_id: str | None = None


class OutputScanRequest(BaseModel):
    text: str
    redact: bool = True


class ApprovalDecisionRequest(BaseModel):
    decision: str  # approve | deny
    note: str = ""
    decided_by: str = "analyst"


class ChatCompletionMessage(BaseModel):
    role: str
    content: str
    provenance: str | None = None


class ChatCompletionRequest(BaseModel):
    model: str = "prooflayer-shield"
    messages: list[ChatCompletionMessage]
    tools: list[dict[str, Any]] | None = None
    temperature: float | None = 0.7
    stream: bool | None = False


class PolicySimulateRequest(BaseModel):
    policy_yaml: str
    test_events: list[dict[str, Any]] = Field(default_factory=list)


# --- Endpoints ---


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok", "service": "prooflayer-gateway"}


@app.get("/readyz")
def readyz() -> dict[str, Any]:
    return {
        "status": "ready",
        "detectors_loaded": ensemble.classifier.is_trained,
        "rules_count": len(ensemble.rules_engine.rules),
        "audit_events_count": len(audit_ledger.events),
    }


@app.get("/metrics")
def metrics() -> Response:
    """Prometheus-compatible plaintext metrics."""
    events_count = len(audit_ledger.events)
    pending_approvals = len(approval_queue.list_requests(status="pending"))
    prom_metrics = (
        f"# HELP prooflayer_scanned_events_total Total number of audit-recorded events\n"
        f"# TYPE prooflayer_scanned_events_total counter\n"
        f"prooflayer_scanned_events_total {events_count}\n"
        f"# HELP prooflayer_pending_approvals Current pending approvals\n"
        f"# TYPE prooflayer_pending_approvals gauge\n"
        f"prooflayer_pending_approvals {pending_approvals}\n"
    )
    return Response(content=prom_metrics, media_type="text/plain")


@app.post("/v1/chat/completions")
async def chat_completions(
    req: ChatCompletionRequest, background_tasks: BackgroundTasks
) -> dict[str, Any]:
    """OpenAI-compatible chat completion proxy with inline Shield inspection."""
    highest_score = 0.0
    worst_decision = "ALLOW"
    last_expl = {"en": "Request allowed.", "bn": "অনুরোধ অনুমোদিত।"}
    categories: set[str] = set()

    for msg in req.messages:
        prov = msg.provenance or (
            "TOOL_OUTPUT" if msg.role == "tool" else ("SYSTEM" if msg.role == "system" else "USER")
        )
        res = ensemble.scan(msg.content, provenance=prov)  # type: ignore[arg-type]
        if res.risk_score > highest_score:
            highest_score = res.risk_score
            worst_decision = res.decision
            last_expl = {"en": res.explanation.en, "bn": res.explanation.bn}
        for c in res.categories:
            categories.add(c)

    audit_ev = audit_ledger.append_event(
        event_type="CHAT_COMPLETION",
        decision=worst_decision,
        risk_score=highest_score,
        rule_ids=list(categories),
        evidence={"model": req.model, "messages_count": len(req.messages)},
    )

    cmpl_id = f"chatcmpl-{audit_ev.sequence}"
    created_ts = int(time.time())

    # If blocked or requires approval, return safety refusal response
    if worst_decision in ("BLOCK", "REQUIRE_APPROVAL"):
        content = f"I cannot fulfill this request due to ProofLayer security policy violation: {last_expl['en']}"
        finish_reason = "content_filter"
    else:
        # Allowed: return simulated compliant response for testing
        content = "Request safely verified and processed through ProofLayer Shield."
        finish_reason = "stop"

    return {
        "id": cmpl_id,
        "object": "chat.completion",
        "created": created_ts,
        "model": req.model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content,
                },
                "finish_reason": finish_reason,
            }
        ],
        "prooflayer": {
            "decision": worst_decision,
            "risk_score": highest_score,
            "categories": sorted(categories),
            "audit_sequence": audit_ev.sequence,
            "explanation": last_expl,
        },
    }


@app.post("/v1/shield/scan")
async def shield_scan(req: ShieldScanRequest, background_tasks: BackgroundTasks) -> dict[str, Any]:
    """Inspect text segments for prompt injection, sensitive data, and policy violations."""
    if not req.segments:
        raise HTTPException(status_code=400, detail="Segments list cannot be empty")

    highest_score = 0.0
    combined_categories: set[str] = set()
    worst_decision = "ALLOW"
    last_expl = {"en": "", "bn": ""}
    spotlighted_parts: list[str] = []
    total_latency = 0.0

    for seg in req.segments:
        res = ensemble.scan(seg.text, provenance=seg.provenance)  # type: ignore[arg-type]
        total_latency += res.latency_ms
        if res.risk_score > highest_score:
            highest_score = res.risk_score
            worst_decision = res.decision
            last_expl = {"en": res.explanation.en, "bn": res.explanation.bn}

        for cat in res.categories:
            combined_categories.add(cat)
        spotlighted_parts.append(res.spotlighted_text)

    # Append to signed audit ledger
    audit_ev = audit_ledger.append_event(
        event_type="SHIELD_SCAN",
        decision=worst_decision,
        risk_score=highest_score,
        rule_ids=list(combined_categories),
        evidence={"segments_count": len(req.segments), "risk_score": highest_score},
    )

    # Broadcast event to SSE console stream
    event_payload = {
        "id": f"scan-{audit_ev.sequence}",
        "sequence": audit_ev.sequence,
        "type": "SHIELD_SCAN",
        "decision": worst_decision,
        "risk_score": highest_score,
        "categories": sorted(combined_categories),
        "explanation": last_expl,
        "timestamp": audit_ev.timestamp,
    }
    background_tasks.add_task(broadcaster.broadcast, "SCAN", event_payload)

    return {
        "decision": worst_decision,
        "risk_score": highest_score,
        "categories": sorted(combined_categories),
        "explanation": last_expl,
        "spotlighted_content": "".join(spotlighted_parts),
        "audit_sequence": audit_ev.sequence,
        "latency_ms": round(total_latency, 2),
    }


@app.post("/v1/tools/authorize")
async def authorize_tool(
    req: ToolAuthorizeRequest, background_tasks: BackgroundTasks
) -> dict[str, Any]:
    """Pre-execution validation of agent tool invocations."""
    res = policy_engine.authorize_tool(
        agent_id=req.agent_id,
        tool_name=req.tool_name,
        arguments=req.arguments,
        context=req.context,
    )

    # If requires approval, register in approval queue
    approval_id = res.approval_id
    if res.requires_approval and approval_id:
        approval_queue.create_request(
            approval_id=approval_id,
            agent_id=req.agent_id,
            tool_name=req.tool_name,
            arguments=req.arguments,
            context=req.context,
            rule_ids=res.reasons,
            risk_score=0.50,
            explanation_en=f"Tool '{req.tool_name}' triggered approval: {'; '.join(res.reasons)}",
            explanation_bn=f"টুল '{req.tool_name}' অনুমোদন প্রয়োজন: {'; '.join(res.reasons)}",
        )

    # Record in audit ledger
    audit_ev = audit_ledger.append_event(
        event_type="TOOL_AUTHORIZATION",
        decision=res.decision,
        agent_id=req.agent_id,
        rule_ids=res.reasons,
        evidence={"tool": req.tool_name, "arguments": req.arguments},
    )

    # Broadcast to SSE
    background_tasks.add_task(
        broadcaster.broadcast,
        "TOOL",
        {
            "sequence": audit_ev.sequence,
            "tool": req.tool_name,
            "decision": res.decision,
            "reasons": res.reasons,
            "requires_approval": res.requires_approval,
            "approval_id": approval_id,
        },
    )

    return {
        "decision": res.decision,
        "effective_decision": res.effective_decision,
        "reasons": res.reasons,
        "requires_approval": res.requires_approval,
        "approval_id": approval_id,
        "audit_sequence": audit_ev.sequence,
    }


@app.post("/v1/output/scan")
def scan_output(req: OutputScanRequest) -> dict[str, Any]:
    """Scan model output for secret or PII leakage."""
    res = ensemble.pii_scanner.scan(req.text)
    findings_dicts = [
        {
            "entity_type": f.entity_type,
            "category": f.category,
            "start": f.start,
            "end": f.end,
            "redacted_value": f.redacted_value,
        }
        for f in res.findings
    ]

    if res.has_leakage:
        audit_ledger.append_event(
            event_type="OUTPUT_SCAN",
            decision="ALLOW_WITH_REDACTION",
            risk_score=0.40,
            evidence={"findings_count": len(findings_dicts)},
        )

    return {
        "has_leakage": res.has_leakage,
        "findings": findings_dicts,
        "sanitized_text": res.sanitized_text if req.redact else req.text,
    }


@app.get("/v1/approvals")
def list_approvals(status: str | None = None) -> list[dict[str, Any]]:
    """List pending or filtered human approvals."""
    requests = approval_queue.list_requests(status=status)  # type: ignore[arg-type]
    return [
        {
            "id": r.id,
            "agent_id": r.agent_id,
            "tool_name": r.tool_name,
            "arguments": r.arguments,
            "status": r.status,
            "risk_score": r.risk_score,
            "explanation": {"en": r.explanation_en, "bn": r.explanation_bn},
            "created_at": r.created_at,
            "expires_at": r.expires_at,
            "decided_by": r.decided_by,
            "decision_note": r.decision_note,
        }
        for r in requests
    ]


@app.post("/v1/approvals/{approval_id}/decision")
def decide_approval(approval_id: str, req: ApprovalDecisionRequest) -> dict[str, Any]:
    """Approve or deny a held tool invocation."""
    ok, msg, req_obj = approval_queue.submit_decision(
        approval_id=approval_id,
        decision=req.decision,  # type: ignore[arg-type]
        decided_by=req.decided_by,
        note=req.note,
    )
    if not ok:
        raise HTTPException(status_code=400, detail=msg)

    # Audit the decision
    audit_ledger.append_event(
        event_type="APPROVAL_DECISION",
        decision="ALLOW" if req.decision == "approve" else "DENY",
        evidence={"approval_id": approval_id, "decided_by": req.decided_by, "note": req.note},
    )

    return {"status": "ok", "message": msg, "approval_id": approval_id}


@app.get("/v1/audit/events")
def get_audit_events(limit: int = 50, offset: int = 0) -> dict[str, Any]:
    """Fetch paginated audit ledger events."""
    all_events = audit_ledger.events
    total = len(all_events)
    # Return newest first
    reversed_events = list(reversed(all_events))
    sliced = reversed_events[offset : offset + limit]
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "events": [ev.to_dict() for ev in sliced],
    }


@app.get("/v1/audit/verify")
def verify_audit_ledger() -> dict[str, Any]:
    """Cryptographically verify the entire SHA-256 hash chain and Ed25519 signatures."""
    result = audit_ledger.verify()
    return {
        "valid": result.valid,
        "checked_count": result.checked_count,
        "first_broken_index": result.first_broken_index,
        "reason": result.reason,
    }


@app.get("/v1/audit/pubkey")
def get_public_key() -> dict[str, str]:
    """Get public key for external verification."""
    return {
        "key_id": audit_ledger.key_id,
        "public_key_hex": audit_ledger.public_key_hex,
        "public_key_pem": audit_ledger.public_key_pem,
    }


@app.post("/v1/audit/tamper-demo")
def tamper_demo(target_index: int = 1) -> dict[str, Any]:
    """Live interactive demonstration of cryptographic tampering detection."""
    if not audit_ledger.events:
        # Seed dummy event if empty
        audit_ledger.append_event("SHIELD_SCAN", "BLOCK", risk_score=0.99)

    verify_res, details = audit_ledger.simulate_tampering(target_index=target_index)
    return {
        "tampering_detected": not verify_res.valid,
        "details": details,
    }


@app.post("/v1/policies/simulate")
def simulate_policy(req: PolicySimulateRequest) -> dict[str, Any]:
    """Dry-run candidate policy on events."""
    try:
        summary = policy_simulator.simulate(req.policy_yaml, req.test_events)
        return {
            "total_events": summary.total_events,
            "allowed_count": summary.allowed_count,
            "denied_count": summary.denied_count,
            "approval_count": summary.approval_count,
            "decisions_changed": summary.decisions_changed,
            "events": [
                {
                    "event_id": e.event_id,
                    "tool_name": e.tool_name,
                    "original_decision": e.original_decision,
                    "simulated_decision": e.simulated_decision,
                    "changed": e.changed,
                    "reasons": e.reasons,
                }
                for e in summary.events
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Policy simulation error: {e}") from e


@app.get("/v1/events/stream")
async def events_stream() -> StreamingResponse:
    """Server-Sent Events (SSE) telemetry stream for real-time console updates."""
    queue = broadcaster.subscribe()

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            # Send initial keepalive
            yield f"data: {json.dumps({'event': 'CONNECTED', 'timestamp': time.time()})}\n\n"
            while True:
                msg = await queue.get()
                yield f"data: {msg}\n\n"
        except asyncio.CancelledError:
            broadcaster.unsubscribe(queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/v1/auth/me")
def get_caller_identity(user: TenantUser = Depends(get_current_user)) -> dict[str, Any]:
    """Return currently authenticated tenant identity, role, and permissions."""
    return {
        "tenant_id": user.tenant_id,
        "role": user.role,
        "name": user.name,
        "auth_enabled": auth_manager.auth_enabled,
    }
