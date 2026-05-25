def verificar_alerta(valor, min_lim, max_lim):
    """Lógica que decide si se envía mensaje a Telegram/Mail"""
    return valor < min_lim or valor > max_lim

def test_disparo_alerta_ph_acido():
    # Caso: pH de 4.0 (Muy ácido, fuera de rango 6.5-8.5)
    resultado = verificar_alerta(4.0, 6.5, 8.5)
    assert resultado is True, "Debería activar alerta para pH 4.0"

def test_no_disparo_ph_normal():
    # Caso: pH de 7.0 (Normal)
    resultado = verificar_alerta(7.0, 6.5, 8.5)
    assert resultado is False, "No debería activar alerta para pH 7.0"