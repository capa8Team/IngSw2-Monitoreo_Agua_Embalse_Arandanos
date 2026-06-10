import logging
from typing import Annotated

from fastapi import APIRouter, Depends

from core.tenant import TenantContext, get_tenant_context
from services.mongodb import (
    chile_now,
    db,
    get_latest_sensor_reading,
    to_chile_time,
)
from services.aws_iot import aws_iot_service
from core.config import settings
from db.database import engine
from db.supabase_db import check_logs_db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Diagnostics"])


@router.get("/api/diagnostics")
def get_diagnostics(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
) -> dict:
    """Estado del sistema para la organización activa."""
    mongodb_connected = db is not None
    readings_filter = tenant.readings_filter()

    sensor_reading = None
    last_reading_time = None
    arduino_connected = False
    data_source = "simulated"

    if mongodb_connected:
        sensor_reading = get_latest_sensor_reading(tenant_filter=readings_filter)
        if sensor_reading:
            last_reading_time = sensor_reading.get("timestamp")
            seconds_since = max(
                0.0,
                (chile_now() - to_chile_time(last_reading_time)).total_seconds(),
            )
            arduino_connected = seconds_since <= 30
            data_source = "real"

    iot = aws_iot_service.status
    logs_db = check_logs_db(engine)
    return {
        "mongodb_connected": mongodb_connected,
        "logs_db": logs_db,
        "data_source": data_source,
        "has_sensor_data": sensor_reading is not None,
        "arduino_connected": arduino_connected,
        "last_reading": str(last_reading_time) if last_reading_time else None,
        "organization_id": tenant.organization_id,
        "organization_slug": tenant.organization_slug,
        "db": settings.MONGODB_DB if mongodb_connected else "none",
        "aws_iot": {
            "enabled": iot.enabled,
            "configured": iot.configured,
            "connected": iot.connected,
            "subscribed": iot.subscribed,
            "topic": iot.topic,
            "messages_received": iot.messages_received,
            "last_message_at": str(iot.last_message_at) if iot.last_message_at else None,
            "last_error": iot.last_error,
        },
        "message": (
            "Usando datos reales de MongoDB"
            if data_source == "real"
            else "MongoDB no disponible o sin datos para esta organización"
        ),
    }


@router.get("/api/data/mongodb")
def get_mongodb_all_data(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
) -> dict:
    """Lecturas de sensor_readings de la organización activa (debug)."""
    if db is None:
        return {
            "error": True,
            "message": "MongoDB no está conectado",
            "data": [],
        }

    try:
        collection = db["sensor_readings"]
        readings_filter = tenant.readings_filter()
        documents = list(
            collection.find(readings_filter).sort("timestamp", -1).limit(500)
        )

        data = []
        for doc in documents:
            doc["_id"] = str(doc["_id"])
            doc["timestamp"] = str(doc.get("timestamp", ""))
            data.append(doc)

        return {
            "error": False,
            "total_registros": len(data),
            "organization_id": tenant.organization_id,
            "organization_slug": tenant.organization_slug,
            "message": f"Se encontraron {len(data)} registros para esta organización",
            "data": data,
        }
    except Exception as e:
        logger.error("Error obteniendo datos de MongoDB: %s", e)
        return {
            "error": True,
            "message": f"Error: {e}",
            "data": [],
        }
