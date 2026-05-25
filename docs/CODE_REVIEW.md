# Code Review — Monitoreo Agua Embalse Arándanos

> **Fecha:** 2026-05-23  
> **Revisión hecha sobre:** rama `implementacionLogs`  
> **Alcance:** Frontend (Vue 3), Backend (FastAPI), scripts auxiliares

---

## Índice

1. [Estado general](#1-estado-general)
2. [Problemas críticos (P0)](#2-problemas-críticos-p0)
3. [Problemas importantes (P1)](#3-problemas-importantes-p1)
4. [Mejoras de calidad (P2 / P3)](#4-mejoras-de-calidad-p2--p3)
5. [Código muerto identificado](#5-código-muerto-identificado)
6. [Evaluación de escalabilidad](#6-evaluación-de-escalabilidad)
7. [Evaluación de comentarios y legibilidad](#7-evaluación-de-comentarios-y-legibilidad)
8. [Plan de acción](#8-plan-de-acción)

---

## 1. Estado general

### Lo que está bien

| Área | Fortaleza |
|---|---|
| Estructura de carpetas (backend) | `routers/`, `services/`, `core/` correctamente separados |
| Configuración centralizada | `core/config.py` con `pydantic_settings` — correcto y escalable |
| Sistema de logging | Logging en Supabase con niveles, origen y correlation_id — maduro |
| `HistoricalData` (frontend) | Composable + servicio + componentes atómicos + vista orquestadora — excelente |
| Middleware de correlación | `CorrelationIdMiddleware` muestra criterio de diseño real |
| Manejo de temas (dark/light) | Evento global `embalse-theme-change` es un patrón limpio |

### Valoración honesta

El proyecto tiene una base estructural sólida tras el refactor. Los problemas que existen son principalmente **deuda técnica acumulada antes del refactor**, no fallas de diseño nuevas. Con las correcciones prioritarias aplicadas, el proyecto estaría en condición profesional real.

---

## 2. Problemas críticos (P0)

> Estos problemas deben resolverse **antes de cualquier despliegue en producción**. Algunos representan riesgos de seguridad directos.

---

### P0-A — Credenciales de demo hardcodeadas en la UI

**Archivo:** `src/views/Login.vue` (aprox. línea 51)

**Descripción:**  
Las credenciales `admin@test.com / 123456789` están visibles en el código fuente del componente de login. Cualquier usuario puede ver esto en las DevTools del navegador o haciendo `View Source`.

**Por qué es grave:**  
En producción, el bundle de Vue se sirve tal cual. No hay ofuscación real. Las credenciales de una cuenta con privilegios de administrador quedan expuestas a cualquier persona que acceda al sitio.

**Solución:**  
Eliminar el bloque de demo completamente del template y del script. Si se necesita facilitar el acceso durante desarrollo, usar un archivo `.env.local` con variables que el servidor de desarrollo lea, pero que nunca lleguen al bundle de producción.

```vue
<!-- ELIMINAR esto de Login.vue -->
<div class="demo-credentials">
  <p>Demo: admin@test.com / 123456789</p>
</div>
```

---

### P0-B — Tres sistemas de autenticación en conflicto

**Archivos involucrados:**
- `src/services/sessionAuth.js` — JWT almacenado en `localStorage`
- `src/stores/authStore.js` — Pinia store con Supabase
- `src/services/SupabaseAuthService.js` — llamadas directas a Supabase

**Descripción:**  
El proyecto tiene tres implementaciones de autenticación que coexisten y se solapan. Algunos componentes usan `sessionAuth.js` para verificar roles; otros usan el store de Pinia; otros llaman a `SupabaseAuthService` directamente. No hay un flujo único y predecible.

**Por qué es grave:**  
- Un componente puede considerar al usuario autenticado mientras otro lo considera no autenticado, dependiendo de cuál capa consulta.
- Los guards del router usan `sessionAuth` (localStorage), pero el store de Pinia puede tener un estado diferente si Supabase invalidó la sesión.
- Los bugs de sesión intermitentes son casi imposibles de reproducir y depurar.
- Representa una superficie de ataque más grande: tres lugares donde puede fallar la validación de permisos.

**Solución — criterio para elegir:**

| Sistema | Ventaja | Cuándo usarlo |
|---|---|---|
| `authStore.js` (Pinia + Supabase) | Reactivo, centralizado, integrado con Supabase Auth | **Recomendado si Supabase es el auth principal** |
| `sessionAuth.js` (JWT local) | Simple, sin dependencia de Supabase | Recomendado si el backend emite sus propios JWT |

**Acción concreta:**  
1. Decidir cuál sistema es el definitivo (probablemente `authStore` + Supabase).  
2. Migrar todos los componentes que usen `sessionAuth.js` al store.  
3. Eliminar `sessionAuth.js` y `SupabaseAuthService.js` (o reducirlo a un thin wrapper).  
4. Actualizar los guards del router para usar el store.

---

## 3. Problemas importantes (P1)

> No bloquean el lanzamiento inmediato, pero sí generan bugs reales en escenarios de uso normal.

---

### P1-A — Configuración de límites de sensor en 5 lugares distintos

**Archivos involucrados:**
- `src/views/DeviceDashboard.vue` (valores por defecto inline)
- `src/views/AdminAlerts.vue` (valores por defecto inline)
- `src/services/AlertService.js` (valores por defecto inline)
- `src/utils/sensorUtils.js` — `SENSOR_META` con `min` y `max`
- `backend_fastapi/core/config.py` — variables de entorno

**Descripción:**  
Los umbrales que definen cuándo un sensor está en alerta (ej. pH entre 6 y 8.5) están definidos de forma independiente en cada uno de estos archivos. Si el equipo decide cambiar el límite máximo de conductividad, hay que modificar 5 archivos distintos y confiar en que nadie se olvide de alguno.

**Por qué es grave:**  
Ya existe un caso concreto: `SENSOR_META` en `sensorUtils.js` tiene los límites para el frontend, pero `config.py` también los tiene como env vars para el backend. Si divergen, el frontend puede mostrar "Normal" para un valor que el backend considera alerta, o viceversa. El usuario ve mensajes contradictorios.

**Solución propuesta:**  
El backend debe ser el **único source of truth** de los límites. Crear un endpoint:

```
GET /api/sensors/limits
→ { ph: { min: 6, max: 8.5 }, temperature: { min: 15, max: 30 }, conductivity: { min: 700, max: 1600 } }
```

El frontend obtiene estos límites al iniciar y los almacena en un store de Pinia. `SENSOR_META` en `sensorUtils.js` mantiene solo `label` y `unit` (metadatos de presentación), no límites de negocio.

---

### P1-B — `localStorage` como persistencia de configuración de alertas

**Archivos:** `src/views/AdminAlerts.vue`, `src/views/AlertsManagement.vue`, `src/components/DeviceDashboard.vue`

**Descripción:**  
Cuando un administrador modifica los límites de alerta desde la UI, los cambios se guardan en `localStorage`. Esto significa:
- Los cambios se pierden si el usuario limpia los datos del navegador.
- Cada dispositivo/navegador tiene su propia configuración: dos administradores distintos ven límites diferentes.
- Si hay múltiples administradores, no hay manera de saber cuál configuración está "activa".

**Por qué es grave:**  
Los "guardados" son una ilusión. El sistema da feedback visual de que algo fue guardado, pero en un entorno multiusuario o multi-dispositivo, esa configuración no existe para nadie más.

**Solución:**  
Persistir los límites en la base de datos (Supabase ya tiene la tabla `alert_limits` según el esquema SQL). `AlertService.js` debe hacer `POST /api/alerts/limits` en lugar de escribir en `localStorage`.

---

### P1-C — Código muerto que confunde la navegación del proyecto

Ver sección [5. Código muerto identificado](#5-código-muerto-identificado) para la lista completa.

**El más urgente:** `src/views/Dashboard.vue` está definido pero no aparece en ninguna ruta del router. `DeviceDashboard.vue` es el componente real. `Dashboard.vue` genera confusión sobre cuál es el componente activo cuando alguien nuevo lee el código.

---

### P1-D — `console.log([DEBUG])` en producción

**Archivo principal:** `src/views/DeviceDashboard.vue` (20+ instancias)

**Descripción:**  
El archivo tiene docenas de `console.log` marcados con `[DEBUG]` que fueron útiles durante el desarrollo pero que en producción:
1. Exponen información interna del estado de la aplicación en la consola del navegador (visible para cualquier usuario).
2. Degradan el rendimiento en modo producción.
3. Dificultan la lectura de la consola cuando hay errores reales.

**Solución:**  
Ya existe `src/utils/logger.js`. Reemplazar los `console.log([DEBUG] ...)` por llamadas al logger, o eliminarlos directamente si son información que ya no aporta valor.

```js
// En lugar de:
console.log('[DEBUG] Fetching from', url)

// Usar el logger existente:
logger.debug('Fetching sensor data', { url })
// O simplemente eliminar si ya no es necesario en producción
```

---

## 4. Mejoras de calidad (P2 / P3)

> No son urgentes pero mejoran la mantenibilidad y escalabilidad a mediano plazo.

---

### P2-A — Polling sin control de errores ni throttle

**Archivos:** `src/services/ArduinoConfig.js`, `src/composables/useHistoricalData.js`

**Descripción:**  
El polling cada 2–5 segundos no tiene:
- **Backoff exponencial**: si el servidor devuelve 503, el cliente sigue bombardeando con la misma frecuencia.
- **Deduplicación de requests**: si el usuario navega rápido entre vistas y ambas hacen polling al mismo endpoint, pueden acumularse 4-5 requests simultáneos.
- **Control de límite de reintentos**: un error permanente (servidor caído) sigue generando requests infinitamente.

**Solución sugerida:**  
Implementar un helper de polling con backoff:

```js
// src/utils/pollingUtils.js
export function createPoller(fn, { interval = 5000, maxInterval = 60000 } = {}) {
  let timer = null
  let currentInterval = interval

  async function tick() {
    try {
      await fn()
      currentInterval = interval // reset on success
    } catch {
      currentInterval = Math.min(currentInterval * 2, maxInterval) // backoff
    }
    timer = setTimeout(tick, currentInterval)
  }

  return {
    start: () => tick(),
    stop:  () => clearTimeout(timer),
  }
}
```

---

### P2-B — Sin paginación real en el historial de sensores

**Archivos:** `backend_fastapi/routers/sensors.py`, `src/components/historical/MeasurementsTable.vue`

**Descripción:**  
El endpoint `/api/sensors/history?limit=200` carga hasta 200 registros de una vez. Con datos reales de producción (un ESP32 enviando cada 30 segundos = 2.880 registros/día), en menos de una semana el cliente estaría descargando miles de registros para renderizar solo 10 en la tabla.

**Solución:**  
Agregar paginación cursor al endpoint:

```
GET /api/sensors/history?limit=50&before=<timestamp>
```

El componente `MeasurementsTable.vue` ya tiene la UI de paginación lista; solo necesita conectarla a un endpoint paginado en lugar de hacer el slice en cliente.

---

### P2-C — Envolvente de respuesta API inconsistente

**Descripción:**  
Algunos endpoints del backend devuelven `{ status, message, data }`, otros devuelven `{ error, data }`, y algunos devuelven el objeto directamente sin envolver. El frontend tiene lógica condicional en múltiples lugares para manejar cada formato.

**Solución:**  
Definir un único schema de respuesta en `models.py` y usarlo en todos los routers:

```python
class ApiResponse(BaseModel):
    success: bool
    data: Any = None
    message: str = ""
```

---

### P3-A — Mezcla de español e inglés en el código

**Descripción:**  
El backend tiene docstrings y mensajes en español, el frontend los tiene en inglés, y hay variables mezcladas (`nombreDispositivo` junto a `deviceName`). No es un bug, pero dificulta la colaboración y las búsquedas en el código.

**Recomendación:**  
Elegir un idioma para el código (inglés es el estándar en proyectos técnicos) y usar español solo para los textos visibles al usuario final. Documentación interna puede estar en español si el equipo es hispanohablante.

---

### P3-B — Sin tipado en el frontend

**Descripción:**  
Los props de los componentes usan `{ type: Object }` sin especificar la forma del objeto. Por ejemplo, `DeviceCard.vue` acepta un `device` sin validar qué propiedades tiene. Esto hace que los errores de "property undefined" aparezcan en runtime y no en desarrollo.

**Recomendación (a futuro):**  
Migrar gradualmente a TypeScript, o al menos documentar la forma de los objetos con JSDoc:

```js
/**
 * @typedef {Object} DeviceReading
 * @property {string} device
 * @property {Date} timestamp
 * @property {number} ph
 * @property {number} temperature
 * @property {number} conductivity
 */
```

---

## 5. Código muerto identificado

| Archivo | Estado | Acción recomendada |
|---|---|---|
| `src/views/Dashboard.vue` | No enrutado, nunca se renderiza | Eliminar o confirmar si hay plan de uso |
| `src/services/SupabaseAuthService.js` — `saveAlertLimits()`, `getAlertLimitsByAdmin()` | Funciones definidas pero nunca llamadas | Eliminar esas funciones o conectarlas a la UI |
| `src/utils/simulador.js` | Verificar si algún componente lo importa actualmente | Revisar y eliminar si no hay imports activos |
| `backend_fastapi/telegram_service.py` (raíz) | Duplicado de `services/telegram.py` | Eliminar el archivo raíz |
| `backend_fastapi/routers/dashboard.py` — comentario `# ... resto de tu lógica` | Comentario placeholder sin código real | Limpiar |
| `alertas/telegram_service.py` líneas 116-117 | `@classmethod` duplicado — bug real en tiempo de ejecución | Corregir eliminando el decorador extra |

---

## 6. Evaluación de escalabilidad

### ¿El proyecto escala? Respuesta: **Sí, con condiciones**

La separación de capas que existe hoy (routers → services → core) permite crecer sin reescribir. El sistema de logging ya está pensado para producción. La arquitectura de componentes del frontend (tras el refactor) permite agregar nuevas vistas sin tocar las existentes.

**Pero hay dos limitaciones concretas que se volverán problemas reales:**

#### Limitación 1 — Datos sin paginación
Con un solo dispositivo enviando datos cada 30 segundos, en 7 días hay ~20.000 registros. El sistema actual los carga todos en memoria. La tabla se vuelve inutilizable y la API empieza a dar timeouts.

**Cuándo se siente:** Con más de 2 dispositivos activos o más de 1 semana de datos históricos.

#### Limitación 2 — Polling agresivo sin control
Cada instancia del dashboard hace requests cada 2-5 segundos. Con 10 usuarios simultáneos, son 120 requests por minuto solo para el dashboard. Sin rate limiting en el backend ni backoff en el cliente, un pico de tráfico puede tumbar la API.

**Cuándo se siente:** Con más de 5 usuarios simultáneos.

### Lo que sí escala bien hoy
- Agregar nuevos tipos de sensor → solo agregar a `SENSOR_META` y al esquema de MongoDB.
- Agregar nuevas vistas → el router y la estructura de componentes lo soporta.
- Agregar nuevos dispositivos Arduino → el sistema de `arduino_id` ya lo contempla.
- Escalar el backend horizontalmente → `main.py` es stateless excepto por el bot de Telegram.

---

## 7. Evaluación de comentarios y legibilidad

### Backend — Buena calidad general
Los routers del backend tienen una estructura legible: imports, instancia del router, endpoints claramente separados. Los docstrings en `services/mongodb.py` son útiles. El sistema de logging con `LogOrigin` y `LogLevel` está bien documentado en `LOGGING.md`.

**Mejorable:** `AlertService` (frontend) no tiene ningún comentario. No queda claro desde el código cuándo se dispara una alerta vs. cuándo solo se verifica un rango.

### Frontend — Irregular
- `useHistoricalData.js` — limpio, sin comentarios innecesarios. ✓
- `DeviceDashboard.vue` — demasiado largo aún, con bloques de `console.log` que añaden ruido visual.
- `SupabaseAuthService.js` — la función de normalización de usuarios (que intenta 6 nombres distintos para el mismo campo) debería tener al menos un comentario explicando por qué existe esa complejidad.

### Regla aplicada en este proyecto
El estándar que se siguió en el refactor es correcto: **no escribir comentarios que describan qué hace el código** (eso ya lo dicen los nombres), sino solo comentar **por qué** existe una decisión no obvia. Esa regla debe aplicarse de manera consistente en los archivos que aún no la siguen.

---

## 8. Plan de acción

### Fase 1 — Seguridad y estabilidad (1–2 días)
> Objetivo: el proyecto puede desplegarse sin riesgos de seguridad obvios.

| # | Tarea | Archivo(s) | Estimado |
|---|---|---|---|
| 1.1 | Eliminar credenciales demo del login | `Login.vue` | 10 min |
| 1.2 | Corregir bug `@classmethod` duplicado | `alertas/telegram_service.py:116-117` | 5 min |
| 1.3 | Eliminar archivo legacy `telegram_service.py` raíz del backend | `backend_fastapi/telegram_service.py` | 5 min |
| 1.4 | Eliminar todos los `console.log([DEBUG])` | `DeviceDashboard.vue` | 30 min |
| 1.5 | Eliminar `Dashboard.vue` si no tiene uso planificado | `src/views/Dashboard.vue` | 5 min |

---

### Fase 2 — Unificación de autenticación (2–3 días)
> Objetivo: un solo flujo de auth predecible de principio a fin.

| # | Tarea | Descripción |
|---|---|---|
| 2.1 | Decidir sistema definitivo | Recomendado: `authStore.js` (Pinia + Supabase) |
| 2.2 | Auditar todos los componentes que usan `sessionAuth.js` | Listar los que necesitan migración |
| 2.3 | Migrar componentes al store de Pinia | Uno a uno, verificando que los guards del router funcionen |
| 2.4 | Actualizar guards del router | `src/router.js` — usar el store en lugar de `sessionAuth` |
| 2.5 | Eliminar `sessionAuth.js` | Solo después de confirmar que ningún componente lo importa |
| 2.6 | Reducir `SupabaseAuthService.js` | Mantener solo lo que el store no cubre |

---

### Fase 3 — Source of truth único para configuración (1 día)
> Objetivo: cambiar un límite de sensor en un solo lugar y que toda la app lo refleje.

| # | Tarea | Descripción |
|---|---|---|
| 3.1 | Crear endpoint `GET /api/sensors/limits` | Devuelve los límites desde `config.py` |
| 3.2 | Crear store de Pinia `useSensorLimitsStore` | Carga los límites al iniciar la app, los expone reactivamente |
| 3.3 | Actualizar `SENSOR_META` en `sensorUtils.js` | Eliminar `min` y `max`, dejar solo `label` y `unit` |
| 3.4 | Conectar `AdminAlerts.vue` al backend | `POST /api/sensors/limits` en lugar de `localStorage` |
| 3.5 | Conectar `DeviceDashboard.vue` al store | Leer límites del store en lugar de valores hardcodeados |

---

### Fase 4 — Paginación y rendimiento (1–2 días)
> Objetivo: el sistema funciona correctamente con semanas de datos históricos.

| # | Tarea | Descripción |
|---|---|---|
| 4.1 | Agregar paginación cursor al endpoint de historial | `GET /api/sensors/history?limit=50&before=<timestamp>` |
| 4.2 | Actualizar `MeasurementsTable.vue` | Solicitar la página siguiente al llegar al final en lugar de paginar en cliente |
| 4.3 | Implementar `pollingUtils.js` con backoff | Helper reutilizable para todos los pollers del frontend |
| 4.4 | Reemplazar polling directo en `ArduinoConfig.js` | Usar el nuevo helper |

---

### Fase 5 — Consistencia y limpieza (1 día)
> Objetivo: cero código muerto, respuestas API uniformes.

| # | Tarea | Descripción |
|---|---|---|
| 5.1 | Normalizar envolvente de respuesta API | `ApiResponse` model en `models.py`, aplicar en todos los routers |
| 5.2 | Eliminar funciones muertas en `SupabaseAuthService.js` | `saveAlertLimits`, `getAlertLimitsByAdmin` |
| 5.3 | Revisar y eliminar `simulador.js` si es dead code | Verificar imports primero |
| 5.4 | Limpiar comentario placeholder en `dashboard.py` | Línea `# ... resto de tu lógica` |

---

### Resumen de esfuerzo total estimado

| Fase | Esfuerzo estimado | Impacto |
|---|---|---|
| Fase 1 — Seguridad | 1 hora | Crítico para producción |
| Fase 2 — Auth unificada | 2–3 días | Crítico para estabilidad |
| Fase 3 — Config centralizada | 1 día | Alto para mantenibilidad |
| Fase 4 — Paginación | 1–2 días | Alto para escalabilidad |
| Fase 5 — Limpieza | 1 día | Medio para legibilidad |
| **Total** | **~7–9 días** | — |

---

> Este documento debe actualizarse conforme se completen las fases. Cuando una tarea se complete, marcarla con ✓ y anotar la fecha para mantener trazabilidad del trabajo realizado.
