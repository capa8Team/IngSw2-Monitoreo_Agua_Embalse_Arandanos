# Sistema de logging — Monitoreo Embalse Arándanos

Rama: **`implementacionLogs`** · Repositorio: [capa8Team/IngSw2-Monitoreo_Agua_Embalse_Arandanos](https://github.com/capa8Team/IngSw2-Monitoreo_Agua_Embalse_Arandanos)

---

## 1. Resumen

| Aspecto | Detalle |
|---------|---------|
| Niveles | `INFO`, `WARN`, `FATAL` |
| Persistencia | 7 tablas en **Supabase (PostgreSQL)** |
| Fallback | `backend_fastapi/logs/fallback.log` |
| Correlación | Header `X-Correlation-Id` |
| Escritura | Solo **backend** (nunca desde el navegador) |

---

## 2. Tablas Supabase

Script: [`database/supabase/supabase_logs_schema.sql`](../database/supabase/supabase_logs_schema.sql)

| Origen | Tabla |
|--------|-------|
| Dashboard / API HTTP | `dashboard_logs` |
| Historial sensores | `registro_historico_logs` |
| Export PDF | `exportar_pdf_logs` |
| Login JWT | `login_logs` |
| MongoDB / persistencia | `supabase_db_logs` |
| Telegram | `telegram_bot_logs` |
| MailerSend | `mailersend_api_logs` |

---

## 3. Estructura en el código

```
backend_fastapi/
  core/log_service.py      # API central
  core/log_sanitizer.py
  core/middleware.py         # X-Correlation-Id
  db/log_models.py
  logs_router.py             # GET /api/logs/...
src/utils/logger.js          # Consola frontend
```

---

## 4. Configuración

En `backend_fastapi/.env` (ver `.env.example`):

```env
SUPABASE_DB_URL=postgresql+psycopg2://postgres:PASSWORD@db.xxx.supabase.co:5432/postgres
LOG_DIR=logs
APP_ENV=development
```

1. **Supabase:** ejecutar `database/supabase/supabase_logs_schema.sql` solo si las tablas **aún no existen** (ver §4.1).
2. Arrancar stack: `docker compose up --build` desde la raíz del repo.

### 4.1 Ya ejecuté los scripts en el SQL Editor

**No vuelvas a correr el script completo** si las tablas ya están creadas (obtendrás errores del tipo `relation already exists`).

1. En Supabase → **Table Editor**, confirma las 7 tablas `*_logs`.
2. En **Project Settings → Database**, copia el connection string (modo URI) y ponlo en `backend_fastapi/.env` como `SUPABASE_DB_URL`.
3. Arranca el backend y sigue la verificación en §5.

Comprobación en SQL Editor:

```sql
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public' AND table_name LIKE '%_logs'
ORDER BY table_name;
```

Si falta alguna tabla, ejecuta únicamente el `CREATE TABLE` de esa tabla desde `database/supabase/supabase_logs_schema.sql`, no el archivo entero otra vez.

---

## 5. Verificación paso a paso

### 5.1 Arranque

```bash
docker compose up --build
```

- Backend: http://localhost:8000/health  
- Docs: http://localhost:8000/docs  
- Frontend: http://localhost:5173  

Comprobar logs de arranque:

```bash
docker logs backend-fastapi --tail 40
```

Debe aparecer `[dashboard_logs]` o líneas en `backend_fastapi/logs/fallback.log` si Supabase aún no tiene tablas.

### 5.2 Flujo normal (INFO)

| Paso | Acción | Tabla esperada |
|------|--------|----------------|
| 1 | `GET /health` | — (excluido del middleware ruidoso) |
| 2 | `GET /api/dashboard` | `dashboard_logs` INFO |
| 3 | `POST` lectura sensor (ESP8266 o simulador) | `supabase_db_logs` INFO |
| 4 | `GET /api/sensors/history` | `registro_historico_logs` INFO |
| 5 | Login correcto `POST /api/auth/login` | `login_logs` INFO |

Ejemplo login:

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -H "X-Correlation-Id: test-login-001" \
  -d "{\"email\":\"admin@test.com\",\"password\":\"123456789\"}"
```

### 5.3 Anomalías (WARN)

| Paso | Acción | Resultado |
|------|--------|-----------|
| A | Login con contraseña incorrecta | `login_logs` WARN |
| B | `GET /api/sensors/history` sin datos | `registro_historico_logs` WARN |
| C | Dashboard sin MongoDB (solo simulado) | `dashboard_logs` WARN |
| D | MailerSend sin token en `.env` | `mailersend_api_logs` WARN |

### 5.4 Críticos (FATAL)

| Paso | Acción | Resultado |
|------|--------|-----------|
| E | Detener MongoDB y `POST` sensor | `supabase_db_logs` FATAL o WARN en escritura |
| F | Forzar error 500 (ruta inválida interna) | `dashboard_logs` FATAL vía exception handler |

### 5.5 Consulta API

```bash
curl http://localhost:8000/api/logs/origins
curl "http://localhost:8000/api/logs/login_logs?limit=10"
curl "http://localhost:8000/api/logs/dashboard_logs/export?format=txt&limit=20" -o logs.txt
```

Filtros: `level`, `component`, `correlation_id`, `from`, `to`, `limit`, `offset`.

### 5.6 SQL en Supabase

```sql
SELECT created_at, level, component, message, correlation_id
FROM login_logs
ORDER BY created_at DESC
LIMIT 20;
```

### 5.7 Tests automáticos

```bash
pip install pytest sqlalchemy psycopg2-binary
pytest tests/test_log_service.py -v
```

### 5.8 Frontend

1. Abrir http://localhost:5173 e iniciar sesión.  
2. F12 → consola: en error de red debe verse `[WARN] [frontend]` con contexto.  
3. El `correlation_id` del header debe coincidir con el de `/api/logs/dashboard_logs`.

---

## 6. Seguridad

- No se guardan contraseñas, tokens ni API keys (sanitizador en `core/log_sanitizer.py`).
- Telegram: solo `chat_id_hash` (SHA-256).
- RLS habilitado en SQL; inserción con `SUPABASE_DB_URL` desde el servidor.

---

## 7. Nota sobre la rama anterior (Sistema Riego)

El trabajo de logs hecho en el repo `VBenjaV/SistemaRiegoInteligenteTI` quedó en **stash** (`git stash list`). La implementación vigente está solo en **`implementacionLogs`** de este repositorio.
