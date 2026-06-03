import logging
from fastapi import APIRouter, HTTPException, Query

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
def list_devices(active_only: bool = Query(True, description="Mostrar solo dispositivos activos")):
    """
    Obtiene la lista de todos los dispositivos registrados.
    
    - **active_only**: Si es True, solo devuelve dispositivos activos
    """
    devices = get_all_devices(active_only=active_only)
    
    if not devices:
        log_service.log(
            LogOrigin.DASHBOARD, LogLevel.INFO, "Lista de dispositivos solicitada (vacía)",
            component="api.devices", operation="list"
        )
        return []
    
    return [DeviceResponse(**device) for device in devices]


@router.post("", response_model=DeviceResponse, status_code=201)
async def create_new_device(payload: DeviceCreate) -> DeviceResponse:
    """
    Crea un nuevo dispositivo/microcontrolador.
    
    Parámetros:
    - **name**: Nombre del dispositivo (requerido)
    - **device_type**: Tipo de microcontrolador (ESP8266, Arduino, STM32, other)
    - **location**: Ubicación o zona del dispositivo
    - **city**: Ciudad donde está ubicado (para datos de clima)
    - **arduino_id**: ID del Arduino (opcional, puede ser auto-detectado)
    """
    device = create_device(
        name=payload.name,
        device_type=payload.device_type,
        location=payload.location,
        city=payload.city,
        arduino_id=payload.arduino_id,
        topic=payload.topic,
        telemetry_key=payload.telemetry_key,
    )
    
    if not device:
        raise HTTPException(status_code=500, detail="Error creando dispositivo")
    
    log_service.log(
        LogOrigin.DASHBOARD, LogLevel.INFO,
        f"Nuevo dispositivo creado: {payload.name}",
        component="api.devices", operation="create",
        details={"device_type": payload.device_type, "location": payload.location, "city": payload.city}
    )
    
    return DeviceResponse(**device)


@router.post("/detect", response_model=DeviceResponse, status_code=201)
async def detect_microcontroller(payload: DeviceDetectionPayload) -> DeviceResponse:
    """
    Detecta y registra un nuevo microcontrolador automáticamente.

    Este endpoint se llama cuando el frontend detecta un nuevo dispositivo.

    Parámetros:
    - **arduino_id**: ID del Arduino detectado (requerido)
    - **device_name**: Nombre personalizado del dispositivo (opcional)
    - **device_type**: Tipo de microcontrolador (ESP8266, Arduino, STM32, other)
    - **location**: Ubicación del dispositivo (opcional)
    """
    # Verificar si ya existe
    existing = get_device_by_arduino_id(payload.arduino_id)
    if existing:
        log_service.log(
            LogOrigin.DASHBOARD, LogLevel.WARN,
            f"Intento de registrar microcontrolador duplicado: {payload.arduino_id}",
            component="api.devices", operation="detect"
        )
        return DeviceResponse(**existing)

    # Registrar nuevo
    device = register_new_microcontroller(
        arduino_id=payload.arduino_id,
        device_name=payload.device_name,
        device_type=payload.device_type,
        location=payload.location or ""
    )

    if not device:
        raise HTTPException(status_code=500, detail="Error detectando microcontrolador")

    log_service.log(
        LogOrigin.DASHBOARD, LogLevel.INFO,
        f"Nuevo microcontrolador detectado: {payload.arduino_id}",
        component="api.devices", operation="detect",
        details={"device_type": payload.device_type}
    )

    return DeviceResponse(**device)


@router.get("/detect-available")
async def get_available_microcontrollers():
    """
    Obtiene la lista de microcontroladores disponibles para registrar.
    (Basado en los Arduino IDs detectados en las lecturas de sensores)
    """
    from services.mongodb import db

    if db is None:
        return {"available": [], "total": 0}

    try:
        # Obtener todos los arduino_id únicos de sensor_readings
        sensor_collection = db["sensor_readings"]
        available = sensor_collection.distinct("arduino_id")

        # Solo dispositivos activos cuentan como registrados
        device_collection = db["devices"]
        registered_keys: set[str] = set()
        for doc in device_collection.find(
            {"active": {"$ne": False}},
            {"arduino_id": 1, "name": 1, "telemetry_key": 1, "topic": 1},
        ):
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
def get_device_info(device_id: str) -> DeviceResponse:
    """
    Obtiene la información de un dispositivo específico.
    """
    device = get_device(device_id)
    
    if not device:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")
    
    return DeviceResponse(**device)


@router.put("/{device_id}", response_model=DeviceResponse)
async def update_device_info(device_id: str, payload: DeviceUpdate) -> DeviceResponse:
    """
    Actualiza la información de un dispositivo.
    """
    device = update_device(
        device_id=device_id,
        name=payload.name,
        location=payload.location,
        city=payload.city,
        active=payload.active,
        arduino_id=payload.arduino_id,
        telemetry_key=payload.telemetry_key,
        topic=payload.topic,
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
async def delete_device_endpoint(device_id: str):
    """
    Elimina (desactiva) un dispositivo.
    """
    success = delete_device(device_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")
    
    log_service.log(
        LogOrigin.DASHBOARD, LogLevel.INFO,
        f"Dispositivo eliminado: {device_id}",
        component="api.devices", operation="delete"
    )


@router.post("/{device_id}/status")
async def update_device_connection_status(device_id: str, status: str = "online", battery: int | None = None):
    """
    Actualiza el estado de conexión de un dispositivo.
    
    Parámetros:
    - **status**: Estado del dispositivo (online, offline, unknown)
    - **battery**: Porcentaje de batería (0-100)
    """
    device = get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")
    
    # Usar arduino_id para actualizar estado
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
async def get_device_weather(device_id: str):
    """
    Obtiene el clima actual del lugar donde está ubicado el dispositivo.
    
    Usa la ciudad configurada en el dispositivo para obtener datos de OpenWeather.
    """
    device = get_device(device_id)
    
    if not device:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")
    
    city = device.get("city")
    if not city:
        raise HTTPException(
            status_code=400,
            detail="El dispositivo no tiene ciudad configurada. Agregue una ciudad en la configuración."
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
async def get_weather_by_city(city: str):
    """
    Obtiene el clima actual para una ciudad específica desde OpenWeather.
    
    Parámetros:
    - **city**: Nombre de la ciudad (ej: Madrid, Buenos Aires)
    """
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
