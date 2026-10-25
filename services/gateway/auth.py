"""Multi-tenant API Key authentication and Role-Based Access Control (RBAC).

Supports:
- Tenant isolation (each request scoped to tenant_id)
- RBAC roles: 'admin', 'analyst', 'viewer'
- Graceful fallback for local development / demo mode
"""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from dataclasses import dataclass

from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


@dataclass
class TenantUser:
    tenant_id: str
    role: str  # admin, analyst, viewer
    name: str
    api_key_prefix: str

    def can_access(self, required_roles: list[str]) -> bool:
        if self.role == "admin":
            return True
        return self.role in required_roles


# Default development and demonstration tenants
DEFAULT_TENANTS: dict[str, TenantUser] = {
    "pl-admin-demo-key-2026": TenantUser(
        tenant_id="tenant-padma-bank",
        role="admin",
        name="Padma Bank Admin",
        api_key_prefix="pl-admin",
    ),
    "pl-analyst-demo-key-2026": TenantUser(
        tenant_id="tenant-padma-bank",
        role="analyst",
        name="Security Analyst",
        api_key_prefix="pl-analyst",
    ),
    "pl-viewer-demo-key-2026": TenantUser(
        tenant_id="tenant-padma-bank",
        role="viewer",
        name="Compliance Auditor",
        api_key_prefix="pl-viewer",
    ),
}


class AuthManager:
    """Manages multi-tenant API key resolution and role verification."""

    def __init__(self) -> None:
        self.auth_enabled = os.getenv("PROOF_LAYER_AUTH_ENABLED", "false").lower() in (
            "true",
            "1",
            "yes",
        )
        self.tenants = dict(DEFAULT_TENANTS)

        # Load custom keys from env if provided
        custom_keys_json = os.getenv("PROOF_LAYER_CUSTOM_API_KEYS")
        if custom_keys_json:
            try:
                parsed = json.loads(custom_keys_json)
                for key, meta in parsed.items():
                    self.tenants[key] = TenantUser(
                        tenant_id=meta.get("tenant_id", "default-tenant"),
                        role=meta.get("role", "viewer"),
                        name=meta.get("name", "Custom User"),
                        api_key_prefix=key[:8],
                    )
            except Exception:
                pass

    def authenticate(self, api_key: str | None) -> TenantUser:
        """Authenticate request or provide default development user if auth disabled."""
        if not self.auth_enabled:
            # If header is provided, use it if known, else default admin
            if api_key and api_key in self.tenants:
                return self.tenants[api_key]
            return TenantUser(
                tenant_id=os.getenv("DEFAULT_TENANT_ID", "tenant-padma-bank"),
                role="admin",
                name="Default Admin (Dev Mode)",
                api_key_prefix="dev-admin",
            )

        if not api_key:
            raise HTTPException(
                status_code=401,
                detail="Missing API key. Provide 'X-API-Key' header or Authorization header.",
            )

        # Bearer token strip
        if api_key.startswith("Bearer "):
            api_key = api_key[len("Bearer ") :].strip()

        user = self.tenants.get(api_key)
        if not user:
            raise HTTPException(
                status_code=403,
                detail="Invalid API key or unauthorized tenant.",
            )

        return user


auth_manager = AuthManager()


def get_current_user(api_key: str | None = Security(API_KEY_HEADER)) -> TenantUser:
    """FastAPI dependency to extract current tenant user."""
    return auth_manager.authenticate(api_key)


def require_role(allowed_roles: list[str]) -> Callable[[TenantUser], TenantUser]:
    """Dependency factory checking RBAC authorization."""

    def role_checker(user: TenantUser = Depends(get_current_user)) -> TenantUser:
        if not user.can_access(allowed_roles):
            raise HTTPException(
                status_code=403,
                detail=f"Forbidden: role '{user.role}' lacks required permissions {allowed_roles}",
            )
        return user

    return role_checker
