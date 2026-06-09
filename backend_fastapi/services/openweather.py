"""
Servicio para integración con OpenWeather API.
Obtiene datos de clima basados en la ciudad del dispositivo.
"""

import requests
import logging
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# Clave de API de OpenWeather (debe ser configurada en variables de entorno)
# Usa tu propia clave de: https://openweathermap.org/api
OPENWEATHER_API_KEY = None  # Será seteado en init_openweather()
OPENWEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

COUNTRY_ALIASES = {
    "chile": "CL",
    "argentina": "AR",
    "peru": "PE",
    "perú": "PE",
    "uruguay": "UY",
    "bolivia": "BO",
    "colombia": "CO",
    "mexico": "MX",
    "méxico": "MX",
    "españa": "ES",
    "spain": "ES",
    "brasil": "BR",
    "brazil": "BR",
}


def normalize_city_query(city: str) -> str:
    """Normaliza nombres como 'Santiago Chile' a 'Santiago,CL' para OpenWeather."""
    city = city.strip()
    if not city or "," in city:
        return city

    parts = city.split()
    if len(parts) >= 2:
        country_key = parts[-1].lower()
        if country_key in COUNTRY_ALIASES:
            city_name = " ".join(parts[:-1])
            return f"{city_name},{COUNTRY_ALIASES[country_key]}"

    return city


def init_openweather(api_key: str) -> None:
    """
    Inicializa la clave de API de OpenWeather.
    
    Args:
        api_key: Clave de API de OpenWeather
    """
    global OPENWEATHER_API_KEY
    OPENWEATHER_API_KEY = api_key
    if api_key:
        logger.info("OpenWeather API inicializado")
    else:
        logger.warning("OpenWeather API key no configurada")


def get_weather_data(city: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene datos de clima actuales para una ciudad desde OpenWeather.
    
    Args:
        city: Nombre de la ciudad (ej: "Madrid", "Buenos Aires")
        
    Returns:
        Dict con datos de clima o None si falla
        
    Ejemplo de respuesta:
        {
            "city": "Madrid",
            "temperature": 22.5,
            "feels_like": 21.0,
            "temp_min": 20.0,
            "temp_max": 24.0,
            "humidity": 65,
            "pressure": 1013,
            "description": "Cielo Claro",
            "main": "Clear",
            "icon": "01d",
            "wind_speed": 5.2,
            "clouds": 10,
            "sunrise": "2026-06-03T06:30:00Z",
            "sunset": "2026-06-03T21:45:00Z",
            "timestamp": "2026-06-03T14:30:00Z"
        }
    """
    if not OPENWEATHER_API_KEY:
        logger.warning(f"OpenWeather API key no configurada. No se puede obtener clima para {city}")
        return None
    
    if not city or not city.strip():
        logger.warning("Ciudad no proporcionada para obtener clima")
        return None
    
    try:
        query_city = normalize_city_query(city)
        params = {
            "q": query_city,
            "appid": OPENWEATHER_API_KEY,
            "units": "metric",  # Usar grados Celsius
            "lang": "es"  # Respuesta en español
        }
        
        response = requests.get(
            OPENWEATHER_BASE_URL,
            params=params,
            timeout=5
        )
        
        if response.status_code == 404:
            logger.warning(f"Ciudad no encontrada en OpenWeather: {city}")
            return None
        
        if response.status_code != 200:
            logger.error(f"Error en OpenWeather API: {response.status_code} - {response.text}")
            return None
        
        data = response.json()
        
        # Extraer datos relevantes
        weather_data = {
            "city": data.get("name", city),
            "country": data.get("sys", {}).get("country", ""),
            "temperature": data.get("main", {}).get("temp"),
            "feels_like": data.get("main", {}).get("feels_like"),
            "temp_min": data.get("main", {}).get("temp_min"),
            "temp_max": data.get("main", {}).get("temp_max"),
            "humidity": data.get("main", {}).get("humidity"),
            "pressure": data.get("main", {}).get("pressure"),
            "description": data.get("weather", [{}])[0].get("description", ""),
            "main": data.get("weather", [{}])[0].get("main", ""),
            "icon": data.get("weather", [{}])[0].get("icon", ""),
            "wind_speed": data.get("wind", {}).get("speed"),
            "wind_deg": data.get("wind", {}).get("deg"),
            "clouds": data.get("clouds", {}).get("all", 0),
            "visibility": data.get("visibility"),
            "sunrise": datetime.fromtimestamp(
                data.get("sys", {}).get("sunrise", 0)
            ).isoformat() + "Z" if data.get("sys", {}).get("sunrise") else None,
            "sunset": datetime.fromtimestamp(
                data.get("sys", {}).get("sunset", 0)
            ).isoformat() + "Z" if data.get("sys", {}).get("sunset") else None,
            "timestamp": datetime.fromtimestamp(
                data.get("dt", 0)
            ).isoformat() + "Z" if data.get("dt") else None
        }
        
        logger.info(f"Datos de clima obtenidos para {city}: {weather_data['temperature']}°C")
        return weather_data
        
    except requests.exceptions.Timeout:
        logger.error(f"Timeout al conectar con OpenWeather para {city}")
        return None
    except requests.exceptions.ConnectionError:
        logger.error(f"Error de conexión con OpenWeather para {city}")
        return None
    except Exception as e:
        logger.error(f"Error al obtener clima para {city}: {str(e)}")
        return None


def get_weather_emoji(icon_code: str) -> str:
    """
    Convierte el código de icono de OpenWeather a un emoji.
    
    Args:
        icon_code: Código de icono de OpenWeather (ej: "01d", "02n")
        
    Returns:
        Emoji representativo del clima
    """
    icon_map = {
        "01d": "☀️",   # Clear sky (día)
        "01n": "🌙",   # Clear sky (noche)
        "02d": "⛅",   # Few clouds (día)
        "02n": "☁️",   # Few clouds (noche)
        "03d": "☁️",   # Scattered clouds
        "03n": "☁️",   # Scattered clouds
        "04d": "☁️",   # Broken clouds
        "04n": "☁️",   # Broken clouds
        "09d": "🌧️",  # Shower rain (día)
        "09n": "🌧️",  # Shower rain (noche)
        "10d": "🌦️",  # Rain (día)
        "10n": "🌧️",  # Rain (noche)
        "11d": "⛈️",   # Thunderstorm (día)
        "11n": "⛈️",   # Thunderstorm (noche)
        "13d": "❄️",   # Snow (día)
        "13n": "❄️",   # Snow (noche)
        "50d": "🌫️",  # Mist (día)
        "50n": "🌫️",  # Mist (noche)
    }
    return icon_map.get(icon_code, "🌡️")
