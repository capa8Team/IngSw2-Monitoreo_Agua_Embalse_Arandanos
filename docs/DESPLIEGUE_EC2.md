# Despliegue en AWS EC2

Guía para publicar el stack completo (MongoDB + FastAPI + Vue/nginx) en una instancia EC2 usando Docker Compose.

## Requisitos previos

| Recurso | Recomendación |
|---------|----------------|
| Instancia | **t3.small** o superior (mín. 2 GB RAM para MongoDB) |
| SO | **Ubuntu 22.04 LTS** (AMI oficial) |
| Disco | 20 GB gp3 o más |
| Supabase | Proyecto configurado (scripts en `database/supabase/`, ver `README.md`) |
| Certificados IoT | Carpeta `IotCore/` (no está en git; copiar por SCP) |

## 1. Crear la instancia EC2

1. En **EC2 → Launch instance**:
   - AMI: Ubuntu Server 22.04 LTS
   - Tipo: `t3.small`
   - Par de claves SSH (.pem)
   - Almacenamiento: 20 GB

2. **Security Group** (reglas de entrada):

| Puerto | Origen | Uso |
|--------|--------|-----|
| 22 | Tu IP (`x.x.x.x/32`) | SSH (no uses `0.0.0.0/0` en producción) |
| 80 | `0.0.0.0/0` | HTTP (aplicación web) |
| 443 | `0.0.0.0/0` | HTTPS (opcional, con Certbot o ALB) |

No abras **27017** (MongoDB) ni **8000** (API) a Internet; en producción solo se expone el frontend en el puerto 80.

3. Asigna una **Elastic IP** si quieres una IP fija para DNS o certificados SSL.

## 2. Conectar por SSH

```bash
chmod 400 tu-clave.pem
ssh -i tu-clave.pem ubuntu@EC2_PUBLIC_IP
```

## 3. Instalar Docker

Desde la raíz del repositorio (después de clonarlo) o copiando solo el script:

```bash
sudo bash deploy/ec2-bootstrap.sh
```

Cierra la sesión SSH y vuelve a entrar para que el grupo `docker` aplique al usuario `ubuntu`.

## 4. Clonar el proyecto

```bash
sudo mkdir -p /opt/embalse-arandanos
sudo chown ubuntu:ubuntu /opt/embalse-arandanos
cd /opt/embalse-arandanos
git clone https://github.com/TU_ORG/IngSw2-Monitoreo_Agua_Embalse_Arandanos.git .
```

## 5. Configurar variables de entorno

```bash
cp deploy/.env.ec2.example .env
nano .env
```

Obligatorio en producción:

- `JWT_SECRET` — secreto largo y aleatorio
- `MONGO_ROOT_PASSWORD` — contraseña fuerte de MongoDB
- `VITE_SUPABASE_URL` y `VITE_SUPABASE_ANON_KEY`
- `SUPABASE_DB_URL` — connection string de Postgres en Supabase (logs y roles)

Deja `VITE_API_URL` **vacío** para que el navegador use `/api/...` y nginx del contenedor frontend reenvíe al backend.

## 6. Copiar certificados AWS IoT

Los archivos de `IotCore/` están en `.gitignore`. Desde tu máquina local:

```bash
scp -i tu-clave.pem -r IotCore/* ubuntu@EC2_PUBLIC_IP:/opt/embalse-arandanos/IotCore/
```

En `.env`:

```env
AWS_IOT_ENABLED=true
AWS_IOT_CERTS_DIR=./IotCore
```

## 7. Levantar el stack

```bash
cd /opt/embalse-arandanos
docker compose -f docker-compose.yml -f deploy/docker-compose.ec2.override.yml up -d --build
```

Comprobar:

```bash
docker compose -f docker-compose.yml -f deploy/docker-compose.ec2.override.yml ps
curl -s -o /dev/null -w "Frontend HTTP %{http_code}\n" http://127.0.0.1/
docker exec backend-fastapi python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1/health').read().decode())"
```

Abre en el navegador: `http://EC2_PUBLIC_IP`

## 8. Arranque automático (systemd)

Ajusta `WorkingDirectory` en `deploy/embalse-docker.service` si usas otra ruta:

```bash
sudo cp deploy/embalse-docker.service /etc/systemd/system/embalse-docker.service
sudo systemctl daemon-reload
sudo systemctl enable embalse-docker
sudo systemctl start embalse-docker
```

## 9. HTTPS (opcional)

### Opción A — Application Load Balancer + ACM

- ALB en frente de la instancia, listener 443 con certificado ACM.
- Target group al puerto **80** de la EC2.
- Útil si ya usas Route 53 y dominio en AWS.

### Opción B — Certbot en la misma EC2

1. Instala nginx en el host y Certbot.
2. Proxy `https://tu-dominio` → `http://127.0.0.1:80` (contenedor frontend).
3. Apunta el registro DNS A al Elastic IP.

Ejemplo mínimo de sitio nginx en el host (`/etc/nginx/sites-available/embalse`):

```nginx
server {
    listen 80;
    server_name monitoreo.tudominio.com;
    location / {
        proxy_pass http://127.0.0.1:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

> Si nginx del host también escucha en 80, cambia el mapeo del contenedor a `"8080:8000"` en `deploy/docker-compose.ec2.override.yml` y usa `proxy_pass http://127.0.0.1:8080`.

```bash
sudo certbot --nginx -d monitoreo.tudominio.com
```

## 10. Actualizar la aplicación

```bash
cd /opt/embalse-arandanos
git pull
docker compose -f docker-compose.yml -f deploy/docker-compose.ec2.override.yml up -d --build
```

## Comandos útiles

```bash
# Logs
docker compose -f docker-compose.yml -f deploy/docker-compose.ec2.override.yml logs -f backend
docker compose -f docker-compose.yml -f deploy/docker-compose.ec2.override.yml logs -f frontend

# Detener
docker compose -f docker-compose.yml -f deploy/docker-compose.ec2.override.yml down

# Reiniciar un servicio
docker compose -f docker-compose.yml -f deploy/docker-compose.ec2.override.yml restart backend
```

## Checklist de producción

- [ ] `JWT_SECRET` y `MONGO_ROOT_PASSWORD` únicos y fuertes
- [ ] Security Group sin puertos 27017/8000 públicos
- [ ] SSH restringido a tu IP
- [ ] Supabase SQL ejecutado y usuario admin en Auth
- [ ] Certificados `IotCore/` en la instancia y `AWS_IOT_ENABLED=true`
- [ ] Elastic IP o dominio configurado
- [ ] HTTPS habilitado (ALB o Certbot)
- [ ] Backups de volumen MongoDB (`mongodb_data`)

### Backup MongoDB (ejemplo)

```bash
docker exec mongodb-arandanos mongodump \
  --username admin --password 'TU_MONGO_ROOT_PASSWORD' \
  --authenticationDatabase admin --db Arandanos --out /data/backup
docker cp mongodb-arandanos:/data/backup ./backup-mongo-$(date +%F)
```

## Solución de problemas

| Síntoma | Qué revisar |
|---------|-------------|
| No carga la web | `docker compose ps`, SG puerto 80, `curl localhost` en la EC2 |
| Login falla | `VITE_SUPABASE_*` en `.env` y rebuild del frontend (`--build`) |
| Sin datos de sensores | `AWS_IOT_ENABLED`, certificados en `IotCore/`, logs del backend |
| Contenedor backend unhealthy | `docker compose logs backend`, `SUPABASE_DB_URL` válida |

Más detalle en [DOCKER.md](./DOCKER.md) y [AWS_IOT_CORE.md](./AWS_IOT_CORE.md).
