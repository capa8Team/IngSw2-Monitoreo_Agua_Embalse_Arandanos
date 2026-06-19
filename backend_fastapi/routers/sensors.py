import logging
from datetime import date, datetime, timedelta, timezone
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query

from core.tenant import TenantContext, ensure_device_in_tenant, get_tenant_context
from models import HistoricalTableResponse, SensorDataResponse
from services.historical_table import get_historical_table_page
from services.mongodb import (
    HISTORICAL_MAX_LIMIT,
    find_device_by_key,
    get_latest_sensor_reading,
    query_sensor_readings,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sensors", tags=["Sensores"])

# Ingesta de lecturas: AWS IoT Core (MQTT, topic boya/sensores) → MongoDB.
# Este router expone consultas acotadas para dashboard e histórico (scope por organización).


def _validate_arduino_for_tenant(arduino_id: str | None, tenant: TenantContext) -> None:
    if not arduino_id:
        return
    device = find_device_by_key(arduino_id)
    if not device:
        raise HTTPException(status_code=403, detail="Dispositivo fuera de tu organización")
    ensure_device_in_tenant(device, tenant)


def _tenant_filters(tenant: TenantContext) -> tuple[dict, dict]:
    return tenant.device_filter(), tenant.readings_filter()


@router.get("/latest", response_model=SensorDataResponse | None)
def get_latest_reading(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    arduino_id: str | None = Query(default=None),
):
    """Última lectura almacenada del tenant (origen MQTT / MongoDB)."""
    _validate_arduino_for_tenant(arduino_id, tenant)
    _, readings_filter = _tenant_filters(tenant)
    reading = get_latest_sensor_reading(arduino_id, tenant_filter=readings_filter)
    return SensorDataResponse(**reading) if reading else None


@router.get("/history", response_model=list[SensorDataResponse])
def get_readings_history(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    limit: int = Query(default=100, ge=1, le=HISTORICAL_MAX_LIMIT),
    arduino_id: str | None = Query(default=None),
):
    """Historial reciente del tenant (compatibilidad con clientes anteriores)."""
    _validate_arduino_for_tenant(arduino_id, tenant)
    _, readings_filter = _tenant_filters(tenant)
    readings = query_sensor_readings(
        limit=limit,
        arduino_id=arduino_id,
        tenant_filter=readings_filter,
    )
    return [SensorDataResponse(**r) for r in readings]


@router.get("/history/range", response_model=list[SensorDataResponse])
def get_readings_in_range(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    since: datetime | None = Query(default=None, description="Inicio del rango (ISO 8601, UTC)"),
    until: datetime | None = Query(default=None, description="Fin del rango (ISO 8601, UTC)"),
    days: int | None = Query(default=None, ge=1, le=30, description="Alternativa: últimos N días"),
    arduino_id: str | None = Query(default=None),
    limit: int = Query(default=500, ge=1, le=HISTORICAL_MAX_LIMIT),
):
    """Lecturas acotadas por rango temporal para gráficos históricos del tenant."""
    _validate_arduino_for_tenant(arduino_id, tenant)
    effective_since = since
    if effective_since is None and days is not None:
        effective_since = datetime.now(timezone.utc) - timedelta(days=days)
    if effective_since is None:
        effective_since = datetime.now(timezone.utc) - timedelta(days=7)

    _, readings_filter = _tenant_filters(tenant)
    readings = query_sensor_readings(
        since=effective_since,
        until=until,
        arduino_id=arduino_id,
        limit=limit,
        tenant_filter=readings_filter,
    )
    return [SensorDataResponse(**r) for r in readings]


@router.get("/history/table", response_model=HistoricalTableResponse)
def get_historical_table(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    sensor: Literal["all", "ph", "temperature", "conductivity"] = Query(default="all"),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    live: bool = Query(
        default=False,
        description="Solo lecturas recientes (más rápido; ideal para actualización en vivo)",
    ),
    since: datetime | None = Query(
        default=None,
        description="Solo lecturas con timestamp >= since (ISO 8601, UTC)",
    ),
):
    """Filas paginadas para la tabla de mediciones históricas del tenant."""
    org_filter, readings_filter = _tenant_filters(tenant)
    payload = get_historical_table_page(
        page=page,
        page_size=page_size,
        sensor=sensor,
        date_from=date_from,
        date_to=date_to,
        live=live,
        since=since,
        org_filter=org_filter,
        readings_filter=readings_filter,
    )
    return HistoricalTableResponse(**payload)
