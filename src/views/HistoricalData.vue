<template>
  <div class="historical-view">
    <div class="history-header">
      <div class="header-left">
        <button class="back-btn" @click="goBack">← Volver</button>
        <h1>Datos Históricos</h1>
      </div>
      <button class="pdf-btn" @click="downloadPDF">📥 Descargar PDF</button>
    </div>

    <main class="history-content">
      <!-- pH Chart -->
      <div class="chart-wrapper">
        <div class="chart-title">
          <h3>pH</h3>
          <div class="period-buttons">
            <button 
              @click="phPeriod = 'day'" 
              :class="{ active: phPeriod === 'day' }"
              class="period-btn"
            >
              1 día
            </button>
            <button 
              @click="phPeriod = 'week'" 
              :class="{ active: phPeriod === 'week' }"
              class="period-btn"
            >
              1 semana
            </button>
          </div>
        </div>
        <div class="chart-container">
          <canvas ref="phChartRef"></canvas>
        </div>
        <div class="measurements">
          <span>Máx: {{ chartStats.ph.max.toFixed(2) }}</span>
          <span>Mín: {{ chartStats.ph.min.toFixed(2) }}</span>
          <span>Prom: {{ chartStats.ph.avg.toFixed(2) }}</span>
        </div>
      </div>

      <!-- Temperature Chart -->
      <div class="chart-wrapper">
        <div class="chart-title">
          <h3>Temperatura (°C)</h3>
          <div class="period-buttons">
            <button 
              @click="tempPeriod = 'day'" 
              :class="{ active: tempPeriod === 'day' }"
              class="period-btn"
            >
              1 día
            </button>
            <button 
              @click="tempPeriod = 'week'" 
              :class="{ active: tempPeriod === 'week' }"
              class="period-btn"
            >
              1 semana
            </button>
          </div>
        </div>
        <div class="chart-container">
          <canvas ref="tempChartRef"></canvas>
        </div>
        <div class="measurements">
          <span>Máx: {{ chartStats.temperature.max.toFixed(2) }}</span>
          <span>Mín: {{ chartStats.temperature.min.toFixed(2) }}</span>
          <span>Prom: {{ chartStats.temperature.avg.toFixed(2) }}</span>
        </div>
      </div>

      <!-- Conductivity Chart -->
      <div class="chart-wrapper">
        <div class="chart-title">
          <h3>Conductividad (µS/cm)</h3>
          <div class="period-buttons">
            <button 
              @click="condPeriod = 'day'" 
              :class="{ active: condPeriod === 'day' }"
              class="period-btn"
            >
              1 día
            </button>
            <button 
              @click="condPeriod = 'week'" 
              :class="{ active: condPeriod === 'week' }"
              class="period-btn"
            >
              1 semana
            </button>
          </div>
        </div>
        <div class="chart-container">
          <canvas ref="condChartRef"></canvas>
        </div>
        <div class="measurements">
          <span>Máx: {{ chartStats.conductivity.max.toFixed(2) }}</span>
          <span>Mín: {{ chartStats.conductivity.min.toFixed(2) }}</span>
          <span>Prom: {{ chartStats.conductivity.avg.toFixed(2) }}</span>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, reactive, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/authStore'
import Chart from 'chart.js/auto'

const router = useRouter()
const authStore = useAuthStore()

const phPeriod = ref('day')
const tempPeriod = ref('day')
const condPeriod = ref('day')

const phChartRef = ref(null)
const tempChartRef = ref(null)
const condChartRef = ref(null)

let phChart = null
let tempChart = null
let condChart = null

const chartStats = reactive({
  ph: { max: 8.5, min: 6.0, avg: 7.2 },
  temperature: { max: 28, min: 18, avg: 22.5 },
  conductivity: { max: 1500, min: 800, avg: 1100 },
})

const generateMockData = async (type, period) => {
  try {
    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
    console.log(`[DEBUG] Fetching from ${apiUrl}/api/dashboard for type: ${type}`)
    const response = await fetch(`${apiUrl}/api/dashboard`)
    const data = await response.json()
    console.log(`[DEBUG] API response:`, data)
    
    const now = new Date()
    const dataPoints = period === 'day' ? 24 : 7
    const labels = []
    const values = []
    
    let baseValue = 0, maxVal = 0, minVal = 0

    // Extraer el valor base del sensor correspondiente
    if (type === 'ph') {
      baseValue = data.ph?.value || 7.2
      maxVal = data.ph?.max || 8.5
      minVal = data.ph?.min || 6.0
    } else if (type === 'temperature') {
      baseValue = data.temperature?.value || 22.5
      maxVal = data.temperature?.max || 28
      minVal = data.temperature?.min || 18
    } else if (type === 'conductivity') {
      baseValue = data.conductivity?.value || 1100
      maxVal = data.conductivity?.max || 1500
      minVal = data.conductivity?.min || 800
    }

    // Generar datos históricos simulados basados en el valor actual
    for (let i = 0; i < dataPoints; i++) {
      const date = new Date(now)
      if (period === 'day') {
        date.setHours(i, 0, 0, 0)
        labels.push(`${String(i).padStart(2, '0')}:00`)
      } else {
        date.setDate(date.getDate() - (6 - i))
        labels.push(date.toLocaleDateString('es-ES', { weekday: 'short' }))
      }
      
      // Agregar pequeña variación al valor real (±5% del rango)
      const variance = (maxVal - minVal) * 0.05
      const value = baseValue + (Math.random() - 0.5) * variance
      values.push(Math.max(minVal, Math.min(maxVal, value)))
    }

    const avg = values.reduce((a, b) => a + b, 0) / values.length
    const max = Math.max(...values)
    const min = Math.min(...values)
    
    console.log(`[DEBUG] Generated data for ${type}:`, { labels: labels.length, values: values.length, avg, max, min })

    return { labels, data: values, avg, max, min }
  } catch (error) {
    console.error('Error fetching data:', error)
    // Fallback a datos locales si hay error
    const dataPoints = period === 'day' ? 24 : 7
    const labels = []
    const data = []
    
    let baseValue = 0, maxVal = 0, minVal = 0
    
    if (type === 'ph') {
      baseValue = 7.2; maxVal = 8.5; minVal = 6.0
    } else if (type === 'temperature') {
      baseValue = 22.5; maxVal = 28; minVal = 18
    } else if (type === 'conductivity') {
      baseValue = 1100; maxVal = 1500; minVal = 800
    }

    for (let i = 0; i < dataPoints; i++) {
      const now = new Date()
      if (period === 'day') {
        now.setHours(i, 0, 0, 0)
        labels.push(`${String(i).padStart(2, '0')}:00`)
      } else {
        now.setDate(now.getDate() - (6 - i))
        labels.push(now.toLocaleDateString('es-ES', { weekday: 'short' }))
      }
      
      const variance = (maxVal - minVal) * 0.05
      const value = baseValue + (Math.random() - 0.5) * variance
      data.push(Math.max(minVal, Math.min(maxVal, value)))
    }
    
    const avg = data.reduce((a, b) => a + b, 0) / data.length
    return { labels, data, avg, max: Math.max(...data), min: Math.min(...data) }
  }
}

const updateCharts = async () => {
  console.log('[DEBUG] updateCharts called')
  const phData = await generateMockData('ph', phPeriod.value)
  const tempData = await generateMockData('temperature', tempPeriod.value)
  const condData = await generateMockData('conductivity', condPeriod.value)

  chartStats.ph = { max: phData.max, min: phData.min, avg: phData.avg }
  chartStats.temperature = { max: tempData.max, min: tempData.min, avg: tempData.avg }
  chartStats.conductivity = { max: condData.max, min: condData.min, avg: condData.avg }

  if (phChart) {
    phChart.data.labels = phData.labels
    phChart.data.datasets[0].data = phData.data
    phChart.update('none')
    console.log('[DEBUG] pH chart updated')
  } else if (phChartRef.value) {
    createChart(phChartRef, phData, 'pH', 6, 8.5, phChart, 'phChart')
    console.log('[DEBUG] pH chart created')
  }

  if (tempChart) {
    tempChart.data.labels = tempData.labels
    tempChart.data.datasets[0].data = tempData.data
    tempChart.update('none')
    console.log('[DEBUG] Temperature chart updated')
  } else if (tempChartRef.value) {
    createChart(tempChartRef, tempData, 'Temperatura (°C)', 15, 30, tempChart, 'tempChart')
    console.log('[DEBUG] Temperature chart created')
  }

  if (condChart) {
    condChart.data.labels = condData.labels
    condChart.data.datasets[0].data = condData.data
    condChart.update('none')
    console.log('[DEBUG] Conductivity chart updated')
  } else if (condChartRef.value) {
    createChart(condChartRef, condData, 'Conductividad (µS/cm)', 700, 1600, condChart, 'condChart')
    console.log('[DEBUG] Conductivity chart created')
  }
}

const createChart = (chartRef, data, label, minVal, maxVal, chartInstance, varName) => {
  if (chartInstance) chartInstance.destroy()
  
  const ctx = chartRef.value.getContext('2d')
  const newChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: data.labels,
      datasets: [{
        label: label,
        data: data.data,
        borderColor: '#66bb6a',
        backgroundColor: 'rgba(102, 187, 106, 0.08)',
        borderWidth: 2.5,
        fill: true,
        tension: 0.3,
        pointBackgroundColor: '#66bb6a',
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        pointRadius: 3,
        pointHoverRadius: 5,
      }]
    },
    options: {
      responsive: false,
      maintainAspectRatio: false,
      animation: { duration: 0 },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: 'rgba(0, 0, 0, 0.75)',
          padding: 8,
          titleFont: { size: 11 },
          bodyFont: { size: 11 },
        }
      },
      scales: {
        y: { 
          min: minVal, 
          max: maxVal, 
          ticks: { color: '#666', font: { size: 10 } }, 
          grid: { color: 'rgba(0, 0, 0, 0.04)' },
          beginAtZero: false,
          title: { display: true, text: label, font: { size: 11, weight: 'bold' }, color: '#66bb6a' }
        },
        x: { 
          ticks: { color: '#666', font: { size: 10 } }, 
          grid: { display: false } 
        }
      }
    }
  })
  
  // Actualizar la referencia global
  if (varName === 'phChart') phChart = newChart
  else if (varName === 'tempChart') tempChart = newChart
  else if (varName === 'condChart') condChart = newChart
}

watch(phPeriod, async () => {
  await updateCharts()
})

watch(tempPeriod, async () => {
  await updateCharts()
})

watch(condPeriod, async () => {
  await updateCharts()
})

let updateInterval = null

onMounted(async () => {
  await nextTick()
  await updateCharts()
  // Actualizar datos cada 5 segundos
  updateInterval = setInterval(async () => {
    try {
      await updateCharts()
    } catch (error) {
      console.error('Error actualizando gráficos:', error)
    }
  }, 5000)
})

onBeforeUnmount(() => {
  if (updateInterval) clearInterval(updateInterval)
  if (phChart) phChart.destroy()
  if (tempChart) tempChart.destroy()
  if (condChart) condChart.destroy()
})

const goBack = () => {
  router.back()
}

const downloadPDF = () => {
  alert('Función de descarga PDF en desarrollo')
}
</script>

<style scoped>
.historical-view {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f5f7fa;
}

.history-header {
  background: white;
  color: #333;
  padding: 14px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 2px solid #66bb6a;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
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
  overflow-y: auto;
  padding: 20px;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 10px;
  max-width: 100%;
}

.chart-wrapper {
  background: white;
  border-radius: 8px;
  padding: 12px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.chart-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.chart-title h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.period-buttons {
  display: flex;
  gap: 6px;
}

.period-btn {
  padding: 4px 10px;
  background: #f0f0f0;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  color: #666;
  transition: all 0.2s;
}

.period-btn:hover {
  background: #e8e8e8;
}

.period-btn.active {
  background: #66bb6a;
  color: white;
  border-color: #66bb6a;
}

.chart-container {
  position: relative;
  height: 140px;
  width: 100%;
  flex-shrink: 0;
}

.chart-container canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

.measurements {
  display: flex;
  justify-content: space-around;
  font-size: 12px;
  color: #666;
  padding-top: 8px;
  border-top: 1px solid #e8ecf1;
}

.measurements span {
  font-weight: 500;
}
</style>
