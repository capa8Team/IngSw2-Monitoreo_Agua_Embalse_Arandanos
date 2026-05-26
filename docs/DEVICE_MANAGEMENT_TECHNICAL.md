# Documentación Técnica: Sistema de Gestión de Dispositivos

## 📐 Arquitectura

```
Frontend (Vue 3)
├── Views
│   ├── DeviceManagement.vue (principal)
│   └── AdminDashboard.vue (integración)
├── Components
│   ├── AddDeviceModal.vue (modal agregar)
│   └── DeviceDetectionModal.vue (modal detección)
├── Composables
│   └── useDeviceManagement.js (lógica reutilizable)
└── Stores
    └── deviceStore.js (estado con Pinia)
         ↓
Backend (FastAPI)
├── Models
│   ├── Device
│   ├── DeviceCreate
│   ├── DeviceUpdate
│   ├── DeviceResponse
│   └── DeviceDetectionPayload
├── Routers
│   └── routers/devices.py (7 endpoints)
└── Services
    └── services/mongodb.py (12 funciones MongoDB)
         ↓
Database (MongoDB)
└── Collections
    └── devices
    └── sensor_readings (relación)
```

---

## 🔌 Endpoints API

### 1. Listar Dispositivos
```
GET /api/devices?active_only=true
Response: Array<DeviceResponse>
```

### 2. Crear Dispositivo Manual
```
POST /api/devices
Body: DeviceCreate
Response: DeviceResponse (201)
```

### 3. Obtener Dispositivo
```
GET /api/devices/{device_id}
Response: DeviceResponse
```

### 4. Actualizar Dispositivo
```
PUT /api/devices/{device_id}
Body: DeviceUpdate
Response: DeviceResponse
```

### 5. Eliminar Dispositivo
```
DELETE /api/devices/{device_id}
Response: 204 No Content
```

### 6. Detectar y Registrar (Automático)
```
POST /api/devices/detect
Body: DeviceDetectionPayload
Response: DeviceResponse (201)
```

### 7. Obtener Disponibles
```
GET /api/devices/detect-available
Response: {
  available: string[],
  total: number,
  already_registered: string[],
  message: string
}
```

---

## 🗄️ Esquema MongoDB

### Colección: `devices`

```javascript
{
  "_id": ObjectId | String,           // ID único (UUID)
  "id": String,                       // Copia de _id para compatibilidad
  "name": String,                     // Nombre del dispositivo
  "device_type": "ESP8266|Arduino|STM32|other",
  "location": String,                 // Ubicación/zona
  "status": "online|offline|unknown",
  "arduino_id": String | null,        // ID del microcontrolador
  "battery": Number (0-100),          // % batería
  "last_sync": DateTime | null,       // Última sincronización
  "created_at": DateTime,
  "updated_at": DateTime,
  "active": Boolean                   // Soft delete
}
```

### Índices Recomendados

```javascript
db.devices.createIndex({ "arduino_id": 1 })
db.devices.createIndex({ "active": 1 })
db.devices.createIndex({ "created_at": -1 })
db.devices.createIndex({ "status": 1 })
```

---

## 🔄 Flujo de Detección Automática

### Paso 1: Recibir Datos del Sensor

```
Arduino/ESP8266
    ↓
POST /api/sensors (payload)
    ↓
Backend: save_sensor_payload_to_mongodb()
    ↓
MongoDB: sensor_readings
    └─ documento con: arduino_id, timestamp, mediciones, bateria
```

### Paso 2: Escanear Disponibles

```
Frontend: GET /api/devices/detect-available
    ↓
Backend: 
  1. db.sensor_readings.distinct("arduino_id") → [id1, id2, id3]
  2. db.devices.distinct("arduino_id") → [id1]
  3. available = [id2, id3] (no registrados)
    ↓
Return: { available: [id2, id3], total: 2 }
```

### Paso 3: Registrar Detectado

```
Frontend: POST /api/devices/detect
Body: { arduino_id: "id2", device_name: "Mi Sensor", ... }
    ↓
Backend:
  1. Verificar si ya existe (por arduino_id)
  2. Si no existe: create_device()
  3. Registrar en log
  4. Retornar Device
    ↓
MongoDB: devices
    └─ nuevo documento creado
```

---

## 📊 Funciones de Servicio MongoDB

### Gestión Básica

| Función | Parámetros | Retorna | Propósito |
|---------|-----------|---------|----------|
| `create_device()` | name, type, location, arduino_id | Device | Crea nuevo dispositivo |
| `get_device()` | device_id | Device \| None | Obtiene por ID |
| `get_all_devices()` | active_only | List[Device] | Obtiene todos |
| `update_device()` | device_id, updates | Device \| None | Actualiza info |
| `delete_device()` | device_id | bool | Desactiva dispositivo |

### Búsqueda

| Función | Parámetros | Retorna | Propósito |
|---------|-----------|---------|----------|
| `get_device_by_arduino_id()` | arduino_id | Device \| None | Busca por Arduino ID |

### Detección y Registro

| Función | Parámetros | Retorna | Propósito |
|---------|-----------|---------|----------|
| `register_new_microcontroller()` | arduino_id, name, type, location | Device \| None | Auto-registra descubierto |

### Estado

| Función | Parámetros | Retorna | Propósito |
|---------|-----------|---------|----------|
| `update_device_status()` | arduino_id, status, battery | Device \| None | Actualiza estado/batería |

---

## 🎨 Componentes Frontend

### `DeviceManagement.vue` (Vista Principal)

- **Props:** None
- **Emits:** None
- **Características:**
  - Tabla responsiva de dispositivos
  - Búsqueda y filtrado en tiempo real
  - Estadísticas (total, activos, inactivos)
  - Integración de modales
  - Indicadores visuales (batería, estado)

### `AddDeviceModal.vue` (Componente Modal)

- **Props:**
  - `show: Boolean` - Mostrar/ocultar
  - `title: String` - Título personalizable
  - `onSubmit: Function` - Callback de envío
  - `onClose: Function` - Callback de cierre

- **Emits:**
  - `update:show` - Para v-model
  - `submit` - Al enviar formulario
  - `close` - Al cerrar

- **Validación:**
  - Nombre requerido
  - Tipo de dispositivo por defecto ESP8266
  - Arduino ID opcional

### `DeviceDetectionModal.vue` (Componente Modal)

- **Props:**
  - `show: Boolean`
  - `availableMicrocontrollers: Array`
  - `isDetecting: Boolean`
  - `detectionMessage: String`
  - `onDetect: Function`
  - `onRegister: Function`
  - `onClose: Function`

- **Estados:**
  - Escaneando (spinner)
  - Dispositivos encontrados (lista con botones)
  - Sin dispositivos (mensaje con consejos)
  - Error (alerta)

---

## 🎯 Composable: `useDeviceManagement.js`

**Responsabilidades:**
- Gestión de estado local (formularios, modales)
- Comunicación con store Pinia
- Lógica de validación
- Helpers de formato (iconos, colores)
- Casos de uso (agregar, detectar, registrar, eliminar)

**Métodos Principales:**
```javascript
// Modales
openAddModal()
closeAddModal()
openDetectionModal()
closeDetectionModal()

// Operaciones
addNewDevice()
updateExistingDevice()
removeDevice()
scanForNewDevices()
registerDetectedDevice()

// Helpers
getDeviceStatusIcon(device)
getDeviceStatusText(device)
getDeviceTypeName(type)
```

---

## 🏪 Store Pinia: `deviceStore.js`

**State:**
```javascript
const devices = ref([])           // Array de dispositivos
const loading = ref(false)        // Estado de carga
const error = ref(null)           // Mensajes de error
const selectedDevice = ref(null)  // Dispositivo seleccionado
const availableMicrocontrollers = ref([])  // Para detección
```

**Computed:**
```javascript
activeDevices        // Devices con active: true
offlineDevices       // Devices con status: offline
deviceCount          // Cantidad total
activeDeviceCount    // Cantidad activos
```

**Actions:**
```javascript
fetchDevices()                    // GET /api/devices
createDevice(data)                // POST /api/devices
updateDevice(id, data)            // PUT /api/devices/{id}
deleteDevice(id)                  // DELETE /api/devices/{id}
detectMicrocontroller(data)       // POST /api/devices/detect
getAvailableMicrocontrollers()   // GET /api/devices/detect-available
selectDevice(device)
clearSelection()
reset()
```

---

## 🔐 Seguridad

### Autenticación
- Los endpoints requieren JWT válido
- Guard de Vue Router verifica rol `administrador`
- Guard global en `/devices` y `/admin`

### Autorización
- Solo administradores pueden:
  - Crear dispositivos
  - Actualizar dispositivos
  - Eliminar dispositivos
  - Detectar microcontroladores

### Validación
- Backend: Pydantic valida tipos y rangos
- Frontend: Validación en formularios
- MongoDB: Soft delete (no elimina, solo marca inactivo)

---

## 📈 Performance

### Optimizaciones Implementadas

1. **Lazy Loading de Rutas**
   ```javascript
   const DeviceManagement = () => import('./views/DeviceManagement.vue')
   ```

2. **Computed Properties** con caché automático
   ```javascript
   const activeDevices = computed(() => 
     devices.value.filter(d => d.active)
   )
   ```

3. **Índices MongoDB** para búsquedas rápidas
   ```javascript
   { "arduino_id": 1 }
   { "active": 1, "created_at": -1 }
   ```

4. **Paginación en API** (preparado)
   ```javascript
   GET /api/devices?active_only=true&limit=50&offset=0
   ```

---

## 🧪 Testing

### Endpoints a Probar

```bash
# Listar
curl http://localhost:8000/api/devices

# Crear
curl -X POST http://localhost:8000/api/devices \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Device", "device_type": "ESP8266"}'

# Detectar disponibles
curl http://localhost:8000/api/devices/detect-available

# Detectar y registrar
curl -X POST http://localhost:8000/api/devices/detect \
  -H "Content-Type: application/json" \
  -d '{"arduino_id": "test_01", "device_name": "Test"}'
```

### Casos de Prueba Frontend

1. **Agregar dispositivo manual**
   - Abre modal
   - Completa formulario
   - Envía
   - Verifica en tabla

2. **Detección automática**
   - Asegura que haya datos enviados
   - Ejecuta detección
   - Registra dispositivo encontrado
   - Verifica en tabla

3. **Edición**
   - Edita nombre y ubicación
   - Verifica cambios en tabla

4. **Eliminación**
   - Elimina dispositivo
   - Confirma eliminación
   - Verifica desaparición

---

## 🔧 Configuración Requerida

### Variables de Entorno
```bash
VITE_API_URL=http://localhost:8000
MONGODB_URL=mongodb://user:pass@localhost:27017/
MONGODB_DB=Arandanos
```

### Dependencias Backend
```
fastapi>=0.104.0
pymongo>=4.0.0
pydantic>=2.0.0
```

### Dependencias Frontend
```
vue>=3.3.0
pinia>=2.1.0
vue-router>=4.2.0
```

---

## 📝 Logs y Monitoreo

### Logs Creados (Backend)

```
[START] Aplicacion iniciando...
[MONGO] Conexión a MongoDB establecida
[API] Dispositivo creado: Sensor Embalse (ID: uuid-123)
[API] Microcontrolador detectado: esp8266_01
[API] Dispositivo eliminado: uuid-123
```

### Métricas Disponibles

```javascript
// En DeviceStore
store.deviceCount          // Total dispositivos
store.activeDeviceCount    // Conectados
store.offlineDevices       // Desconectados
```

---

## 🚀 Roadmap Futuro

### Corto Plazo
- [ ] Exportar dispositivos a CSV
- [ ] Importar dispositivos desde CSV
- [ ] Historial de cambios de estado
- [ ] Alertas cuando batería < 40%

### Mediano Plazo
- [ ] Asignar dispositivos a usuarios específicos
- [ ] Permisos granulares por dispositivo
- [ ] Webhook notifications
- [ ] Real-time updates con WebSocket

### Largo Plazo
- [ ] Machine Learning para predecir fallos
- [ ] API pública para integraciones
- [ ] Dashboard con gráficos por dispositivo
- [ ] Sistema de backup y recuperación

---

**Última actualización:** 26/05/2026
**Versión:** 1.0.0
**Estatus:** ✅ Production Ready
