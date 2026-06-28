from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.exc import OperationalError, ProgrammingError, SQLAlchemyError
from sqlalchemy.orm import Session

from db.database import SessionLocal, init_log_tables
from db.log_models import LoginLogDB
from db.supabase_db import is_dns_resolution_error, is_ipv6_unreachable_error
from core.tenant import TenantContext, get_tenant_context
from routers.auth_jwt import require_admin_payload
from services.organization_service import (
    fetch_organization_member_emails,
    user_is_org_admin,
)
from services.redis_cache import (
    TTL_ACCOUNT_ACTIVITY,
    account_activity_key,
    cache_aside,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/activity", tags=["Admin Activity"])


def get_log_db():
    if SessionLocal is None:
        raise HTTPException(
            status_code=503,
            detail="SUPABASE_DB_URL no está configurada. Agrega la URL de Postgres en el archivo .env de la raíz.",
        )
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _parse_dt(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def _aggregate_activity(rows: list, *, days: int) -> dict:
    by_email: dict[str, dict] = {}
    now = datetime.now(timezone.utc)
    since_7d = now - timedelta(days=7)

    for r in rows:
        details = r.details or {}
        event = str(details.get("event") or "").lower()
        email = str(details.get("user_email") or "").strip().lower()
        if not email:
            continue
        if event not in ("login", "login_failed"):
            continue

        item = by_email.get(email)
        if item is None:
            item = {
                "email": email,
                "last_login_at": None,
                "last_login_failed_at": None,
                "last_role": None,
                "logins_total": 0,
                "logins_last_7d": 0,
                "failed_logins_total": 0,
                "failed_logins_last_7d": 0,
            }
            by_email[email] = item

        created_at = r.created_at
        if created_at is not None and created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)

        if event == "login":
            item["logins_total"] += 1
            if created_at and created_at >= since_7d:
                item["logins_last_7d"] += 1
            if item["last_login_at"] is None and created_at is not None:
                item["last_login_at"] = created_at.isoformat()
                role = details.get("role")
                if role:
                    item["last_role"] = str(role)
        else:
            item["failed_logins_total"] += 1
            if created_at and created_at >= since_7d:
                item["failed_logins_last_7d"] += 1
            if item["last_login_failed_at"] is None and created_at is not None:
                item["last_login_failed_at"] = created_at.isoformat()

    def _sort_key(x: dict):
        a = _parse_dt(x.get("last_login_at"))
        b = _parse_dt(x.get("last_login_failed_at"))
        return a or b or datetime.fromtimestamp(0, tz=timezone.utc)

    items = sorted(by_email.values(), key=_sort_key, reverse=True)
    return {
        "window_days": days,
        "items": items,
        "total_accounts_in_window": len(items),
    }


def _filter_rows_for_organization(rows: list, *, organization_id: str) -> list:
    member_emails = fetch_organization_member_emails(organization_id)
    org_id_str = str(organization_id)
    filtered = []
    for row in rows:
        details = row.details or {}
        email = str(details.get("user_email") or "").strip().lower()
        log_org = str(details.get("organization_id") or "").strip()
        if email and email in member_emails:
            filtered.append(row)
        elif log_org and log_org == org_id_str:
            filtered.append(row)
    return filtered


@router.get("/users")
def list_user_activity(
    _admin: Annotated[dict, Depends(require_admin_payload)],
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(5000, ge=1, le=20000),
    db: Session = Depends(get_log_db),
):
    """
    Devuelve un resumen por cuenta basado en eventos de login.
    Solo cuentas de la organización activa del administrador.
    """
    organization_id = tenant.organization_id
    admin_user_id = tenant.user_id or ""
    if not organization_id:
        raise HTTPException(status_code=400, detail="Organización activa no definida en la sesión")
    if not user_is_org_admin(user_id=admin_user_id, organization_id=organization_id):
        raise HTTPException(
            status_code=403,
            detail="No tienes permisos de administrador en esa organización",
        )
    try:
        init_log_tables()
    except Exception as exc:
        logger.warning("No se pudieron inicializar tablas de logs: %s", exc)

    since = datetime.now(timezone.utc) - timedelta(days=days)

    cache_key = account_activity_key(organization_id, days, limit)

    def loader():
        rows = (
            db.query(LoginLogDB)
            .filter(LoginLogDB.created_at >= since)
            .order_by(desc(LoginLogDB.created_at))
            .limit(limit)
            .all()
        )
        scoped_rows = _filter_rows_for_organization(rows, organization_id=organization_id)
        result = _aggregate_activity(scoped_rows, days=days)
        result["organization_id"] = organization_id
        return result

    try:
        return cache_aside(cache_key, TTL_ACCOUNT_ACTIVITY, loader)
    except OperationalError as exc:
        logger.error("Conexión a Supabase Postgres fallida: %s", exc)
        if is_ipv6_unreachable_error(exc):
            detail = (
                "Supabase Postgres no accesible por IPv6 desde Docker. "
                "Reinicia el backend (docker compose up --build -d backend) o usa SUPABASE_DB_POOLER_URL."
            )
        elif is_dns_resolution_error(exc):
            detail = (
                "No se pudo resolver el host de Supabase. "
                "Configura SUPABASE_DB_POOLER_URL (Session pooler en el panel de Supabase)."
            )
        elif is_ipv6_unreachable_error(exc) or "connection refused" in str(exc).lower():
            detail = (
                "Supabase Postgres no es accesible desde Docker con la URI directa (IPv6). "
                "Agrega SUPABASE_DB_POOLER_URL en .env (Session pooler del panel de Supabase) y reinicia el backend."
            )
        else:
            detail = (
                "No se pudo conectar a Supabase Postgres (logs). "
                "Verifica SUPABASE_DB_POOLER_URL o SUPABASE_DB_URL en .env."
            )
        raise HTTPException(status_code=503, detail=detail) from exc
    except ProgrammingError as exc:
        logger.error("Tablas de logs no encontradas: %s", exc)
        raise HTTPException(
            status_code=503,
            detail=(
                "Faltan las tablas de logs en Supabase. "
                "Ejecuta database/supabase/supabase_logs_schema.sql en el SQL Editor de Supabase."
            ),
        ) from exc
    except SQLAlchemyError as exc:
        logger.exception("Error consultando actividad de cuentas")
        if is_dns_resolution_error(exc):
            raise HTTPException(
                status_code=503,
                detail=(
                    "No se pudo resolver el host de Supabase desde el contenedor Docker. "
                    "Usa la URI del «Session pooler» en SUPABASE_DB_POOLER_URL (Supabase → Database)."
                ),
            ) from exc
        raise HTTPException(
            status_code=503,
            detail="Error al leer la actividad de cuentas en la base de datos de logs.",
        ) from exc
    except Exception as exc:
        logger.exception("Error inesperado en actividad de cuentas")
        if is_dns_resolution_error(exc):
            raise HTTPException(
                status_code=503,
                detail=(
                    "No se pudo conectar a Supabase Postgres (resolución DNS). "
                    "Configura SUPABASE_DB_POOLER_URL con el connection string del pooler."
                ),
            ) from exc
        raise HTTPException(
            status_code=503,
            detail=f"Error al cargar actividad: {type(exc).__name__}",
        ) from exc
