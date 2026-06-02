"""Resolución y comprobación de la URL de Postgres (Supabase) para logs."""
from __future__ import annotations

import os
import socket
from typing import Any, Optional
from urllib.parse import urlparse

from urllib.parse import unquote

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError


def _project_ref_from_direct_host(hostname: str) -> Optional[str]:
    if hostname.startswith("db.") and hostname.endswith(".supabase.co"):
        return hostname[3:-len(".supabase.co")]
    return None


def transform_direct_url_to_pooler(
    direct_url: str,
    region: str = "us-west-2",
    *,
    pooler_prefix: str = "aws-1",
) -> str:
    """
    Convierte URI directa (IPv6) a Session pooler (IPv4) para Docker.
    Usuario pooler: postgres.<project-ref>
    El prefijo suele ser aws-0 o aws-1 (copiar host del panel de Supabase si falla).
    """
    raw = direct_url.replace("postgresql+psycopg2://", "postgresql://")
    parsed = urlparse(raw)
    host = parsed.hostname or ""
    project_ref = _project_ref_from_direct_host(host)
    if not project_ref:
        return direct_url

    password = parsed.password or ""
    port = parsed.port or 5432
    dbname = (parsed.path or "/postgres").lstrip("/") or "postgres"
    prefix = (pooler_prefix or "aws-1").strip() or "aws-1"
    reg = (region or "us-west-2").strip()
    pooler_host = f"{prefix}-{reg}.pooler.supabase.com"
    user = f"postgres.{project_ref}"
    # Mantener codificación de la contraseña tal cual en la URL original
    return (
        f"postgresql+psycopg2://{user}:{password}@{pooler_host}:{port}/{dbname}"
    )


def resolve_supabase_db_url() -> str:
    """
    Orden de preferencia:
    1. SUPABASE_DB_POOLER_URL (recomendado en Docker Desktop / Windows)
    2. SUPABASE_DB_URL + SUPABASE_DB_USE_POOLER=1 → Session pooler (IPv4)
    3. SUPABASE_DB_URL directa
    """
    pooler = (os.getenv("SUPABASE_DB_POOLER_URL") or "").strip()
    direct = (os.getenv("SUPABASE_DB_URL") or "").strip()
    use_pooler = (os.getenv("SUPABASE_DB_USE_POOLER") or "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )
    region = (os.getenv("SUPABASE_DB_POOLER_REGION") or "us-west-2").strip()
    pooler_prefix = (os.getenv("SUPABASE_DB_POOLER_PREFIX") or "aws-1").strip()

    if pooler:
        return pooler
    if use_pooler and direct and "pooler.supabase.com" not in direct:
        return transform_direct_url_to_pooler(
            direct, region=region, pooler_prefix=pooler_prefix
        )
    return direct


def db_host_from_url(url: str) -> Optional[str]:
    if not url:
        return None
    try:
        return urlparse(url).hostname
    except Exception:
        return None


def resolve_ipv4_hostaddr(hostname: str) -> Optional[str]:
    """Fuerza IPv4 (Docker Desktop suele fallar con IPv6 «Network is unreachable»)."""
    if not hostname:
        return None
    try:
        infos = socket.getaddrinfo(hostname, 5432, socket.AF_INET, socket.SOCK_STREAM)
        return infos[0][4][0]
    except OSError:
        return None


def preferred_hostaddr(hostname: Optional[str]) -> Optional[str]:
    override = (os.getenv("SUPABASE_DB_HOSTADDR") or "").strip()
    if override:
        return override
    if hostname:
        return resolve_ipv4_hostaddr(hostname)
    return None


def build_pg_connect_args(hostname: Optional[str]) -> dict[str, Any]:
    args: dict[str, Any] = {"sslmode": "require"}
    ipv4 = preferred_hostaddr(hostname)
    if ipv4:
        args["hostaddr"] = ipv4
    return args


def make_psycopg2_creator(db_url: str):
    """Conexión explícita para evitar IPv6 inalcanzable en Docker Desktop."""
    import psycopg2

    raw = db_url.replace("postgresql+psycopg2://", "postgresql://")
    parsed = urlparse(raw)
    host = parsed.hostname or ""
    port = parsed.port or 5432
    user = parsed.username or "postgres"
    password = unquote(parsed.password or "")
    dbname = (parsed.path or "/postgres").lstrip("/") or "postgres"
    hostaddr = preferred_hostaddr(host)

    def _creator():
        kwargs: dict[str, Any] = {
            "host": host,
            "port": port,
            "user": user,
            "password": password,
            "dbname": dbname,
            "sslmode": "require",
        }
        if hostaddr:
            kwargs["hostaddr"] = hostaddr
        return psycopg2.connect(**kwargs)

    return _creator


def is_ipv6_unreachable_error(exc: BaseException) -> bool:
    text_err = str(exc).lower()
    if "network is unreachable" in text_err and ":" in text_err:
        return True
    cause = getattr(exc, "__cause__", None)
    if cause is not None and cause is not exc:
        return is_ipv6_unreachable_error(cause)
    return False


def is_dns_resolution_error(exc: BaseException) -> bool:
    text_err = str(exc).lower()
    if "could not translate host name" in text_err:
        return True
    if "name or service not known" in text_err:
        return True
    if "temporary failure in name resolution" in text_err:
        return True
    cause = getattr(exc, "__cause__", None)
    if cause is not None and cause is not exc:
        return is_dns_resolution_error(cause)
    return False


def check_logs_db(engine: Optional[Engine]) -> dict:
    """Prueba conexión a Postgres de logs (sin auth)."""
    url = resolve_supabase_db_url()
    host = db_host_from_url(url)
    if not url:
        return {
            "configured": False,
            "connected": False,
            "host": None,
            "hint": "Define SUPABASE_DB_URL o SUPABASE_DB_POOLER_URL en el .env de la raíz.",
        }
    if engine is None:
        return {
            "configured": True,
            "connected": False,
            "host": host,
            "hint": "Motor SQLAlchemy no inicializado (revisa la URL).",
        }
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {
            "configured": True,
            "connected": True,
            "host": host,
            "hint": None,
        }
    except SQLAlchemyError as exc:
        hint = None
        if is_ipv6_unreachable_error(exc):
            hint = (
                "El contenedor no tiene ruta IPv6 hacia Supabase. Reinicia el backend tras el último build "
                "(usa hostaddr IPv4) o define SUPABASE_DB_POOLER_URL desde Supabase → Session pooler."
            )
        elif is_dns_resolution_error(exc):
            hint = (
                "Docker no resuelve el host de Supabase. En Supabase → Database → Connection string "
                "elige «Session pooler» y pon esa URI en SUPABASE_DB_POOLER_URL."
            )
        elif "login_logs" in str(exc).lower() or "does not exist" in str(exc).lower():
            hint = "Ejecuta database/supabase/supabase_logs_schema.sql en el SQL Editor de Supabase."
        return {
            "configured": True,
            "connected": False,
            "host": host,
            "error": str(exc)[:500],
            "hint": hint or "Revisa credenciales, SSL y que el proyecto Supabase esté activo.",
        }
