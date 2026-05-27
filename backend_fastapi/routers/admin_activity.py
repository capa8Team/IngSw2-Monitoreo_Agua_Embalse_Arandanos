from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from db.database import SessionLocal
from db.log_models import LoginLogDB
from routers.auth_jwt import require_admin_payload

router = APIRouter(prefix="/api/admin/activity", tags=["Admin Activity"])


def get_log_db():
    if SessionLocal is None:
        raise HTTPException(503, "SUPABASE_DB_URL no configurada para logs")
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


@router.get("/users")
def list_user_activity(
    _admin: Annotated[dict, Depends(require_admin_payload)],
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(5000, ge=1, le=20000),
    db: Session = Depends(get_log_db),
):
    """
    Devuelve un resumen por cuenta basado en eventos de login.
    Requiere rol administrador.
    """
    since = datetime.now(timezone.utc) - timedelta(days=days)

    rows = (
        db.query(LoginLogDB)
        .filter(LoginLogDB.created_at >= since)
        .order_by(desc(LoginLogDB.created_at))
        .limit(limit)
        .all()
    )

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
            # Como iteramos desde más nuevo → más viejo, el primero fija el "último"
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

    # Orden: más recientemente activo primero (por last_login_at; si no, por last_login_failed_at)
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

