<template>
  <div class="chart-wrapper">
    <div class="chart-title">
      <h3>{{ title }}</h3>
      <div class="period-buttons">
        <button class="period-btn" :class="{ active: period === 'hour' }" @click="$emit('update:period', 'hour')">1 hora</button>
        <button class="period-btn" :class="{ active: period === 'day' }" @click="$emit('update:period', 'day')">1 día</button>
        <button class="period-btn" :class="{ active: period === 'week' }" @click="$emit('update:period', 'week')">1 semana</button>
      </div>
    </div>
    <div class="chart-container" :class="{ 'chart-container--loading': loading }">
      <div v-if="loading" class="chart-loading-overlay" role="status" aria-live="polite" aria-busy="true">
        <div class="chart-loading-spinner" aria-hidden="true"></div>
        <span class="chart-loading-text">Cargando gráfico…</span>
      </div>
      <canvas ref="canvasRef"></canvas>
    </div>
    <div class="measurements">
      <span>Máx: {{ stats.max.toFixed(2) }}</span>
      <span>Mín: {{ stats.min.toFixed(2) }}</span>
      <span>Prom: {{ stats.avg.toFixed(2) }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import Chart from 'chart.js/auto'
import { SENSOR_META } from '../../utils/sensorUtils.js'

const props = defineProps({
  sensorKey: { type: String, required: true },
  period:    { type: String, required: true },
  chartData: { type: Object, required: true },
  stats:     { type: Object, required: true },
  loading:   { type: Boolean, default: false },
})

defineEmits(['update:period'])

const canvasRef = ref(null)
let chartInstance = null

const meta  = computed(() => SENSOR_META[props.sensorKey])
const title = computed(() => `${meta.value.label}${meta.value.unit ? ` (${meta.value.unit})` : ''}`)

function getTheme() {
  const dark = document.documentElement.getAttribute('data-theme') === 'dark'
  return dark
    ? { tick: '#94a3b8', grid: 'rgba(148,163,184,0.14)', axisTitle: '#86efac' }
    : { tick: '#666',    grid: 'rgba(0,0,0,0.04)',       axisTitle: '#66bb6a' }
}

function buildChart() {
  if (!canvasRef.value) return
  chartInstance?.destroy()
  const theme = getTheme()
  chartInstance = new Chart(canvasRef.value.getContext('2d'), {
    type: 'line',
    data: {
      labels: props.chartData.labels,
      datasets: [{
        label: meta.value.label,
        data:  props.chartData.values,
        borderColor: '#66bb6a',
        backgroundColor: 'rgba(102,187,106,0.08)',
        borderWidth: 2.5,
        fill: true,
        tension: 0.3,
        spanGaps: false,
        pointBackgroundColor: '#66bb6a',
        pointBorderColor:     '#fff',
        pointBorderWidth: 2,
        pointRadius:      props.chartData.values.length <= 12 ? 5 : 3,
        pointHoverRadius: props.chartData.values.length <= 12 ? 7 : 5,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: { duration: 0 },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: 'rgba(0,0,0,0.75)',
          padding: 8,
          titleFont: { size: 11 },
          bodyFont:  { size: 11 },
        },
      },
      scales: {
        y: {
          min: meta.value.min,
          max: meta.value.max,
          beginAtZero: false,
          ticks: { color: theme.tick, font: { size: 10 } },
          grid:  { color: theme.grid },
          title: { display: true, text: meta.value.label, font: { size: 11, weight: 'bold' }, color: theme.axisTitle },
        },
        x: {
          ticks: {
            color: theme.tick,
            font: { size: 10 },
            maxRotation: 45,
            minRotation: 0,
            autoSkip: true,
            maxTicksLimit: props.chartData.labels.length > 12 ? 12 : undefined,
          },
          grid: { display: false },
        },
      },
    },
  })
}

function syncChartData() {
  if (!chartInstance) { buildChart(); return }
  const n = props.chartData.values.length
  chartInstance.data.labels = props.chartData.labels
  chartInstance.data.datasets[0].data = props.chartData.values
  chartInstance.data.datasets[0].pointRadius = n <= 12 ? 5 : 3
  chartInstance.data.datasets[0].pointHoverRadius = n <= 12 ? 7 : 5
  chartInstance.update('none')
}

function refreshTheme() {
  if (!chartInstance) return
  const theme = getTheme()
  const sc = chartInstance.options.scales
  sc.y.ticks.color = theme.tick
  sc.y.grid.color  = theme.grid
  sc.y.title.color = theme.axisTitle
  sc.x.ticks.color = theme.tick
  chartInstance.update('none')
}

watch(() => props.chartData, syncChartData, { deep: true })

onMounted(() => {
  buildChart()
  window.addEventListener('embalse-theme-change', refreshTheme)
})

onBeforeUnmount(() => {
  window.removeEventListener('embalse-theme-change', refreshTheme)
  chartInstance?.destroy()
})
</script>

<style scoped>
.chart-wrapper {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 10px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
  border: 1px solid #e8ecf1;
  display: flex;
  flex-direction: column;
  gap: 6px;
  height: fit-content;
  width: 100%;
}

.chart-container--loading canvas {
  opacity: 0.25;
}

.chart-loading-overlay {
  position: absolute;
  inset: 0;
  z-index: 2;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  background: rgba(255, 255, 255, 0.82);
  border-radius: 6px;
}

.chart-loading-spinner {
  width: 36px;
  height: 36px;
  border: 3px solid #e8f5e9;
  border-top-color: #66bb6a;
  border-radius: 50%;
  animation: chart-loading-spin 0.85s linear infinite;
}

.chart-loading-text {
  font-size: 13px;
  font-weight: 600;
  color: #2e7d32;
}

@keyframes chart-loading-spin {
  to {
    transform: rotate(360deg);
  }
}

.chart-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
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
  padding: 6px 8px;
  min-height: 36px;
  white-space: nowrap;
  background: #f0f0f0;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  color: #666;
  transition: all 0.2s;
  box-sizing: border-box;
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
  height: 210px;
  width: 100%;
  flex-shrink: 0;
}

.chart-container canvas {
  display: block;
  width: 100%;
  height: 100%;
}

.measurements {
  display: flex;
  justify-content: space-around;
  font-size: 12px;
  color: #666;
  padding-top: 6px;
  border-top: 1px solid #e8ecf1;
}

.measurements span {
  font-weight: 500;
}

@media (max-width: 768px) {
  .chart-title {
    align-items: flex-start;
    flex-direction: column;
  }

  .chart-title h3 {
    font-size: 13px;
  }

  .period-buttons {
    width: 100%;
  }

  .period-btn {
    flex: 1;
    text-align: center;
  }

  .chart-container {
    height: 185px;
  }

  .measurements {
    flex-wrap: wrap;
    gap: 6px 10px;
    justify-content: space-between;
  }
}

@media (max-width: 480px) {
  .chart-wrapper {
    padding: 8px;
  }

  .chart-container {
    height: 170px;
  }
}
</style>

<style>
html[data-theme='dark'] .chart-wrapper {
  background: #2e3240;
  border-color: #3d4254;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25);
}

html[data-theme='dark'] .chart-title h3 {
  color: #f1f5f9;
}

html[data-theme='dark'] .chart-loading-overlay {
  background: rgba(38, 42, 54, 0.88);
}

html[data-theme='dark'] .chart-loading-text {
  color: #bbf7d0;
}

html[data-theme='dark'] .chart-loading-spinner {
  border-color: #3d4254;
  border-top-color: #4ade80;
}

html[data-theme='dark'] .measurements {
  color: #94a3b8;
  border-top-color: #3d4254;
}
</style>
