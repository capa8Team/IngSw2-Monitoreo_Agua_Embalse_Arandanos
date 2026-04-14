import os
import logging
import asyncio
import math
import random
from datetime import datetime, timezone
from typing import Literal, Optional
from logging.handlers import RotatingFileHandler
from zoneinfo import ZoneInfo

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
CHILE_TZ = ZoneInfo("America/Santiago")


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


def configure_logging() -> None:
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    base_dir = os.path.dirname(os.path.abspath(__file__))
    logs_dir = os.path.join(base_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    log_file_path = os.path.join(logs_dir, "app.log")

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s: %(message)s [in %(filename)s:%(lineno)d]"
    )

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)

    file_handler = RotatingFileHandler(log_file_path, maxBytes=16384, backupCount=20)
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
    # Intentar con SSL verificado primero
    mongo_client = MongoClient(
        MONGODB_URL, 
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000,
        socketTimeoutMS=5000,
    )
    # Verificar conexión
    mongo_client.admin.command('ping')
    db = mongo_client[MONGODB_DB]
    logger.info("Conexion a MongoDB establecida")
except Exception as e:
    logger.warning(f"No se pudo conectar a MongoDB con SSL verificado: {e}")
    try:
        # Intentar sin verificación SSL como fallback
        import ssl
        mongo_client = MongoClient(
            MONGODB_URL,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            socketTimeoutMS=5000,
            tlsAllowInvalidCertificates=True,
            tlsAllowInvalidHostnames=True,
        )
        mongo_client.admin.command('ping')
        db = mongo_client[MONGODB_DB]
        logger.info("Conexión a MongoDB establecida (con SSL deshabilitado)")
    except Exception as e2:
        logger.warning(f"No se pudo conectar a MongoDB. Usando almacenamiento en memoria. Error: {e2}")
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


class SensorPhPostReading(BaseModel):
    sensor_id: str
    id_env: int
    ph: float
    timestamp: int | None = None
    temperature: float | None = None
    conductivity: float | None = None
    bateria: int = Field(default=100, ge=0, le=100)


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
    template_id: str
    max_recipients_per_request: int


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

# Variable para controlar la tarea de background que genera datos simulados
background_task: Optional[asyncio.Task] = None
# Desactivado por defecto para priorizar datos reales del ESP8266.
SIMULATED_DATA_ENABLED = os.getenv("SIMULATED_DATA_ENABLED", "false").lower() == "true"


# ============================================================================
# FUNCIONES MONGODB
# ============================================================================

def _resolve_sensor_timestamp(timestamp: int | None) -> tuple[datetime, int | None]:
    if timestamp is None:
        return utc_now(), None

    # ESP8266 suele enviar millis()/1000; si no parece epoch UTC, usamos hora del servidor.
    if timestamp >= 1_500_000_000:
        return epoch_to_utc_datetime(timestamp), None
    return utc_now(), timestamp


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


def build_payload_from_ph_post(reading: SensorPhPostReading) -> SensorMongoPayload:
    """Convierte el payload reducido del ESP8266 a esquema completo para MongoDB."""
    latest = get_latest_sensor_reading() or {}

    temperature = (
        float(reading.temperature)
        if reading.temperature is not None
        else float(latest.get("temperature", 0.0))
    )
    conductivity = (
        float(reading.conductivity)
        if reading.conductivity is not None
        else float(latest.get("conductivity", 0.0))
    )

    return SensorMongoPayload(
        arduino_id=f"{reading.sensor_id}-{reading.id_env}",
        timestamp=reading.timestamp,
        mediciones=SensorMeasurements(
            ph=float(reading.ph),
            temperatura=temperature,
            conductividad=conductivity,
        ),
        bateria=reading.bateria,
    )


def normalize_sensor_document(reading: dict) -> dict:
    """Normaliza documento Mongo (esquema nuevo o legado) al formato usado por la API."""
    mediciones = reading.get("mediciones", {})
    ph = mediciones.get("ph", reading.get("ph"))
    temperature = mediciones.get("temperatura", reading.get("temperature"))
    conductivity = mediciones.get("conductividad", reading.get("conductivity"))

    normalized_timestamp = to_chile_time(reading.get("timestamp", utc_now()))

    return {
        "id": str(reading.get("_id", reading.get("id", ""))),
        "arduino_id": reading.get("arduino_id", reading.get("sensor_id", "esp8266_1")),
        "ph": float(ph) if ph is not None else 0.0,
        "temperature": float(temperature) if temperature is not None else 0.0,
        "conductivity": float(conductivity) if conductivity is not None else 0.0,
        "bateria": int(reading.get("bateria", 100)),
        "timestamp": normalized_timestamp,
    }


def get_latest_sensor_reading() -> Optional[dict]:
    """Obtener la última lectura de sensores desde MongoDB"""
    if db is None:
        logger.warning("MongoDB no está disponible")
        return None
    
    try:
        collection = db["sensor_readings"]
        # Usamos _id para obtener la última inserción real y evitar bloqueos por
        # dispositivos con reloj desfasado o timestamps futuros.
        reading = collection.find_one(sort=[("_id", -1)])
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
        readings = list(collection.find().sort("_id", -1).limit(limit))
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

    now = chile_now()

    # Determinar estado basado en rangos
    def get_status(value: float, min_val: float, max_val: float, safe_max: float) -> str:
        if value < min_val or value > max_val:
            return "critical"
        if value > safe_max:
            return "warning"
        return "stable"

    last_updated = to_chile_time(reading.get("timestamp"))
    # El Arduino se considera conectado si hay una lectura en los últimos 30 segundos
    time_since_reading = max(0.0, (now - last_updated).total_seconds())
    connected = time_since_reading <= 30
    
    # Calcular uptime del sistema (cuánto tiempo ha pasado desde la última lectura)
    uptime_seconds = max(0, int(time_since_reading))

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
            uptime=uptime_seconds,
            activeSensors=3 if connected else 0,
        ),
    )
    logger.info(f"Dashboard actualizado desde MongoDB. Arduino conectado: {connected}")
    return dashboard_state


def get_mailersend_config() -> MailerSendConfig:
    to_emails_raw = os.getenv("MAILERSEND_TO_EMAILS", "")
    # Mantener orden y remover duplicados para evitar envios repetidos.
    to_emails = list(dict.fromkeys(email.strip() for email in to_emails_raw.split(",") if email.strip()))

    max_recipients_raw = os.getenv("MAILERSEND_MAX_RECIPIENTS_PER_REQUEST", "1").strip()
    try:
        max_recipients = max(1, int(max_recipients_raw))
    except ValueError:
        logger.warning(
            "MAILERSEND_MAX_RECIPIENTS_PER_REQUEST invalido (%s). Usando 1.",
            max_recipients_raw,
        )
        max_recipients = 1

    return MailerSendConfig(
        api_token=os.getenv("MAILERSEND_API_TOKEN"),
        from_email=os.getenv("MAILERSEND_FROM_EMAIL"),
        from_name=os.getenv("MAILERSEND_FROM_NAME", "Monitoreo Embalse Arandanos"),
        to_emails=to_emails,
        template_id=os.getenv("MAILERSEND_TEMPLATE_ID", "351ndgw8m7rgzqx8"),
        max_recipients_per_request=max_recipients,
    )


def chunk_recipients(recipients: list[str], chunk_size: int) -> list[list[str]]:
    if chunk_size <= 0:
        chunk_size = 1
    return [recipients[i:i + chunk_size] for i in range(0, len(recipients), chunk_size)]


def is_mailersend_recipient_limit_error(response: requests.Response) -> bool:
    if response.status_code != 422:
        return False

    text = response.text or ""
    if "MS42205" in text:
        return True

    try:
        data = response.json()
    except ValueError:
        return False

    if isinstance(data, dict):
        message_text = f"{data.get('message', '')} {data.get('code', '')}"
        if "MS42205" in message_text:
            return True
    return False


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

    def build_payload(recipients: list[str]) -> dict:
        return {
            "from": {
                "email": config.from_email,
                "name": config.from_name,
            },
            "to": [{"email": email} for email in recipients],
            "subject": f"⚠️ Alerta: {sensor} fuera de rango - {device_name}",
            "template_id": config.template_id,
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
                for email in recipients
            ],
        }

    headers = {
        "Authorization": f"Bearer {config.api_token}",
        "Content-Type": "application/json",
    }

    recipient_batches = chunk_recipients(config.to_emails, config.max_recipients_per_request)

    for recipients_batch in recipient_batches:
        try:
            response = requests.post(
                "https://api.mailersend.com/v1/email",
                json=build_payload(recipients_batch),
                headers=headers,
                timeout=10,
            )
        except requests.RequestException as exc:
            logger.error(f"Error enviando email a lote {recipients_batch}: {exc}")
            continue

        if response.status_code in [200, 202]:
            logger.info(f"Email enviado exitosamente a lote {recipients_batch}")
            continue

        if is_mailersend_recipient_limit_error(response) and len(recipients_batch) > 1:
            logger.warning(
                "MailerSend limito cantidad de destinatarios en lote. Reintentando 1 a 1."
            )
            for email in recipients_batch:
                try:
                    single_response = requests.post(
                        "https://api.mailersend.com/v1/email",
                        json=build_payload([email]),
                        headers=headers,
                        timeout=10,
                    )
                    if single_response.status_code in [200, 202]:
                        logger.info(f"Email enviado exitosamente a {email}")
                    else:
                        logger.error(
                            "Respuesta MailerSend individual %s para %s: %s",
                            single_response.status_code,
                            email,
                            single_response.text,
                        )
                except requests.RequestException as single_exc:
                    logger.error(f"Error enviando email individual a {email}: {single_exc}")
            continue

        logger.error(
            "Respuesta MailerSend para lote %s: %s - %s",
            recipients_batch,
            response.status_code,
            response.text,
        )


# ============================================================================
# DATOS SIMULADOS EN BACKGROUND
# ============================================================================

def generate_simulated_sensor_data() -> SensorMongoPayload:
    """Generar datos de sensores simulados realistas"""
    now = chile_now()
    
    # Simular variación natural usando funciones trigonométricas
    hours_elapsed = (now.hour + now.minute / 60 + now.second / 3600)
    
    # pH con variación leve (~6.5-7.5)
    ph_value = 7.0 + 0.3 * math.sin(hours_elapsed * 0.26)  # Ciclo cada ~24h
    
    # Temperatura con variación diaria (~18-26°C)
    temp_value = 22.0 + 3.5 * math.sin(hours_elapsed * 0.26)
    
    # Conductividad con variación (~800-1100)
    conductivity_value = 950 + 100 * math.sin(hours_elapsed * 0.26)
    
    # Agregar pequeño ruido
    ph_value += random.uniform(-0.1, 0.1)
    temp_value += random.uniform(-0.3, 0.3)
    conductivity_value += random.uniform(-20, 20)
    
    # Limitar rangos
    ph_value = max(6.0, min(8.5, ph_value))
    temp_value = max(5, min(35, temp_value))
    conductivity_value = max(100, min(2000, conductivity_value))
    
    payload = SensorMongoPayload(
        arduino_id="simulador-arandanos",
        timestamp=int(now.timestamp()),
        mediciones=SensorMeasurements(
            ph=round(ph_value, 2),
            temperatura=round(temp_value, 2),
            conductividad=round(conductivity_value, 2),
        ),
        bateria=95,
    )
    return payload


async def simulated_data_background_task():
    """Tarea de background que genera y guarda datos simulados cada 10 segundos"""
    logger.info("[INFO] Iniciando generador de datos simulados (cada 10 segundos)")
    
    while SIMULATED_DATA_ENABLED:
        try:
            # Generar datos simulados
            payload = generate_simulated_sensor_data()
            
            # Guardar en MongoDB
            mongo_id = save_sensor_payload_to_mongodb(payload)
            
            # Actualizar estado del dashboard
            update_dashboard_state_from_mongodb()
            
            logger.info(f"[OK] Datos simulados guardados en MongoDB (ID: {mongo_id})")
            
            # Esperar 10 segundos antes de la siguiente lectura
            await asyncio.sleep(10)
        except Exception as e:
            logger.error(f"[ERROR] Error en tarea de datos simulados: {e}")
            await asyncio.sleep(5)  # Esperar 5 segundos antes de reintentar


@app.on_event("startup")
async def startup_event():
    """Ejecutar cuando la aplicación inicia"""
    global background_task
    logger.info("[START] Aplicacion iniciando...")
    
    if SIMULATED_DATA_ENABLED and db is not None:
        # Iniciar la tarea de background para generar datos simulados
        background_task = asyncio.create_task(simulated_data_background_task())
        logger.info("[OK] Tarea de datos simulados iniciada")
    else:
        if db is None:
            logger.warning("[WARN] MongoDB no disponible, datos simulados desactivados")
        else:
            logger.info("[INFO] Datos simulados desactivados (SIMULATED_DATA_ENABLED=False)")


@app.on_event("shutdown")
async def shutdown_event():
    """Ejecutar cuando la aplicación se detiene"""
    global background_task
    logger.info("[STOP] Aplicacion deteniendo...")
    
    if background_task:
        background_task.cancel()
        try:
            await background_task
        except asyncio.CancelledError:
            logger.info("[OK] Tarea de datos simulados cancelada")


@app.get("/", tags=["Health"])
def root() -> dict[str, str]:
    return {"message": "API de Monitoreo Embalse Arandanos activa"}


@app.get("/health", tags=["Health"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/diagnostics", tags=["Diagnostics"])
def get_diagnostics() -> dict:
    """Endpoint de diagnóstico para verificar el estado del sistema"""
    mongodb_connected = db is not None
    
    sensor_reading = None
    last_reading_time = None
    arduino_connected = False
    data_source = "simulated"  # Por defecto datos simulados
    
    if mongodb_connected:
        sensor_reading = get_latest_sensor_reading()
        if sensor_reading:
            last_reading_time = sensor_reading.get("timestamp")
            # El Arduino se considera conectado si hay una lectura en los últimos 30 segundos
            time_since_reading = max(0.0, (chile_now() - to_chile_time(last_reading_time)).total_seconds())
            arduino_connected = time_since_reading <= 30
            data_source = "real"
    
    return {
        "mongodb_connected": mongodb_connected,
        "data_source": data_source,  # "real" o "simulated"
        "has_sensor_data": sensor_reading is not None,
        "arduino_connected": arduino_connected,
        "last_reading": str(last_reading_time) if last_reading_time else None,
        "db": MONGODB_DB if mongodb_connected else "none",
        "message": "Usando datos reales de MongoDB" if data_source == "real" else "Usando datos simulados",
    }


@app.get("/api/dashboard", response_model=DashboardResponse, tags=["Dashboard"])
def get_dashboard_data() -> DashboardResponse:
    """Obtener datos del dashboard, usando MongoDB o fallback simulado."""
    state = update_dashboard_state_from_mongodb()
    if state is None:
        simulated_payload = generate_simulated_sensor_data()
        now = chile_now()

        def get_status(value: float, min_val: float, max_val: float, safe_max: float) -> str:
            if value < min_val or value > max_val:
                return "critical"
            if value > safe_max:
                return "warning"
            return "stable"

        ph_value = simulated_payload.mediciones.ph
        temperature_value = simulated_payload.mediciones.temperatura
        conductivity_value = simulated_payload.mediciones.conductividad

        state = DashboardResponse(
            ph=SensorData(
                value=ph_value,
                min=6.0,
                max=8.5,
                safeMax=8.0,
                lastUpdated=now,
                status=get_status(ph_value, 6.0, 8.5, 8.0),
            ),
            temperature=SensorData(
                value=temperature_value,
                min=5,
                max=35,
                safeMax=28,
                lastUpdated=now,
                status=get_status(temperature_value, 5, 35, 28),
            ),
            conductivity=SensorData(
                value=conductivity_value,
                min=100,
                max=2000,
                safeMax=1500,
                lastUpdated=now,
                status=get_status(conductivity_value, 100, 2000, 1500),
            ),
            metadata=Metadata(
                systemStatus="operational",
                arduinoConnected=True,
                lastSync=now,
                uptime=0,
                activeSensors=3,
            ),
        )
        logger.info("Devolviendo datos simulados (fallback)")
    return state


# ============================================================================
# ENDPOINTS PARA SENSORES (ESP8266)
# ============================================================================

@app.post("/api/sensors/ph", response_model=dict, status_code=201, tags=["Sensores"])
def create_sensor_ph_post(reading: SensorPhPostReading):
    """
    Recibir lecturas de pH enviadas por ESP8266 vía HTTP POST.
    Formato esperado:
    {
      "sensor_id": "sensor-ph-a",
      "id_env": 1,
      "ph": 7.12,
      "timestamp": 12345
    }
    """
    logger.info(
        "POST pH recibido: sensor_id=%s, id_env=%s, pH=%s",
        reading.sensor_id,
        reading.id_env,
        reading.ph,
    )

    payload = build_payload_from_ph_post(reading)
    mongo_id = save_sensor_payload_to_mongodb(payload)
    update_dashboard_state_from_mongodb()

    return {
        "status": "success",
        "message": "Lectura de pH guardada",
        "id": mongo_id,
        "data": {
            "sensor_id": reading.sensor_id,
            "id_env": reading.id_env,
            "ph": reading.ph,
            "timestamp": reading.timestamp,
            "temperature": payload.mediciones.temperatura,
            "conductivity": payload.mediciones.conductividad,
        },
    }

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
    now = chile_now()
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


@app.get("/api/data/mongodb", tags=["Datos"])
def get_mongodb_all_data() -> dict:
    """
    Obtener TODOS los datos guardados en MongoDB.
    Extremadamente útil para ver exactamente qué está guardado.
    """
    if db is None:
        return {
            "error": True,
            "message": "MongoDB no está conectado",
            "data": []
        }
    
    try:
        collection = db["sensor_readings"]
        documents = list(collection.find().sort("timestamp", -1))
        
        # Convertir ObjectId a string para JSON
        data = []
        for doc in documents:
            doc["_id"] = str(doc["_id"])
            doc["timestamp"] = str(doc.get("timestamp", ""))
            data.append(doc)
        
        return {
            "error": False,
            "total_registros": len(data),
            "message": f"Se encontraron {len(data)} registros en MongoDB",
            "data": data
        }
    except Exception as e:
        logger.error(f"Error obteniendo datos de MongoDB: {e}")
        return {
            "error": True,
            "message": f"Error: {str(e)}",
            "data": []
        }
