<template>
  <div class="historical-view">
    <header class="history-header">
      <div class="header-left">
        <ThemeToggleButton />
        <button class="back-btn" @click="router.back()">←</button>
        <h1>Datos Históricos</h1>
        <span class="source-badge" :class="isSimulatedMode ? 'source-simulated' : 'source-real'">
          {{ isSimulatedMode ? '⚙️ Datos simulados' : '📡 Datos en vivo' }}
        </span>
      </div>
      <button v-if="isUserAdmin" class="pdf-btn" @click="openPdfModal">Descargar PDF</button>
    </header>

    <main class="history-content">
      <p v-if="initialLoading" class="history-loading-hint">Cargando datos históricos…</p>
      <SensorChart sensorKey="ph"           v-model:period="phPeriod"   :chartData="chartData.ph"           :stats="chartStats.ph"           />
      <SensorChart sensorKey="temperature"  v-model:period="tempPeriod" :chartData="chartData.temperature"  :stats="chartStats.temperature"  />
      <SensorChart sensorKey="conductivity" v-model:period="condPeriod" :chartData="chartData.conductivity" :stats="chartStats.conductivity" />
      <MeasurementsTable
        :rows="measurementRows"
        :total-rows="tableTotal"
        :current-page="tablePage"
        :loading="tableLoading"
        @page-change="onTablePageChange"
        @filters-change="onTableFiltersChange"
      />
    </main>

    <PdfExportModal
      v-if="showPdfModal"
      :measurementRows="exportRows"
      :deviceOptions="deviceOptions"
      @close="showPdfModal = false"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { isAdminRole } from '../services/sessionAuth.js'
import ThemeToggleButton from '../components/ThemeToggleButton.vue'
import SensorChart       from '../components/historical/SensorChart.vue'
import MeasurementsTable from '../components/historical/MeasurementsTable.vue'
import PdfExportModal    from '../components/historical/PdfExportModal.vue'
import { useHistoricalData } from '../composables/useHistoricalData.js'

const router      = useRouter()
const isUserAdmin = computed(() => isAdminRole(localStorage.getItem('userRole')))
const showPdfModal = ref(false)

const {
  measurementRows, exportRows, deviceOptions, tableTotal, tablePage, tableLoading, initialLoading,
  isSimulatedMode,
  phPeriod, tempPeriod, condPeriod,
  chartData, chartStats,
  refreshHistorical,
  onTablePageChange, onTableFiltersChange, prepareExportRows,
  startPolling, stopPolling,
} = useHistoricalData()

async function openPdfModal() {
  await prepareExportRows()
  showPdfModal.value = true
}

onMounted(async () => {
  await nextTick()
  await refreshHistorical({ full: true })
  startPolling()
})

onBeforeUnmount(stopPolling)
</script>

<style scoped>
.historical-view {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  min-height: 100dvh;
  height: 100vh;
  height: 100dvh;
  max-height: 100vh;
  max-height: 100dvh;
  background: #f5f7fa;
  min-width: 0;
}

.history-header {
  background: white;
  color: #333;
  padding: 14px 20px;
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  gap: 10px 12px;
  border-bottom: 2px solid #66bb6a;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  min-width: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.source-badge {
  font-size: 12px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 999px;
  white-space: nowrap;
}

.source-real {
  background: #e8f5e9;
  color: #2e7d32;
}

.source-simulated {
  background: #fff3e0;
  color: #e65100;
}

.back-btn {
  width: 36px;
  height: 36px;
  border: 1px solid #e0e0e0;
  background: white;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  color: #333;
  transition: all 0.2s;
}

.back-btn:hover {
  background: #f0f0f0;
  border-color: #66bb6a;
}

.history-header h1 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #333;
}

.history-loading-hint {
  margin: 0 0 12px;
  padding: 10px 14px;
  border-radius: 8px;
  background: #e8f5e9;
  color: #2e7d32;
  font-size: 14px;
  font-weight: 500;
}

.pdf-btn {
  padding: 8px 16px;
  background: #66bb6a;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
}

.pdf-btn:hover {
  background: #558a5a;
  transform: translateY(-1px);
}

.history-content {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 16px;
  display: grid;
  grid-template-columns: repeat(3, minmax(300px, 1fr));
  gap: 12px;
  align-items: start;
  justify-items: center;
  max-width: 100%;
  margin: 0 auto;
}

@media (max-width: 980px) {
  .history-content {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .historical-view {
    height: auto;
    min-height: 100vh;
    min-height: 100dvh;
    max-height: none;
  }

  .history-header {
    padding: 12px 14px;
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
  }

  .header-left {
    justify-content: flex-start;
  }

  .history-header h1 {
    font-size: 18px;
  }

  .pdf-btn {
    width: 100%;
  }

  .history-content {
    padding: 12px;
    gap: 10px;
  }
}

@media (max-width: 480px) {
  .history-header {
    padding: 10px 12px;
  }

  .history-header h1 {
    font-size: 16px;
    line-height: 1.25;
  }

  .back-btn {
    min-width: 40px;
    min-height: 40px;
  }

  .pdf-btn {
    min-height: 44px;
    font-size: 13px;
  }

  .history-content {
    padding: 10px;
    gap: 8px;
  }
}
</style>
