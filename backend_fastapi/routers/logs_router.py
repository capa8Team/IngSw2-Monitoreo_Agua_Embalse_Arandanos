"""Consulta y exportación de logs en Supabase."""
import csv
import io
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import desc
from sqlalchemy.orm import Session

from core.log_origins import VALID_ORIGINS
from db.database import SessionLocal
from db.log_models import LOG_MODEL_BY_TABLE

router = APIRouter(prefix="/api/logs", tags=["Logs"])


def get_log_db():
    if SessionLocal is None:
        raise HTTPException(503, "SUPABASE_DB_URL no configurada para logs")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _row_to_dict(row: Any) -> dict:
    out = {}
    for col in row.__table__.columns:
        val = getattr(row, col.name)
        if isinstance(val, datetime):
            out[col.name] = val.isoformat()
        elif hasattr(val, "hex"):
            out[col.name] = str(val)
        else:
            out[col.name] = val
    return out


@router.get("/origins")
def list_origins():
    return {"origins": sorted(VALID_ORIGINS)}


@router.get("/{origin}/export")
def export_logs(
    origin: str,
    format: str = Query("txt", pattern="^(syslog|csv|txt)$"),
    level: Optional[str] = None,
    correlation_id: Optional[str] = None,
    limit: int = Query(500, ge=1, le=5000),
    db: Session = Depends(get_log_db),
):
    if origin not in VALID_ORIGINS:
        raise HTTPException(404, f"Origen desconocido: {origin}")
    model = LOG_MODEL_BY_TABLE[origin]
    q = db.query(model)
    if level:
        q = q.filter(model.level == level.upper())
    if correlation_id:
        q = q.filter(model.correlation_id == correlation_id)
    rows = q.order_by(desc(model.created_at)).limit(limit).all()
    items = [_row_to_dict(r) for r in rows]

    if format == "csv":
        buf = io.StringIO()
        if items:
            w = csv.DictWriter(buf, fieldnames=items[0].keys())
            w.writeheader()
            w.writerows(items)
        content, media, name = buf.getvalue(), "text/csv", f"{origin}.csv"
    elif format == "syslog":
        lines = [
            f"{i.get('created_at')} riego-backend riego[{i.get('level')}]: "
            f"component={i.get('component')} correlation_id={i.get('correlation_id')} {i.get('message')}"
            for i in items
        ]
        content, media, name = "\n".join(lines), "text/plain", f"{origin}.syslog"
    else:
        lines = [
            f"[{i.get('created_at')}] {i.get('level')} {i.get('component')} | {i.get('message')} | {i.get('details')}"
            for i in items
        ]
        content, media, name = "\n".join(lines), "text/plain", f"{origin}.txt"

    return Response(content, media_type=media, headers={"Content-Disposition": f'attachment; filename="{name}"'})


@router.get("/{origin}")
def query_logs(
    origin: str,
    level: Optional[str] = None,
    component: Optional[str] = None,
    correlation_id: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_log_db),
):
    if origin not in VALID_ORIGINS:
        raise HTTPException(404, f"Origen desconocido: {origin}")
    model = LOG_MODEL_BY_TABLE[origin]
    q = db.query(model)
    if level:
        q = q.filter(model.level == level.upper())
    if component:
        q = q.filter(model.component.ilike(f"%{component}%"))
    if correlation_id:
        q = q.filter(model.correlation_id == correlation_id)
    total = q.count()
    rows = q.order_by(desc(model.created_at)).offset(offset).limit(limit).all()
    return {"origin": origin, "total": total, "items": [_row_to_dict(r) for r in rows]}
