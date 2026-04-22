# Guía de Despliegue: Sistema de Alertas por Telegram

## 📋 Tabla de Contenidos

1. [Requisitos Previos](#requisitos-previos)
2. [Configuración del Bot de Telegram](#configuración-del-bot-de-telegram)
3. [Preparación del Servidor](#preparación-del-servidor)
4. [Variables de Entorno](#variables-de-entorno)
5. [Instalación de Dependencias](#instalación-de-dependencias)
6. [Despliegue en Servidor](#despliegue-en-servidor)
7. [Verificación y Testing](#verificación-y-testing)
8. [Monitoreo y Mantenimiento](#monitoreo-y-mantenimiento)

---

## Requisitos Previos

- Servidor Linux o Windows con Python 3.8+
- Acceso a terminal SSH o RDP
- MongoDB instalado y corriendo
- Nginx o Apache (recomendado para proxy)
- Dominio o IP pública del servidor
- Cuenta de Telegram y acceso a @BotFather

---

## Configuración del Bot de Telegram

### Paso 1: Crear el Bot en Telegram

1. **Abre Telegram** y busca `@BotFather`
2. **Envía el comando** `/newbot`
3. **Proporciona el nombre del bot** (ej: `Alerta Embalse Arandanos`)
4. **Proporciona el username** (ej: `alertaEmbalseBot`) - debe ser único
5. **Guarda el token** que BotFather te proporcione

```
Formato del token: 123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
```

### Paso 2: Configurar el Webhook (Opcional pero Recomendado)

Para mejor rendimiento en producción, usa webhooks en lugar de polling:

```bash
# Configura el webhook de Telegram
curl -F "url=https://tu-dominio.com/telegram/webhook" \
     -F "allowed_updates=update_id,message,callback_query" \
     https://api.telegram.org/bot<TOKEN>/setWebhook
```

---

## Preparación del Servidor

### Paso 1: Clonar el Repositorio

```bash
cd /home/usuario
git clone <tu-repo> sistema-monitoreo
cd sistema-monitoreo
```

### Paso 2: Crear Directorios Necesarios

```bash
# Logs
mkdir -p backend_fastapi/logs

# Suscriptores
mkdir -p alertas

# SSL (si usas HTTPS)
mkdir -p /etc/ssl/certs/tu-dominio
```

### Paso 3: Instalar Dependencias del Sistema

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install -y python3-pip python3-venv
sudo apt install -y mongodb-server  # Si no está ya instalado
sudo apt install -y nginx  # Server web
sudo apt install -y supervisor  # Para manejar procesos
```

**CentOS/RHEL:**
```bash
sudo yum install -y python3-pip
sudo yum install -y mongodb-server
sudo yum install -y nginx
sudo yum install -y supervisor
```

---

## Variables de Entorno

### Paso 1: Crear archivo .env en servidor

```bash
nano .env
```

### Paso 2: Configurar las variables

```env
# ===== CONFIGURACION DEL BOT DE TELEGRAM =====
TELEGRAM_BOT_TOKEN=<tu-token-de-botfather>
PUBLIC_BASE_URL=https://tu-dominio.com
WEBAPP_URL=https://tu-dominio.com/dashboard

# ===== MONGODB =====
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB=embalse_arandanos

# ===== SUPABASE (AUTENTICACION) =====
VITE_SUPABASE_URL=<tu-url-supabase>
VITE_SUPABASE_ANON_KEY=<tu-clave-anonima>

# ===== API DEL BACKEND =====
VITE_API_URL=https://tu-dominio.com/api

# ===== MODO DE DATOS =====
VITE_DATA_MODE=real
SIMULATED_DATA_ENABLED=false

# ===== EMAIL (MAILERSEND) =====
MAILERSEND_API_TOKEN=<token-opcional>
```

### Paso 3: Asegurar el archivo

```bash
chmod 600 .env
```

---

## Instalación de Dependencias

### Paso 1: Crear entorno virtual

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# o en Windows:
# venv\Scripts\activate
```

### Paso 2: Instalar dependencias de Python

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Contenido de `requirements.txt` (si no lo tienes):

```
fastapi==0.115.8
uvicorn==0.34.0
python-telegram-bot==21.7
pymongo==4.8.0
pydantic==2.5.0
python-dotenv==1.0.0
requests==2.31.0
```

---

## Despliegue en Servidor

### Opción A: Con Supervisor (Recomendado)

#### Paso 1: Crear archivo de configuración

```bash
sudo nano /etc/supervisor/conf.d/monitoreo-backend.conf
```

#### Paso 2: Añadir configuración

```ini
[program:monitoreo-backend]
directory=/home/usuario/sistema-monitoreo
command=/home/usuario/sistema-monitoreo/venv/bin/uvicorn backend_fastapi.main:app --host 0.0.0.0 --port 8000
user=usuario
autostart=true
autorestart=true
stderr_logfile=/var/log/monitoreo-backend.err.log
stdout_logfile=/var/log/monitoreo-backend.out.log
environment=PATH="/home/usuario/sistema-monitoreo/venv/bin"
```

#### Paso 3: Activar supervisor

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start monitoreo-backend
```

### Opción B: Con systemd

#### Paso 1: Crear archivo de servicio

```bash
sudo nano /etc/systemd/system/monitoreo.service
```

#### Paso 2: Configurar

```ini
[Unit]
Description=Sistema de Monitoreo de Embalse
After=network.target

[Service]
Type=notify
User=usuario
WorkingDirectory=/home/usuario/sistema-monitoreo
Environment="PATH=/home/usuario/sistema-monitoreo/venv/bin"
ExecStart=/home/usuario/sistema-monitoreo/venv/bin/uvicorn backend_fastapi.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Paso 3: Activar

```bash
sudo systemctl daemon-reload
sudo systemctl enable monitoreo.service
sudo systemctl start monitoreo.service
```

### Configurar Nginx como Proxy Reverso

#### Paso 1: Crear configuración de Nginx

```bash
sudo nano /etc/nginx/sites-available/monitoreo
```

#### Paso 2: Añadir configuración

```nginx
upstream monitoreo_backend {
    server 127.0.0.1:8000;
}

upstream monitoreo_frontend {
    server 127.0.0.1:5173;
}

server {
    listen 80;
    server_name tu-dominio.com;
    
    # Redirigir HTTP a HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name tu-dominio.com;

    # Certificados SSL
    ssl_certificate /etc/ssl/certs/tu-dominio/cert.pem;
    ssl_certificate_key /etc/ssl/certs/tu-dominio/key.pem;

    # API Backend
    location /api/ {
        proxy_pass http://monitoreo_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 3600s;
        proxy_connect_timeout 3600s;
    }

    # Frontend Dashboard
    location /dashboard {
        proxy_pass http://monitoreo_frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    # Raíz
    location / {
        proxy_pass http://monitoreo_frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    # Telegram Webhook
    location /telegram/webhook {
        proxy_pass http://monitoreo_backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### Paso 3: Activar el sitio

```bash
sudo ln -s /etc/nginx/sites-available/monitoreo /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## Verificación y Testing

### Paso 1: Verificar que el backend está corriendo

```bash
curl -X GET https://tu-dominio.com/api/health
# Deberías recibir: {"status":"ok"}
```

### Paso 2: Verificar estadísticas de Telegram

```bash
curl -X GET https://tu-dominio.com/api/telegram/stats
```

### Paso 3: Inicializar el bot manualmente

```bash
curl -X POST https://tu-dominio.com/api/telegram/init
```

### Paso 4: Enviar alerta de prueba

```bash
curl -X POST https://tu-dominio.com/api/telegram/test-alert-out-of-range
```

### Paso 5: Verificar en Telegram

1. Abre Telegram
2. Busca tu bot (`@alertaEmbalseBot`)
3. Envía `/start` para registrarte
4. Deberías recibir la bienvenida
5. Envía `/webapp` para obtener el link al dashboard

---

## Monitoreo y Mantenimiento

### Revisar logs

**Con Supervisor:**
```bash
sudo tail -f /var/log/monitoreo-backend.out.log
sudo tail -f /var/log/monitoreo-backend.err.log
```

**Con Systemd:**
```bash
sudo journalctl -u monitoreo.service -f
```

### Monitorear procesos

```bash
# Ver estado del servicio
sudo systemctl status monitoreo.service

# Ver procesos de Supervisor
sudo supervisorctl status
```

### Backup de datos

```bash
# Backup de MongoDB
mongodump --out /backup/mongo-$(date +%Y%m%d)

# Backup de archivo de suscriptores
cp alertas/telegram_subscribers.json /backup/subscribers-$(date +%Y%m%d).json
```

### Actualizar código

```bash
cd /home/usuario/sistema-monitoreo
git pull origin main
pip install -r requirements.txt

# Reiniciar el servicio
sudo systemctl restart monitoreo.service
```

---

## Configuración de SSL/HTTPS

### Opción A: Let's Encrypt (Gratuito y Recomendado)

```bash
sudo apt install certbot python3-certbot-nginx

# Generar certificado
sudo certbot certonly --nginx -d tu-dominio.com -d www.tu-dominio.com

# Renovación automática
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

### Opción B: Certificado Autofirmado (Temporal)

```bash
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/certs/tu-dominio/key.pem \
  -out /etc/ssl/certs/tu-dominio/cert.pem
```

---

## Troubleshooting

### El bot no envía mensajes

1. **Verificar que el token es correcto:**
```bash
curl https://api.telegram.org/bot<TOKEN>/getMe
```

2. **Verificar que el suscriptor está registrado:**
```bash
cat alertas/telegram_subscribers.json
```

3. **Ver logs de errores:**
```bash
sudo tail -50 /var/log/monitoreo-backend.err.log
```

### El link no es clickeable

1. **Asegúrate de que WEBAPP_URL tiene formato correcto:**
```bash
grep WEBAPP_URL .env
# Debe ser: https://tu-dominio.com o similar
```

2. **Verifica el mensaje del bot:**
```bash
# El comando /webapp debe mostrar el link directamente en el texto
```

### MongoDB no conecta

```bash
# Reiniciar MongoDB
sudo systemctl restart mongodb

# Verificar que está corriendo
sudo systemctl status mongodb

# Conectar manualmente
mongo mongodb://localhost:27017
```

### Too many requests (Rate Limiting)

- Telegram permite ~10 mensajes por segundo
- Si tienes muchas alertas, espaciarlas con delays
- Añadir `await asyncio.sleep(0.1)` entre mensajes

---

## Configuración Final en .env para Producción

```env
# EJEMPLOS DE VALORES REALES
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklmnoPQRstuvWXYZabcdefg
PUBLIC_BASE_URL=https://monitoreo.ejemplo.com
WEBAPP_URL=https://monitoreo.ejemplo.com

MONGODB_URL=mongodb://mongo-user:password@localhost:27017
MONGODB_DB=embalse_arandanos

VITE_SUPABASE_URL=https://xxxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJ...

VITE_API_URL=https://monitoreo.ejemplo.com/api

VITE_DATA_MODE=real
SIMULATED_DATA_ENABLED=false
```

---

## Checklist de Despliegue

- [ ] Token de Telegram obtenido de BotFather
- [ ] Servidor preparado con Python 3.8+
- [ ] MongoDB instalado y corriendo
- [ ] Archivo `.env` configurado correctamente
- [ ] Dependencias instaladas (`pip install -r requirements.txt`)
- [ ] Nginx/Apache configurado como proxy
- [ ] SSL/HTTPS configurado
- [ ] Supervisor o systemd configurado
- [ ] Backend iniciado y corriendo
- [ ] Frontend compilado y corriendo
- [ ] Bot de Telegram probado con `/start`
- [ ] Alerta de prueba enviada exitosamente
- [ ] Logs monitorizados
- [ ] Backups configurados

---

## Contacto y Soporte

Para problemas con:
- **Telegram Bot API**: https://core.telegram.org/
- **FastAPI**: https://fastapi.tiangolo.com/
- **MongoDB**: https://docs.mongodb.com/
- **Nginx**: https://nginx.org/en/docs/

---

**Última actualización:** Abril 2026  
**Versión:** 1.0
