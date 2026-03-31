import os
import logging
from datetime import datetime
from typing import Literal, Optional
from logging.handlers import RotatingFileHandler

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import requests
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

load_dotenv()

logger = logging.getLogger(__name__)


def configure_logging() -> None:
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s: %(message)s [in %(filename)s:%(lineno)d]"
    )

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)

    file_handler = RotatingFileHandler("app.log", maxBytes=16384, backupCount=20)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)


configure_logging()

# ============================================================================
# CONFIGURACIÓN MONGODB
# ============================================================================

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
MONGODB_DB = os.getenv("MONGODB_DB", "embalse_arandanos")

try:
    mongo_client = MongoClient(MONGODB_URL, serverSelectionTimeoutMS=5000)
    # Verificar conexión
    mongo_client.admin.command('ping')
    db = mongo_client[MONGODB_DB]
    logger.info("Conexion a MongoDB establecida")
except ConnectionFailure:
    logger.warning("No se pudo conectar a MongoDB. Usando almacenamiento en memoria.")
    mongo_client = None
    db = None


app = FastAPI(
    title="API Monitoreo Embalse Arandanos",
    description=(
        "API para exponer lecturas de sensores y respaldo de alertas del dashboard."
    ),
    version="1.0.0",
)

API_PATH_PREFIX = "/api/"

# Agregar middleware CORS para permitir requests desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir todos los orígenes (cambiar a lista específica en prod)
    allow_credentials=True,
    allow_methods=["*"],  # Permitir todos los métodos (GET, POST, OPTIONS, etc)
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if API_PATH_PREFIX in request.url.path:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": True, "message": str(exc.detail)},
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": str(exc.detail)},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error processing request", exc_info=exc)
    if API_PATH_PREFIX in request.url.path:
        return JSONResponse(
            status_code=500,
            content={"error": True, "message": "Error processing API request!"},
        )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
    )


class SensorData(BaseModel):
    value: float
    min: float
    max: float
    safeMax: float
    lastUpdated: datetime
    status: Literal["stable", "warning", "critical"]


# ============================================================================
# MODELOS PARA RECIBIR DATOS DEL ESP8266
# ============================================================================

class SensorReading(BaseModel):
    ph: float
    temperature: float
    conductivity: float
    timestamp: int


class SensorNestedReadings(BaseModel):
    temperature: float | None = None
    humidity: float | None = None
    ph: float | None = None
    conductivity: float | None = None
    timestamp: int | None = None


class SensorReadingNestedPayload(BaseModel):
    readings: SensorNestedReadings


class SensorMeasurements(BaseModel):
    ph: float
    temperatura: float
    conductividad: float


class SensorMongoPayload(BaseModel):
    arduino_id: str
    timestamp: int | None = None
    mediciones: SensorMeasurements
    bateria: int = Field(..., ge=0, le=100)


class SensorDataResponse(BaseModel):
    ph: float
    temperature: float
    conductivity: float
    timestamp: datetime
    id: Optional[str] = None


class Metadata(BaseModel):
    systemStatus: Literal["operational", "degraded", "down"]
    arduinoConnected: bool
    lastSync: datetime
    uptime: int = Field(..., ge=0, description="Tiempo de actividad en segundos")
    activeSensors: int = Field(..., ge=0)


class DashboardResponse(BaseModel):
    ph: SensorData
    temperature: SensorData
    conductivity: SensorData
    metadata: Metadata


class AlertRecord(BaseModel):
    id: int
    fecha: str
    hora: str
    embalse: str
    sensor: str
    medicion: str


class AlertCreate(BaseModel):
    embalse: str
    sensor: str
    medicion: str
    nombreDispositivo: str | None = None
    valor: float | None = None
    minimo: float | None = None
    maximo: float | None = None


class MailerSendConfig(BaseModel):
    api_token: str | None
    from_email: str | None
    from_name: str
    to_emails: list[str]


dashboard_state: DashboardResponse | None = None

alerts_store: list[AlertRecord] = [
    AlertRecord(
        id=1,
        fecha="2026-03-24",
        hora="14:30",
        embalse="Embalse Norte",
        sensor="Conductividad",
        medicion="1.2 mS/cm",
    )
]


# ============================================================================
# FUNCIONES MONGODB
# ============================================================================

def _resolve_sensor_timestamp(timestamp: int | None) -> tuple[datetime, int | None]:
    if timestamp is None:
        return datetime.utcnow(), None

    # ESP8266 suele enviar millis()/1000; si no parece epoch UTC, usamos hora del servidor.
    if timestamp >= 1_500_000_000:
        return datetime.utcfromtimestamp(timestamp), None
    return datetime.utcnow(), timestamp


def save_sensor_payload_to_mongodb(payload: SensorMongoPayload) -> Optional[str]:
    """Guardar documento con el esquema solicitado por el usuario."""
    if db is None:
        logger.warning("MongoDB no está disponible")
        return None

    try:
        collection = db["sensor_readings"]
        sensor_timestamp, sensor_uptime_seconds = _resolve_sensor_timestamp(payload.timestamp)

        document = {
            "arduino_id": payload.arduino_id,
            "timestamp": sensor_timestamp,
            "mediciones": {
                "ph": payload.mediciones.ph,
                "temperatura": payload.mediciones.temperatura,
                "conductividad": payload.mediciones.conductividad,
            },
            "bateria": payload.bateria,
        }
        if sensor_uptime_seconds is not None:
            document["sensor_uptime_seconds"] = sensor_uptime_seconds

        result = collection.insert_one(document)
        logger.info(f"Lectura guardada en MongoDB con ID: {result.inserted_id}")
        return str(result.inserted_id)
    except Exception as e:
        logger.error(f"Error guardando en MongoDB: {e}")
        return None


def save_sensor_reading_to_mongodb(reading: SensorReading, arduino_id: str = "esp8266_1", bateria: int = 100) -> Optional[str]:
    """Compatibilidad: convierte formato plano al esquema oficial solicitado."""
    payload = SensorMongoPayload(
        arduino_id=arduino_id,
        timestamp=reading.timestamp,
        mediciones=SensorMeasurements(
            ph=reading.ph,
            temperatura=reading.temperature,
            conductividad=reading.conductivity,
        ),
        bateria=bateria,
    )
    return save_sensor_payload_to_mongodb(payload)


def normalize_sensor_document(reading: dict) -> dict:
    """Normaliza documento Mongo (esquema nuevo o legado) al formato usado por la API."""
    mediciones = reading.get("mediciones", {})
    ph = mediciones.get("ph", reading.get("ph"))
    temperature = mediciones.get("temperatura", reading.get("temperature"))
    conductivity = mediciones.get("conductividad", reading.get("conductivity"))

    return {
        "id": str(reading.get("_id", reading.get("id", ""))),
        "arduino_id": reading.get("arduino_id", reading.get("sensor_id", "esp8266_1")),
        "ph": float(ph) if ph is not None else 0.0,
        "temperature": float(temperature) if temperature is not None else 0.0,
        "conductivity": float(conductivity) if conductivity is not None else 0.0,
        "bateria": int(reading.get("bateria", 100)),
        "timestamp": reading.get("timestamp", datetime.utcnow()),
    }


def get_latest_sensor_reading() -> Optional[dict]:
    """Obtener la última lectura de sensores desde MongoDB"""
    if db is None:
        logger.warning("MongoDB no está disponible")
        return None
    
    try:
        collection = db["sensor_readings"]
        reading = collection.find_one(sort=[("timestamp", -1)])
        if reading:
            return normalize_sensor_document(reading)
        return None
    except Exception as e:
        logger.error(f"Error leyendo de MongoDB: {e}")
        return None


def get_sensor_readings_history(limit: int = 100) -> list[dict]:
    """Obtener historial de lecturas de sensores"""
    if db is None:
        logger.warning("MongoDB no está disponible")
        return []
    
    try:
        collection = db["sensor_readings"]
        readings = list(collection.find().sort("timestamp", -1).limit(limit))
        return [normalize_sensor_document(reading) for reading in readings]
    except Exception as e:
        logger.error(f"Error leyendo historial de MongoDB: {e}")
        return []


def update_dashboard_state_from_mongodb() -> DashboardResponse | None:
    """Actualizar el estado del dashboard desde la última lectura en MongoDB"""
    global dashboard_state
    
    reading = get_latest_sensor_reading()
    if not reading:
        dashboard_state = None
        return None

    now = datetime.utcnow()

    # Determinar estado basado en rangos
    def get_status(value: float, min_val: float, max_val: float, safe_max: float) -> str:
        if value < min_val or value > max_val:
            return "critical"
        if value > safe_max:
            return "warning"
        return "stable"

    last_updated = reading.get("timestamp", now)
    connected = (now - last_updated).total_seconds() <= 30

    dashboard_state = DashboardResponse(
        ph=SensorData(
            value=reading["ph"],
            min=6.0,
            max=8.5,
            safeMax=8.0,
            lastUpdated=last_updated,
            status=get_status(reading["ph"], 6.0, 8.5, 8.0),
        ),
        temperature=SensorData(
            value=reading["temperature"],
            min=5,
            max=35,
            safeMax=28,
            lastUpdated=last_updated,
            status=get_status(reading["temperature"], 5, 35, 28),
        ),
        conductivity=SensorData(
            value=reading["conductivity"],
            min=100,
            max=2000,
            safeMax=1500,
            lastUpdated=last_updated,
            status=get_status(reading["conductivity"], 100, 2000, 1500),
        ),
        metadata=Metadata(
            systemStatus="operational" if connected else "degraded",
            arduinoConnected=connected,
            lastSync=now,
            uptime=max(0, int((now - last_updated).total_seconds())),
            activeSensors=3,
        ),
    )
    logger.info("Dashboard actualizado desde MongoDB")
    return dashboard_state


def get_mailersend_config() -> MailerSendConfig:
    to_emails_raw = os.getenv("MAILERSEND_TO_EMAILS", "")
    to_emails = [email.strip() for email in to_emails_raw.split(",") if email.strip()]
    return MailerSendConfig(
        api_token=os.getenv("MAILERSEND_API_TOKEN"),
        from_email=os.getenv("MAILERSEND_FROM_EMAIL"),
        from_name=os.getenv("MAILERSEND_FROM_NAME", "Monitoreo Embalse Arandanos"),
        to_emails=to_emails,
    )


def measurement_is_out_of_range(payload: AlertCreate) -> bool:
    if payload.valor is None or payload.minimo is None or payload.maximo is None:
        return True
    return payload.valor < payload.minimo or payload.valor > payload.maximo


def send_mailersend_notification(device_name: str, sensor: str, medicion: str, now: datetime) -> None:
    config = get_mailersend_config()
    if not config.api_token or not config.from_email or not config.to_emails:
        logger.warning(
            f"MailerSend no configurado. API Token: {bool(config.api_token)}, "
            f"From Email: {bool(config.from_email)}, To Emails: {bool(config.to_emails)}"
        )
        return

    logger.info(f"Enviando alerta por email: {device_name} - {sensor}")

    day_names = {
        0: "Lunes",
        1: "Martes",
        2: "Miercoles",
        3: "Jueves",
        4: "Viernes",
        5: "Sabado",
        6: "Domingo",
    }
    day_name = day_names[now.weekday()]
    fecha = now.strftime("%Y-%m-%d")
    hora = now.strftime("%H:%M:%S")

    payload = {
        "from": {
            "email": config.from_email,
            "name": config.from_name,
        },
        "to": [{"email": email} for email in config.to_emails],
        "subject": f"⚠️ Alerta: {sensor} fuera de rango - {device_name}",
        "template_id": "351ndgw8m7rgzqx8",
        "personalization": [
            {
                "email": email,
                "data": {
                    "DEVICE_NAME": device_name,
                    "DAY_NAME": day_name,
                    "FECHA": fecha,
                    "HORA": hora,
                    "SENSOR": sensor,
                    "MEDICION": medicion,
                }
            }
            for email in config.to_emails
        ],
    }
    headers = {
        "Authorization": f"Bearer {config.api_token}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            "https://api.mailersend.com/v1/email",
            json=payload,
            headers=headers,
            timeout=10,
        )

        if response.status_code not in [200, 202]:
            logger.error(f"Respuesta MailerSend: {response.status_code} - {response.text}")
            response.raise_for_status()

        logger.info(f"Email enviado exitosamente a {config.to_emails}")
    except requests.RequestException as exc:
        logger.error(f"Error enviando email: {exc}")


@app.get("/", tags=["Health"])
def root() -> dict[str, str]:
    return {"message": "API de Monitoreo Embalse Arandanos activa"}


@app.get("/health", tags=["Health"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/dashboard", response_model=DashboardResponse, tags=["Dashboard"])
def get_dashboard_data() -> DashboardResponse:
    """Obtener datos del dashboard, actualizados desde MongoDB"""
    state = update_dashboard_state_from_mongodb()
    if state is None:
        # Devolver datos simulados si no hay datos reales
        now = datetime.utcnow()
        state = DashboardResponse(
            ph=SensorData(
                value=6.66,
                min=6.0,
                max=8.5,
                safeMax=8.0,
                lastUpdated=now,
                status="stable",
            ),
            temperature=SensorData(
                value=21.35,
                min=5,
                max=35,
                safeMax=28,
                lastUpdated=now,
                status="stable",
            ),
            conductivity=SensorData(
                value=968.34,
                min=100,
                max=2000,
                safeMax=1500,
                lastUpdated=now,
                status="stable",
            ),
            metadata=Metadata(
                systemStatus="degraded",
                arduinoConnected=False,
                lastSync=now,
                uptime=0,
                activeSensors=0,
            ),
        )
        logger.info("Devolviendo datos simulados por falta de datos reales")
    return state


# ============================================================================
# ENDPOINTS PARA SENSORES (ESP8266)
# ============================================================================

@app.put("/api/sensors/ph", response_model=dict, status_code=200, tags=["Sensores"])
def update_sensor_readings(reading: SensorReading):
    """
    Recibir lecturas de sensores del ESP8266 y guardar en MongoDB.
    El ESP8266 envia datos vía HTTP PUT en formato JSON.
    """
    logger.info(f"Recibiendo datos de sensores: pH={reading.ph}, Temp={reading.temperature}, Cond={reading.conductivity}")
    
    # Guardar en MongoDB
    mongo_id = save_sensor_reading_to_mongodb(reading)
    
    # Actualizar dashboard inmediatamente
    update_dashboard_state_from_mongodb()
    
    return {
        "status": "success",
        "message": "Datos guardados en MongoDB",
        "id": mongo_id,
        "data": {
            "ph": reading.ph,
            "temperature": reading.temperature,
            "conductivity": reading.conductivity,
            "timestamp": reading.timestamp
        }
    }


@app.post("/api/sensors/readings", response_model=dict, status_code=201, tags=["Sensores"])
def create_sensor_reading(reading: SensorReading):
    """
    Recibir y guardar una lectura de sensores.
    Alternativa POST al endpoint PUT.
    """
    logger.info(f"Nueva lectura de sensores: pH={reading.ph}, Temp={reading.temperature}, Cond={reading.conductivity}")
    
    mongo_id = save_sensor_reading_to_mongodb(reading)
    update_dashboard_state_from_mongodb()
    
    return {
        "status": "success",
        "message": "Lectura guardada",
        "id": mongo_id,
        "data": reading.dict()
    }


@app.put("/api/sensors/{sensor_id}", response_model=dict, status_code=200, tags=["Sensores"])
def update_sensor_readings_by_id(
    sensor_id: str,
    payload: SensorMongoPayload | SensorReadingNestedPayload,
):
    """
    Recibe y guarda lecturas de ESP8266 en MongoDB.
    Esquema recomendado:
    {
      "arduino_id": "flotador-1",
      "timestamp": 1710788070,
      "mediciones": {"ph": 6.5, "temperatura": 20, "conductividad": 1},
      "bateria": 80
    }
    También acepta el esquema legacy: {"readings": {...}}.
    """
    if isinstance(payload, SensorMongoPayload):
        normalized_payload = payload.model_copy(
            update={"arduino_id": payload.arduino_id or sensor_id}
        )
        mongo_id = save_sensor_payload_to_mongodb(normalized_payload)
        response_data = {
            "arduino_id": normalized_payload.arduino_id,
            "timestamp": normalized_payload.timestamp,
            "mediciones": normalized_payload.mediciones.model_dump(),
            "bateria": normalized_payload.bateria,
        }
    else:
        latest = get_latest_sensor_reading() or {}
        incoming = payload.readings

        ph = incoming.ph if incoming.ph is not None else latest.get("ph")
        temperature = incoming.temperature if incoming.temperature is not None else latest.get("temperature")
        conductivity = incoming.conductivity if incoming.conductivity is not None else latest.get("conductivity")

        if ph is None or temperature is None or conductivity is None:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Lectura incompleta. Debes enviar ph, temperature y conductivity "
                    "(o tener una lectura previa para completar valores faltantes)."
                ),
            )

        normalized_payload = SensorMongoPayload(
            arduino_id=sensor_id,
            timestamp=incoming.timestamp,
            mediciones=SensorMeasurements(
                ph=float(ph),
                temperatura=float(temperature),
                conductividad=float(conductivity),
            ),
            bateria=100,
        )
        mongo_id = save_sensor_payload_to_mongodb(normalized_payload)
        response_data = {
            "arduino_id": normalized_payload.arduino_id,
            "timestamp": normalized_payload.timestamp,
            "mediciones": normalized_payload.mediciones.model_dump(),
            "bateria": normalized_payload.bateria,
            "humidity": incoming.humidity,
        }

    update_dashboard_state_from_mongodb()

    return {
        "status": "success",
        "message": "Datos guardados en MongoDB",
        "id": mongo_id,
        "sensor_id": sensor_id,
        "data": response_data,
    }


@app.get("/api/sensors/latest", response_model=Optional[SensorDataResponse], tags=["Sensores"])
def get_latest_reading():
    """Obtener la última lectura de sensores desde MongoDB"""
    reading = get_latest_sensor_reading()
    if reading:
        return SensorDataResponse(**reading)
    return None


@app.get("/api/sensors/history", response_model=list[SensorDataResponse], tags=["Sensores"])
def get_readings_history(limit: int = 100):
    """Obtener historial de lecturas de sensores (últimas N lecturas)"""
    readings = get_sensor_readings_history(limit)
    return [SensorDataResponse(**r) for r in readings]


@app.get("/api/alerts", response_model=list[AlertRecord], tags=["Alertas"])
def list_alerts() -> list[AlertRecord]:
    return alerts_store


@app.post("/api/alerts", response_model=AlertRecord, status_code=201, tags=["Alertas"])
def create_alert(payload: AlertCreate) -> AlertRecord:
    now = datetime.utcnow()
    device_name = payload.nombreDispositivo or payload.embalse
    new_alert = AlertRecord(
        id=(alerts_store[-1].id + 1) if alerts_store else 1,
        fecha=now.strftime("%Y-%m-%d"),
        hora=now.strftime("%H:%M"),
        embalse=device_name,
        sensor=payload.sensor,
        medicion=payload.medicion,
    )

    if measurement_is_out_of_range(payload):
        send_mailersend_notification(
            device_name=device_name,
            sensor=payload.sensor,
            medicion=payload.medicion,
            now=now,
        )

    alerts_store.append(new_alert)
    return new_alert


@app.get("/api/alerts/{alert_id}", response_model=AlertRecord, tags=["Alertas"])
def get_alert(alert_id: int) -> AlertRecord:
    for alert in alerts_store:
        if alert.id == alert_id:
            return alert
    raise HTTPException(status_code=404, detail="Alerta no encontrada")
