# Certificados AWS IoT Core

Archivos generados al registrar el Thing en AWS IoT (región **sa-east-1**).

| Archivo | Uso |
|---------|-----|
| `*-certificate.pem.crt` | Certificado del dispositivo |
| `*-private.pem.key` | Clave privada (no compartir) |
| `AmazonRootCA1.pem` | CA raíz (mismo que en `ReciberConPostMQTT/secrets.h`) |

El backend y el sketch `SketchArduino/ReciberConPostMQTT` usan estos archivos para MQTT en el puerto **8883**.

- **Endpoint:** `a319gtmfe1r2jb-ats.iot.sa-east-1.amazonaws.com`
- **Topic de publicación (ESP8266):** `boya/sensores`
- **Thing (Arduino):** `ESP8266-InfraTI` (ver `secrets.h`)
- **Client ID backend (suscriptor):** `embalse-backend`

En Docker: el directorio se monta en `/app/iot-certs` (`AWS_IOT_CERTS_DIR=./IotCore`).
