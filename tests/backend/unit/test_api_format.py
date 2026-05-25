import pytest

def test_sensor_data_ranges():
    # Si tienes una API, aquí podrías usar 'client.get("/api/data")'
    mock_data = {
        "ph": 7.2, 
        "temp": 25.5, 
        "conductividad": 1.5
    }
    
    assert 0 <= mock_data["ph"] <= 14, "El pH debe estar entre 0 y 14"
    assert -10 <= mock_data["temp"] <= 50, "Temperatura fuera de rango lógico"
    assert mock_data["conductividad"] >= 0, "La conductividad no puede ser negativa"