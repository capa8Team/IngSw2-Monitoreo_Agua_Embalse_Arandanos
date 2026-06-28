import logging
from datetime import datetime, timezone
from typing import Optional
from zoneinfo import ZoneInfo

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

from core.config import settings
from services.organization_service import DEFAULT_ORGANIZATION_SLUG, get_default_organization
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

HISTORICAL_MAX_LIMIT = 2000


def ensure_sensor_indexes() -> None:
    """Índices para consultas históricas por tiempo y dispositivo."""
    if db is None:
        return
    try:
        collection = db["sensor_readings"]
        collection.create_index([("timestamp", -1)], name="timestamp_desc")
        collection.create_index(
            [("arduino_id", 1), ("timestamp", -1)],
            name="arduino_timestamp_desc",
        )
        collection.create_index(
            [("organization_id", 1), ("timestamp", -1)],
            name="org_timestamp_desc",
        )
        logger.info("Índices de sensor_readings verificados")
    except Exception as e:
        logger.warning("No se pudieron crear índices en sensor_readings: %s", e)


if db is not None:
    ensure_sensor_indexes()


def _default_org_fields() -> dict[str, str]:
    org = get_default_organization()
    if org:
        return {"organization_id": org.id, "organization_slug": org.slug}
    return {"organization_slug": DEFAULT_ORGANIZATION_SLUG}


def migrate_devices_organization() -> None:
    """Asigna organización por defecto a dispositivos legacy sin scope."""
    if db is None:
        return
    try:
        defaults = _default_org_fields()
        result = db["devices"].update_many(
            {
                "$or": [
                    {"organization_id": {"$exists": False}},
                    {"organization_id": None},
                    {"organization_slug": {"$exists": False}},
                    {"organization_slug": None},
                ]
            },
            {"$set": defaults},
        )
        if result.modified_count:
            logger.info(
                "Migrados %s dispositivos a organización %s",
                result.modified_count,
                defaults.get("organization_slug"),
            )
    except Exception as e:
        logger.warning("No se pudo migrar organization en devices: %s", e)


def migrate_sensor_readings_organization() -> None:
    """Etiqueta lecturas legacy con la organización de su dispositivo."""
    if db is None:
        return
    try:
        devices = list(
            db["devices"].find(
                {},
                {"arduino_id": 1, "name": 1, "telemetry_key": 1, "organization_id": 1, "organization_slug": 1},
            )
        )
        key_to_org: dict[str, dict[str, str]] = {}
        for device in devices:
            org_payload = {
                "organization_id": device.get("organization_id"),
                "organization_slug": device.get("organization_slug") or DEFAULT_ORGANIZATION_SLUG,
            }
            for field in ("arduino_id", "name", "telemetry_key"):
                value = str(device.get(field) or "").strip()
                if value:
                    key_to_org[value] = org_payload

        updated = 0
        for key, org_payload in key_to_org.items():
            if not org_payload.get("organization_id"):
                continue
            result = db["sensor_readings"].update_many(
                {
                    "arduino_id": key,
                    "$or": [
                        {"organization_id": {"$exists": False}},
                        {"organization_id": None},
                    ],
                },
                {"$set": org_payload},
            )
            updated += result.modified_count
        if updated:
            logger.info("Migradas %s lecturas con organization_id", updated)
    except Exception as e:
        logger.warning("No se pudo migrar organization en sensor_readings: %s", e)


if db is not None:
    migrate_devices_organization()
    migrate_sensor_readings_organization()

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
        org_fields = _org_fields_for_arduino(payload.arduino_id)
        document = {
            "arduino_id": payload.arduino_id,
            "timestamp": sensor_timestamp,
            "mediciones": payload.mediciones.model_dump(),
            "bateria": payload.bateria,
            "source": source,
            **org_fields,
        }
        if sensor_uptime is not None:
            document["sensor_uptime_seconds"] = sensor_uptime

        result = collection.insert_one(document)
        logger.info("Lectura guardada en MongoDB con ID: %s (origen: %s)", result.inserted_id, source)
        try:
            from services.redis_cache import invalidate_sensor_readings

            invalidate_sensor_readings(
                org_fields.get("organization_id"),
                org_fields.get("organization_slug"),
                payload.arduino_id,
            )
        except Exception as cache_exc:
            logger.warning("No se pudo invalidar caché Redis: %s", cache_exc)
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

def get_latest_sensor_reading(
    arduino_id: str | None = None,
    *,
    tenant_filter: dict | None = None,
) -> Optional[dict]:
    if db is not None:
        try:
            query: dict = {"arduino_id": arduino_id} if arduino_id else {}
            query = _merge_org_filter(query, tenant_filter)
            reading = db["sensor_readings"].find_one(query, sort=[("timestamp", -1)])
            if reading:
                return normalize_sensor_document(reading)
        except Exception as e:
            logger.error("Error leyendo de MongoDB: %s", e)

    if simulated_data_store:
        return normalize_sensor_document(simulated_data_store[-1])
    return None

def _build_readings_query(
    since: datetime | None = None,
    until: datetime | None = None,
    arduino_id: str | None = None,
    tenant_filter: dict | None = None,
) -> dict:
    query: dict = {}
    ts_filter: dict = {}
    if since is not None:
        ts_filter["$gte"] = since
    if until is not None:
        ts_filter["$lte"] = until
    if ts_filter:
        query["timestamp"] = ts_filter
    if arduino_id:
        query["arduino_id"] = arduino_id
    return _merge_org_filter(query, tenant_filter)


def query_sensor_readings(
    *,
    since: datetime | None = None,
    until: datetime | None = None,
    arduino_id: str | None = None,
    limit: int = 500,
    tenant_filter: dict | None = None,
) -> list[dict]:
    """Consulta acotada por rango temporal (orden descendente por timestamp)."""
    limit = max(1, min(limit, HISTORICAL_MAX_LIMIT))
    if db is not None:
        try:
            query = _build_readings_query(since, until, arduino_id, tenant_filter)
            projection = {
                "_id": 1,
                "timestamp": 1,
                "arduino_id": 1,
                "embalse": 1,
                "ph": 1,
                "temperature": 1,
                "conductivity": 1,
                "mediciones": 1,
            }
            readings = list(
                db["sensor_readings"]
                .find(query, projection)
                .sort("timestamp", -1)
                .limit(limit)
            )
            return [normalize_sensor_document(reading) for reading in readings]
        except Exception as e:
            logger.error("Error leyendo lecturas acotadas de MongoDB: %s", e)

    rows = simulated_data_store
    if since is not None or until is not None or arduino_id:
        filtered = []
        for reading in rows:
            ts = to_chile_time(reading.get("timestamp", utc_now()))
            if since is not None and ts < since:
                continue
            if until is not None and ts > until:
                continue
            if arduino_id and reading.get("arduino_id") != arduino_id:
                continue
            filtered.append(reading)
        rows = filtered
    rows = rows[-limit:][::-1]
    return [normalize_sensor_document(reading) for reading in rows]


def get_sensor_readings_history(limit: int = 100) -> list[dict]:
    return query_sensor_readings(limit=limit)

def update_dashboard_state_from_mongodb(
    arduino_id: str | None = None,
    *,
    tenant_filter: dict | None = None,
) -> Optional[DashboardResponse]:
    global dashboard_state
    reading = get_latest_sensor_reading(arduino_id, tenant_filter=tenant_filter)
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

def _merge_org_filter(base_query: dict, org_filter: dict | None) -> dict:
    if not org_filter:
        return base_query
    if not base_query:
        return org_filter
    return {"$and": [base_query, org_filter]}


def get_organization_telemetry_keys(
    *,
    organization_id: str | None = None,
    organization_slug: str | None = None,
    org_filter: dict | None = None,
) -> set[str]:
    """Claves MQTT/arduino asociadas a dispositivos de una organización."""
    if db is None:
        return set()
    try:
        query = _active_device_filter()
        if org_filter:
            query = _merge_org_filter(query, org_filter)
        keys: set[str] = set()
        for doc in db["devices"].find(
            query,
            {"arduino_id": 1, "name": 1, "telemetry_key": 1},
        ):
            for field in ("arduino_id", "name", "telemetry_key"):
                value = doc.get(field)
                if value:
                    keys.add(str(value))
        return keys
    except Exception as e:
        logger.error("Error obteniendo claves de telemetría por organización: %s", e)
        return set()


def create_device(
    name: str,
    device_type: str,
    location: str,
    city: str = "",
    arduino_id: str | None = None,
    topic: str | None = None,
    telemetry_key: str | None = None,
    organization_id: str | None = None,
    organization_slug: str | None = None,
    group_id: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
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
        
        org_defaults = _default_org_fields()
        device = {
            "_id": device_id,
            "id": device_id,
            "name": name,
            "device_type": device_type,
            "location": location,
            "city": city,
            "group_id": group_id,
            "latitude": latitude,
            "longitude": longitude,
            "status": "unknown",
            "arduino_id": arduino_id,
            "telemetry_key": telemetry_key,
            "topic": topic,
            "battery": 100,
            "last_sync": None,
            "created_at": now,
            "updated_at": now,
            "active": True,
            "organization_id": organization_id or org_defaults.get("organization_id"),
            "organization_slug": organization_slug or org_defaults.get("organization_slug"),
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


def _org_fields_for_arduino(arduino_id: str | None) -> dict[str, str | None]:
    """Resuelve organization_id/slug desde el dispositivo registrado."""
    key = str(arduino_id or "").strip()
    if key:
        device = find_device_by_key(key, include_inactive=True)
        if device:
            org_id = device.get("organization_id")
            org_slug = device.get("organization_slug")
            if org_id or org_slug:
                return {
                    "organization_id": str(org_id) if org_id else None,
                    "organization_slug": str(org_slug or DEFAULT_ORGANIZATION_SLUG),
                }
    defaults = _default_org_fields()
    return {
        "organization_id": defaults.get("organization_id"),
        "organization_slug": defaults.get("organization_slug", DEFAULT_ORGANIZATION_SLUG),
    }


def get_all_devices(
    active_only: bool = True,
    org_filter: dict | None = None,
) -> list[dict]:
    """Obtiene todos los dispositivos registrados."""
    if db is None:
        return []
    
    try:
        collection = db["devices"]
        query: dict = _active_device_filter() if active_only else {}
        query = _merge_org_filter(query, org_filter)
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
    city: str | None = None,
    active: bool | None = None,
    arduino_id: str | None = None,
    telemetry_key: str | None = None,
    topic: str | None = None,
    group_id: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    *,
    unset_group: bool = False,
    unset_coordinates: bool = False,
) -> Optional[dict]:
    """Actualiza un dispositivo existente."""
    if db is None:
        return None
    
    try:
        collection = db["devices"]
        update_data = {"updated_at": utc_now()}
        unset_data: dict = {}
        
        if name is not None:
            update_data["name"] = name
        if location is not None:
            update_data["location"] = location
        if city is not None:
            update_data["city"] = city
        if active is not None:
            update_data["active"] = active
        if arduino_id is not None:
            update_data["arduino_id"] = arduino_id
        if telemetry_key is not None:
            update_data["telemetry_key"] = telemetry_key
        if topic is not None:
            update_data["topic"] = topic
        if unset_group:
            unset_data["group_id"] = ""
        elif group_id is not None:
            update_data["group_id"] = group_id
        if unset_coordinates:
            unset_data["latitude"] = ""
            unset_data["longitude"] = ""
        else:
            if latitude is not None:
                update_data["latitude"] = latitude
            if longitude is not None:
                update_data["longitude"] = longitude
        
        update_op: dict = {"$set": update_data}
        if unset_data:
            update_op["$unset"] = unset_data
        
        result = collection.find_one_and_update(
            {"_id": device_id},
            update_op,
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

def register_new_microcontroller(
    arduino_id: str,
    device_name: str | None = None,
    device_type: str = "ESP8266",
    location: str = "",
    organization_id: str | None = None,
    organization_slug: str | None = None,
) -> Optional[dict]:
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
            organization_id=organization_id,
            organization_slug=organization_slug,
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


# ============================================================================
# GRUPOS DE DISPOSITIVOS
# ============================================================================
def _count_devices_in_group(group_id: str, org_filter: dict | None = None) -> int:
    if db is None:
        return 0
    try:
        query: dict = {"group_id": group_id, **_active_device_filter()}
        query = _merge_org_filter(query, org_filter)
        return db["devices"].count_documents(query)
    except Exception as e:
        logger.error("Error contando dispositivos del grupo %s: %s", group_id, e)
        return 0


def _serialize_group(doc: dict, org_filter: dict | None = None) -> dict:
    group_id = doc.get("_id", "")
    return {
        "id": group_id,
        "name": doc.get("name", ""),
        "description": doc.get("description", ""),
        "location_label": doc.get("location_label", ""),
        "city": doc.get("city", ""),
        "latitude": doc.get("latitude", 0.0),
        "longitude": doc.get("longitude", 0.0),
        "device_count": _count_devices_in_group(group_id, org_filter),
        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
        "active": doc.get("active", True),
    }


def create_device_group(
    name: str,
    latitude: float,
    longitude: float,
    description: str = "",
    location_label: str = "",
    city: str = "",
    organization_id: str | None = None,
    organization_slug: str | None = None,
) -> Optional[dict]:
    if db is None:
        return None
    try:
        import uuid
        group_id = str(uuid.uuid4())
        now = utc_now()
        org_defaults = _default_org_fields()
        doc = {
            "_id": group_id,
            "id": group_id,
            "name": name,
            "description": description,
            "location_label": location_label,
            "city": city,
            "latitude": latitude,
            "longitude": longitude,
            "created_at": now,
            "updated_at": now,
            "active": True,
            "organization_id": organization_id or org_defaults.get("organization_id"),
            "organization_slug": organization_slug or org_defaults.get("organization_slug"),
        }
        db["device_groups"].insert_one(doc)
        return _serialize_group(doc)
    except Exception as e:
        logger.error("Error creando grupo de dispositivos: %s", e)
        return None


def get_device_group(group_id: str) -> Optional[dict]:
    if db is None:
        return None
    try:
        doc = db["device_groups"].find_one({"_id": group_id, "active": {"$ne": False}})
        if not doc:
            return None
        return _serialize_group(doc)
    except Exception as e:
        logger.error("Error obteniendo grupo %s: %s", group_id, e)
        return None


def get_all_device_groups(
    active_only: bool = True,
    org_filter: dict | None = None,
) -> list[dict]:
    if db is None:
        return []
    try:
        query: dict = {"active": {"$ne": False}} if active_only else {}
        query = _merge_org_filter(query, org_filter)
        docs = list(db["device_groups"].find(query).sort("name", 1))
        return [_serialize_group(doc, org_filter) for doc in docs]
    except Exception as e:
        logger.error("Error listando grupos de dispositivos: %s", e)
        return []


def update_device_group(
    group_id: str,
    name: str | None = None,
    description: str | None = None,
    location_label: str | None = None,
    city: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    active: bool | None = None,
) -> Optional[dict]:
    if db is None:
        return None
    try:
        update_data = {"updated_at": utc_now()}
        if name is not None:
            update_data["name"] = name
        if description is not None:
            update_data["description"] = description
        if location_label is not None:
            update_data["location_label"] = location_label
        if city is not None:
            update_data["city"] = city
        if latitude is not None:
            update_data["latitude"] = latitude
        if longitude is not None:
            update_data["longitude"] = longitude
        if active is not None:
            update_data["active"] = active

        result = db["device_groups"].find_one_and_update(
            {"_id": group_id},
            {"$set": update_data},
            return_document=True,
        )
        if result:
            return _serialize_group(result)
        return None
    except Exception as e:
        logger.error("Error actualizando grupo %s: %s", group_id, e)
        return None


def delete_device_group(group_id: str) -> bool:
    if db is None:
        return False
    try:
        result = db["device_groups"].update_one(
            {"_id": group_id},
            {"$set": {"active": False, "updated_at": utc_now()}},
        )
        if result.matched_count > 0:
            db["devices"].update_many(
                {"group_id": group_id},
                {"$unset": {"group_id": ""}, "$set": {"updated_at": utc_now()}},
            )
            return True
        return False
    except Exception as e:
        logger.error("Error eliminando grupo %s: %s", group_id, e)
        return False
