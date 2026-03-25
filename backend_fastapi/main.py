import os
import logging
from datetime import datetime
from typing import Literal

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import requests

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = FastAPI(
    title="API Monitoreo Embalse Arandanos",
    description=(
        "API para exponer lecturas de sensores y respaldo de alertas del dashboard."
    ),
    version="1.0.0",
)

# Agregar middleware CORS para permitir requests desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir todos los orígenes (cambiar a lista específica en prod)
    allow_credentials=True,
    allow_methods=["*"],  # Permitir todos los métodos (GET, POST, OPTIONS, etc)
    allow_headers=["*"],
)


class SensorData(BaseModel):
    value: float
    min: float
    max: float
    safeMax: float
    lastUpdated: datetime
    status: Literal["stable", "warning", "critical"]


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


dashboard_state = DashboardResponse(
    ph=SensorData(
        value=7.2,
        min=6.0,
        max=8.5,
        safeMax=8.0,
        lastUpdated=datetime.utcnow(),
        status="stable",
    ),
    temperature=SensorData(
        value=22.5,
        min=5,
        max=35,
        safeMax=28,
        lastUpdated=datetime.utcnow(),
        status="stable",
    ),
    conductivity=SensorData(
        value=650,
        min=100,
        max=2000,
        safeMax=1500,
        lastUpdated=datetime.utcnow(),
        status="stable",
    ),
    metadata=Metadata(
        systemStatus="operational",
        arduinoConnected=True,
        lastSync=datetime.utcnow(),
        uptime=3600,
        activeSensors=3,
    ),
)

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


def build_alert_message(device_name: str, sensor: str, medicion: str, now: datetime) -> str:
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

    return (
        "Alerta de medicion fuera de rango\n\n"
        f"Nombre dispositivo: {device_name}\n"
        f"Dia: {day_name}\n"
        f"Fecha: {fecha}\n"
        f"Hora: {hora}\n"
        f"Sensor: {sensor}\n"
        f"Medicion: {medicion}"
    )


def send_mailersend_notification(device_name: str, sensor: str, medicion: str, now: datetime) -> None:
    config = get_mailersend_config()
    if not config.api_token or not config.from_email or not config.to_emails:
        logger.warning(
            f"MailerSend no configurado. API Token: {bool(config.api_token)}, "
            f"From Email: {bool(config.from_email)}, To Emails: {bool(config.to_emails)}"
        )
        return

    logger.info(f"Enviando alerta por email: {device_name} - {sensor}")

    message = build_alert_message(device_name, sensor, medicion, now)
    payload = {
        "from": {
            "email": config.from_email,
            "name": config.from_name,
        },
        "to": [{"email": email} for email in config.to_emails],
        "subject": f"⚠️ Alerta: {sensor} fuera de rango - {device_name}",
        "text": message,
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

        if response.status_code != 200:
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
    return dashboard_state


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
