# Testing Guide — Docker Local Environment

> **Fecha:** 2026-05-23  
> **Objetivo:** Levantar el proyecto completo en Docker y validar que la refactorización no rompió nada.

---

## 1. Requisitos previos

- **Docker** instalado (versión 20.10+)
- **Docker Compose** instalado (versión 2.0+)
- Puerto 80 y 8000 disponibles en tu máquina (o modificar en `.env`)

### Verificar instalación

```bash
docker --version
docker compose --version
```

---

## 2. Preparación del entorno

### 2.1 — Crear archivo `.env` (opcional)

Copia este contenido en la raíz del proyecto como `.env` para configuración personalizada:

```env
# MongoDB
MONGO_PORT=27017
MONGO_INITDB_ROOT_USERNAME=admin
MONGO_ROOT_PASSWORD=Panconpalta1
MONGODB_DB=Arandanos

# Backend
BACKEND_PORT=8000
JWT_SECRET=dev-secret-cambiar-en-produccion
SIMULATED_DATA_ENABLED=true

# Frontend
FRONTEND_PORT=5173
VITE_API_URL=
VITE_DATA_MODE=simulated

# Opcional: descomenta si usas Telegram o Mailersend
# TELEGRAM_BOT_TOKEN=your_token_here
# MAILERSEND_API_TOKEN=your_token_here
# MAILERSEND_FROM_EMAIL=noreply@example.com
```

Si no creas `.env`, Docker Compose usa los valores por defecto del `docker-compose.yml`.

### 2.2 — Posicionarse en la raíz del proyecto

```bash
cd /path/to/IngSw2-Monitoreo_Agua_Embalse_Arandanos
```

---

## 3. Levantar los servicios

### Opción A — Levantar todo (MongoDB + Backend + Frontend)

```bash
docker compose up --build
```

La primera vez descargará e instalará dependencias (~3-5 minutos).

**Output esperado:**
```
✓ mongodb-arandanos   [RUNNING]
✓ backend-fastapi     [RUNNING]
✓ frontend-arandanos  [RUNNING]

backend-fastapi  | INFO:     Uvicorn running on http://0.0.0.0:8000
frontend-arandanos | /docker-entrypoint.sh: exec: nginx ...
```

### Opción B — Levantar solo backend + MongoDB (sin frontend)

```bash
docker compose up mongodb backend --build
```

Útil si solo quieres testear la API sin compilar el frontend.

### Opción C — Detener servicios

```bash
docker compose down
```

Para detener y eliminar volúmenes (borra datos de MongoDB):

```bash
docker compose down -v
```

---

## 4. URLs de acceso

Una vez levantado todo con `docker compose up`:

| Servicio | URL | Usar para |
|---|---|---|
| Frontend | `http://localhost:5173` o `http://localhost` | Ver la UI completa |
| Backend (API) | `http://localhost:8000` | Llamadas directo a REST API |
| API Docs | `http://localhost:8000/docs` | Swagger interactivo |
| MongoDB | `mongodb://admin:Panconpalta1@localhost:27017` | MongoDBCompass, etc. |

---

## 5. Checklist de validación — Testing post-refactor

Ejecuta estos tests en orden para confirmar que la refactorización no rompió nada.

### 5.1 — API y conectividad

- [ ] **Health check:** `curl http://localhost:8000/health` → debe devolver `{"status":"ok"}`
- [ ] **Swagger API docs:** Abre `http://localhost:8000/docs` en el navegador
  - [ ] Se carga correctamente sin errores de CORS
  - [ ] Listar todos los endpoints disponibles
  - [ ] Verificar que los routers movidos aparecen con sus prefijos (`/api/sensors`, `/api/alerts`, `/api/dashboard`, etc.)

### 5.2 — Backend — Endpoints refactorizados

#### Sensores (`/api/sensors`)
```bash
# Obtener datos del dashboard (actual)
curl -X GET "http://localhost:8000/api/sensors/readings?limit=5" \
  -H "accept: application/json"

# Obtener historial de sensores
curl -X GET "http://localhost:8000/api/sensors/history?limit=50" \
  -H "accept: application/json"
```

- [ ] Status 200, devuelve datos (o arreglo vacío, dependiendo de si hay datos en MongoDB)
- [ ] Estructura de respuesta es consistente

#### Alertas (`/api/alerts`)
```bash
curl -X GET "http://localhost:8000/api/alerts" \
  -H "accept: application/json"
```

- [ ] Status 200, devuelve lista de alertas (puede estar vacía)

#### Dashboard (`/api/dashboard`)
```bash
curl -X GET "http://localhost:8000/api/dashboard" \
  -H "accept: application/json"
```

- [ ] Status 200, devuelve datos del dashboard con campos `ph`, `temperatura`, `conductivity`, `timestamp`

### 5.3 — Frontend — Componentes refactorizados

Abre `http://localhost` (o `http://localhost:5173` si no funciona el primero).

#### Tests de navegación
- [ ] Se carga la UI sin errores en la consola (F12 → Console)
- [ ] Página de login es accesible
- [ ] Ingresa con cualquier usuario (demo mode) y llega al dashboard

#### Tests de vistas refactorizadas
Navega a "Datos Históricos" (HistoricalData.vue refactorizado):

- [ ] Se cargan los tres gráficos (pH, Temperatura, Conductividad)
- [ ] Cada gráfico tiene dos botones "1 día" y "1 semana" y funcionan (cambian datos)
- [ ] La tabla "Mediciones en Tiempo Real" carga correctamente
- [ ] Los filtros de sensor y fecha funcionan
- [ ] La paginación funciona (si hay múltiples páginas)
- [ ] Botón "Descargar PDF" (si eres admin) está visible
- [ ] Modal de PDF se abre y los filtros funcionan

#### Tests de componentes atómicos (refactorización de HistoricalData)
- [ ] `SensorChart.vue` — los gráficos responden a cambios de período (no hay errores en consola)
- [ ] `MeasurementsTable.vue` — la tabla filtra y pagina correctamente
- [ ] `PdfExportModal.vue` — modal se abre/cierra correctamente, genera PDF sin errores

### 5.4 — Frontend — Componentes existentes (regresión)

Verifica que componentes que NO fueron refactorizados siguen funcionando:

- [ ] **Dashboard principal:**
  - [ ] Se cargan las tarjetas de dispositivos
  - [ ] Indicadores de batería se muestran correctamente
  - [ ] Gauges de pH, temperatura, conductividad muestran valores
  - [ ] Los valores se actualizan cada 2-5 segundos (si SIMULATED_DATA_ENABLED=true)

- [ ] **Admin Dashboard (si eres admin):**
  - [ ] Se carga la vista de administración
  - [ ] Puede ver lista de usuarios
  - [ ] Puede ver alertas globales

- [ ] **Tema (dark/light):**
  - [ ] Botón de tema en la esquina superior cambia de light a dark
  - [ ] Los gráficos responden al cambio de tema (colores se actualizan)
  - [ ] No hay errores en consola

### 5.5 — Backend — Logging y monitoreo

Abre los logs del backend:

```bash
docker compose logs -f backend
```

Mientras haces requests:

- [ ] Logs en `INFO` muestran cada request con `correlation_id`
- [ ] Si hay errores, aparecen en `ERROR` o `FATAL` con detalles del origen (component, path)
- [ ] No hay tracebacks no capturados en stderr

### 5.6 — Base de datos — MongoDB

Conecta a MongoDB con cualquier cliente (ej. MongoDB Compass):

```
Connection String: mongodb://admin:Panconpalta1@localhost:27017/?authSource=admin
Database: Arandanos
```

- [ ] Existen las colecciones esperadas (sensors, alerts, etc., dependiendo de tu esquema)
- [ ] Los datos se insertan/actualizan correctamente (si envías un request POST a un endpoint)

---

## 6. Tests de integración — Scenario-based

### Escenario 1: Usuario crea una alerta

1. Navega a "Alertas" (si está disponible)
2. Intenta crear una alerta manualmente o genera una mediante un sensor fuera de rango
3. [ ] La alerta aparece en `/api/alerts`
4. [ ] En el dashboard aparece la alerta visual
5. [ ] Si Telegram está configurado, debería enviarse un mensaje (revisa logs)

### Escenario 2: Cambiar límites de sensor

1. Navega a "Admin Alerts" (si eres admin)
2. Intenta cambiar los límites (ej. pH max de 8.5 a 7.0)
3. [ ] El cambio se refleja en la tabla inmediatamente
4. [ ] **P1-B CRITICAL:** Ahora abre otro navegador / incógnito y recarga la página
   - [ ] Los límites cambiados se mantienen (no están en localStorage de otro navegador)
   - [ ] Si esto NO funciona, es el problema P1-B que necesita ser arreglado

### Escenario 3: Generar y descargar reporte PDF

1. Navega a "Datos Históricos"
2. Haz clic en "Descargar PDF"
3. [ ] Se abre el modal
4. [ ] Selecciona filtros (dispositivo, sensor, rango de fechas)
5. [ ] Haz clic en "Generar PDF"
6. [ ] [ ] El PDF se descarga sin errores
7. [ ] Abre el PDF y verifica:
   - [ ] Título, filtros aplicados están presentes
   - [ ] Tabla de mediciones se renderiza correctamente
   - [ ] Gráficos incrustados se ven (si hay datos)

---

## 7. Troubleshooting

### Problema: "Port 80 already in use"

```bash
# Opción 1: Cambiar puerto en .env
FRONTEND_PORT=8080

# Opción 2: Matar el proceso usando puerto 80
sudo lsof -ti:80 | xargs kill -9
```

### Problema: "MongoDB connection refused"

```bash
# Verificar que MongoDB está corriendo
docker ps | grep mongodb

# Si no aparece, reiniciar los servicios
docker compose down -v
docker compose up --build
```

### Problema: "Backend no encuentra módulos de Python"

```bash
# Reconstruir la imagen del backend
docker compose build --no-cache backend
docker compose up backend
```

### Problema: "CORS errors en el navegador"

- Si ves `No 'Access-Control-Allow-Origin'` en la consola, asegúrate de que:
  1. El backend está corriendo (`docker ps | grep backend`)
  2. Estás llamando a `http://localhost:8000` desde la URL correcta
  3. Si usas `http://localhost` (frontend), nginx debe proxear a `/api/*` → backend (verificar `nginx.conf`)

### Problema: "Datos no se guardan en MongoDB"

```bash
# Verificar que MongoDB tiene datos
docker exec mongodb-arandanos mongosh -u admin -p Panconpalta1 --authenticationDatabase admin
> use Arandanos
> db.sensors.find().limit(5)
```

Si está vacío, envía un POST a un endpoint que guarde datos y verifica los logs.

---

## 8. Limpiar y resetear

### Detener todo sin perder datos

```bash
docker compose stop
```

### Detener todo Y eliminar volúmenes (resetear base de datos)

```bash
docker compose down -v
```

### Reconstruir todo desde cero

```bash
docker compose down -v
docker compose build --no-cache
docker compose up
```

---

## 9. Verificación final — Checklist completa

Antes de dar el proyecto por completamente testado, marca esto:

- [ ] Health check del backend devuelve 200
- [ ] Swagger API docs carga sin errores
- [ ] Los tres routers refactorizados (`sensors`, `alerts`, `dashboard`) responden
- [ ] Frontend se carga sin errores en consola
- [ ] Los tres gráficos de HistoricalData cargan y responden a cambios de período
- [ ] Tabla de mediciones filtra y pagina correctamente
- [ ] PDF se genera sin errores
- [ ] Dashboard principal muestra datos en tiempo real
- [ ] Tema (dark/light) funciona y gráficos responden
- [ ] Logs del backend muestran requests y correlation_ids
- [ ] MongoDB contiene datos esperados
- [ ] No hay errores de CORS, conexión denegada, o módulos faltantes

---

## 10. Próximos pasos

Si todo pasó:
1. Commit los cambios: `git add . && git commit -m "Refactor: HistoricalData architecture + Docker validation"`
2. Revisar los problemas P0 y P1 en [CODE_REVIEW.md](CODE_REVIEW.md)
3. Seguir el plan de acción de Fase 1 (seguridad) antes de cualquier deploy

Si algo no funciona:
1. Recopila los logs: `docker compose logs > test_output.log`
2. Revisa los errores específicos y busca en `TROUBLESHOOTING` (sección 7)
3. Si persiste, examina los archivos de código refactorizado contra el original
