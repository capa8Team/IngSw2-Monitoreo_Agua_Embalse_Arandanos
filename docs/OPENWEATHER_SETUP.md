# Integración de OpenWeather - Guía de Configuración

## 📋 Resumen

Se ha integrado la API de **OpenWeather** en el sistema para mostrar datos climáticos en el dashboard. Cuando un administrador agrega un dispositivo, puede especificar la ciudad donde está ubicado, y el sistema mostrará el clima actual de esa ciudad en la tarjeta del dispositivo.

## 🌐 Características Implementadas

### Backend (FastAPI)

1. **Modelo de Dispositivo Actualizado**
   - Nuevo campo: `city` (Ciudad para datos de clima)
   - Se puede especificar al crear o actualizar un dispositivo

2. **Servicio de OpenWeather** (`services/openweather.py`)
   - Función `get_weather_data(city)` - Obtiene datos climáticos
   - Función `get_weather_emoji(icon_code)` - Convierte códigos de icono a emojis
   - Función `init_openweather(api_key)` - Inicializa el servicio con la clave de API

3. **Nuevos Endpoints API**
   - `GET /api/devices/weather/{city}` - Obtiene clima para una ciudad
   - `GET /api/devices/{device_id}/weather` - Obtiene clima del dispositivo

### Frontend (Vue 3)

1. **Formulario de Agregar Dispositivo**
   - Nuevo campo de entrada: "Ciudad"
   - Placeholder con ejemplos: "Ej: Madrid, Buenos Aires"
   - Descripción clara del propósito

2. **Tarjeta de Dispositivo (DeviceCard.vue)**
   - Sección de clima integrada
   - Muestra: Temperatura, descripción, humedad, velocidad del viento, ciudad
   - Emoji dinámico según condiciones climáticas
   - Interfaz diseñada con gradiente azul cielo
   - Diseño responsivo y soporte para modo oscuro

## 🔑 Configuración Requerida

### Paso 1: Obtener Clave de API de OpenWeather

1. Visita: https://openweathermap.org/api
2. Regístrate para una cuenta gratuita
3. Ve a tu perfil y copia tu **API Key**
4. El plan gratuito permite 1,000 llamadas al día (más que suficiente para monitoreo)

### Paso 2: Configurar la Clave en el Sistema

Agrega la siguiente línea a tu archivo `.env` en la raíz del proyecto:

```env
OPENWEATHER_API_KEY=tu_clave_api_aqui
```

**Ejemplo completo de .env:**
```env
# OpenWeather
OPENWEATHER_API_KEY=

# Otras configuraciones...
MONGODB_URL=mongodb://admin:password@localhost:27017/?authSource=admin
AWS_IOT_ENABLED=true
# ... más configuraciones
```

### Paso 3: Reiniciar el Backend

Después de agregar la clave al `.env`, reinicia el servidor FastAPI:

```bash
# En la carpeta backend_fastapi
python main.py

# O con Docker
docker compose up -d
```

Deberías ver en los logs:
```
[OPENWEATHER] API inicializada correctamente
```

## 📱 Cómo Usar

### Agregar un Dispositivo con Ciudad

1. **Login como Administrador**
   - Accede al dashboard con credenciales de admin

2. **Agregar Nuevo Dispositivo**
   - Click en el botón "➕ Nuevo Dispositivo" o "➕ Agregar Manual"
   - Completa el formulario:
     - **Nombre del Dispositivo** *: "Sensor Embalse Norte"
     - **Tipo de Microcontrolador**: Selecciona el tipo (ESP8266, Arduino, etc.)
     - **Ubicación**: (Opcional) "Zona A - Profundidad 5m"
     - **Ciudad**: (Nuevo) "Madrid" o "Buenos Aires"
     - **Identificador del dispositivo**: (Opcional)
     - **Topic MQTT** *: "boya/sensores"
   - Click en "Agregar Dispositivo"

3. **Ver el Clima en el Dashboard**
   - La tarjeta del dispositivo mostrará automáticamente:
     - Emoji de clima (☀️ ⛅ 🌧️ ⛈️ etc.)
     - Temperatura actual
     - Descripción (Cielo Claro, Nublado, Lluvia, etc.)
     - Humedad
     - Velocidad del viento
     - Nombre de la ciudad

### Actualizar Ciudad de un Dispositivo Existente

Si tienes dispositivos existentes sin ciudad, puedes:

1. Editar el dispositivo (si hay opción de editar)
2. Agregar la ciudad
3. Guardar cambios
4. El clima se cargará automáticamente

## 📊 Datos de Clima Retornados

Cada consulta de clima retorna:

```json
{
  "device_id": "uuid",
  "device_name": "Sensor Embalse Norte",
  "city": "Madrid",
  "weather": {
    "city": "Madrid",
    "country": "ES",
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
    "wind_deg": 180,
    "clouds": 10,
    "visibility": 10000,
    "sunrise": "2026-06-03T06:30:00Z",
    "sunset": "2026-06-03T21:45:00Z",
    "timestamp": "2026-06-03T14:30:00Z"
  }
}
```

## 🎨 Icono-Emoji Mapeados

| Icono OW | Significado | Emoji |
|----------|-------------|-------|
| 01d      | Cielo despejado (día) | ☀️ |
| 01n      | Cielo despejado (noche) | 🌙 |
| 02d      | Pocas nubes (día) | ⛅ |
| 02n      | Pocas nubes (noche) | ☁️ |
| 03-04    | Nubes dispersas/rotas | ☁️ |
| 09d/09n  | Lluvia moderada | 🌧️ |
| 10d      | Lluvia (día) | 🌦️ |
| 10n      | Lluvia (noche) | 🌧️ |
| 11d/11n  | Tormenta | ⛈️ |
| 13d/13n  | Nieve | ❄️ |
| 50d/50n  | Niebla | 🌫️ |

## ⚙️ Arquitectura Técnica

### Backend Flow

```
User agrupa dispositivo con city
         ↓
POST /api/devices { name, city, ... }
         ↓
create_device() en mongodb.py
         ↓
Dispositivo guardado en MongoDB con campo city
         ↓
Frontend carga DeviceCard
         ↓
DeviceCard detecta device.city
         ↓
GET /api/devices/weather/{city}
         ↓
get_weather_data(city) - servicio openweather.py
         ↓
requests.get() a OpenWeather API
         ↓
Parse respuesta JSON
         ↓
Retorna weather data al frontend
         ↓
DeviceCard renderiza sección de clima con emojis
```

### Archivos Modificados

**Backend:**
- `backend_fastapi/models.py` - Agregado campo `city` a Device, DeviceCreate, DeviceUpdate, DeviceResponse
- `backend_fastapi/services/openweather.py` - (NUEVO) Servicio de OpenWeather
- `backend_fastapi/routers/devices.py` - Endpoints de clima + actualización de create_device
- `backend_fastapi/services/mongodb.py` - create_device y update_device con soporte a `city`
- `backend_fastapi/core/config.py` - Configuración de OPENWEATHER_API_KEY
- `backend_fastapi/main.py` - Inicialización de OpenWeather en startup

**Frontend:**
- `src/components/AddDeviceModal.vue` - Agregado campo de ciudad en formulario
- `src/components/DeviceCard.vue` - Sección de clima integrada, carga dinámica de datos

## 🐛 Troubleshooting

### "No se pudo obtener datos de clima"

**Posibles causas:**

1. **Clave de API no configurada**
   ```bash
   # Verificar que existe en .env
   grep OPENWEATHER_API_KEY .env
   ```

2. **Clave de API inválida**
   - Verifica la clave en https://openweathermap.org/api/calls/weather
   - Prueba manualmente en: `https://api.openweathermap.org/data/2.5/weather?q=Madrid&appid=TU_CLAVE`

3. **Ciudad no encontrada**
   - Verifica el nombre de la ciudad (en inglés o español)
   - Ejemplos válidos: "Madrid", "Buenos Aires", "New York", "Tokyo"

4. **Límite de API alcanzado**
   - Plan gratuito: 1,000 llamadas/día
   - Verifica en el dashboard de OpenWeather

### El clima no se actualiza

- OpenWeather actualiza datos cada 10 minutos
- El frontend carga clima cuando:
  - Se abre la tarjeta del dispositivo
  - Cambia el nombre de la ciudad
  - Se refresca la página
- Para forzar actualización, edita y guarda la ciudad del dispositivo

## 📈 Próximas Mejoras Opcionales

- [ ] Pronóstico de 5 días
- [ ] Alertas si temperatura sale de rangos seguros
- [ ] Caché local de datos de clima (5-10 minutos)
- [ ] Selector de ciudad tipo autocomplete
- [ ] Múltiples ciudades por dispositivo
- [ ] Gráfico histórico de temperatura
- [ ] Comparación de temperatura local vs agua

## 📞 Soporte

Si tienes problemas:

1. Verifica los logs del backend: `docker logs arandanos-backend`
2. Comprueba la configuración en `.env`
3. Prueba la API directamente: `curl http://localhost:8000/api/devices/weather/Madrid`
4. Revisa si OpenWeather tiene status de servicio: https://status.openweathermap.org/

---

**Última actualización:** Junio 2026
**Versión:** 1.0.0
