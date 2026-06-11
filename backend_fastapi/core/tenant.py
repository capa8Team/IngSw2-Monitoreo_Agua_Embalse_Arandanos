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


def _organizations_from_jwt_claims(payload: dict) -> list[OrganizationInfo]:
    """Organizaciones embebidas en el access token (evita consulta a Supabase por request)."""
    raw = payload.get("organizations")
    if not isinstance(raw, list) or not raw:
        return []

    orgs: list[OrganizationInfo] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        org_id = str(item.get("id") or "").strip()
        if not org_id:
            continue
        orgs.append(
            OrganizationInfo(
                id=org_id,
                name=str(item.get("name") or ""),
                slug=str(item.get("slug") or DEFAULT_ORGANIZATION_SLUG),
                org_role=str(item.get("org_role") or "employee"),
            )
        )
    return orgs


def _tenant_from_jwt_orgs(
    *,
    payload: dict,
    user_id: str,
    email: str,
    jwt_orgs: list[OrganizationInfo],
    x_organization_id: Optional[str],
) -> TenantContext:
    token_org_id = str(payload.get("organization_id") or "").strip() or None
    header_org_id = (x_organization_id or "").strip() or None
    preferred_org = header_org_id or token_org_id

    if preferred_org and not any(o.id == preferred_org for o in jwt_orgs):
        raise HTTPException(status_code=403, detail="Sin acceso a esta organización")

    active_id: Optional[str] = None
    if preferred_org and any(o.id == preferred_org for o in jwt_orgs):
        active_id = preferred_org
    elif token_org_id and any(o.id == token_org_id for o in jwt_orgs):
        active_id = token_org_id
    elif jwt_orgs:
        active_id = jwt_orgs[0].id

    if not active_id:
        raise HTTPException(
            status_code=403,
            detail="Organización activa no disponible",
        )

    active_slug = DEFAULT_ORGANIZATION_SLUG
    for org in jwt_orgs:
        if org.id == active_id:
            active_slug = org.slug or DEFAULT_ORGANIZATION_SLUG
            break

    return TenantContext(
        organization_id=active_id,
        organization_slug=active_slug,
        user_id=user_id or None,
        email=email or None,
        organizations=jwt_orgs,
    )


def _resolve_tenant(
    credentials: Optional[HTTPAuthorizationCredentials],
    x_organization_id: Optional[str],
) -> TenantContext:
    if credentials is None:
        default_org = get_default_organization()
        return TenantContext(
            organization_id=default_org.id if default_org else None,
            organization_slug=default_org.slug if default_org else DEFAULT_ORGANIZATION_SLUG,
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

    jwt_orgs = _organizations_from_jwt_claims(payload)
    if user_id and jwt_orgs:
        return _tenant_from_jwt_orgs(
            payload=payload,
            user_id=user_id,
            email=email,
            jwt_orgs=jwt_orgs,
            x_organization_id=x_organization_id,
        )

    default_org = get_default_organization()
    default_slug = default_org.slug if default_org else DEFAULT_ORGANIZATION_SLUG

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

    if user_id and not org_context.organizations:
        raise HTTPException(
            status_code=403,
            detail="Usuario sin organización asignada",
        )

    if user_id and not active_id:
        raise HTTPException(
            status_code=403,
            detail="Organización activa no disponible",
        )

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
    tenant_org_id = tenant.organization_id
    device_slug = str(device.get("organization_slug") or DEFAULT_ORGANIZATION_SLUG)
    tenant_slug = str(tenant.organization_slug or DEFAULT_ORGANIZATION_SLUG)

    if device_org_id:
        if not tenant_org_id or str(device_org_id) != str(tenant_org_id):
            raise HTTPException(status_code=403, detail="Dispositivo fuera de tu organización")
        return

    if tenant_org_id and device_slug != tenant_slug:
        raise HTTPException(status_code=403, detail="Dispositivo fuera de tu organización")

    if device_slug != tenant_slug:
        raise HTTPException(status_code=403, detail="Dispositivo fuera de tu organización")
