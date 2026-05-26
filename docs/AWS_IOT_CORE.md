# AWS IoT Core — alineado con ReciberConPostMQTT

## Flujo

```
Sender3Sensores (ESP32, ESP-NOW)
    → ReciberConPostMQTT (ESP8266)
        → MQTT publish topic ``boya/sensores``
            → Backend FastAPI (suscriptor)
                → MongoDB ``sensor_readings``
                    → Dashboard Vue
```

## Topic y payload (firmware)

**Topic:** `boya/sensores` (`ReciberConPostMQTT.ino`)

**JSON publicado:**

```json
{
  "nombre": "NombreBoya",
  "id_env": 1,
  "pH": 7.2,
  "temperatura": 22.5,
  "EC": 480.0,
  "bateria": 87,
  "timestamp": 1716650000,
  "fecha_hora": "2026-05-25 14:30:00",
  "zona_horaria": "America/Santiago"
}
```

El backend mapea `nombre` + `id_env` → `arduino_id` (`NombreBoya-1`), `EC` → conductividad, `bateria` → batería (%).

## Certificados

Carpeta del repo: [`IotCore/`](../IotCore/)

Si no defines rutas en `.env`, el backend resuelve automáticamente:

- `IotCore/4bb52c42...-certificate.pem.crt`
- `IotCore/4bb52c42...-private.pem.key`
- `IotCore/AmazonRootCA1.pem`

## Variables de entorno

```env
AWS_IOT_ENABLED=true
AWS_IOT_ENDPOINT=a319gtmfe1r2jb-ats.iot.sa-east-1.amazonaws.com
AWS_IOT_CLIENT_ID=embalse-backend
AWS_IOT_TOPIC=boya/sensores
```

Opcional (sobrescriben rutas por defecto):

```env
AWS_IOT_CERT_PATH=IotCore/4bb52c4252bfb1b205ea09eb59a655000d689f05c3b72aa689f775caa548496e-certificate.pem.crt
AWS_IOT_KEY_PATH=IotCore/4bb52c4252bfb1b205ea09eb59a655000d689f05c3b72aa689f775caa548496e-private.pem.key
AWS_IOT_CA_PATH=IotCore/AmazonRootCA1.pem
AWS_IOT_CERTS_DIR=./IotCore
```

## Política IoT en AWS

El certificado debe permitir al **ESP8266** `iot:Publish` en `boya/sensores` y al **backend** `iot:Subscribe` + `iot:Receive` en el mismo topic (client ID distinto: `embalse-backend` vs `ESP8266-InfraTI`).

## Verificación

- `GET /api/diagnostics` → bloque `aws_iot`
- Tras una lectura ESP-NOW, revisar logs del backend: `Telemetría IoT guardada`
- `GET /api/data/mongodb` → documentos con `"source": "aws_iot"`

## MongoDB

Sin Atlas: usar `docker compose up` o `MONGODB_URL=mongodb://admin:<password>@localhost:27017/?authSource=admin`.
