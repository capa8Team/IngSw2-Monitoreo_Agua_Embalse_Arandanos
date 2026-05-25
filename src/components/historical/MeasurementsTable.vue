<template>
  <section class="table-wrapper">
    <div class="table-header">
      <h3>Mediciones En Tiempo Real</h3>
      <span class="table-meta">Actualiza cada 30 segundos</span>
    </div>

    <div class="table-filters" aria-label="Filtro de fechas de la tabla">
      <label class="table-filter-field">
        <span>Sensor</span>
        <select v-model="filter.sensor" class="table-filter-select">
          <option value="all">Todos los sensores</option>
          <option value="ph">pH</option>
          <option value="temperature">Temperatura (°C)</option>
          <option value="conductivity">Conductividad (µS/cm)</option>
        </select>
      </label>
      <label class="table-filter-field">
        <span>Fecha</span>
        <select v-model="filter.mode" class="table-filter-select">
          <option value="all">Todas las fechas</option>
          <option value="day">Día específico</option>
          <option value="range">Rango (desde / hasta)</option>
        </select>
      </label>
      <label v-if="filter.mode === 'day'" class="table-filter-field">
        <span>Día</span>
        <input v-model="filter.day" type="date" class="table-filter-input" />
      </label>
      <template v-else-if="filter.mode === 'range'">
        <label class="table-filter-field">
          <span>Desde</span>
          <input v-model="filter.startDate" type="date" class="table-filter-input" />
        </label>
        <label class="table-filter-field">
          <span>Hasta</span>
          <input v-model="filter.endDate" type="date" class="table-filter-input" />
        </label>
      </template>
      <span v-if="filter.mode !== 'all' || filter.sensor !== 'all'" class="table-filter-count">
        {{ filteredRows.length }} registro(s)
      </span>
    </div>

    <div class="table-scroll">
      <table class="measurements-table">
        <thead>
          <tr>
            <th>Dispositivo</th>
            <th>Sensor</th>
            <th>Medición</th>
            <th>Fecha</th>
            <th>Hora</th>
            <th>Alerta</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="visibleRows.length === 0">
            <td colspan="6" class="no-data">
              {{
                rows.length === 0
                  ? 'No hay datos disponibles.'
                  : 'No hay mediciones para el filtro seleccionado.'
              }}
            </td>
          </tr>
          <tr v-for="row in visibleRows" :key="row.key">
            <td>{{ row.device }}</td>
            <td>{{ row.sensorLabel }}</td>
            <td>{{ row.measurementText }}</td>
            <td>{{ row.dateText }}</td>
            <td>{{ row.timeText }}</td>
            <td>
              <span class="alert-chip" :class="row.alertClass">{{ row.alertStatus }}</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="table-actions" v-if="totalPages > 1">
      <div class="pagination-controls">
        <button class="pagination-btn arrow-btn" :disabled="currentPage === 1" @click="prevPage" title="Página anterior">&lt;</button>

        <div class="pagination-numbers">
          <button
            v-for="page in visiblePaginationPages"
            :key="`page-${page}`"
            class="page-number-btn"
            :class="{ active: currentPage === page }"
            @click="goToPage(page)"
          >{{ page }}</button>

          <button
            v-if="shouldShowEllipsis"
            class="page-ellipsis-btn"
            @click="toggleExpandedPagination"
            title="Mostrar más páginas"
          >...</button>

          <button
            v-for="page in expandedPaginationPages"
            v-show="showExpandedPages"
            :key="`page-exp-${page}`"
            class="page-number-btn"
            :class="{ active: currentPage === page }"
            @click="goToPage(page)"
          >{{ page }}</button>
        </div>

        <button class="pagination-btn arrow-btn" :disabled="currentPage === totalPages" @click="nextPage" title="Página siguiente">&gt;</button>
      </div>

      <div class="pagination-footer">
        <span class="pagination-info">Página {{ currentPage }} de {{ totalPages }}</span>
        <div class="go-to-page">
          <label for="pageInput">Ir a página:</label>
          <input
            id="pageInput"
            v-model.number="jumpToPageValue"
            type="number"
            :min="1"
            :max="totalPages"
            @keyup.enter="jumpToPage"
            placeholder="Ej: 5"
            class="page-input"
          />
          <button class="pagination-btn jump-btn" @click="jumpToPage" :disabled="!isValidPageJump">Ir</button>
        </div>
      </div>

      <span class="pagination-records">({{ filteredRows.length }} registros totales)</span>
    </div>
  </section>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { localDateKey } from '../../utils/sensorUtils.js'

const props = defineProps({
  rows: { type: Array, required: true },
})

const ITEMS_PER_PAGE = 10

const currentPage        = ref(1)
const showExpandedPages  = ref(false)
const jumpToPageValue    = ref(null)

const filter = reactive({
  sensor:    'all',
  mode:      'all',
  day:       localDateKey(new Date()),
  startDate: localDateKey(new Date(Date.now() - 6 * 24 * 60 * 60 * 1000)),
  endDate:   localDateKey(new Date()),
})

const filteredRows = computed(() =>
  props.rows.filter(row => {
    if (filter.sensor !== 'all' && row.sensorKey !== filter.sensor) return false
    if (filter.mode === 'all') return true
    if (filter.mode === 'day') return row.dateKey === filter.day
    const start = filter.startDate || '0000-01-01'
    const end   = filter.endDate   || '9999-12-31'
    return row.dateKey >= start && row.dateKey <= end
  })
)

const totalPages = computed(() => Math.ceil(filteredRows.value.length / ITEMS_PER_PAGE) || 1)

const visibleRows = computed(() => {
  const start = (currentPage.value - 1) * ITEMS_PER_PAGE
  return filteredRows.value.slice(start, start + ITEMS_PER_PAGE)
})

const visiblePaginationPages = computed(() =>
  Array.from({ length: Math.min(3, totalPages.value) }, (_, i) => i + 1)
)

const shouldShowEllipsis = computed(() => totalPages.value > 3)

const expandedPaginationPages = computed(() => {
  const start = Math.max(4, totalPages.value - 2)
  return Array.from({ length: totalPages.value - start + 1 }, (_, i) => start + i)
})

const isValidPageJump = computed(() =>
  jumpToPageValue.value >= 1 && jumpToPageValue.value <= totalPages.value
)

watch(
  () => [filter.mode, filter.day, filter.startDate, filter.endDate, filter.sensor],
  () => { currentPage.value = 1 }
)

function goToPage(page)            { currentPage.value = Math.max(1, Math.min(page, totalPages.value)) }
function nextPage()                { if (currentPage.value < totalPages.value) currentPage.value++ }
function prevPage()                { if (currentPage.value > 1) { currentPage.value--; showExpandedPages.value = false } }
function toggleExpandedPagination(){ showExpandedPages.value = !showExpandedPages.value }
function jumpToPage() {
  if (isValidPageJump.value) {
    currentPage.value     = jumpToPageValue.value
    jumpToPageValue.value = null
    showExpandedPages.value = false
  }
}
</script>

<style scoped>
.table-wrapper {
  grid-column: 1 / -1;
  background: white;
  border-radius: 8px;
  padding: 12px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
}

.table-header h3 {
  margin: 0;
  font-size: 15px;
  color: #333;
}

.table-meta {
  font-size: 12px;
  color: #6b7280;
}

.table-filters {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 12px 16px;
  padding: 10px 12px;
  background: #f8fafc;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
}

.table-filter-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.table-filter-field > span {
  font-size: 11px;
  font-weight: 600;
  color: #4b5563;
}

.table-filter-select,
.table-filter-input {
  padding: 7px 10px;
  border-radius: 6px;
  border: 1px solid #d1d5db;
  font-size: 16px;
  color: #111827;
  background: #fff;
  width: 100%;
  max-width: 100%;
  min-width: 0;
  box-sizing: border-box;
}

.table-filter-select:focus,
.table-filter-input:focus {
  outline: none;
  border-color: #66bb6a;
  box-shadow: 0 0 0 2px rgba(102, 187, 106, 0.2);
}

.table-filter-count {
  font-size: 12px;
  color: #374151;
  font-weight: 600;
  margin-left: auto;
  align-self: center;
}

.table-scroll {
  overflow: auto;
  -webkit-overflow-scrolling: touch;
  overscroll-behavior-x: contain;
  max-height: 320px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  min-width: 0;
}

.measurements-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 760px;
}

.measurements-table th,
.measurements-table td {
  text-align: left;
  padding: 9px 10px;
  font-size: 12px;
  border-bottom: 1px solid #eef0f3;
  color: #333;
}

.measurements-table thead th {
  position: sticky;
  top: 0;
  background: #f8fafc;
  z-index: 1;
  font-weight: 600;
}

.no-data {
  text-align: center !important;
  color: #6b7280 !important;
}

.alert-chip {
  padding: 3px 8px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
}

.alert-chip.normal  { background: #e8f5e9; color: #2e7d32; }
.alert-chip.warning { background: #ffebee; color: #c62828; }

.table-actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
  align-items: center;
  justify-content: center;
  padding-top: 12px;
}

.pagination-controls {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: center;
}

.pagination-btn {
  padding: 8px 12px;
  border-radius: 6px;
  border: 1px solid #66bb6a;
  background: #66bb6a;
  color: white;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.pagination-btn:hover:not(:disabled) {
  background: #558a5a;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.pagination-btn:disabled {
  background: #ccc;
  color: #888;
  cursor: not-allowed;
  opacity: 0.6;
}

.pagination-numbers {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
  justify-content: center;
}

.page-number-btn {
  min-width: 36px;
  height: 36px;
  padding: 0 8px;
  border-radius: 4px;
  border: 1px solid #ddd;
  background: #f5f5f5;
  color: #333;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.page-number-btn:hover  { background: #e8e8e8; border-color: #66bb6a; }
.page-number-btn.active { background: #66bb6a; color: white; border-color: #66bb6a; box-shadow: 0 2px 4px rgba(102, 187, 106, 0.3); }

.page-ellipsis-btn {
  padding: 6px 8px;
  font-size: 14px;
  font-weight: bold;
}

.pagination-footer {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-top: 12px;
  flex-wrap: wrap;
}

.pagination-info {
  font-size: 12px;
  color: #666;
  text-align: center;
  width: 100%;
}

.go-to-page {
  display: flex;
  align-items: center;
  gap: 8px;
}

.go-to-page label {
  font-size: 12px;
  color: #666;
  white-space: nowrap;
}

.page-input {
  width: 45px;
  height: 32px;
  padding: 4px 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 12px;
  text-align: center;
}

.page-input:focus {
  outline: none;
  border-color: #66bb6a;
  box-shadow: 0 0 0 2px rgba(102, 187, 106, 0.1);
}

.jump-btn {
  padding: 6px 12px;
  font-size: 11px;
  min-width: 0;
}

.pagination-records {
  font-size: 12px;
  color: #999;
  text-align: center;
  width: 100%;
  margin-top: 8px;
}

@media (max-width: 768px) {
  .table-wrapper {
    padding: 10px;
  }

  .table-filters {
    flex-direction: column;
    align-items: stretch;
  }

  .table-filter-count {
    margin-left: 0;
  }

  .table-scroll {
    max-height: 280px;
  }
}
</style>
