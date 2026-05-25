<template>
  <div class="pdf-modal-overlay" @click.self="$emit('close')">
    <div class="pdf-modal">
      <div class="pdf-modal-header">
        <h3>Descargar Reporte Alertas PDF</h3>
        <button class="modal-close-btn" @click="$emit('close')">✕</button>
      </div>

      <div class="pdf-modal-body">
        <div class="filter-grid">
          <label>
            <span>Dispositivo</span>
            <select v-model="pdfFilters.device">
              <option value="all">Todos</option>
              <option v-for="device in deviceOptions" :key="device" :value="device">{{ device }}</option>
            </select>
          </label>
          <label>
            <span>Sensor</span>
            <select v-model="pdfFilters.sensor">
              <option value="all">Todos los sensores</option>
              <option value="ph">pH</option>
              <option value="temperature">Temperatura</option>
              <option value="conductivity">Conductividad</option>
            </select>
          </label>
          <label>
            <span>Datos</span>
            <select v-model="pdfFilters.dataType">
              <option value="alerts">Alertas</option>
              <option value="normal">Normales</option>
              <option value="all">Todos</option>
            </select>
          </label>
          <label>
            <span>Filtro de fechas</span>
            <select v-model="pdfFilters.rangeType">
              <option value="day">Día específico</option>
              <option value="range">Rango de fechas</option>
            </select>
          </label>
          <label v-if="pdfFilters.rangeType === 'day'">
            <span>Día</span>
            <input v-model="pdfFilters.day" type="date" />
          </label>
          <label v-else>
            <span>Desde</span>
            <input v-model="pdfFilters.startDate" type="date" />
          </label>
          <label v-if="pdfFilters.rangeType === 'range'">
            <span>Hasta</span>
            <input v-model="pdfFilters.endDate" type="date" />
          </label>
        </div>

        <p class="pdf-preview-text">
          Registros a exportar ({{ selectedDataLabel }}): <strong>{{ selectedRows.length }}</strong>
        </p>
        <p class="pdf-preview-text">
          Registros de alerta (referencia): <strong>{{ alertRows.length }}</strong>
        </p>
        <p class="pdf-preview-text">
          Porcentaje de alertas sobre total filtrado: <strong>{{ alertPercentage.toFixed(2) }}%</strong>
        </p>
      </div>

      <div class="pdf-modal-actions">
        <button class="secondary-btn" @click="$emit('close')">Cancelar</button>
        <button class="primary-btn" :disabled="isGeneratingPdf" @click="downloadPDF">
          {{ isGeneratingPdf ? 'Generando...' : 'Generar PDF' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { jsPDF } from 'jspdf'
import Chart from 'chart.js/auto'
import { localDateKey, SENSOR_META, measurementText, downsampleRows } from '../../utils/sensorUtils.js'

const props = defineProps({
  measurementRows: { type: Array, required: true },
  deviceOptions:   { type: Array, required: true },
})

defineEmits(['close'])

const isGeneratingPdf = ref(false)

const pdfFilters = reactive({
  device:    'all',
  sensor:    'all',
  dataType:  'alerts',
  rangeType: 'day',
  day:       localDateKey(new Date()),
  startDate: localDateKey(new Date(Date.now() - 6 * 24 * 60 * 60 * 1000)),
  endDate:   localDateKey(new Date()),
})

const filteredRows = computed(() =>
  props.measurementRows.filter(row => {
    if (pdfFilters.device !== 'all' && row.device !== pdfFilters.device) return false
    if (pdfFilters.sensor !== 'all' && row.sensorKey !== pdfFilters.sensor) return false
    if (pdfFilters.rangeType === 'day') return row.dateKey === pdfFilters.day
    const start = pdfFilters.startDate || '0000-01-01'
    const end   = pdfFilters.endDate   || '9999-12-31'
    return row.dateKey >= start && row.dateKey <= end
  })
)

const alertRows   = computed(() => filteredRows.value.filter(r => r.alertStatus === 'Alerta'))
const normalRows  = computed(() => filteredRows.value.filter(r => r.alertStatus === 'Normal'))

const selectedRows = computed(() => {
  if (pdfFilters.dataType === 'alerts') return alertRows.value
  if (pdfFilters.dataType === 'normal') return normalRows.value
  return filteredRows.value
})

const selectedDataLabel = computed(() => {
  if (pdfFilters.dataType === 'alerts') return 'Alertas'
  if (pdfFilters.dataType === 'normal') return 'Normales'
  return 'Todos'
})

const alertPercentage = computed(() => {
  const total = filteredRows.value.length
  return total ? (alertRows.value.length / total) * 100 : 0
})

watch(() => pdfFilters.rangeType, newType => {
  if (newType === 'day') {
    pdfFilters.day = pdfFilters.day || localDateKey(new Date())
  } else {
    pdfFilters.startDate = pdfFilters.startDate || localDateKey(new Date(Date.now() - 6 * 24 * 60 * 60 * 1000))
    pdfFilters.endDate   = pdfFilters.endDate   || localDateKey(new Date())
  }
})

watch(() => props.deviceOptions, options => {
  if (pdfFilters.device !== 'all' && !options.includes(pdfFilters.device))
    pdfFilters.device = 'all'
})

// ─── PDF helpers ──────────────────────────────────────────────────

const PDF_COLUMNS = [
  { title: 'Dispositivo', width: 45 },
  { title: 'Sensor',      width: 24 },
  { title: 'Medición',    width: 30 },
  { title: 'Fecha',       width: 28 },
  { title: 'Hora',        width: 20 },
  { title: 'Alerta',      width: 35 },
]

function addTableHeader(doc, y) {
  const rowH  = 6
  const startX = 14
  const totalW = PDF_COLUMNS.reduce((s, c) => s + c.width, 0)
  doc.setDrawColor(170, 178, 186)
  doc.setLineWidth(0.2)
  doc.setFillColor(232, 242, 232)
  doc.rect(startX, y, totalW, rowH, 'FD')
  let x = startX
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(8)
  doc.setTextColor(38, 45, 52)
  PDF_COLUMNS.forEach(col => {
    doc.text(col.title, x + 1.5, y + 4)
    x += col.width
    if (x < startX + totalW) doc.line(x, y, x, y + rowH)
  })
  doc.setFont('helvetica', 'normal')
  return y + rowH
}

function drawTableRow(doc, y, values) {
  const rowH  = 6
  let x = 14
  doc.setDrawColor(170, 178, 186)
  doc.setLineWidth(0.15)
  PDF_COLUMNS.forEach((col, i) => {
    doc.rect(x, y, col.width, rowH, 'S')
    const text = String(values[i] ?? '').slice(0, Math.max(8, Math.floor(col.width * 1.2)))
    doc.setFontSize(8)
    doc.setTextColor(48, 55, 60)
    doc.text(text, x + 1.5, y + 4)
    x += col.width
  })
  return y + rowH
}

function ensurePageSpace(doc, y, need) {
  if (y + need > 285) { doc.addPage(); return 14 }
  return y
}

function drawChartBlock(doc, y, title, imgData) {
  const bX = 14, bY = y, bW = 182, bH = 68
  doc.setDrawColor(160, 168, 176)
  doc.setLineWidth(0.4)
  doc.roundedRect(bX, bY, bW, bH, 1.2, 1.2, 'S')
  doc.setFillColor(243, 247, 243)
  doc.rect(bX + 0.2, bY + 0.2, bW - 0.4, 8, 'F')
  doc.setFontSize(11)
  doc.setTextColor(40, 44, 52)
  doc.text(`Gráfico ${title}`, bX + 3, bY + 5.6)
  doc.addImage(imgData, 'PNG', bX + 3, bY + 10.5, bW - 6, 54)
  return bY + bH + 4
}

function computeSensorStats(exportRows) {
  const groups = { ph: [], temperature: [], conductivity: [] }
  for (const row of exportRows) {
    if (Number.isFinite(row.rawValue) && groups[row.sensorKey])
      groups[row.sensorKey].push(row.rawValue)
  }
  const keys = pdfFilters.sensor === 'all'
    ? ['ph', 'temperature', 'conductivity']
    : [pdfFilters.sensor]

  return keys.reduce((acc, key) => {
    const vals = groups[key]
    if (!vals?.length) return acc
    const min = Math.min(...vals)
    const max = Math.max(...vals)
    const avg = vals.reduce((a, b) => a + b, 0) / vals.length
    acc.push({ sensorKey: key, label: SENSOR_META[key].label, min, max, avg, count: vals.length })
    return acc
  }, [])
}

function drawSensorStatsBlock(doc, y, exportRows) {
  const stats = computeSensorStats(exportRows)
  if (!stats.length) return y

  const cols = [
    { title: 'Sensor',   width: 44 },
    { title: 'Mínimo',   width: 38 },
    { title: 'Máximo',   width: 38 },
    { title: 'Promedio', width: 38 },
    { title: 'N',        width: 14 },
  ]
  const rowH = 6, startX = 14

  doc.setFontSize(11)
  doc.setFont('helvetica', 'bold')
  doc.setTextColor(38, 45, 52)
  doc.text('Resumen estadístico por sensor', startX, y)
  y += 6

  doc.setFontSize(8)
  doc.setFont('helvetica', 'italic')
  doc.setTextColor(90, 90, 90)
  doc.text('Valores calculados sobre los registros exportados en esta tabla.', startX, y)
  y += 5
  doc.setFont('helvetica', 'normal')

  const totalW = cols.reduce((s, c) => s + c.width, 0)
  doc.setDrawColor(170, 178, 186)
  doc.setLineWidth(0.2)
  doc.setFillColor(232, 242, 232)
  doc.rect(startX, y, totalW, rowH, 'FD')
  let cx = startX
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(8)
  doc.setTextColor(38, 45, 52)
  cols.forEach((col, i) => {
    doc.text(col.title, cx + 1.5, y + 4)
    cx += col.width
    if (i < cols.length - 1) doc.line(cx, y, cx, y + rowH)
  })
  doc.setFont('helvetica', 'normal')
  y += rowH

  for (const s of stats) {
    const vals = [
      s.label,
      measurementText(s.sensorKey, s.min),
      measurementText(s.sensorKey, s.max),
      measurementText(s.sensorKey, s.avg),
      String(s.count),
    ]
    cx = startX
    doc.setDrawColor(170, 178, 186)
    doc.setLineWidth(0.15)
    cols.forEach((col, i) => {
      doc.rect(cx, y, col.width, rowH, 'S')
      doc.setFontSize(8)
      doc.setTextColor(48, 55, 60)
      doc.text(String(vals[i] ?? '').slice(0, 32), cx + 1.5, y + 4)
      cx += col.width
    })
    y += rowH
  }
  return y + 6
}

async function renderChartImage(sensorKey, rows) {
  const meta = SENSOR_META[sensorKey]
  const sensorRows = rows
    .filter(r => r.sensorKey === sensorKey)
    .sort((a, b) => a.timestamp - b.timestamp)
  if (!sensorRows.length) return null

  const maxPoints  = pdfFilters.rangeType === 'day' ? 24 : 45
  const sampled    = downsampleRows(sensorRows, maxPoints)
  const labels     = sampled.map(r =>
    pdfFilters.rangeType === 'day' ? r.timeText : `${r.dateText} ${r.timeText.slice(0, 5)}`
  )

  const canvas = document.createElement('canvas')
  canvas.width  = 1200
  canvas.height = 380
  const tempChart = new Chart(canvas.getContext('2d'), {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: meta.label,
        data:  sampled.map(r => r.rawValue),
        borderColor: '#66bb6a',
        backgroundColor: 'rgba(102,187,106,0.08)',
        borderWidth: 2.5, fill: true, tension: 0.3,
        pointBackgroundColor: '#66bb6a', pointBorderColor: '#ffffff',
        pointBorderWidth: 2, pointRadius: 2.5, pointHoverRadius: 4,
      }],
    },
    options: {
      responsive: false,
      maintainAspectRatio: false,
      animation: false,
      plugins: { legend: { display: false } },
      scales: {
        y: {
          min: meta.min, max: meta.max, beginAtZero: false,
          title: { display: true, text: `${meta.label}${meta.unit ? ` (${meta.unit})` : ''}`, color: '#66bb6a', font: { size: 12, weight: 'bold' } },
          ticks: { color: '#666', font: { size: 10 } },
          grid:  { color: 'rgba(0,0,0,0.05)' },
        },
        x: { ticks: { color: '#666', font: { size: 9 }, maxRotation: 35, minRotation: 0 }, grid: { display: false } },
      },
    },
  })

  await new Promise(resolve => setTimeout(resolve, 60))
  const image = canvas.toDataURL('image/png')
  tempChart.destroy()
  return { title: meta.label, image }
}

function sanitizeSegment(value) {
  return String(value ?? '').trim().replace(/[/\\:*?"<>|]/g, '-').replace(/\s+/g, '_').replace(/_+/g, '_')
}

function buildFilename() {
  const device = sanitizeSegment(pdfFilters.device === 'all' ? 'Todos_los_dispositivos' : pdfFilters.device)
  if (pdfFilters.rangeType === 'day') {
    return `reporte_${device}_${sanitizeSegment(pdfFilters.day || '')}.pdf`
  }
  const from = sanitizeSegment(pdfFilters.startDate || 'inicio')
  const to   = sanitizeSegment(pdfFilters.endDate   || 'fin')
  return `reporte_${device}_${from}_a_${to}.pdf`
}

async function downloadPDF() {
  const exportRows = selectedRows.value
  if (!exportRows.length) {
    const typeMsg = { alerts: 'alertas', normal: 'mediciones normales', all: 'datos' }[pdfFilters.dataType]
    alert(`No hay ${typeMsg} para exportar con los filtros seleccionados.`)
    return
  }

  isGeneratingPdf.value = true
  try {
    const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' })
    let y = 14

    doc.setFont('helvetica', 'bold')
    doc.setFontSize(11)
    doc.setTextColor(38, 45, 52)
    doc.text(`Reporte de Sensores (${selectedDataLabel.value})`, 14, y)
    y += 6

    doc.setFont('helvetica', 'normal')
    doc.setFontSize(10)
    doc.setTextColor(30, 30, 30)
    const deviceLabel = pdfFilters.device === 'all' ? 'Todos' : pdfFilters.device
    const sensorLabel = pdfFilters.sensor === 'all' ? 'Todos los sensores' : SENSOR_META[pdfFilters.sensor].label
    const rangeLabel  = pdfFilters.rangeType === 'day'
      ? `Día: ${pdfFilters.day}`
      : `Rango: ${pdfFilters.startDate || 'inicio'} a ${pdfFilters.endDate || 'hoy'}`

    for (const line of [
      `Dispositivo: ${deviceLabel}`,
      `Sensor: ${sensorLabel}`,
      `Filtro de fecha: ${rangeLabel}`,
      `Datos seleccionados: ${selectedDataLabel.value}`,
      `Registros exportados: ${exportRows.length}`,
      `Registros de alerta (referencia): ${alertRows.value.length}`,
      `Porcentaje de alertas sobre total filtrado: ${alertPercentage.value.toFixed(2)}%`,
    ]) {
      doc.text(line, 14, y)
      y += 5
    }
    y += 3

    y = ensurePageSpace(doc, y, 52)
    y = drawSensorStatsBlock(doc, y, exportRows)
    y = addTableHeader(doc, y)

    const rowsForTable = [...exportRows]
      .sort((a, b) => b.timestamp - a.timestamp)
      .slice(0, 120)

    for (const row of rowsForTable) {
      y = ensurePageSpace(doc, y, 6)
      if (y === 14) y = addTableHeader(doc, y)
      y = drawTableRow(doc, y, [row.device, row.sensorLabel, row.measurementText, row.dateText, row.timeText.slice(0, 5), row.alertStatus])
    }

    const sensorKeys = pdfFilters.sensor === 'all' ? ['ph', 'temperature', 'conductivity'] : [pdfFilters.sensor]
    for (const key of sensorKeys) {
      const chart = await renderChartImage(key, filteredRows.value)
      if (!chart) continue
      y = ensurePageSpace(doc, y, 72)
      y = drawChartBlock(doc, y, chart.title, chart.image)
    }

    doc.save(buildFilename())
  } catch (err) {
    console.error('Error al generar PDF:', err)
    alert('No se pudo generar el PDF. Revisa la consola para más detalles.')
  } finally {
    isGeneratingPdf.value = false
  }
}
</script>

<style scoped>
.pdf-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: max(12px, env(safe-area-inset-top, 0px)) max(14px, env(safe-area-inset-right, 0px))
    max(12px, env(safe-area-inset-bottom, 0px)) max(14px, env(safe-area-inset-left, 0px));
  z-index: 40;
  box-sizing: border-box;
}

.pdf-modal {
  width: min(760px, 100%);
  max-height: min(92vh, 100dvh - 24px);
  background: white;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.2);
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.pdf-modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  border-bottom: 1px solid #e5e7eb;
  flex-shrink: 0;
  gap: 8px;
  min-width: 0;
}

.pdf-modal-header h3 {
  margin: 0;
  font-size: 16px;
}

.modal-close-btn {
  border: none;
  background: transparent;
  font-size: 16px;
  cursor: pointer;
  color: #374151;
}

.pdf-modal-body {
  padding: 14px 16px;
  overflow-y: auto;
  flex: 1;
  min-height: 0;
}

.filter-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
}

.filter-grid label {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.filter-grid span {
  font-size: 12px;
  color: #4b5563;
  font-weight: 600;
}

.filter-grid select,
.filter-grid input {
  height: 40px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  padding: 0 10px;
  font-size: 16px;
  color: #1f2937;
  width: 100%;
  max-width: 100%;
  min-width: 0;
  box-sizing: border-box;
}

.pdf-preview-text {
  margin: 12px 0 0;
  font-size: 13px;
  color: #374151;
}

.pdf-modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 12px 16px max(16px, env(safe-area-inset-bottom, 0px));
  border-top: 1px solid #e5e7eb;
  flex-shrink: 0;
  flex-wrap: wrap;
}

.secondary-btn,
.primary-btn {
  min-width: 120px;
  height: 36px;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
}

.secondary-btn {
  border: 1px solid #d1d5db;
  background: white;
  color: #374151;
}

.primary-btn {
  border: 1px solid #66bb6a;
  background: #66bb6a;
  color: white;
}

.primary-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .pdf-modal {
    width: 100%;
    max-height: min(92vh, 100dvh - 24px);
  }

  .filter-grid {
    grid-template-columns: 1fr;
  }

  .pdf-modal-actions {
    flex-direction: column;
  }

  .secondary-btn,
  .primary-btn {
    width: 100%;
  }
}

@media (max-width: 480px) {
  .pdf-modal-header h3 {
    font-size: 14px;
    line-height: 1.3;
  }

  .pdf-modal-body {
    padding: 12px;
  }

  .pdf-preview-text {
    font-size: 12px;
  }
}
</style>
