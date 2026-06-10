"""
Autenticación JWT: access corto solo para administrador (30 min por defecto);
access más largo para empleado. Refresh token (JWT) para ambos con validez extendida.
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel, Field

from services.organization_service import (
    assign_user_to_organization,
    fetch_user_organizations,
    get_organization_by_id,
    list_organization_auth_users,
    organizations_to_claims,
    resolve_user_organization_context,
    user_can_access_organization,
    user_is_org_admin,
)
from services.supabase_auth import (
    is_supabase_auth_configured,
    resolve_role_for_user,
    verify_supabase_access_token,
    verify_supabase_password,
)
from services.user_password_setup import (
    email_requires_password_setup,
    get_must_set_password,
    set_must_set_password,
)

try:
    from core.log_origins import LogLevel
    from core.log_service import log_service
except ImportError:
    log_service = None
    LogLevel = None

router = APIRouter()

JWT_SECRET = os.getenv("JWT_SECRET", "dev-cambiar-en-produccion-embalse-arandanos")
JWT_ALGORITHM = "HS256"

# Access: 30 min solo rol administrador
JWT_ACCESS_MINUTES_ADMIN = int(os.getenv("JWT_ACCESS_MINUTES_ADMIN", "30"))
# Access empleado (horas por defecto 8)
JWT_ACCESS_HOURS_EMPLOYEE = int(os.getenv("JWT_ACCESS_HOURS_EMPLOYEE", "8"))

# Refresh: ambos roles (días)
JWT_REFRESH_DAYS = int(os.getenv("JWT_REFRESH_DAYS", "7"))

AUTH_DEMO_PASSWORD = os.getenv("AUTH_DEMO_PASSWORD", "123456789")

ROLE_ADMIN = "administrador"
ROLE_EMPLOYEE = "empleado"
CLAIM_TYP = "typ"
TYP_ACCESS = "access"
TYP_REFRESH = "refresh"

security = HTTPBearer(auto_error=False)


class LoginBody(BaseModel):
    email: str = Field(..., min_length=3, max_length=320)
    password: str = Field(..., min_length=1, max_length=256)


class RefreshBody(BaseModel):
    refresh_token: str = Field(..., min_length=20)


class SupabaseSessionBody(BaseModel):
    email: str = Field(..., min_length=3, max_length=320)
    access_token: str = Field(..., min_length=20)


class SwitchOrganizationBody(BaseModel):
    organization_id: str = Field(..., min_length=8, max_length=64)


class FirstAccessCheckBody(BaseModel):
    email: str = Field(..., min_length=3, max_length=320)


class MarkPasswordSetupBody(BaseModel):
    user_id: str = Field(..., min_length=8, max_length=64)


class CompletePasswordSetupBody(BaseModel):
    email: str = Field(..., min_length=3, max_length=320)
    access_token: str = Field(..., min_length=20)


class AssignUserOrganizationBody(BaseModel):
    user_id: str = Field(..., min_length=8, max_length=64)
    organization_id: str = Field(..., min_length=8, max_length=64)
    org_role: str = Field(default="employee", max_length=32)


def _resolve_role(email: str) -> str:
    e = email.strip().lower()
    if "admin" in e:
        return ROLE_ADMIN
    return ROLE_EMPLOYEE


def _access_delta(role: str) -> timedelta:
    if role == ROLE_ADMIN:
        return timedelta(minutes=JWT_ACCESS_MINUTES_ADMIN)
    return timedelta(hours=JWT_ACCESS_HOURS_EMPLOYEE)


def _token_extras(
    *,
    user_id: str | None = None,
    organization_id: str | None = None,
    organizations: list | None = None,
) -> dict:
    extras: dict = {}
    if user_id:
        extras["user_id"] = user_id
    if organization_id:
        extras["organization_id"] = organization_id
    if organizations:
        extras["organizations"] = organizations
    return extras


def create_access_token(
    *,
    email: str,
    role: str,
    user_id: str | None = None,
    organization_id: str | None = None,
    organizations: list | None = None,
) -> tuple[str, int]:
    """Devuelve (jwt, expires_in_segundos)."""
    now = datetime.now(timezone.utc)
    expire = now + _access_delta(role)
    payload = {
        "sub": email,
        "email": email,
        "role": role,
        CLAIM_TYP: TYP_ACCESS,
        "jti": str(uuid.uuid4()),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        **_token_extras(
            user_id=user_id,
            organization_id=organization_id,
            organizations=organizations,
        ),
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token, int((expire - now).total_seconds())


def create_refresh_token(
    *,
    email: str,
    role: str,
    user_id: str | None = None,
    organization_id: str | None = None,
    organizations: list | None = None,
) -> tuple[str, int]:
    """Refresh JWT para administrador y empleado. Devuelve (jwt, expires_in_segundos)."""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=JWT_REFRESH_DAYS)
    payload = {
        "sub": email,
        "email": email,
        "role": role,
        CLAIM_TYP: TYP_REFRESH,
        "jti": str(uuid.uuid4()),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        **_token_extras(
            user_id=user_id,
            organization_id=organization_id,
            organizations=organizations,
        ),
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token, int((expire - now).total_seconds())


def decode_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])


def require_bearer(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
) -> HTTPAuthorizationCredentials:
    if credentials is None or (credentials.scheme or "").lower() != "bearer":
        raise HTTPException(status_code=401, detail="Token requerido")
    return credentials


def require_access_payload(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(require_bearer)],
) -> dict:
    try:
        payload = decode_token(credentials.credentials)
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

    if payload.get(CLAIM_TYP) == TYP_REFRESH:
        raise HTTPException(status_code=401, detail="Usa el access token, no el refresh")

    return payload


def require_admin_payload(payload: Annotated[dict, Depends(require_access_payload)]) -> dict:
    role = str(payload.get("role") or "").lower()
    if role != ROLE_ADMIN and role != "admin":
        raise HTTPException(status_code=403, detail="Acceso restringido a administradores")
    return payload


def _issue_tokens_for_auth_user(*, email: str, user_id: str) -> dict:
    if get_must_set_password(user_id=user_id):
        return {
            "requires_password_setup": True,
            "email": email,
            "user_id": user_id,
        }

    role = resolve_role_for_user(user_id=user_id, email=email)
    org_context = resolve_user_organization_context(user_id=user_id)
    org_claims = organizations_to_claims(org_context.organizations)
    active_org_id = org_context.active_organization_id

    if log_service:
        log_service.log_login(
            LogLevel.INFO, "Login exitoso",
            component="auth.jwt",
            details={
                "event": "login",
                "role": role,
                "user_email": email,
                "email_domain": email.split("@")[-1],
                "organization_id": active_org_id,
            },
        )
    access_token, access_expires = create_access_token(
        email=email,
        role=role,
        user_id=user_id,
        organization_id=active_org_id,
        organizations=org_claims,
    )
    refresh_token, refresh_expires = create_refresh_token(
        email=email,
        role=role,
        user_id=user_id,
        organization_id=active_org_id,
        organizations=org_claims,
    )
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": access_expires,
        "refresh_expires_in": refresh_expires,
        "role": role,
        "email": email,
        "user_id": user_id,
        "organization_id": active_org_id,
        "organizations": org_claims,
    }


@router.post("/session")
def login_with_supabase_session(body: SupabaseSessionBody):
    """
    Emite JWT de la app tras validar un access_token de Supabase.
    El frontend autentica primero con signInWithPassword (misma vía que al crear usuarios).
    """
    email = body.email.strip().lower()
    auth_user = verify_supabase_access_token(body.access_token)
    if not auth_user:
        if log_service:
            log_service.log_login(
                LogLevel.WARN, "Token Supabase inválido",
                component="auth.jwt",
                details={"event": "login_failed", "user_email": email, "source": "supabase_token"},
            )
        raise HTTPException(status_code=401, detail="Sesión de Supabase inválida o expirada")

    token_email = (auth_user.get("email") or "").lower()
    if token_email and token_email != email:
        raise HTTPException(status_code=401, detail="El correo no coincide con la sesión de Supabase")

    return _issue_tokens_for_auth_user(email=token_email or email, user_id=auth_user["id"])


@router.post("/first-access/check")
def check_first_access(body: FirstAccessCheckBody):
    """Indica si el correo debe configurar contraseña en su primer acceso."""
    email = body.email.strip().lower()
    return {
        "email": email,
        "requires_password_setup": email_requires_password_setup(email),
    }


@router.get("/admin/organization-users")
def admin_list_organization_users(
    payload: Annotated[dict, Depends(require_admin_payload)],
):
    """Lista usuarios de Auth que pertenecen a la organización activa del admin."""
    admin_user_id = str(payload.get("user_id") or "")
    organization_id = str(payload.get("organization_id") or "").strip()
    if not organization_id:
        raise HTTPException(status_code=400, detail="Organización activa no definida en la sesión")

    if not user_is_org_admin(user_id=admin_user_id, organization_id=organization_id):
        raise HTTPException(
            status_code=403,
            detail="No tienes permisos de administrador en esa organización",
        )

    users = list_organization_auth_users(organization_id)
    verified_count = sum(1 for u in users if u.get("is_verified"))
    org = get_organization_by_id(organization_id)
    return {
        "success": True,
        "users": users,
        "total": len(users),
        "verified_count": verified_count,
        "pending_count": len(users) - verified_count,
        "organization_id": organization_id,
        "organization_name": org.name if org else None,
        "source": "organization_scope",
    }


@router.post("/admin/assign-organization")
def admin_assign_user_organization(
    body: AssignUserOrganizationBody,
    payload: Annotated[dict, Depends(require_admin_payload)],
):
    """Asigna un usuario a una organización (evita RLS recursivo del cliente Supabase)."""
    admin_user_id = str(payload.get("user_id") or "")
    organization_id = (
        body.organization_id.strip()
        or str(payload.get("organization_id") or "").strip()
    )
    org_role = body.org_role.strip().lower()

    if not organization_id:
        raise HTTPException(status_code=400, detail="Organización activa no definida")

    admin_orgs = fetch_user_organizations(admin_user_id)
    is_org_admin = any(
        o.id == organization_id and o.org_role == "admin" for o in admin_orgs
    )
    if not is_org_admin:
        raise HTTPException(
            status_code=403,
            detail="No tienes permisos de administrador en esa organización",
        )

    ok, err = assign_user_to_organization(
        user_id=body.user_id.strip(),
        organization_id=organization_id,
        org_role=org_role,
    )
    if not ok:
        raise HTTPException(status_code=400, detail=err or "No se pudo asignar la organización")
    return {"success": True, "user_id": body.user_id, "organization_id": organization_id}


@router.post("/first-access/mark")
def mark_password_setup_required(
    body: MarkPasswordSetupBody,
    payload: Annotated[dict, Depends(require_admin_payload)],
):
    """Marca cuenta recién creada para definir contraseña en primer acceso (solo admin)."""
    ok, err = set_must_set_password(user_id=body.user_id.strip(), required=True)
    if not ok:
        raise HTTPException(status_code=400, detail=err or "No se pudo marcar el usuario")
    return {"success": True, "user_id": body.user_id}


@router.post("/first-access/complete")
def complete_password_setup(body: CompletePasswordSetupBody):
    """Quita el flag tras actualizar la contraseña en Supabase Auth y emite sesión JWT."""
    email = body.email.strip().lower()
    auth_user = verify_supabase_access_token(body.access_token)
    if not auth_user:
        raise HTTPException(status_code=401, detail="Sesión de Supabase inválida")

    token_email = (auth_user.get("email") or "").lower()
    user_id = str(auth_user.get("id") or "")
    if token_email and token_email != email:
        raise HTTPException(status_code=401, detail="El correo no coincide con la sesión")

    if not get_must_set_password(user_id=user_id):
        raise HTTPException(status_code=400, detail="Esta cuenta ya tiene contraseña configurada")

    ok, err = set_must_set_password(user_id=user_id, required=False)
    if not ok:
        raise HTTPException(status_code=500, detail=err or "No se pudo actualizar el estado del usuario")

    return _issue_tokens_for_auth_user(email=token_email or email, user_id=user_id)


@router.get("/config-status")
def auth_config_status():
    """Diagnóstico sin secretos: confirma si el backend ve Supabase Auth."""
    return {
        "supabase_auth_configured": is_supabase_auth_configured(),
        "demo_fallback": not is_supabase_auth_configured(),
    }


@router.post("/login")
def login(body: LoginBody):
    email = body.email.strip().lower()

    if is_supabase_auth_configured():
        auth_user, auth_error = verify_supabase_password(email, body.password)
        if not auth_user:
            if log_service:
                log_service.log_login(
                    LogLevel.WARN, "Intento de login fallido",
                    component="auth.jwt",
                    details={"event": "login_failed", "user_email": email, "source": "supabase"},
                )
            raise HTTPException(status_code=401, detail=auth_error or "Credenciales inválidas")
        return _issue_tokens_for_auth_user(email=email, user_id=auth_user["id"])
    if body.password == AUTH_DEMO_PASSWORD:
        return _issue_tokens_for_auth_user(email=email, user_id=email)

    if log_service:
        log_service.log_login(
            LogLevel.WARN, "Intento de login fallido",
            component="auth.jwt",
            details={"event": "login_failed", "user_email": email, "source": "demo"},
        )
    raise HTTPException(status_code=401, detail="Credenciales inválidas")


@router.post("/refresh")
def refresh_session(body: RefreshBody):
    try:
        payload = decode_token(body.refresh_token)
    except JWTError:
        raise HTTPException(status_code=401, detail="Refresh token inválido o expirado")

    if payload.get(CLAIM_TYP) != TYP_REFRESH:
        raise HTTPException(status_code=401, detail="Se requiere refresh token")

    email = payload.get("email") or payload.get("sub")
    role = payload.get("role") or ROLE_EMPLOYEE
    user_id = str(payload.get("user_id") or "")
    if not email:
        raise HTTPException(status_code=401, detail="Token inválido")

    preferred_org = payload.get("organization_id")
    org_context = resolve_user_organization_context(
        user_id=user_id,
        preferred_organization_id=str(preferred_org) if preferred_org else None,
    )
    org_claims = organizations_to_claims(org_context.organizations)
    active_org_id = org_context.active_organization_id

    access_token, access_expires = create_access_token(
        email=str(email),
        role=str(role),
        user_id=user_id or None,
        organization_id=active_org_id,
        organizations=org_claims,
    )
    refresh_token, refresh_expires = create_refresh_token(
        email=str(email),
        role=str(role),
        user_id=user_id or None,
        organization_id=active_org_id,
        organizations=org_claims,
    )
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": access_expires,
        "refresh_expires_in": refresh_expires,
        "role": role,
        "email": email,
        "user_id": user_id or None,
        "organization_id": active_org_id,
        "organizations": org_claims,
    }


@router.post("/switch-organization")
def switch_organization(
    body: SwitchOrganizationBody,
    payload: Annotated[dict, Depends(require_access_payload)],
):
    """Cambia la organización activa (usuarios con acceso a varias organizaciones)."""
    user_id = str(payload.get("user_id") or "")
    email = str(payload.get("email") or payload.get("sub") or "")
    role = str(payload.get("role") or ROLE_EMPLOYEE)
    org_id = body.organization_id.strip()

    if not user_can_access_organization(user_id=user_id, organization_id=org_id):
        raise HTTPException(status_code=403, detail="Sin acceso a esta organización")

    org_context = resolve_user_organization_context(
        user_id=user_id,
        preferred_organization_id=org_id,
    )
    org_claims = organizations_to_claims(org_context.organizations)

    access_token, access_expires = create_access_token(
        email=email,
        role=role,
        user_id=user_id or None,
        organization_id=org_id,
        organizations=org_claims,
    )
    refresh_token, refresh_expires = create_refresh_token(
        email=email,
        role=role,
        user_id=user_id or None,
        organization_id=org_id,
        organizations=org_claims,
    )
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": access_expires,
        "refresh_expires_in": refresh_expires,
        "role": role,
        "email": email,
        "organization_id": org_id,
        "organizations": org_claims,
    }


@router.get("/me")
def me(payload: Annotated[dict, Depends(require_access_payload)]):
    return {
        "email": payload.get("email") or payload.get("sub"),
        "role": payload.get("role"),
        "exp": payload.get("exp"),
        "user_id": payload.get("user_id"),
        "organization_id": payload.get("organization_id"),
        "organizations": payload.get("organizations") or [],
    }
