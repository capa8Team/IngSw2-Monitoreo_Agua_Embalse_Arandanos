"""Parser de telemetría MQTT (formato ReciberConPostMQTT)."""

from services.aws_iot import parse_iot_telemetry


def test_parse_boya_sensores_payload():
    payload = {
        "nombre": "BoyaArandanos",
        "id_env": 7,
        "pH": 7.15,
        "temperatura": 21.3,
        "EC": 512.0,
        "bateria": 92,
        "timestamp": 1716650000,
        "fecha_hora": "2026-05-25 14:30:00",
        "zona_horaria": "America/Santiago",
    }
    result = parse_iot_telemetry(payload, "boya/sensores")

    assert result is not None
    assert result.arduino_id == "BoyaArandanos-7"
    assert result.mediciones.ph == 7.15
    assert result.mediciones.temperatura == 21.3
    assert result.mediciones.conductividad == 512.0
    assert result.bateria == 92
    assert result.timestamp == 1716650000


def test_parse_rejects_incomplete_payload():
    assert parse_iot_telemetry({"pH": 7.0}, "boya/sensores") is None
