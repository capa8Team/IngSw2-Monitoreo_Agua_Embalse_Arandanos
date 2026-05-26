# Backend FastAPI - Embalse Arandanos

## 1. Instalar dependencias

```bash
pip install -r backend_fastapi/requirements.txt
```

## 2. Configurar MongoDB

Con Docker Compose (recomendado), MongoDB corre en el servicio `mongodb`:

```bash
MONGODB_URL=mongodb://admin:Panconpalta1@localhost:27017/?authSource=admin
MONGODB_DB=Arandanos
```

Desde otro contenedor en la misma red: `mongodb://admin:<password>@mongodb:27017/?authSource=admin`

Ver `docker-compose.yml` en la raíz del repositorio.

## 2b. AWS IoT Core (opcional)

Para ingestar telemetría por MQTT, activa `AWS_IOT_ENABLED=true`. El topic y formato coinciden con `SketchArduino/ReciberConPostMQTT` (`boya/sensores`). Certificados en `IotCore/`. Guía: [docs/AWS_IOT_CORE.md](../docs/AWS_IOT_CORE.md).

## 3. Configurar MailerSend (notificaciones por correo)

Define estas variables de entorno:

```bash
MAILERSEND_API_TOKEN=tu_api_token
MAILERSEND_FROM_EMAIL=alertas@tudominio.com
MAILERSEND_FROM_NAME=Monitoreo Embalse Arandanos
MAILERSEND_TO_EMAILS=destino1@correo.com,destino2@correo.com
```

## 4. Ejecutar servidor

```bash
uvicorn backend_fastapi.main:app --reload --port 8000
```

## 5. Swagger y ReDoc

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## Endpoints principales

### Dashboard
- `GET /api/dashboard` - Obtener estado actual de sensores desde MongoDB

### Sensores (datos del ESP8266)
- `PUT /api/sensors/ph` - Recibir datos de sensores del ESP8266 (HTTP PUT)
- `POST /api/sensors/readings` - Recibir datos de sensores (HTTP POST)
- `GET /api/sensors/latest` - Obtener última lectura de MongoDB
- `GET /api/sensors/history?limit=100` - Obtener historial (últimas N lecturas)

### Alertas
- `GET /api/alerts` - Listar alertas
- `POST /api/alerts` - Crear nueva alerta
- `GET /api/alerts/{alert_id}` - Obtener alerta específica

## Flujo de datos

**Opción A — AWS IoT Core (recomendado en producción)**

Dispositivo → MQTT (AWS IoT) → Backend suscriptor → MongoDB → Frontend

**Opción B — HTTP directo (ESP8266)**

1. ESP8266 envía `PUT /api/sensors/ph` o `POST /api/sensors/readings`
2. Backend guarda en `sensor_readings` (MongoDB)
3. Frontend consume `GET /api/dashboard`

## Configuración del archivo .env

Copia `.env.example` a `.env` y completa los valores:

```bash
cp backend_fastapi/.env.example backend_fastapi/.env
```

## Ejemplo de solicitud desde ESP8266

```cpp
// Arduino/ESP8266 code
DynamicJsonDocument doc(256);
doc["ph"] = 7.2;
doc["temperature"] = 22.5;
doc["conductivity"] = 650;
doc["timestamp"] = millis() / 1000;

String jsonData;
serializeJson(doc, jsonData);

http.begin(client, "http://192.168.1.100:8000/api/sensors/ph");
http.addHeader("Content-Type", "application/json");
int httpCode = http.PUT(jsonData);
```

## Ejemplo `POST /api/alerts`

```json
{
	"embalse": "Embalse Norte",
	"nombreDispositivo": "Arduino Embalse A",
	"sensor": "Conductividad",
	"medicion": "2100 uS/cm",
	"valor": 2100,
	"minimo": 100,
	"maximo": 2000
}
```

El mensaje de correo incluye:

- Nombre dispositivo
- Dia
- Fecha
- Hora
- Sensor
- Medicion
