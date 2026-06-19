import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from core.tenant import TenantContext, ensure_device_in_tenant, get_tenant_context
from models import DeviceCreate, DeviceResponse, DeviceUpdate, DeviceDetectionPayload
from services.mongodb import (
    create_device, get_device, get_all_devices, update_device,
    delete_device, register_new_microcontroller, get_device_by_arduino_id,
    update_device_status
)
from services.openweather import get_weather_data
from core.log_service import log_service
from core.log_origins import LogLevel, LogOrigin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/devices", tags=["Dispositivos"])


@router.get("", response_model=list[DeviceResponse])
def list_devices(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    active_only: bool = Query(True, description="Mostrar solo dispositivos activos"),
):
    """
    Obtiene la lista de dispositivos registrados, filtrados por organización activa.
    """
    devices = get_all_devices(active_only=active_only, org_filter=tenant.device_filter())
    
    if not devices:
        log_service.log(
            LogOrigin.DASHBOARD, LogLevel.INFO, "Lista de dispositivos solicitada (vacía)",
            component="api.devices", operation="list"
        )
        return []
    
    return [DeviceResponse(**device) for device in devices]


@router.post("", response_model=DeviceResponse, status_code=201)
async def create_new_device(
    payload: DeviceCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
) -> DeviceResponse:
    """Crea un nuevo dispositivo asociado a la organización activa."""
    device = create_device(
        name=payload.name,
        device_type=payload.device_type,
        location=payload.location,
        city=payload.city,
        arduino_id=payload.arduino_id,
        topic=payload.topic,
        telemetry_key=payload.telemetry_key,
        organization_id=tenant.organization_id,
        organization_slug=tenant.organization_slug,
        group_id=payload.group_id,
        latitude=payload.latitude,
        longitude=payload.longitude,
    )
    
    if not device:
        raise HTTPException(status_code=500, detail="Error creando dispositivo")
    
    log_service.log(
        LogOrigin.DASHBOARD, LogLevel.INFO,
        f"Nuevo dispositivo creado: {payload.name}",
        component="api.devices", operation="create",
        details={
            "device_type": payload.device_type,
            "location": payload.location,
            "city": payload.city,
            "organization_id": tenant.organization_id,
        }
    )
    
    return DeviceResponse(**device)


@router.post("/detect", response_model=DeviceResponse, status_code=201)
async def detect_microcontroller(
    payload: DeviceDetectionPayload,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
) -> DeviceResponse:
    """Detecta y registra un microcontrolador en la organización activa."""
    existing = get_device_by_arduino_id(payload.arduino_id)
    if existing:
        ensure_device_in_tenant(existing, tenant)
        log_service.log(
            LogOrigin.DASHBOARD, LogLevel.WARN,
            f"Intento de registrar microcontrolador duplicado: {payload.arduino_id}",
            component="api.devices", operation="detect"
        )
        return DeviceResponse(**existing)

    device = register_new_microcontroller(
        arduino_id=payload.arduino_id,
        device_name=payload.device_name,
        device_type=payload.device_type,
        location=payload.location or "",
        organization_id=tenant.organization_id,
        organization_slug=tenant.organization_slug,
    )

    if not device:
        raise HTTPException(status_code=500, detail="Error detectando microcontrolador")

    log_service.log(
        LogOrigin.DASHBOARD, LogLevel.INFO,
        f"Nuevo microcontrolador detectado: {payload.arduino_id}",
        component="api.devices", operation="detect",
        details={"device_type": payload.device_type, "organization_id": tenant.organization_id}
    )

    return DeviceResponse(**device)


@router.get("/detect-available")
async def get_available_microcontrollers(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
):
    """Microcontroladores disponibles para registrar en la organización activa."""
    from services.mongodb import db

    if db is None:
        return {"available": [], "total": 0}

    try:
        sensor_collection = db["sensor_readings"]
        readings_filter = tenant.readings_filter()
        available = sensor_collection.distinct("arduino_id", readings_filter)

        org_devices = get_all_devices(active_only=True, org_filter=tenant.device_filter())
        registered_keys: set[str] = set()
        for doc in org_devices:
            for field in ("arduino_id", "name", "telemetry_key"):
                if doc.get(field):
                    registered_keys.add(doc[field])

        new_ids = [aid for aid in available if aid and aid not in registered_keys]

        return {
            "available": new_ids,
            "total": len(new_ids),
            "already_registered": sorted(registered_keys),
            "message": f"{len(new_ids)} microcontrolador(es) disponible(s) para registrar"
        }
    except Exception as e:
        logger.error("Error obteniendo microcontroladores disponibles: %s", e)
        return {"available": [], "total": 0, "error": str(e)}


@router.get("/{device_id}", response_model=DeviceResponse)
def get_device_info(
    device_id: str,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
) -> DeviceResponse:
    """Obtiene la información de un dispositivo de la organización activa."""
    device = get_device(device_id)
    ensure_device_in_tenant(device, tenant)
    return DeviceResponse(**device)


@router.put("/{device_id}", response_model=DeviceResponse)
async def update_device_info(
    device_id: str,
    payload: DeviceUpdate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
) -> DeviceResponse:
    """Actualiza un dispositivo de la organización activa."""
    existing = get_device(device_id)
    ensure_device_in_tenant(existing, tenant)

    unset_group = payload.group_id == ""

    device = update_device(
        device_id=device_id,
        name=payload.name,
        location=payload.location,
        city=payload.city,
        active=payload.active,
        arduino_id=payload.arduino_id,
        telemetry_key=payload.telemetry_key,
        topic=payload.topic,
        group_id=payload.group_id if not unset_group else None,
        latitude=payload.latitude,
        longitude=payload.longitude,
        unset_group=unset_group,
    )
    
    if not device:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")
    
    log_service.log(
        LogOrigin.DASHBOARD, LogLevel.INFO,
        f"Dispositivo actualizado: {device_id}",
        component="api.devices", operation="update"
    )
    
    return DeviceResponse(**device)


@router.delete("/{device_id}", status_code=204)
async def delete_device_endpoint(
    device_id: str,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
):
    """Elimina (desactiva) un dispositivo de la organización activa."""
    existing = get_device(device_id)
    ensure_device_in_tenant(existing, tenant)

    success = delete_device(device_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")
    
    log_service.log(
        LogOrigin.DASHBOARD, LogLevel.INFO,
        f"Dispositivo eliminado: {device_id}",
        component="api.devices", operation="delete"
    )


@router.post("/{device_id}/status")
async def update_device_connection_status(
    device_id: str,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    status: str = Query("online"),
    battery: int | None = Query(None),
):
    """Actualiza el estado de conexión de un dispositivo."""
    device = get_device(device_id)
    ensure_device_in_tenant(device, tenant)
    
    if device.get("arduino_id"):
        device = update_device_status(
            arduino_id=device["arduino_id"],
            status=status,
            battery=battery
        )
    
    if not device:
        raise HTTPException(status_code=500, detail="Error actualizando estado")
    
    return DeviceResponse(**device)


@router.get("/{device_id}/weather")
async def get_device_weather(
    device_id: str,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
):
    """Obtiene el clima del dispositivo (organización activa)."""
    device = get_device(device_id)
    ensure_device_in_tenant(device, tenant)
    
    city = (device.get("city") or device.get("location") or "").strip()
    if not city:
        raise HTTPException(
            status_code=400,
            detail="El dispositivo no tiene ciudad configurada. Agregue una ciudad en la sección de clima."
        )
    
    weather_data = get_weather_data(city)
    
    if not weather_data:
        raise HTTPException(
            status_code=500,
            detail=f"No se pudo obtener datos de clima para la ciudad: {city}"
        )
    
    logger.info(f"Datos de clima obtenidos para dispositivo {device_id} (ciudad: {city})")
    
    return {
        "device_id": device_id,
        "device_name": device.get("name"),
        "city": city,
        "weather": weather_data
    }


@router.get("/weather/{city}")
async def get_weather_by_city(
    city: str,
    _tenant: Annotated[TenantContext, Depends(get_tenant_context)],
):
    """Obtiene el clima actual para una ciudad específica desde OpenWeather."""
    if not city or not city.strip():
        raise HTTPException(status_code=400, detail="Nombre de ciudad no válido")
    
    weather_data = get_weather_data(city)
    
    if not weather_data:
        raise HTTPException(
            status_code=404,
            detail=f"No se pudo obtener datos de clima para la ciudad: {city}. Verifique el nombre y que OpenWeather esté configurado."
        )
    
    logger.info(f"Datos de clima obtenidos para la ciudad: {city}")
    
    return {
        "city": city,
        "weather": weather_data
    }
