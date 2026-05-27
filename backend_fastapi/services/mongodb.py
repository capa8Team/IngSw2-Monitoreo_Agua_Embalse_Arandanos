import logging
from datetime import datetime, timezone
from typing import Optional
from zoneinfo import ZoneInfo

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

from core.config import settings
from core.log_service import log_service
from core.log_origins import LogLevel, LogOrigin
from models import (
    SensorMongoPayload, SensorMeasurements, SensorReading,
    SensorPhPostReading, DashboardResponse, Metadata, SensorData
)

logger = logging.getLogger(__name__)

CHILE_TZ = ZoneInfo("America/Santiago")

# ============================================================================
# ESTADO GLOBAL Y MEMORIA
# ============================================================================
dashboard_state: Optional[DashboardResponse] = None
simulated_data_store: list[dict] = []

# ============================================================================
# UTILIDADES DE TIEMPO
# ============================================================================
def utc_now() -> datetime:
    return datetime.now(timezone.utc)

def chile_now() -> datetime:
    return utc_now().astimezone(CHILE_TZ)

def to_chile_time(value: datetime | None) -> datetime:
    if not isinstance(value, datetime):
        return chile_now()
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(CHILE_TZ)

def epoch_to_utc_datetime(epoch: int) -> datetime:
    seconds = epoch / 1000 if epoch > 10_000_000_000 else epoch
    return datetime.fromtimestamp(seconds, tz=timezone.utc)

# ============================================================================
# CONEXIÓN MONGODB (contenedor Docker o instancia local)
# ============================================================================
db = None
mongo_client: MongoClient | None = None

try:
    mongo_client = MongoClient(
        settings.MONGODB_URL,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000,
        socketTimeoutMS=5000,
    )
    mongo_client.admin.command("ping")
    db = mongo_client[settings.MONGODB_DB]
    logger.info("Conexión a MongoDB establecida (%s)", settings.MONGODB_DB)
    log_service.log_db(
        LogLevel.INFO, "Conexión a MongoDB establecida",
        component="mongo.client", operation="connect", query_type="read",
        table_name="sensor_readings",
    )
except (ConnectionFailure, Exception) as e:
    logger.error("MongoDB no disponible. Fallback a memoria. Error: %s", e)
    log_service.log_db(
        LogLevel.FATAL, f"MongoDB no disponible: {e}",
        component="mongo.client", operation="connect", query_type="read",
        details={"error_type": type(e).__name__},
    )
    mongo_client = None
    db = None

# ============================================================================
# LÓGICA DE NEGOCIO Y BASE DE DATOS
# ============================================================================
def _resolve_sensor_timestamp(timestamp: int | None) -> tuple[datetime, int | None]:
    if timestamp is None:
        return utc_now(), None
    if timestamp >= 1_500_000_000:
        return epoch_to_utc_datetime(timestamp), None
    return utc_now(), timestamp

def save_sensor_payload_to_mongodb(payload: SensorMongoPayload, source: str = "api") -> Optional[str]:
    if db is None:
        logger.warning("MongoDB no está disponible")
        return None
    try:
        collection = db["sensor_readings"]
        sensor_timestamp, sensor_uptime = _resolve_sensor_timestamp(payload.timestamp)
        document = {
            "arduino_id": payload.arduino_id,
            "timestamp": sensor_timestamp,
            "mediciones": payload.mediciones.model_dump(),
            "bateria": payload.bateria,
            "source": source,
        }
        if sensor_uptime is not None:
            document["sensor_uptime_seconds"] = sensor_uptime

        result = collection.insert_one(document)
        logger.info("Lectura guardada en MongoDB con ID: %s (origen: %s)", result.inserted_id, source)
        return str(result.inserted_id)
    except Exception as e:
        logger.error("Error guardando en MongoDB: %s", e)
        return None

def save_sensor_reading_to_mongodb(reading: SensorReading, arduino_id: str = "esp8266_1", bateria: int = 100) -> Optional[str]:
    payload = SensorMongoPayload(
        arduino_id=arduino_id,
        timestamp=reading.timestamp,
        mediciones=SensorMeasurements(
            ph=reading.ph, temperatura=reading.temperature, conductividad=reading.conductivity,
        ),
        bateria=bateria,
    )
    return save_sensor_payload_to_mongodb(payload)

def normalize_sensor_document(reading: dict) -> dict:
    mediciones = reading.get("mediciones", {})
    return {
        "id": str(reading.get("_id", reading.get("id", ""))),
        "arduino_id": reading.get("arduino_id", reading.get("sensor_id", "esp8266_1")),
        "ph": float(mediciones.get("ph", reading.get("ph", 0.0))),
        "temperature": float(mediciones.get("temperatura", reading.get("temperature", 0.0))),
        "conductivity": float(mediciones.get("conductividad", reading.get("conductivity", 0.0))),
        "bateria": int(reading.get("bateria", 100)),
        "timestamp": to_chile_time(reading.get("timestamp", utc_now())),
    }

def get_latest_sensor_reading(arduino_id: str | None = None) -> Optional[dict]:
    if db is not None:
        try:
            query = {"arduino_id": arduino_id} if arduino_id else {}
            reading = db["sensor_readings"].find_one(query, sort=[("_id", -1)])
            if reading:
                return normalize_sensor_document(reading)
        except Exception as e:
            logger.error("Error leyendo de MongoDB: %s", e)

    if simulated_data_store:
        return normalize_sensor_document(simulated_data_store[-1])
    return None

def get_sensor_readings_history(limit: int = 100) -> list[dict]:
    if db is not None:
        try:
            readings = list(db["sensor_readings"].find().sort("_id", -1).limit(limit))
            return [normalize_sensor_document(reading) for reading in readings]
        except Exception as e:
            logger.error("Error leyendo historial de MongoDB: %s", e)

    if simulated_data_store:
        readings = simulated_data_store[-limit:][::-1]
        return [normalize_sensor_document(reading) for reading in readings]
    return []

def update_dashboard_state_from_mongodb(arduino_id: str | None = None) -> Optional[DashboardResponse]:
    global dashboard_state
    reading = get_latest_sensor_reading(arduino_id)
    if not reading:
        dashboard_state = None
        return None

    now = chile_now()

    def get_status(value: float, min_val: float, max_val: float, safe_max: float) -> str:
        if value < min_val or value > max_val: return "critical"
        if value > safe_max: return "warning"
        return "stable"

    last_updated = to_chile_time(reading.get("timestamp"))
    time_since_reading = max(0.0, (now - last_updated).total_seconds())
    connected = time_since_reading <= 30

    dashboard_state = DashboardResponse(
        ph=SensorData(
            value=reading["ph"], min=6.0, max=8.5, safeMax=8.0,
            lastUpdated=last_updated, status=get_status(reading["ph"], 6.0, 8.5, 8.0)
        ),
        temperature=SensorData(
            value=reading["temperature"], min=5, max=35, safeMax=28,
            lastUpdated=last_updated, status=get_status(reading["temperature"], 5, 35, 28)
        ),
        conductivity=SensorData(
            value=reading["conductivity"], min=100, max=2000, safeMax=1500,
            lastUpdated=last_updated, status=get_status(reading["conductivity"], 100, 2000, 1500)
        ),
        metadata=Metadata(
            systemStatus="operational" if connected else "degraded",
            arduinoConnected=connected,
            lastSync=now,
            uptime=max(0, int(time_since_reading)),
            activeSensors=3 if connected else 0,
        ),
        battery=reading.get("bateria", 100),
    )
    return dashboard_state

def build_payload_from_ph_post(reading: SensorPhPostReading) -> SensorMongoPayload:
    latest = get_latest_sensor_reading() or {}
    temperature = float(reading.temperature) if reading.temperature is not None else float(latest.get("temperature", 0.0))
    conductivity = float(reading.conductivity) if reading.conductivity is not None else float(latest.get("conductivity", 0.0))

    return SensorMongoPayload(
        arduino_id=str(reading.sensor_id).strip(),
        timestamp=reading.timestamp,
        mediciones=SensorMeasurements(
            ph=float(reading.ph), temperatura=temperature, conductividad=conductivity,
        ),
        bateria=reading.bateria,
    )

# ============================================================================
# GESTIÓN DE DISPOSITIVOS (MICROCONTROLADORES / ARDUINOS)
# ============================================================================

def create_device(
    name: str,
    device_type: str,
    location: str,
    arduino_id: str | None = None,
    topic: str | None = None,
    telemetry_key: str | None = None,
) -> Optional[dict]:
    """Crea un nuevo dispositivo en la base de datos."""
    if db is None:
        logger.warning("MongoDB no está disponible")
        return None
    
    try:
        import uuid
        collection = db["devices"]
        device_id = str(uuid.uuid4())
        now = utc_now()
        
        device = {
            "_id": device_id,
            "id": device_id,
            "name": name,
            "device_type": device_type,
            "location": location,
            "status": "unknown",
            "arduino_id": arduino_id,
            "telemetry_key": telemetry_key,
            "topic": topic,
            "battery": 100,
            "last_sync": None,
            "created_at": now,
            "updated_at": now,
            "active": True,
        }
        
        collection.insert_one(device)
        logger.info("Dispositivo creado: %s (ID: %s)", name, device_id)
        return device
    except Exception as e:
        logger.error("Error creando dispositivo: %s", e)
        return None

def get_device(device_id: str) -> Optional[dict]:
    """Obtiene un dispositivo por su ID."""
    if db is None:
        return None
    
    try:
        collection = db["devices"]
        device = collection.find_one({"_id": device_id})
        if device:
            device["id"] = device.get("_id", "")
        return device
    except Exception as e:
        logger.error("Error obteniendo dispositivo: %s", e)
        return None

def _active_device_filter() -> dict:
    """Incluye activos y registros legacy sin campo ``active``; excluye ``active: false``."""
    return {"active": {"$ne": False}}


def find_device_by_key(key: str, *, include_inactive: bool = False) -> Optional[dict]:
    """Busca dispositivo por ``arduino_id`` o ``name``."""
    if db is None:
        return None

    device_key = str(key).strip()
    if not device_key:
        return None

    try:
        query: dict = {
            "$or": [
                {"arduino_id": device_key},
                {"name": device_key},
                {"telemetry_key": device_key},
            ]
        }
        if not include_inactive:
            query = {"$and": [query, _active_device_filter()]}

        collection = db["devices"]
        device = collection.find_one(query)
        if device:
            device["id"] = device.get("_id", "")
        return device
    except Exception as e:
        logger.error("Error buscando dispositivo por clave: %s", e)
        return None


def get_all_devices(active_only: bool = True) -> list[dict]:
    """Obtiene todos los dispositivos registrados."""
    if db is None:
        return []
    
    try:
        collection = db["devices"]
        query = _active_device_filter() if active_only else {}
        devices = list(collection.find(query).sort("created_at", -1))
        
        for device in devices:
            device["id"] = device.get("_id", "")
        
        return devices
    except Exception as e:
        logger.error("Error obteniendo dispositivos: %s", e)
        return []

def get_device_by_arduino_id(arduino_id: str) -> Optional[dict]:
    """Obtiene un dispositivo activo por nombre/clave MQTT o arduino_id."""
    return find_device_by_key(arduino_id, include_inactive=False)

def update_device(
    device_id: str,
    name: str | None = None,
    location: str | None = None,
    active: bool | None = None,
    arduino_id: str | None = None,
    telemetry_key: str | None = None,
    topic: str | None = None,
) -> Optional[dict]:
    """Actualiza un dispositivo existente."""
    if db is None:
        return None
    
    try:
        collection = db["devices"]
        update_data = {"updated_at": utc_now()}
        
        if name is not None:
            update_data["name"] = name
        if location is not None:
            update_data["location"] = location
        if active is not None:
            update_data["active"] = active
        if arduino_id is not None:
            update_data["arduino_id"] = arduino_id
        if telemetry_key is not None:
            update_data["telemetry_key"] = telemetry_key
        if topic is not None:
            update_data["topic"] = topic
        
        result = collection.find_one_and_update(
            {"_id": device_id},
            {"$set": update_data},
            return_document=True
        )
        
        if result:
            result["id"] = result.get("_id", "")
            logger.info("Dispositivo actualizado: %s", device_id)
        
        return result
    except Exception as e:
        logger.error("Error actualizando dispositivo: %s", e)
        return None

def update_device_status(arduino_id: str, status: str, battery: int | None = None) -> Optional[dict]:
    """Actualiza el estado y batería de un dispositivo basado en arduino_id."""
    if db is None:
        return None
    
    try:
        collection = db["devices"]
        update_data = {
            "status": status,
            "last_sync": utc_now(),
            "updated_at": utc_now(),
        }
        
        if battery is not None:
            update_data["battery"] = max(0, min(100, battery))
        
        key = str(arduino_id).strip()
        result = collection.find_one_and_update(
            {
                "$and": [
                    {
                        "$or": [
                            {"arduino_id": key},
                            {"name": key},
                            {"telemetry_key": key},
                        ]
                    },
                    _active_device_filter(),
                ]
            },
            {"$set": update_data},
            return_document=True
        )
        
        if result:
            result["id"] = result.get("_id", "")
        
        return result
    except Exception as e:
        logger.error("Error actualizando estado del dispositivo: %s", e)
        return None

def register_new_microcontroller(arduino_id: str, device_name: str | None = None, device_type: str = "ESP8266", location: str = "") -> Optional[dict]:
    """Registra un nuevo microcontrolador detectado automáticamente."""
    if db is None:
        return None
    
    try:
        key = str(arduino_id).strip()
        existing_any = find_device_by_key(key, include_inactive=True)
        if existing_any:
            if existing_any.get("active") is False:
                logger.info(
                    "Microcontrolador eliminado; no se re-registra automáticamente: %s",
                    key,
                )
                return None
            logger.info("Microcontrolador ya registrado: %s", key)
            return existing_any

        name = (device_name or key).strip()
        device = create_device(
            name=name,
            device_type=device_type,
            location=location,
            arduino_id=key,
        )
        
        if device:
            logger.info("Nuevo microcontrolador registrado: %s", arduino_id)
            log_service.log(
                LogOrigin.DASHBOARD, LogLevel.INFO,
                f"Nuevo microcontrolador detectado: {name} ({arduino_id})",
                component="device.registration", details={"arduino_id": arduino_id, "device_type": device_type}
            )
        
        return device
    except Exception as e:
        logger.error("Error registrando microcontrolador: %s", e)
        return None

def delete_device(device_id: str) -> bool:
    """Elimina (desactiva) un dispositivo."""
    if db is None:
        return False
    
    try:
        collection = db["devices"]
        update = {"$set": {"active": False, "updated_at": utc_now()}}
        result = collection.update_one({"_id": device_id}, update)

        if result.matched_count == 0:
            result = collection.update_one({"id": device_id}, update)

        if result.matched_count > 0:
            logger.info("Dispositivo eliminado: %s", device_id)
            return True
        return False
    except Exception as e:
        logger.error("Error eliminando dispositivo: %s", e)
        return False
