from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field

# ============================================================================
# DASHBOARD Y METADATA
# ============================================================================
class SensorData(BaseModel):
    value: float
    min: float
    max: float
    safeMax: float
    lastUpdated: datetime
    status: Literal["stable", "warning", "critical"]

class Metadata(BaseModel):
    systemStatus: Literal["operational", "degraded", "down"]
    arduinoConnected: bool
    lastSync: datetime
    uptime: int = Field(..., ge=0, description="Tiempo de actividad en segundos")
    activeSensors: int = Field(..., ge=0)

class DashboardResponse(BaseModel):
    ph: SensorData
    temperature: SensorData
    conductivity: SensorData
    metadata: Metadata
    battery: int = Field(default=100, ge=0, le=100, description="Batería del dispositivo (%)")

# ============================================================================
# SENSORES (LECTURA Y ESCRITURA MONGODB)
# ============================================================================
class SensorMeasurements(BaseModel):
    ph: float
    temperatura: float
    conductividad: float

class SensorMongoPayload(BaseModel):
    arduino_id: str
    timestamp: int | None = None
    mediciones: SensorMeasurements
    bateria: int = Field(..., ge=0, le=100)

class SensorDataResponse(BaseModel):
    ph: float
    temperature: float
    conductivity: float
    timestamp: datetime
    id: Optional[str] = None

# ============================================================================
# PAYLOADS DE HARDWARE (ESP8266)
# ============================================================================
class SensorReading(BaseModel):
    ph: float
    temperature: float
    conductivity: float
    timestamp: int

class SensorPhPostReading(BaseModel):
    sensor_id: str
    id_env: int
    ph: float
    timestamp: int | None = None
    temperature: float | None = None
    conductivity: float | None = None
    bateria: int = Field(default=100, ge=0, le=100)

class SensorNestedReadings(BaseModel):
    temperature: float | None = None
    humidity: float | None = None
    ph: float | None = None
    conductivity: float | None = None
    timestamp: int | None = None

class SensorReadingNestedPayload(BaseModel):
    readings: SensorNestedReadings

# ============================================================================
# ALERTAS
# ============================================================================
class AlertRecord(BaseModel):
    id: int
    fecha: str
    hora: str
    embalse: str
    sensor: str
    medicion: str

class AlertCreate(BaseModel):
    embalse: str
    sensor: str
    medicion: str
    nombreDispositivo: str | None = None
    valor: float | None = None
    minimo: float | None = None
    maximo: float | None = None

# ============================================================================
# DISPOSITIVOS (MICROCONTROLADORES / ARDUINOS)
# ============================================================================
class Device(BaseModel):
    id: str
    name: str = Field(..., min_length=1, max_length=100)
    device_type: Literal["ESP8266", "Arduino", "STM32", "other"] = "ESP8266"
    location: str = Field(default="", max_length=200)
    status: Literal["online", "offline", "unknown"] = "unknown"
    arduino_id: str | None = None
    battery: int = Field(default=100, ge=0, le=100)
    last_sync: datetime | None = None
    created_at: datetime
    updated_at: datetime
    active: bool = True

class DeviceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Nombre del dispositivo")
    device_type: Literal["ESP8266", "Arduino", "STM32", "other"] = Field(default="ESP8266", description="Tipo de microcontrolador")
    location: str = Field(default="", max_length=200, description="Ubicación o zona del dispositivo")
    arduino_id: str | None = Field(default=None, description="ID del Arduino (auto-detectado)")

class DeviceUpdate(BaseModel):
    name: str | None = Field(None, max_length=100)
    location: str | None = Field(None, max_length=200)
    active: bool | None = None

class DeviceResponse(BaseModel):
    id: str
    name: str
    device_type: str
    location: str
    status: str
    battery: int
    last_sync: datetime | None
    created_at: datetime
    updated_at: datetime
    active: bool
    arduino_id: str | None = None

class DeviceDetectionPayload(BaseModel):
    arduino_id: str
    device_name: str | None = None
    device_type: str = "ESP8266"
    location: str | None = None