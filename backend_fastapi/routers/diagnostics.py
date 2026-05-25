import logging
from fastapi import APIRouter
from services.mongodb import db, get_latest_sensor_reading, chile_now, to_chile_time
from core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Diagnostics"])


@router.get("/api/diagnostics")
def get_diagnostics() -> dict:
    """Estado del sistema: conexión MongoDB, fuente de datos, última lectura y estado del Arduino."""
    mongodb_connected = db is not None

    sensor_reading = None
    last_reading_time = None
    arduino_connected = False
    data_source = "simulated"

    if mongodb_connected:
        sensor_reading = get_latest_sensor_reading()
        if sensor_reading:
            last_reading_time = sensor_reading.get("timestamp")
            seconds_since = max(
                0.0,
                (chile_now() - to_chile_time(last_reading_time)).total_seconds(),
            )
            arduino_connected = seconds_since <= 30
            data_source = "real"

    return {
        "mongodb_connected": mongodb_connected,
        "data_source": data_source,
        "has_sensor_data": sensor_reading is not None,
        "arduino_connected": arduino_connected,
        "last_reading": str(last_reading_time) if last_reading_time else None,
        "db": settings.MONGODB_DB if mongodb_connected else "none",
        "message": (
            "Usando datos reales de MongoDB"
            if data_source == "real"
            else "MongoDB no disponible o sin datos"
        ),
    }


@router.get("/api/data/mongodb")
def get_mongodb_all_data() -> dict:
    """Retorna todos los documentos de sensor_readings ordenados por timestamp descendente. Útil para debug."""
    if db is None:
        return {
            "error": True,
            "message": "MongoDB no está conectado",
            "data": [],
        }

    try:
        collection = db["sensor_readings"]
        documents = list(collection.find().sort("timestamp", -1))

        data = []
        for doc in documents:
            doc["_id"] = str(doc["_id"])
            doc["timestamp"] = str(doc.get("timestamp", ""))
            data.append(doc)

        return {
            "error": False,
            "total_registros": len(data),
            "message": f"Se encontraron {len(data)} registros en MongoDB",
            "data": data,
        }
    except Exception as e:
        logger.error("Error obteniendo datos de MongoDB: %s", e)
        return {
            "error": True,
            "message": f"Error: {e}",
            "data": [],
        }
