"""
Sensores — lectura desde MongoDB.

La ingesta de telemetría (pH, temperatura, conductividad, batería) se realiza
vía AWS IoT Core (MQTT, topic boya/sensores), no por HTTP desde el dispositivo.
"""
import logging
from typing import Optional

from fastapi import APIRouter

from models import SensorDataResponse
from services.mongodb import get_latest_sensor_reading, get_sensor_readings_history

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sensors", tags=["Sensores"])


@router.get("/latest", response_model=Optional[SensorDataResponse])
def get_latest_reading():
    """Última lectura persistida (origen: AWS IoT → MongoDB)."""
    reading = get_latest_sensor_reading()
    return SensorDataResponse(**reading) if reading else None


@router.get("/history", response_model=list[SensorDataResponse])
def get_readings_history(limit: int = 100):
    """Historial de lecturas (origen: AWS IoT → MongoDB)."""
    readings = get_sensor_readings_history(limit)
    return [SensorDataResponse(**r) for r in readings]
