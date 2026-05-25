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