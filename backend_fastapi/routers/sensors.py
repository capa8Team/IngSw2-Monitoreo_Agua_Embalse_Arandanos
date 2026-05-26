import logging
from typing import Optional
from fastapi import APIRouter, HTTPException

from models import (
    SensorPhPostReading, SensorReading, SensorMongoPayload, 
    SensorReadingNestedPayload, SensorMeasurements, SensorDataResponse
)
from services.mongodb import (
    save_sensor_payload_to_mongodb, save_sensor_reading_to_mongodb,
    get_latest_sensor_reading, get_sensor_readings_history,
    update_dashboard_state_from_mongodb, build_payload_from_ph_post
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sensors", tags=["Sensores"])

@router.post("/ph", response_model=dict, status_code=201)
def create_sensor_ph_post(reading: SensorPhPostReading):
    logger.info("POST pH recibido: sensor_id=%s, id_env=%s, pH=%s", reading.sensor_id, reading.id_env, reading.ph)
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

@router.put("/ph", response_model=dict, status_code=200)
def update_sensor_readings(reading: SensorReading):
    logger.info(f"Recibiendo datos de sensores: pH={reading.ph}, Temp={reading.temperature}, Cond={reading.conductivity}")
    mongo_id = save_sensor_reading_to_mongodb(reading)
    update_dashboard_state_from_mongodb()
    
    return {
        "status": "success",
        "message": "Datos guardados en MongoDB",
        "id": mongo_id,
        "data": reading.model_dump()
    }

@router.post("/readings", response_model=dict, status_code=201)
def create_sensor_reading(reading: SensorReading):
    logger.info(f"Nueva lectura de sensores: pH={reading.ph}, Temp={reading.temperature}, Cond={reading.conductivity}")
    mongo_id = save_sensor_reading_to_mongodb(reading)
    update_dashboard_state_from_mongodb()
    
    return {
        "status": "success",
        "message": "Lectura guardada",
        "id": mongo_id,
        "data": reading.model_dump()
    }

@router.put("/{sensor_id}", response_model=dict, status_code=200)
def update_sensor_readings_by_id(sensor_id: str, payload: SensorMongoPayload | SensorReadingNestedPayload):
    if isinstance(payload, SensorMongoPayload):
        normalized_payload = payload.model_copy(update={"arduino_id": payload.arduino_id or sensor_id})
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
            raise HTTPException(status_code=400, detail="Lectura incompleta. Faltan datos.")

        normalized_payload = SensorMongoPayload(
            arduino_id=sensor_id,
            timestamp=incoming.timestamp,
            mediciones=SensorMeasurements(ph=float(ph), temperatura=float(temperature), conductividad=float(conductivity)),
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
    return {"status": "success", "message": "Datos guardados en MongoDB", "id": mongo_id, "sensor_id": sensor_id, "data": response_data}

@router.get("/latest", response_model=Optional[SensorDataResponse])
def get_latest_reading():
    reading = get_latest_sensor_reading()
    return SensorDataResponse(**reading) if reading else None

@router.get("/history", response_model=list[SensorDataResponse])
def get_readings_history(limit: int = 100):
    readings = get_sensor_readings_history(limit)
    return [SensorDataResponse(**r) for r in readings]