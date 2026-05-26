"""
Suscriptor MQTT a AWS IoT Core.
Recibe telemetría (pH, temperatura, conductividad, batería) y la persiste en MongoDB.
"""
from __future__ import annotations

import json
import logging
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from core.config import settings
from core.log_service import log_service
from core.log_origins import LogLevel, LogOrigin
from models import SensorMeasurements, SensorMongoPayload

logger = logging.getLogger(__name__)


@dataclass
class AwsIotStatus:
    enabled: bool = False
    configured: bool = False
    connected: bool = False
    subscribed: bool = False
    last_message_at: Optional[datetime] = None
    last_error: Optional[str] = None
    topic: str = ""
    messages_received: int = 0


class AwsIotService:
    """Cliente MQTT (mTLS) hacia AWS IoT Core en un hilo en segundo plano."""

    def __init__(self) -> None:
        self._status = AwsIotStatus()
        self._connection = None
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

    @property
    def status(self) -> AwsIotStatus:
        return self._status

    def is_configured(self) -> bool:
        if not settings.AWS_IOT_ENABLED:
            return False
        required = (
            settings.AWS_IOT_ENDPOINT,
            settings.AWS_IOT_CLIENT_ID,
            settings.AWS_IOT_TOPIC,
            settings.AWS_IOT_CERT_PATH,
            settings.AWS_IOT_KEY_PATH,
            settings.AWS_IOT_CA_PATH,
        )
        if not all(required):
            return False
        for path in (
            settings.AWS_IOT_CERT_PATH,
            settings.AWS_IOT_KEY_PATH,
            settings.AWS_IOT_CA_PATH,
        ):
            if not Path(path).is_file():
                logger.warning("Certificado IoT no encontrado: %s", path)
                return False
        return True

    def start(self) -> None:
        self._status.enabled = settings.AWS_IOT_ENABLED
        self._status.topic = settings.AWS_IOT_TOPIC or ""

        if not settings.AWS_IOT_ENABLED:
            logger.info("AWS IoT Core deshabilitado (AWS_IOT_ENABLED=false)")
            return

        if not self.is_configured():
            msg = "AWS IoT habilitado pero faltan endpoint, topic o certificados"
            self._status.last_error = msg
            logger.warning(msg)
            log_service.log(
                LogOrigin.DASHBOARD, LogLevel.WARN, msg,
                component="aws_iot.client", operation="start",
            )
            return

        self._status.configured = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name="aws-iot-mqtt", daemon=True)
        self._thread.start()
        logger.info(
            "Hilo AWS IoT iniciado (endpoint=%s, topic=%s)",
            settings.AWS_IOT_ENDPOINT,
            settings.AWS_IOT_TOPIC,
        )

    def stop(self) -> None:
        self._stop_event.set()
        with self._lock:
            if self._connection is not None:
                try:
                    disconnect = self._connection.disconnect()
                    disconnect.result(timeout=5)
                except Exception as e:
                    logger.debug("Error al desconectar IoT: %s", e)
                self._connection = None
        self._status.connected = False
        self._status.subscribed = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=8)
        self._thread = None

    def _run(self) -> None:
        try:
            from awscrt import mqtt
            from awsiot import mqtt_connection_builder
        except ImportError as e:
            msg = f"Dependencia awsiotsdk no instalada: {e}"
            self._status.last_error = msg
            logger.error(msg)
            return

        def on_connection_interrupted(connection, error, **kwargs):
            self._status.connected = False
            self._status.subscribed = False
            self._status.last_error = str(error) if error else "conexión interrumpida"
            logger.warning("AWS IoT desconectado: %s", self._status.last_error)

        def on_connection_resumed(connection, return_code, session_present, **kwargs):
            self._status.connected = True
            self._status.last_error = None
            logger.info("AWS IoT reconectado (session_present=%s)", session_present)

        def on_message_received(topic, payload, dup, qos, retain, **kwargs):
            self._handle_message(topic, payload)

        try:
            connection = mqtt_connection_builder.mtls_from_path(
                endpoint=settings.AWS_IOT_ENDPOINT,
                port=settings.AWS_IOT_PORT,
                cert_filepath=settings.AWS_IOT_CERT_PATH,
                pri_key_filepath=settings.AWS_IOT_KEY_PATH,
                ca_filepath=settings.AWS_IOT_CA_PATH,
                client_id=settings.AWS_IOT_CLIENT_ID,
                clean_session=False,
                keep_alive_secs=30,
                on_connection_interrupted=on_connection_interrupted,
                on_connection_resumed=on_connection_resumed,
            )
            with self._lock:
                self._connection = connection

            connect_future = connection.connect()
            connect_future.result(timeout=15)
            self._status.connected = True
            self._status.last_error = None
            logger.info("Conectado a AWS IoT Core")

            subscribe_future, _packet_id = connection.subscribe(
                topic=settings.AWS_IOT_TOPIC,
                qos=mqtt.QoS.AT_LEAST_ONCE,
                callback=on_message_received,
            )
            subscribe_future.result(timeout=10)
            self._status.subscribed = True
            log_service.log(
                LogOrigin.DASHBOARD, LogLevel.INFO,
                f"Suscrito a {settings.AWS_IOT_TOPIC}",
                component="aws_iot.client", operation="subscribe",
            )

            while not self._stop_event.wait(timeout=1.0):
                pass
        except Exception as e:
            self._status.last_error = str(e)
            self._status.connected = False
            self._status.subscribed = False
            logger.exception("Error en cliente AWS IoT: %s", e)
            log_service.log(
                LogOrigin.DASHBOARD, LogLevel.FATAL, f"AWS IoT error: {e}",
                component="aws_iot.client", operation="connect",
                details={"error_type": type(e).__name__},
            )

    def _handle_message(self, topic: str, payload: bytes) -> None:
        from services.mongodb import (
            save_sensor_payload_to_mongodb,
            update_dashboard_state_from_mongodb,
            get_device_by_arduino_id,
            register_new_microcontroller
        )

        self._status.messages_received += 1
        self._status.last_message_at = datetime.now(timezone.utc)

        try:
            data = json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            self._status.last_error = f"JSON inválido: {e}"
            logger.warning("Mensaje IoT no parseable en %s: %s", topic, e)
            return

        sensor_payload = parse_iot_telemetry(data, topic)
        if sensor_payload is None:
            self._status.last_error = "Payload sin mediciones completas"
            logger.warning("Payload IoT incompleto en %s: %s", topic, data)
            return

        # 🔍 Detección automática de nuevos dispositivos por MQTT
        existing_device = get_device_by_arduino_id(sensor_payload.arduino_id)
        if not existing_device:
            # Auto-registrar nuevo dispositivo detectado
            device_name = data.get("nombre") or data.get("Nombre") or f"Dispositivo {sensor_payload.arduino_id}"
            new_device = register_new_microcontroller(
                arduino_id=sensor_payload.arduino_id,
                device_name=device_name,
                device_type="ESP8266",  # Por defecto ESP8266 para MQTT
                location=""
            )
            if new_device:
                logger.info(
                    "🔔 Nuevo dispositivo auto-registrado por MQTT (arduino_id=%s, name=%s)",
                    sensor_payload.arduino_id,
                    device_name
                )
                log_service.log(
                    LogOrigin.DASHBOARD, LogLevel.INFO,
                    f"Nuevo dispositivo detectado automáticamente: {device_name}",
                    component="aws_iot.auto_detect", operation="register_device",
                    details={"arduino_id": sensor_payload.arduino_id}
                )

        mongo_id = save_sensor_payload_to_mongodb(sensor_payload, source="aws_iot")
        if mongo_id:
            update_dashboard_state_from_mongodb()
            self._status.last_error = None
            logger.info(
                "Telemetría IoT guardada (device=%s, ph=%.2f, temp=%.1f, cond=%.0f, bat=%s%%)",
                sensor_payload.arduino_id,
                sensor_payload.mediciones.ph,
                sensor_payload.mediciones.temperatura,
                sensor_payload.mediciones.conductividad,
                sensor_payload.bateria,
            )
        else:
            self._status.last_error = "No se pudo guardar en MongoDB"


def _first_present(data: dict, *keys: str) -> Any:
    for key in keys:
        if key in data and data[key] is not None:
            return data[key]
    return None


def _device_id_from_topic(topic: str) -> Optional[str]:
    parts = [p for p in topic.split("/") if p]
    if len(parts) >= 2:
        return parts[-2] if parts[-1] in ("telemetry", "telemetria", "data") else parts[-1]
    return None


def parse_iot_telemetry(data: dict, topic: str) -> Optional[SensorMongoPayload]:
    """
    Formato principal: ReciberConPostMQTT → topic ``boya/sensores``::

        {
          "nombre": "Boya1",
          "id_env": 42,
          "pH": 7.1,
          "temperatura": 22.5,
          "EC": 480.0,
          "bateria": 87,
          "timestamp": 1716650000,
          "fecha_hora": "2026-05-25 14:30:00",
          "zona_horaria": "America/Santiago"
        }
    """
    mediciones_raw = data.get("mediciones") or data.get("measurements") or data

    ph = _first_present(mediciones_raw, "pH", "ph")
    temperatura = _first_present(mediciones_raw, "temperatura", "temperature", "temp", "Temp")
    conductividad = _first_present(
        mediciones_raw, "EC", "ec", "conductividad", "conductivity",
    )
    bateria = _first_present(data, "bateria", "battery", "bat", "CBat")
    if bateria is None:
        bateria = _first_present(mediciones_raw, "bateria", "battery", "bat", "CBat")

    if ph is None or temperatura is None or conductividad is None:
        return None

    nombre = _first_present(data, "nombre", "Nombre")
    id_env = _first_present(data, "id_env")
    if nombre is not None and id_env is not None:
        arduino_id = f"{nombre}-{id_env}"
    else:
        arduino_id = (
            _first_present(data, "arduino_id", "device_id", "thing_name", "sensor_id")
            or _device_id_from_topic(topic)
            or settings.AWS_IOT_DEFAULT_DEVICE_ID
        )

    timestamp = _first_present(data, "timestamp", "ts", "time")
    if timestamp is not None:
        timestamp = int(timestamp)

    bateria_val = int(bateria) if bateria is not None else 100
    bateria_val = max(0, min(100, bateria_val))

    return SensorMongoPayload(
        arduino_id=str(arduino_id),
        timestamp=timestamp,
        mediciones=SensorMeasurements(
            ph=float(ph),
            temperatura=float(temperatura),
            conductividad=float(conductividad),
        ),
        bateria=bateria_val,
    )


aws_iot_service = AwsIotService()
