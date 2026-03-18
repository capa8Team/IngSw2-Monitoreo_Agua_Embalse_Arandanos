<template>
  <div class="devices-view">
    <header class="devices-header">
      <div class="header-content">
        <h1 class="header-title">Dispositivos Conectados</h1>
        <p class="header-subtitle">Selecciona un Arduino para ver las mediciones en tiempo real</p>
      </div>
      
      <div class="view-controls">
        <button 
          class="view-btn grid-view"
          :class="{ active: viewMode === 'grid' }"
          @click="viewMode = 'grid'"
          title="Vista de cuadrícula"
        >
          <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
            <path d="M3 3h8v8H3V3zm10 0h8v8h-8V3zM3 13h8v8H3v-8zm10 0h8v8h-8v-8z"/>
          </svg>
        </button>
        
        <button 
          class="view-btn list-view"
          :class="{ active: viewMode === 'list' }"
          @click="viewMode = 'list'"
          title="Vista de lista"
        >
          <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
            <path d="M3 4h18v2H3V4zm0 7h18v2H3v-2zm0 7h18v2H3v-2z"/>
          </svg>
        </button>
      </div>
    </header>

    <main class="devices-container">
      <div class="devices-grid" :class="`view-${viewMode}`">
        <DeviceCard
          v-for="device in devices"
          :key="device.id"
          :device="device"
          :is-selected="selectedDeviceId === device.id"
          @select="selectDevice(device)"
        />
      </div>

      <div v-if="devices.length === 0" class="empty-state">
        <div class="empty-icon">
          <svg viewBox="0 0 24 24" width="64" height="64" fill="currentColor">
            <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V5h14v14zm-5-4h-2v2h2v-2zm0-4h-2v2h2V7z"/>
          </svg>
        </div>
        <p class="empty-text">No hay dispositivos conectados</p>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import DeviceCard from './DeviceCard.vue'

const viewMode = ref('grid')
const selectedDeviceId = ref(null)

// Datos de ejemplo de dispositivos
const devices = ref([
  {
    id: 1,
    name: 'Arduino Embalse A',
    model: 'Arduino Uno - Zona Norte',
    status: 'connected',
    lastUpdate: 'hace 2 segundos',
    sensors: [
      { id: 'ph', name: 'pH', value: 7.2, unit: 'pH' },
      { id: 'temp', name: 'Temperatura', value: 22.5, unit: '°C' },
      { id: 'cond', name: 'Conductividad', value: 650, unit: 'µS/cm' }
    ]
  },
  {
    id: 2,
    name: 'Arduino Embalse B',
    model: 'Arduino Uno - Zona Sur',
    status: 'connected',
    lastUpdate: 'hace 1 segundo',
    sensors: [
      { id: 'ph', name: 'pH', value: 7.1, unit: 'pH' },
      { id: 'temp', name: 'Temperatura', value: 21.8, unit: '°C' },
      { id: 'cond', name: 'Conductividad', value: 620, unit: 'µS/cm' }
    ]
  },
  {
    id: 3,
    name: 'Arduino Embalse C',
    model: 'Arduino Uno - Zona Este',
    status: 'connected',
    lastUpdate: 'hace 3 segundos',
    sensors: [
      { id: 'ph', name: 'pH', value: 7.4, unit: 'pH' },
      { id: 'temp', name: 'Temperatura', value: 23.2, unit: '°C' },
      { id: 'cond', name: 'Conductividad', value: 680, unit: 'µS/cm' }
    ]
  },
  {
    id: 4,
    name: 'Arduino Embalse D',
    model: 'Arduino Uno - Zona Oeste',
    status: 'disconnected',
    lastUpdate: 'hace 5 minutos',
    sensors: [
      { id: 'ph', name: 'pH', value: 0, unit: 'pH' },
      { id: 'temp', name: 'Temperatura', value: 0, unit: '°C' },
      { id: 'cond', name: 'Conductividad', value: 0, unit: 'µS/cm' }
    ]
  }
])

const selectDevice = (device) => {
  selectedDeviceId.value = device.id
  // Emitir evento al componente padre para cambiar a la vista del dashboard
  emit('select-device', device)
}

const emit = defineEmits(['select-device'])
</script>

<style scoped>
.devices-view {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%);
  display: flex;
  flex-direction: column;
}

.devices-header {
  background: #ffffff;
  border-bottom: 1px solid #e8e8e8;
  padding: 32px 40px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 32px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04);
}

.header-content h1 {
  margin: 0;
  font-size: 28px;
  font-weight: 700;
  color: #222;
  letter-spacing: -0.5px;
}

.header-subtitle {
  margin: 8px 0 0 0;
  color: #888;
  font-size: 14px;
  font-weight: 400;
}

.view-controls {
  display: flex;
  gap: 8px;
  background: #f8f9fa;
  padding: 8px;
  border-radius: 8px;
  flex-shrink: 0;
}

.view-btn {
  width: 40px;
  height: 40px;
  border: 1px solid transparent;
  background: transparent;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #888;
  transition: all 0.2s ease;
}

.view-btn:hover {
  color: #333;
  background: #ffffff;
}

.view-btn.active {
  background: #ffffff;
  color: #66bb6a;
  border-color: #66bb6a;
}

.devices-container {
  flex: 1;
  padding: 40px;
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
}

.devices-grid {
  display: grid;
  gap: 24px;
}

.devices-grid.view-grid {
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
}

.devices-grid.view-list {
  grid-template-columns: 1fr;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 40px;
  text-align: center;
  color: #888;
}

.empty-icon {
  width: 100px;
  height: 100px;
  background: #f0f2f5;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 24px;
  color: #bbb;
}

.empty-text {
  font-size: 16px;
  margin: 0;
}

@media (max-width: 1024px) {
  .devices-header {
    flex-wrap: wrap;
  }

  .devices-grid.view-grid {
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  }
}

@media (max-width: 768px) {
  .devices-header {
    padding: 20px 16px;
    gap: 12px;
    flex-direction: column;
    align-items: stretch;
  }

  .header-content {
    text-align: center;
  }

  .header-content h1 {
    font-size: 22px;
  }

  .header-subtitle {
    font-size: 13px;
  }

  .view-controls {
    width: 100%;
    justify-content: center;
  }

  .devices-container {
    padding: 16px;
  }

  .devices-grid {
    gap: 16px;
  }

  .devices-grid.view-grid {
    grid-template-columns: 1fr;
  }

  .devices-grid.view-list {
    grid-template-columns: 1fr;
  }

  .empty-state {
    padding: 60px 20px;
  }

  .empty-icon {
    width: 80px;
    height: 80px;
  }
}

@media (max-width: 480px) {
  .devices-header {
    padding: 16px 12px;
  }

  .header-content h1 {
    font-size: 18px;
  }

  .header-subtitle {
    font-size: 12px;
  }

  .view-btn {
    width: 36px;
    height: 36px;
  }

  .devices-container {
    padding: 12px;
  }

  .devices-grid {
    gap: 12px;
  }

  .empty-state {
    padding: 40px 16px;
  }
}
</style>
