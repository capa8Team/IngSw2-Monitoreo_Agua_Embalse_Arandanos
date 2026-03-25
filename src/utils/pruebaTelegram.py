from datetime import datetime


def preparar_alerta_telegram(sensor, valor, limites):
    """Simula el armado del contenido mínimo de una alerta Telegram."""
    min_f, max_f = limites
    if valor < min_f or valor > max_f:
        now = datetime.now()
        return {
            "dispositivo": "ESP32_Embalse_01",
            "fecha": now.strftime("%d/%m/%Y"),
            "hora": now.strftime("%H:%M:%S"),
            "sensor": sensor,
            "medicion": valor,
            "estatus": "ANOMALIA_DETECTADA",
        }
    return None


def test_hu15_contenido_mensaje_telegram_fuera_rango():
    """HU15: Verifica campos obligatorios del mensaje cuando hay anomalía."""
    limites_ph = (6.5, 8.5)
    lectura_critica = 4.0

    alerta = preparar_alerta_telegram("pH", lectura_critica, limites_ph)

    assert alerta is not None
    assert alerta["sensor"] == "pH"
    assert alerta["medicion"] == 4.0
    assert alerta["estatus"] == "ANOMALIA_DETECTADA"
    assert "dispositivo" in alerta
    assert "fecha" in alerta
    assert "hora" in alerta


def test_hu15_no_alerta_si_dato_en_rango():
    """HU15: No debe generarse alerta si la medición está en rango."""
    limites_ph = (6.5, 8.5)
    lectura_normal = 7.1

    alerta = preparar_alerta_telegram("pH", lectura_normal, limites_ph)

    assert alerta is None