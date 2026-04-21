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


def _resolve_role(email: str) -> str:
    e = email.strip().lower()
    if "admin" in e:
        return ROLE_ADMIN
    return ROLE_EMPLOYEE


def _access_delta(role: str) -> timedelta:
    if role == ROLE_ADMIN:
        return timedelta(minutes=JWT_ACCESS_MINUTES_ADMIN)
    return timedelta(hours=JWT_ACCESS_HOURS_EMPLOYEE)


def create_access_token(*, email: str, role: str) -> tuple[str, int]:
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
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token, int((expire - now).total_seconds())


def create_refresh_token(*, email: str, role: str) -> tuple[str, int]:
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


@router.post("/login")
def login(body: LoginBody):
    if body.password != AUTH_DEMO_PASSWORD:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    email = body.email.strip().lower()
    role = _resolve_role(email)
    access_token, access_expires = create_access_token(email=email, role=role)
    refresh_token, refresh_expires = create_refresh_token(email=email, role=role)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": access_expires,
        "refresh_expires_in": refresh_expires,
        "role": role,
        "email": email,
    }


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
    if not email:
        raise HTTPException(status_code=401, detail="Token inválido")

    access_token, access_expires = create_access_token(email=str(email), role=str(role))
    refresh_token, refresh_expires = create_refresh_token(email=str(email), role=str(role))
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": access_expires,
        "refresh_expires_in": refresh_expires,
        "role": role,
        "email": email,
    }


@router.get("/me")
def me(credentials: Annotated[HTTPAuthorizationCredentials, Depends(require_bearer)]):
    try:
        payload = decode_token(credentials.credentials)
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

    if payload.get(CLAIM_TYP) == TYP_REFRESH:
        raise HTTPException(status_code=401, detail="Usa el access token, no el refresh")

    return {
        "email": payload.get("email") or payload.get("sub"),
        "role": payload.get("role"),
        "exp": payload.get("exp"),
    }
