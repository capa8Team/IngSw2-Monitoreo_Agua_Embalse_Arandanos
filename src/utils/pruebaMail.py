import time


def procesar_alerta_mail(valor, limites):
    """Simula la lógica de activación de alerta por correo."""
    start_time = time.time()
    min_f, max_f = limites

    if valor < min_f or valor > max_f:
        end_time = time.time()
        return {
            "enviar_mail": True,
            "tiempo_procesamiento": end_time - start_time,
            "asunto": "Alerta de Medición Anómala - Sistema de Riego",
        }

    end_time = time.time()
    return {
        "enviar_mail": False,
        "tiempo_procesamiento": end_time - start_time,
        "asunto": "Sin alertas",
    }


def test_hu16_tiempo_y_activacion_mail_fuera_rango():
    """HU16: Cuando el valor está fuera de rango, se activa el envío de mail."""
    limites_temp = (10.0, 30.0)
    lectura_critica = 35.0

    resultado = procesar_alerta_mail(lectura_critica, limites_temp)

    assert resultado["enviar_mail"] is True
    assert resultado["tiempo_procesamiento"] < 30
    assert "anómala" in resultado["asunto"].lower()


def test_hu16_no_mail_si_valor_en_rango():
    """HU16: Si la medición es normal, no se debe activar envío de mail."""
    limites_temp = (10.0, 30.0)
    lectura_normal = 22.5

    resultado = procesar_alerta_mail(lectura_normal, limites_temp)

    assert resultado["enviar_mail"] is False
    assert resultado["tiempo_procesamiento"] < 30