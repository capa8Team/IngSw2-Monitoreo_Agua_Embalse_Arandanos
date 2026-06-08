/**
 * Servicio para obtener datos de clima de OpenWeather API.
 * Integración con el backend que consume OpenWeather.
 */

const API_BASE = import.meta.env.VITE_API_URL || ''

/**
 * Obtiene datos de clima para un dispositivo específico.
 * El dispositivo debe tener configurada una ciudad.
 * 
 * @param {string} deviceId - ID del dispositivo
 * @returns {Promise<Object>} Datos de clima
 */
export async function getDeviceWeather(deviceId) {
  try {
    const response = await fetch(`${API_BASE}/api/devices/${deviceId}/weather`, {
      headers: {
        'Content-Type': 'application/json',
      }
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || `Error: ${response.status}`)
    }

    return await response.json()
  } catch (err) {
    console.error(`Error obteniendo clima para dispositivo ${deviceId}:`, err)
    throw err
  }
}

/**
 * Obtiene datos de clima para una ciudad específica.
 * 
 * @param {string} city - Nombre de la ciudad (ej: "Madrid", "Buenos Aires")
 * @returns {Promise<Object>} Datos de clima
 */
export async function getWeatherByCity(city) {
  try {
    const response = await fetch(`${API_BASE}/api/devices/weather/${encodeURIComponent(city)}`, {
      headers: {
        'Content-Type': 'application/json',
      }
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || `Error: ${response.status}`)
    }

    return await response.json()
  } catch (err) {
    console.error(`Error obteniendo clima para ${city}:`, err)
    throw err
  }
}

/**
 * Convierte un código de icono de OpenWeather a un emoji.
 * 
 * @param {string} iconCode - Código del icono (ej: "01d", "02n")
 * @returns {string} Emoji representativo
 */
export function getWeatherEmoji(iconCode) {
  const iconMap = {
    '01d': '☀️',   // Clear sky (día)
    '01n': '🌙',   // Clear sky (noche)
    '02d': '⛅',   // Few clouds (día)
    '02n': '☁️',   // Few clouds (noche)
    '03d': '☁️',   // Scattered clouds
    '03n': '☁️',   // Scattered clouds
    '04d': '☁️',   // Broken clouds
    '04n': '☁️',   // Broken clouds
    '09d': '🌧️',  // Shower rain (día)
    '09n': '🌧️',  // Shower rain (noche)
    '10d': '🌦️',  // Rain (día)
    '10n': '🌧️',  // Rain (noche)
    '11d': '⛈️',   // Thunderstorm (día)
    '11n': '⛈️',   // Thunderstorm (noche)
    '13d': '❄️',   // Snow (día)
    '13n': '❄️',   // Snow (noche)
    '50d': '🌫️',  // Mist (día)
    '50n': '🌫️',  // Mist (noche)
  }
  return iconMap[iconCode] || '🌡️'
}

/**
 * Determina la condición general del clima basado en el código principal.
 * 
 * @param {string} mainWeather - Clima principal (Clear, Clouds, Rain, etc.)
 * @returns {string} Descripción legible
 */
export function getWeatherCondition(mainWeather) {
  const conditions = {
    'Clear': 'Despejado',
    'Clouds': 'Nublado',
    'Rain': 'Lluvia',
    'Drizzle': 'Llovizna',
    'Thunderstorm': 'Tormenta',
    'Snow': 'Nieve',
    'Mist': 'Niebla',
    'Smoke': 'Humo',
    'Haze': 'Calina',
    'Dust': 'Polvo',
    'Fog': 'Niebla',
    'Sand': 'Arena',
    'Ash': 'Ceniza',
    'Squall': 'Ráfagas',
    'Tornado': 'Tornado'
  }
  return conditions[mainWeather] || mainWeather
}

/**
 * Calcula el índice de sensación térmica (Wind Chill) aproximado.
 * Fórmula simplificada para temperaturas.
 * 
 * @param {number} temp - Temperatura en Celsius
 * @param {number} windSpeed - Velocidad del viento en m/s
 * @returns {number} Temperatura de sensación térmica
 */
export function calculateWindChill(temp, windSpeed) {
  // Convertir m/s a km/h
  const windKmh = windSpeed * 3.6
  
  // Fórmula simplificada
  if (temp <= 10 && windKmh >= 4.8) {
    return 13.12 + 0.6215 * temp - 11.37 * Math.pow(windKmh, 0.16) + 0.3965 * temp * Math.pow(windKmh, 0.16)
  }
  return temp
}

/**
 * Determina si el clima es seguro para operaciones exteriores basándose
 * en temperatura y otras condiciones.
 * 
 * @param {Object} weatherData - Datos de clima
 * @returns {Object} {isSafe: boolean, warnings: string[], advice: string}
 */
export function assessWeatherSafety(weatherData) {
  const warnings = []
  let advice = 'Condiciones favorables'

  if (!weatherData) {
    return { isSafe: false, warnings: ['Sin datos de clima'], advice: 'No se pudieron obtener datos de clima' }
  }

  const temp = weatherData.temperature
  const humidity = weatherData.humidity
  const windSpeed = weatherData.wind_speed
  const mainWeather = weatherData.main

  // Análisis de temperatura
  if (temp > 35) {
    warnings.push('Calor extremo')
    advice = 'Evite exposición prolongada al sol'
  } else if (temp < 0) {
    warnings.push('Congelamiento posible')
    advice = 'Tome precauciones contra el frío'
  }

  // Análisis de viento
  if (windSpeed > 10) {
    warnings.push('Vientos fuertes')
    advice = 'Tenga cuidado con objetos sueltos'
  }

  // Análisis de humedad
  if (humidity > 80) {
    warnings.push('Humedad muy alta')
    advice = 'Condiciones húmedas, posible sensación de calor'
  }

  // Análisis de tipo de clima
  if (mainWeather === 'Thunderstorm' || mainWeather === 'Tornado') {
    warnings.push('Clima severo')
    advice = 'Busque refugio inmediatamente'
  } else if (mainWeather === 'Snow' || mainWeather === 'Squall') {
    warnings.push('Condiciones invernales')
    advice = 'Extreme precauciones, posibilidad de resbalones'
  } else if (mainWeather === 'Rain' || mainWeather === 'Drizzle') {
    warnings.push('Precipitación')
    advice = 'Lleve protección contra lluvia'
  }

  const isSafe = warnings.length === 0

  return { isSafe, warnings, advice }
}

/**
 * Formatea la data de clima para mostrar en la UI.
 * 
 * @param {Object} weatherData - Datos crudos de clima
 * @returns {Object} Datos formateados
 */
export function formatWeatherData(weatherData) {
  if (!weatherData) return null

  return {
    city: weatherData.city || 'Desconocido',
    country: weatherData.country || '',
    temperature: Math.round(weatherData.temperature),
    feelsLike: Math.round(weatherData.feels_like),
    tempMin: Math.round(weatherData.temp_min),
    tempMax: Math.round(weatherData.temp_max),
    humidity: weatherData.humidity,
    pressure: weatherData.pressure,
    description: weatherData.description,
    main: weatherData.main,
    icon: weatherData.icon,
    windSpeed: (weatherData.wind_speed || 0).toFixed(1),
    windDeg: weatherData.wind_deg || 0,
    clouds: weatherData.clouds,
    visibility: weatherData.visibility ? (weatherData.visibility / 1000).toFixed(1) : 'N/A',
    sunrise: weatherData.sunrise,
    sunset: weatherData.sunset,
    timestamp: weatherData.timestamp
  }
}
