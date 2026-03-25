# Backend FastAPI - Embalse Arandanos

## 1. Instalar dependencias

```bash
pip install -r backend_fastapi/requirements.txt
```

## Configurar MailerSend (notificaciones por correo)

Define estas variables de entorno antes de ejecutar la API:

```bash
MAILERSEND_API_TOKEN=tu_api_token
MAILERSEND_FROM_EMAIL=alertas@tudominio.com
MAILERSEND_FROM_NAME=Monitoreo Embalse Arandanos
MAILERSEND_TO_EMAILS=destino1@correo.com,destino2@correo.com
```

La API enviara correo solo para mediciones fuera de rango cuando en `POST /api/alerts` incluyas:

- `valor`
- `minimo`
- `maximo`

Si no envias esos campos, para mantener compatibilidad se enviara igualmente la notificacion.

## 2. Ejecutar servidor

```bash
uvicorn backend_fastapi.main:app --reload --port 8000
```

## 3. Swagger y ReDoc

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## Endpoints principales

- `GET /health`
- `GET /api/dashboard`
- `GET /api/alerts`
- `POST /api/alerts`
- `GET /api/alerts/{alert_id}`

### Ejemplo `POST /api/alerts`

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
