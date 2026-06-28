"""Caché Redis con patrón cache-aside, TTL e invalidación automática."""
from __future__ import annotations

import json
import logging
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)

_client: Any = None
_enabled = False

# TTL en segundos
TTL_DASHBOARD = 20
TTL_SENSOR_LATEST = 15
TTL_SENSOR_HISTORY = 45
TTL_SENSOR_HISTORY_SHORT = 30
TTL_DEVICES_LIST = 60
TTL_HISTORICAL_TABLE = 30
TTL_ORG_USERS = 90
TTL_ACCOUNT_ACTIVITY = 45
TTL_WEATHER = 600


def init_redis(url: str | None) -> None:
    """Conecta a Redis; si falla, la app sigue sin caché."""
    global _client, _enabled
    if not url or not str(url).strip():
        logger.info("Redis no configurado (REDIS_URL vacío); caché deshabilitada")
        return
    try:
        import redis

        _client = redis.from_url(
            str(url).strip(),
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        _client.ping()
        _enabled = True
        logger.info("Redis conectado correctamente")
    except Exception as exc:
        logger.warning("Redis no disponible, caché deshabilitada: %s", exc)
        _client = None
        _enabled = False


def close_redis() -> None:
    global _client, _enabled
    if _client is not None:
        try:
            _client.close()
        except Exception:
            pass
    _client = None
    _enabled = False


def is_enabled() -> bool:
    return _enabled and _client is not None


def _tenant_scope(org_id: str | None, org_slug: str | None = None) -> str:
    return str(org_id or org_slug or "default")


def dashboard_key(org_id: str | None, org_slug: str | None, arduino_id: str | None) -> str:
    scope = _tenant_scope(org_id, org_slug)
    device = arduino_id or "all"
    return f"dashboard:{scope}:{device}"


def sensor_latest_key(org_id: str | None, org_slug: str | None, arduino_id: str | None) -> str:
    scope = _tenant_scope(org_id, org_slug)
    device = arduino_id or "all"
    return f"sensor:latest:{scope}:{device}"


def sensor_history_key(
    org_id: str | None,
    org_slug: str | None,
    *,
    arduino_id: str | None,
    since: str | None,
    until: str | None,
    days: int | None,
    limit: int,
) -> str:
    scope = _tenant_scope(org_id, org_slug)
    device = arduino_id or "all"
    since_part = since or "none"
    until_part = until or "none"
    days_part = str(days) if days is not None else "none"
    return f"sensor:history:{scope}:{device}:{since_part}:{until_part}:{days_part}:{limit}"


def devices_list_key(org_id: str | None, org_slug: str | None, active_only: bool) -> str:
    scope = _tenant_scope(org_id, org_slug)
    return f"devices:list:{scope}:active-{int(active_only)}"


def historical_table_key(
    org_id: str | None,
    org_slug: str | None,
    *,
    page: int,
    page_size: int,
    sensor: str,
    date_from: str | None,
    date_to: str | None,
    live: bool,
    since: str | None,
) -> str:
    scope = _tenant_scope(org_id, org_slug)
    return (
        f"sensor:table:{scope}:p{page}:s{page_size}:f{sensor}:"
        f"{date_from or 'none'}:{date_to or 'none'}:live-{int(live)}:{since or 'none'}"
    )


def org_users_key(org_id: str) -> str:
    return f"admin:org-users:{org_id}"


def account_activity_key(org_id: str, days: int, limit: int) -> str:
    return f"admin:activity:{org_id}:d{days}:l{limit}"


def weather_city_key(city: str) -> str:
    return f"weather:city:{city.strip().lower()}"


def weather_device_key(org_id: str | None, org_slug: str | None, device_id: str) -> str:
    scope = _tenant_scope(org_id, org_slug)
    return f"weather:device:{scope}:{device_id}"


def cache_get(key: str) -> Any | None:
    if not is_enabled():
        return None
    try:
        raw = _client.get(key)
        if raw is None:
            return None
        return json.loads(raw)
    except Exception as exc:
        logger.warning("Redis GET falló (%s): %s", key, exc)
        return None


def cache_set(key: str, value: Any, ttl: int) -> None:
    if not is_enabled() or value is None:
        return
    try:
        _client.setex(key, max(1, ttl), json.dumps(value, default=str))
    except Exception as exc:
        logger.warning("Redis SET falló (%s): %s", key, exc)


def cache_aside(key: str, ttl: int, loader: Callable[[], Any]) -> Any:
    """Cache-aside: lee de Redis; si no hay hit, ejecuta loader y guarda."""
    cached = cache_get(key)
    if cached is not None:
        return cached
    result = loader()
    if result is not None:
        cache_set(key, result, ttl)
    return result


def invalidate_pattern(pattern: str) -> None:
    if not is_enabled():
        return
    try:
        keys = list(_client.scan_iter(match=pattern, count=200))
        if keys:
            _client.delete(*keys)
    except Exception as exc:
        logger.warning("Redis invalidación falló (%s): %s", pattern, exc)


def invalidate_sensor_readings(
    org_id: str | None,
    org_slug: str | None = None,
    arduino_id: str | None = None,
) -> None:
    """Invalida caché de dashboard e historial tras nueva lectura."""
    scope = _tenant_scope(org_id, org_slug)
    if arduino_id:
        invalidate_pattern(f"dashboard:{scope}:{arduino_id}")
        invalidate_pattern(f"sensor:*:{scope}:{arduino_id}*")
        invalidate_pattern(f"sensor:*:{scope}:all*")
    else:
        invalidate_pattern(f"dashboard:{scope}:*")
        invalidate_pattern(f"sensor:*:{scope}:*")
    invalidate_pattern(f"sensor:table:{scope}:*")


def invalidate_devices(org_id: str | None, org_slug: str | None = None) -> None:
    scope = _tenant_scope(org_id, org_slug)
    invalidate_pattern(f"devices:list:{scope}:*")


def invalidate_organization_users(org_id: str | None) -> None:
    if not org_id:
        invalidate_pattern("admin:org-users:*")
        return
    invalidate_pattern(f"admin:org-users:{org_id}")


def invalidate_account_activity(org_id: str | None = None) -> None:
    if org_id:
        invalidate_pattern(f"admin:activity:{org_id}:*")
    else:
        invalidate_pattern("admin:activity:*")


def invalidate_weather_city(city: str | None) -> None:
    if not city or not str(city).strip():
        return
    invalidate_pattern(f"weather:city:{str(city).strip().lower()}")


def invalidate_weather_device(
    org_id: str | None,
    org_slug: str | None = None,
    device_id: str | None = None,
) -> None:
    scope = _tenant_scope(org_id, org_slug)
    if device_id:
        invalidate_pattern(f"weather:device:{scope}:{device_id}")
    else:
        invalidate_pattern(f"weather:device:{scope}:*")
