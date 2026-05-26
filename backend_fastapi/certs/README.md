# Certificados AWS IoT Core

Coloca aquí los archivos generados en la consola de AWS IoT (o con `aws iot` CLI):

| Archivo | Descripción |
|---------|-------------|
| `device.pem.crt` | Certificado del dispositivo/thing |
| `private.pem.key` | Clave privada |
| `AmazonRootCA1.pem` | CA raíz de Amazon ([descarga](https://www.amazontrust.com/repository/AmazonRootCA1.pem)) |

Estos archivos están en `.gitignore` por seguridad. En Docker, el directorio se monta en `/app/certs` (ver `AWS_IOT_CERTS_DIR` en `.env`).
