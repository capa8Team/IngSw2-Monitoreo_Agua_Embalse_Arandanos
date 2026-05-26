import logging
from typing import Optional

from fastapi import APIRouter

from models import SensorDataResponse
from services.mongodb import get_latest_sensor_reading, get_sensor_readings_history

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sensors", tags=["Sensores"])

# Ingesta de lecturas: AWS IoT Core (MQTT, topic boya/sensores) → MongoDB.
# Este router solo expone consulta para el dashboard.


@router.get("/latest", response_model=Optional[SensorDataResponse])
def get_latest_reading():
    """Última lectura almacenada (origen MQTT / MongoDB)."""
    reading = get_latest_sensor_reading()
    return SensorDataResponse(**reading) if reading else None


@router.get("/history", response_model=list[SensorDataResponse])
def get_readings_history(limit: int = 100):
    """Historial de lecturas para gráficos y tablas."""
    readings = get_sensor_readings_history(limit)
    return [SensorDataResponse(**r) for r in readings]
