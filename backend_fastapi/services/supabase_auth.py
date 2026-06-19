"""Validación de credenciales contra Supabase Auth y resolución de rol en users_roles."""
from __future__ import annotations

import os
from typing import Any, Optional

import requests
from sqlalchemy import text

from core.config import settings
from db.database import SessionLocal

ROLE_ADMIN = "administrador"
ROLE_EMPLOYEE = "empleado"


_PLACEHOLDER_MARKERS = ("your-project", "your-anon-key", "tu-proyecto", "anon-key-here")


def _is_placeholder(value: str | None) -> bool:
    normalized = str(value or "").strip().lower()
    if not normalized:
        return True
    return any(marker in normalized for marker in _PLACEHOLDER_MARKERS)


def _first_valid_supabase_value(*values: str | None) -> str:
    for value in values:
        if not _is_placeholder(value):
            return str(value).strip()
    return ""


def _get_supabase_url() -> str:
    return _first_valid_supabase_value(
        settings.VITE_SUPABASE_URL,
        settings.SUPABASE_URL,
        os.getenv("VITE_SUPABASE_URL"),
        os.getenv("SUPABASE_URL"),
    ).rstrip("/")


def _get_supabase_anon_key() -> str:
    return _first_valid_supabase_value(
        settings.VITE_SUPABASE_ANON_KEY,
        settings.SUPABASE_ANON_KEY,
        os.getenv("VITE_SUPABASE_ANON_KEY"),
        os.getenv("SUPABASE_ANON_KEY"),
    )


def _auth_headers(*, bearer: Optional[str] = None) -> dict[str, str]:
    anon = _get_supabase_anon_key()
    headers = {
        "apikey": anon,
        "Content-Type": "application/json",
    }
    token = bearer or anon
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def is_supabase_auth_configured() -> bool:
    return bool(_get_supabase_url() and _get_supabase_anon_key())


def map_db_role_to_jwt(role: Optional[str]) -> str:
    r = str(role or "").lower().strip()
    if r in ("admin", "administrador"):
        return ROLE_ADMIN
    return ROLE_EMPLOYEE


def fetch_role_from_users_roles(user_id: str) -> Optional[str]:
    if not SessionLocal or not user_id:
        return None
    db = SessionLocal()
    try:
        row = db.execute(
            text("SELECT role FROM public.users_roles WHERE id::text = :uid LIMIT 1"),
            {"uid": user_id},
        ).fetchone()
        return str(row[0]) if row and row[0] else None
    except Exception:
        db.rollback()
        return None
    finally:
        db.close()


def _parse_auth_error(response: requests.Response) -> str:
    detail = "Credenciales inválidas"
    try:
        body = response.json()
        raw = (
            body.get("error_description")
            or body.get("msg")
            or body.get("message")
            or body.get("error")
            or ""
        )
        raw_lower = str(raw).lower()
        if "email not confirmed" in raw_lower or "email_not_confirmed" in raw_lower:
            return "Debes confirmar tu correo en Supabase antes de iniciar sesión"
        if "invalid login credentials" in raw_lower or "invalid_credentials" in raw_lower:
            return "Correo o contraseña incorrectos"
        if raw:
            return str(raw)
    except Exception:
        pass
    if response.status_code in (401, 403):
        return "Correo o contraseña incorrectos"
    return detail


def verify_supabase_password(email: str, password: str) -> tuple[Optional[dict[str, Any]], Optional[str]]:
    """Valida email/contraseña con grant_type=password (GoTrue)."""
    if not is_supabase_auth_configured():
        return None, None

    url = f"{_get_supabase_url()}/auth/v1/token?grant_type=password"
    try:
        response = requests.post(
            url,
            json={"email": email, "password": password},
            headers=_auth_headers(),
            timeout=20,
        )
    except requests.RequestException:
        return None, "No se pudo contactar Supabase Auth. Intenta de nuevo más tarde."

    if response.status_code == 200:
        payload = response.json()
        user = payload.get("user") or {}
        user_id = user.get("id")
        if not user_id and payload.get("access_token"):
            verified = verify_supabase_access_token(str(payload["access_token"]))
            if verified:
                return verified, None
        if not user_id:
            return None, "Respuesta inválida de Supabase Auth"
        return {
            "id": str(user_id),
            "email": (user.get("email") or email).lower(),
        }, None

    return None, _parse_auth_error(response)


def verify_supabase_access_token(access_token: str) -> Optional[dict[str, Any]]:
    """Valida un access token de Supabase (GET /auth/v1/user)."""
    if not is_supabase_auth_configured() or not access_token:
        return None

    url = f"{_get_supabase_url()}/auth/v1/user"
    try:
        response = requests.get(
            url,
            headers=_auth_headers(bearer=access_token),
            timeout=20,
        )
    except requests.RequestException:
        return None

    if response.status_code != 200:
        return None

    data = response.json()
    user_id = data.get("id")
    if not user_id:
        return None
    return {
        "id": str(user_id),
        "email": str(data.get("email") or "").lower(),
    }


def resolve_role_for_user(*, user_id: str, email: str) -> str:
    db_role = fetch_role_from_users_roles(user_id)
    if db_role:
        return map_db_role_to_jwt(db_role)
    e = email.strip().lower()
    if "admin" in e:
        return ROLE_ADMIN
    return ROLE_EMPLOYEE
