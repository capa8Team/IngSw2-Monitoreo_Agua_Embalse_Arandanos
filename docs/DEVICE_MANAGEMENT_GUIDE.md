# Guía: Gestión de Dispositivos y Detección de Microcontroladores

## 📋 Descripción General

El sistema de gestión de dispositivos permite agregar, monitorear y eliminar múltiples microcontroladores (ESP8266, Arduino, STM32, etc.) que envían datos de sensores al embalse de Arandanos.

**Características principales:**
- ✅ Detección automática de nuevos microcontroladores
- ✅ Registro manual de dispositivos
- ✅ Monitoreo de estado de conexión en tiempo real
- ✅ Seguimiento de nivel de batería
- ✅ Historial de sincronización
- ✅ Gestión completa (crear, editar, eliminar)

---

## 🚀 Inicio Rápido

### Acceder al Panel de Dispositivos

1. Inicia sesión como **Administrador**
2. Ve al **Panel de Administración** (`/admin`)
3. Haz clic en la pestaña **📱 Dispositivos**

O directamente: `/devices`

---

## 🔍 Detección Automática

### ¿Cómo funciona?

El sistema escanea automáticamente todos los `arduino_id` que han enviado datos recientemente a la API y que aún no están registrados como dispositivos.

### Pasos para detectar un nuevo microcontrolador:

1. **Asegúrate de que el dispositivo esté enviando datos:**
   - El microcontrolador debe estar activo
   - Debe estar conectado a la red WiFi
   - Debe enviar al menos una lectura de sensores

2. **En el panel de dispositivos, haz clic en "🔍 Detectar Nuevos"**

3. **Espera el escaneo:**
   - El sistema buscará microcontroladores disponibles
   - Si encuentra alguno, los mostrará en una lista

4. **Registra el dispositivo:**
   - Haz clic en "✓ Registrar" en el dispositivo que desees agregar
   - El sistema lo confirmará y lo agregará a tu lista

5. **Personaliza (opcional):**
   - Después de registrarlo, puedes editar el nombre y ubicación

### Troubleshooting - Si no aparecen dispositivos:

- ⚠️ **El microcontrolador no envía datos:** Verifica que esté encendido y conectado
- ⚠️ **Hace mucho que no envía datos:** Intenta escanear nuevamente en unos segundos
- ⚠️ **El API no está disponible:** Verifica la conexión con el backend

---

## ➕ Agregar Dispositivo Manualmente

### Cuándo usarlo:

- Cuando ya tienes un Arduino ID conocido
- Cuando prefieres configurar el dispositivo antes de que envíe datos
- Cuando el sistema de detección automática no funciona

### Pasos:

1. Haz clic en **"➕ Agregar Manual"**
2. Completa el formulario:
   - **Nombre del Dispositivo** * (obligatorio): Ej: "Sensor Embalse Norte"
   - **Tipo de Microcontrolador**: Selecciona ESP8266, Arduino, STM32 u Otro
   - **Ubicación** (opcional): Ej: "Profundidad 5m - Zona A"
   - **Arduino ID** (opcional): Si lo conoces, colócalo aquí
3. Haz clic en **"Agregar Dispositivo"**

---

## 📊 Gestión de Dispositivos

### Tabla de Dispositivos

La tabla muestra todos tus dispositivos registrados con:

| Columna | Significado |
|---------|------------|
| 🟢 Estado | 🟢 Conectado, 🔴 Desconectado, ⚫ Desconocido |
| Nombre | Nombre del dispositivo |
| Tipo | Tipo de microcontrolador (ESP8266, Arduino, etc.) |
| Ubicación | Zona donde está el dispositivo |
| Batería | % de batería restante |
| Última Sincronización | Hace cuánto tiempo envió datos |
| Acciones | Editar (✏️) o Eliminar (🗑️) |

### Estados de Conexión

- **🟢 Conectado (online):** El dispositivo ha enviado datos en los últimos 30 segundos
- **🔴 Desconectado (offline):** No ha enviado datos en más de 30 segundos
- **⚫ Desconocido (unknown):** Estado inicial, sin información

### Indicador de Batería

- **Verde (≥70%):** Batería buena
- **Naranja (40-69%):** Batería media, planifica recarga pronto
- **Rojo (<40%):** Batería baja, requiere atención urgente

---

## ✏️ Editar un Dispositivo

1. En la tabla de dispositivos, haz clic en el botón **✏️ (Editar)**
2. Modifica:
   - Nombre del dispositivo
   - Ubicación
   - Otros campos según sea necesario
3. Guarda los cambios

---

## 🗑️ Eliminar un Dispositivo

1. En la tabla de dispositivos, haz clic en el botón **🗑️ (Eliminar)**
2. Confirma la eliminación
3. El dispositivo se desactivará (no se eliminará completamente, solo se marcará como inactivo)

---

## 🔧 Configuración del Microcontrolador

### Qué información necesita el Arduino

El microcontrolador debe enviar:

```json
{
  "arduino_id": "esp8266_01",           // Identificador único
  "timestamp": 1234567890000,            // Timestamp Unix en ms
  "mediciones": {
    "ph": 7.2,                           // Valor pH
    "temperatura": 22.5,                 // Temperatura en °C
    "conductividad": 850                 // Conductividad en µS/cm
  },
  "bateria": 85                          // Porcentaje de batería
}
```

### Endpoint API

```
POST /api/sensors
```

Envía los datos en este formato para que se registren automáticamente.

---

## 📱 Identificación de Arduino

### ¿Qué es `arduino_id`?

Es un identificador único para cada microcontrolador. Puede ser:

- **Generado automáticamente:** `esp8266_01`, `arduino_02`, etc.
- **Basado en MAC:** `aa:bb:cc:dd:ee:ff`
- **Personalizado:** Cualquier string único que definas en el código del Arduino

### Buenas prácticas:

```c
// En tu código Arduino/ESP8266:
const char* DEVICE_ID = "embalse_norte_sensor_01";  // ✅ Claro y único
// NO uses: "device" o "sensor" (muy genéricos)
// NO uses: Espacios o caracteres especiales
```

---

## 🚨 Alertas y Monitoreo

### Cambios de Estado

Cuando un dispositivo:
- **Se conecta por primera vez:** Se registra automáticamente si se ejecuta la detección
- **Se desconecta:** El estado cambia a "offline" después de 30 segundos sin datos
- **Vuelve a conectarse:** El estado vuelve a "online" inmediatamente

### Batería

- Se actualiza automáticamente con cada lectura de sensores
- Los dispositivos con batería baja (<40%) aparecen destacados
- Puedes ver el historial en el endpoint `/api/devices`

---

## 🔗 Endpoints API

### GET `/api/devices`
Obtiene lista de dispositivos. Parámetros:
- `active_only` (bool, default: true): Solo dispositivos activos

```bash
curl http://localhost:8000/api/devices
curl http://localhost:8000/api/devices?active_only=false
```

### POST `/api/devices`
Crea un nuevo dispositivo manualmente

```bash
curl -X POST http://localhost:8000/api/devices \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sensor Embalse",
    "device_type": "ESP8266",
    "location": "Profundidad 5m",
    "arduino_id": "esp8266_01"
  }'
```

### POST `/api/devices/detect`
Detecta y registra un nuevo microcontrolador

```bash
curl -X POST http://localhost:8000/api/devices/detect \
  -H "Content-Type: application/json" \
  -d '{
    "arduino_id": "esp8266_01",
    "device_name": "Sensor Nuevo",
    "device_type": "ESP8266",
    "location": "Zona A"
  }'
```

### GET `/api/devices/detect-available`
Obtiene microcontroladores disponibles para registrar

```bash
curl http://localhost:8000/api/devices/detect-available
```

### PUT `/api/devices/{device_id}`
Actualiza un dispositivo

```bash
curl -X PUT http://localhost:8000/api/devices/uuid-123 \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Nuevo Nombre",
    "location": "Nueva Ubicación"
  }'
```

### DELETE `/api/devices/{device_id}`
Elimina (desactiva) un dispositivo

```bash
curl -X DELETE http://localhost:8000/api/devices/uuid-123
```

---

## 📊 Ejemplo de Flujo Completo

### Escenario: Agregar un nuevo ESP8266

```
1. Enciendes el ESP8266 (ya tiene código que envía datos)
   ↓
2. El ESP8266 se conecta a WiFi y comienza a enviar datos al API
   ↓
3. Accedes al panel /devices
   ↓
4. Haces clic en "🔍 Detectar Nuevos"
   ↓
5. El sistema escanea y encuentra: esp8266_embalse_01
   ↓
6. Haces clic en "✓ Registrar"
   ↓
7. Aparece en la tabla como "Dispositivo esp8266_embalse_01" (⚫ estado desconocido)
   ↓
8. Esperas ~30 segundos y el estado cambia a "🟢 Conectado"
   ↓
9. (Opcional) Editas el nombre a "Sensor Embalse Norte"
   ↓
✅ ¡Dispositivo listo!
```

---

## 🆘 Solución de Problemas

### El dispositivo no aparece en detección

**Causas posibles:**
- El Arduino no está enviando datos
- El endpoint `/api/sensors` no está recibiendo la información
- El `arduino_id` es inválido

**Solución:**
1. Verifica logs del Arduino
2. Prueba enviando datos manualmente:
   ```bash
   curl -X POST http://localhost:8000/api/sensors \
     -H "Content-Type: application/json" \
     -d '{"arduino_id": "test_01", "timestamp": 1234567890000, "mediciones": {"ph": 7.0, "temperatura": 20.0, "conductividad": 800}, "bateria": 90}'
   ```
3. Intenta agregar manualmente con el Arduino ID

### El estado siempre es "Desconocido"

**Causa:** El dispositivo nunca ha enviado datos después de registrarse

**Solución:**
- Espera a que envíe la primera lectura
- Verifica que esté conectado y enviando datos

### No puedo eliminar un dispositivo

**Verificar:**
- Tienes permisos de administrador
- El dispositivo existe en la base de datos

---

## 📚 Información Técnica

### Base de Datos (MongoDB)

Los dispositivos se almacenan en la colección `devices`:

```json
{
  "_id": "uuid-123",
  "name": "Sensor Embalse",
  "device_type": "ESP8266",
  "location": "Profundidad 5m",
  "arduino_id": "esp8266_01",
  "status": "online",
  "battery": 95,
  "last_sync": "2026-05-26T12:34:56Z",
  "created_at": "2026-05-26T10:00:00Z",
  "updated_at": "2026-05-26T12:34:56Z",
  "active": true
}
```

### Actualizaciones Automáticas

- **Status:** Se actualiza cuando se reciben datos (online/offline después de 30s)
- **Battery:** Se actualiza con cada lectura de sensores
- **last_sync:** Se actualiza con cada lectura
- **updated_at:** Se actualiza en cualquier cambio

---

## ✅ Checklist de Implementación

- ✅ Backend: Modelos Device en `models.py`
- ✅ Backend: Funciones MongoDB en `services/mongodb.py`
- ✅ Backend: Endpoints en `routers/devices.py`
- ✅ Frontend: Store `deviceStore.js`
- ✅ Frontend: Composable `useDeviceManagement.js`
- ✅ Frontend: Componente `AddDeviceModal.vue`
- ✅ Frontend: Componente `DeviceDetectionModal.vue`
- ✅ Frontend: Vista `DeviceManagement.vue`
- ✅ Frontend: Integración en `AdminDashboard.vue`
- ✅ Frontend: Rutas en `router.js`

---

**¿Necesitas ayuda?** Consulta la documentación técnica en `docs/DEVICE_MANAGEMENT_TECHNICAL.md`
