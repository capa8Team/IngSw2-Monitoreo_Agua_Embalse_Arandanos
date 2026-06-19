<template>
  <div class="device-map-wrapper">
    <div ref="mapContainer" class="device-map" role="application" aria-label="Mapa de dispositivos"></div>
    <div v-if="markers.length === 0" class="map-empty-hint">
      No hay ubicaciones en el mapa. Agrupa dispositivos o asigna coordenadas desde la configuración (admin).
    </div>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref, watch } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { buildMapMarkers } from '../composables/useMapMarkers.js'
import { createRedMarkerIcon, DEFAULT_MAP_CENTER, DEFAULT_MAP_ZOOM } from '../utils/mapUtils.js'

const props = defineProps({
  devices: { type: Array, default: () => [] },
  groups: { type: Array, default: () => [] },
})

const emit = defineEmits(['select-device', 'select-group'])

const mapContainer = ref(null)
let mapInstance = null
let markerLayer = null

const markers = ref([])

const popupHtml = (marker) => {
  const deviceList = marker.devices
    .map((d) => `<li>${d.name}</li>`)
    .join('')
  const countLabel = marker.deviceCount > 1
    ? `${marker.deviceCount} dispositivos`
    : '1 dispositivo'
  return `
    <div class="map-popup">
      <strong>${marker.name}</strong>
      <p>${countLabel}</p>
      ${marker.locationLabel ? `<p class="map-popup-location">${marker.locationLabel}</p>` : ''}
      <ul>${deviceList}</ul>
    </div>
  `
}

const renderMarkers = () => {
  if (!mapInstance || !markerLayer) return

  markerLayer.clearLayers()
  markers.value = buildMapMarkers(props.devices, props.groups)

  const bounds = []
  for (const marker of markers.value) {
    const latLng = [marker.latitude, marker.longitude]
    bounds.push(latLng)
    const icon = createRedMarkerIcon(marker.deviceCount)
    const leafletMarker = L.marker(latLng, { icon })
    leafletMarker.bindPopup(popupHtml(marker))
    leafletMarker.on('click', () => {
      if (marker.type === 'group') {
        emit('select-group', marker)
      } else if (marker.devices[0]) {
        emit('select-device', marker.devices[0])
      }
    })
    markerLayer.addLayer(leafletMarker)
  }

  if (bounds.length === 1) {
    mapInstance.setView(bounds[0], 12)
  } else if (bounds.length > 1) {
    mapInstance.fitBounds(bounds, { padding: [40, 40], maxZoom: 14 })
  } else {
    mapInstance.setView(DEFAULT_MAP_CENTER, DEFAULT_MAP_ZOOM)
  }
}

onMounted(() => {
  if (!mapContainer.value) return

  mapInstance = L.map(mapContainer.value, {
    center: DEFAULT_MAP_CENTER,
    zoom: DEFAULT_MAP_ZOOM,
    scrollWheelZoom: true,
  })

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    maxZoom: 19,
  }).addTo(mapInstance)

  markerLayer = L.layerGroup().addTo(mapInstance)
  renderMarkers()

  setTimeout(() => mapInstance?.invalidateSize(), 100)
})

onUnmounted(() => {
  if (mapInstance) {
    mapInstance.remove()
    mapInstance = null
    markerLayer = null
  }
})

watch(
  () => [props.devices, props.groups],
  () => renderMarkers(),
  { deep: true },
)
</script>

<style scoped>
.device-map-wrapper {
  position: relative;
  width: 100%;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid #d0d0d0;
  background: #e8ecf1;
}

.device-map {
  width: 100%;
  height: 420px;
  z-index: 0;
}

.map-empty-hint {
  position: absolute;
  bottom: 12px;
  left: 12px;
  right: 12px;
  background: rgba(255, 255, 255, 0.92);
  border-radius: 8px;
  padding: 10px 14px;
  font-size: 13px;
  color: #555;
  z-index: 500;
  pointer-events: none;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

:deep(.device-map-marker) {
  background: transparent;
  border: none;
}

:deep(.device-map-marker-dot) {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #e53935;
  border: 3px solid #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.35);
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}

:deep(.map-popup) {
  font-size: 13px;
  line-height: 1.4;
}

:deep(.map-popup ul) {
  margin: 6px 0 0;
  padding-left: 18px;
}

:deep(.map-popup-location) {
  margin: 4px 0 0;
  color: #666;
  font-size: 12px;
}

html[data-theme='dark'] .device-map-wrapper {
  border-color: #3d4254;
  background: #1a1d26;
}

html[data-theme='dark'] .map-empty-hint {
  background: rgba(38, 42, 54, 0.95);
  color: #cbd5e1;
}
</style>
