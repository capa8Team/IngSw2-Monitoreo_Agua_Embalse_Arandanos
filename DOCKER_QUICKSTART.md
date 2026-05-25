# Docker Quick Start — Testing Post-Refactor

> Instrucciones rápidas para levantar y validar el proyecto en Docker.

---

## ⚡ TL;DR — Los 3 pasos esenciales

```bash
# 1. Ir a la raíz del proyecto
cd /ruta/a/IngSw2-Monitoreo_Agua_Embalse_Arandanos

# 2. Levantar todo en Docker
docker compose up --build

# 3. En otra terminal, correr test automatizado
bash scripts/test-docker.sh
```

**Esperar:** 2-3 minutos la primera vez (descargando imágenes + construyendo).

---

## 📍 URLs después de levantar

| Servicio | URL | Qué es |
|---|---|---|
| **Frontend** | `http://localhost` | La aplicación Vue 3 completa |
| **API** | `http://localhost:8000` | Backend FastAPI puro |
| **API Docs** | `http://localhost:8000/docs` | Swagger interactivo |
| **MongoDB** | `localhost:27017` | BD (usuario: `admin`, pwd: `Panconpalta1`) |

---

## ✓ Validaciones críticas post-refactor

Después de que everything está up, verifica esto:

### 1️⃣ Backend está vivo

```bash
curl http://localhost:8000/health
# Respuesta esperada: {"status":"ok"}
```

### 2️⃣ Routers refactorizados responden

```bash
# Sensors refactorizado
curl http://localhost:8000/api/sensors/readings

# Alerts refactorizado
curl http://localhost:8000/api/alerts

# Dashboard (sin cambios pero debe funcionar)
curl http://localhost:8000/api/dashboard
```

### 3️⃣ HistoricalData.vue refactorizado funciona

Abre `http://localhost` en navegador:

1. Login (cualquier usuario en demo mode)
2. Navega a "Datos Históricos"
3. Verifica:
   - [ ] 3 gráficos se cargan (pH, Temperatura, Conductividad)
   - [ ] Botones "1 día" / "1 semana" en cada gráfico funcionan
   - [ ] Tabla con mediciones carga correctamente
   - [ ] Filtros de fecha y sensor funcionan
   - [ ] Paginación funciona (si hay datos)

### 4️⃣ Sin errores de CORS ni JS

Abre DevTools (F12) en el navegador:

- [ ] Pestaña **Console**: ningún mensaje rojo
- [ ] Pestaña **Network**: requests a `/api/*` devuelven 200-201

### 5️⃣ MongoDB tiene datos

```bash
docker exec mongodb-arandanos mongosh -u admin -p Panconpalta1 \
  --authenticationDatabase admin \
  --quiet \
  --eval "use Arandanos; db.sensors.countDocuments()"

# Devuelve un número (puede ser 0 si es DB nueva)
```

---

## 🐛 Si algo no funciona

### Error: "Port 80 already in use"

```bash
# Cambiar puerto en .env:
echo "FRONTEND_PORT=8080" >> .env

# Luego levantar de nuevo
docker compose up --build
```

### Error: "Backend connection refused"

```bash
# Verificar que está corriendo
docker ps | grep backend

# Si no aparece, reconstruir
docker compose build --no-cache backend
docker compose up backend -d
```

### Error: "Cannot find module X" en backend

```bash
# Limpiar e instalar dependencias nuevamente
docker compose down -v
docker compose build --no-cache
docker compose up --build
```

### Error: "Access-Control-Allow-Origin" en el navegador

- Verificar que estás accediendo a `http://localhost` (no `http://127.0.0.1`)
- Verificar que el backend está corriendo (`docker ps | grep backend`)
- Revisar `nginx.conf` para asegurar que proxea `/api/*` a `backend:8000`

---

## 📋 Checklist completa de testing

Ver documento completo en **[docs/TESTING_GUIDE.md](docs/TESTING_GUIDE.md)** para tests exhaustivos.

Quick version:

- [ ] `curl http://localhost:8000/health` → `{"status":"ok"}`
- [ ] `curl http://localhost:8000/docs` carga Swagger sin errores
- [ ] `/api/sensors/readings` devuelve respuesta (datos o vacío)
- [ ] `/api/alerts` devuelve respuesta
- [ ] `/api/dashboard` devuelve datos con campos esperados
- [ ] Frontend `http://localhost` carga sin errores
- [ ] HistoricalData.vue: gráficos se cargan y responden a cambios de período
- [ ] Tabla filtra y pagina correctamente
- [ ] PDF modal se abre y genera PDF sin errores
- [ ] Dashboard principal muestra datos en tiempo real
- [ ] Tema (dark/light) funciona
- [ ] No hay errores en console (F12)

---

## 🛑 Detener servicios

```bash
# Pausar (sin perder datos)
docker compose stop

# Detener completamente
docker compose down

# Detener + borrar volúmenes (resetear BD)
docker compose down -v
```

---

## 🔄 Reconstruir desde cero

```bash
docker compose down -v
docker compose build --no-cache
docker compose up --build
```

---

## 📊 Ver logs en vivo

```bash
# Backend
docker compose logs -f backend

# MongoDB
docker compose logs -f mongodb

# Frontend
docker compose logs -f frontend

# Todo junto
docker compose logs -f
```

---

## 🧪 Script de testing automatizado

```bash
bash scripts/test-docker.sh
```

Ejecuta 5 fases:
1. Verifica Docker + Docker Compose instalados
2. Levanta servicios y espera que estén listos
3. Valida endpoints de API
4. Revisa logs por errores
5. Verifica conexión a MongoDB

---

## 📚 Documentación completa

- **[docs/TESTING_GUIDE.md](docs/TESTING_GUIDE.md)** — Testing exhaustivo post-refactor
- **[docs/CODE_REVIEW.md](docs/CODE_REVIEW.md)** — Problemas identificados y plan de acción
- **[docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md)** — Estructura de carpetas
- **[docker-compose.yml](docker-compose.yml)** — Configuración de servicios
- **[scripts/test-docker.sh](scripts/test-docker.sh)** — Script automatizado de testing

---

## ✅ Siguiente paso

Una vez validado en Docker:

1. **Revisar** los problemas P0 y P1 en [CODE_REVIEW.md](docs/CODE_REVIEW.md)
2. **Ejecutar** el plan de acción Fase 1 (seguridad)
3. **Hacer commit** de los cambios cuando todo esté validado

---

> **Última actualización:** 2026-05-23  
> **Refactorización:** Reorganización profesional de carpetas + HistoricalData.vue refactorizado
