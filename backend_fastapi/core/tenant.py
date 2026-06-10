"""Contexto de organización para filtrado multi-tenant en endpoints."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, Optional

from fastapi import Depends, Header, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from routers.auth_jwt import decode_token, require_bearer

optional_bearer = HTTPBearer(auto_error=False)

from services.organization_service import (
    DEFAULT_ORGANIZATION_SLUG,
    OrganizationInfo,
    get_default_organization,
    get_organization_by_id,
    resolve_user_organization_context,
    user_can_access_organization,
)


@dataclass
class TenantContext:
    organization_id: Optional[str]
    organization_slug: Optional[str]
    user_id: Optional[str]
    email: Optional[str]
    organizations: list[OrganizationInfo]

    @property
    def has_organization_scope(self) -> bool:
        return bool(self.organization_id or self.organization_slug)

    def device_filter(self) -> dict:
        """Filtro MongoDB para dispositivos según organización activa."""
        slug = self.organization_slug or DEFAULT_ORGANIZATION_SLUG
        if self.organization_id:
            return {
                "$or": [
                    {"organization_id": self.organization_id},
                    {
                        "organization_id": {"$exists": False},
                        "organization_slug": slug,
                    },
                    {
                        "organization_id": None,
                        "organization_slug": slug,
                    },
                ]
            }
        return {"organization_slug": slug}

    def readings_filter(self) -> dict:
        """Filtro MongoDB para sensor_readings del tenant activo."""
        from services.mongodb import get_organization_telemetry_keys

        keys = sorted(get_organization_telemetry_keys(org_filter=self.device_filter()))
        clauses: list[dict] = []

        if self.organization_id:
            clauses.append({"organization_id": self.organization_id})

        if keys:
            clauses.append(
                {
                    "$and": [
                        {
                            "$or": [
                                {"organization_id": {"$exists": False}},
                                {"organization_id": None},
                            ]
                        },
                        {"arduino_id": {"$in": keys}},
                    ]
                }
            )

        if not clauses:
            return {"arduino_id": "__tenant_none__"}

        return {"$or": clauses} if len(clauses) > 1 else clauses[0]


def _resolve_tenant(
    credentials: Optional[HTTPAuthorizationCredentials],
    x_organization_id: Optional[str],
) -> TenantContext:
    default_org = get_default_organization()
    default_slug = default_org.slug if default_org else DEFAULT_ORGANIZATION_SLUG
    default_id = default_org.id if default_org else None

    if credentials is None:
        return TenantContext(
            organization_id=default_id,
            organization_slug=default_slug,
            user_id=None,
            email=None,
            organizations=[],
        )

    try:
        payload = decode_token(credentials.credentials)
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

    if payload.get("typ") == "refresh":
        raise HTTPException(status_code=401, detail="Usa el access token, no el refresh")

    email = str(payload.get("email") or payload.get("sub") or "")
    user_id = str(payload.get("user_id") or "")
    token_org_id = payload.get("organization_id")
    header_org_id = (x_organization_id or "").strip() or None
    preferred_org = header_org_id or token_org_id

    org_context = resolve_user_organization_context(
        user_id=user_id,
        preferred_organization_id=str(preferred_org) if preferred_org else None,
    )

    active_id = org_context.active_organization_id
    active_slug = default_slug
    if active_id:
        org = get_organization_by_id(active_id)
        if org:
            active_slug = org.slug
    elif default_org:
        active_id = default_org.id
        active_slug = default_org.slug

    if preferred_org and not user_can_access_organization(
        user_id=user_id,
        organization_id=str(preferred_org),
    ):
        raise HTTPException(status_code=403, detail="Sin acceso a esta organización")

    return TenantContext(
        organization_id=active_id,
        organization_slug=active_slug,
        user_id=user_id or None,
        email=email or None,
        organizations=org_context.organizations,
    )


def get_optional_tenant_context(
    credentials: Annotated[
        Optional[HTTPAuthorizationCredentials], Depends(optional_bearer)
    ] = None,
    x_organization_id: Annotated[Optional[str], Header(alias="X-Organization-Id")] = None,
) -> TenantContext:
    return _resolve_tenant(credentials, x_organization_id)


def get_tenant_context(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(require_bearer)],
    x_organization_id: Annotated[Optional[str], Header(alias="X-Organization-Id")] = None,
) -> TenantContext:
    return _resolve_tenant(credentials, x_organization_id)


def ensure_device_in_tenant(device: Optional[dict], tenant: TenantContext) -> None:
    if not device:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")

    device_org_id = device.get("organization_id")
    device_slug = str(device.get("organization_slug") or DEFAULT_ORGANIZATION_SLUG)
    tenant_slug = str(tenant.organization_slug or DEFAULT_ORGANIZATION_SLUG)

    if device_org_id and tenant.organization_id:
        if str(device_org_id) != str(tenant.organization_id):
            raise HTTPException(status_code=403, detail="Dispositivo fuera de tu organización")
        return

    if device_slug != tenant_slug:
        raise HTTPException(status_code=403, detail="Dispositivo fuera de tu organización")
