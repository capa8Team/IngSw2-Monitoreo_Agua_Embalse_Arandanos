import L from 'leaflet'
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png'
import markerIcon from 'leaflet/dist/images/marker-icon.png'
import markerShadow from 'leaflet/dist/images/marker-shadow.png'

const defaultIcon = L.icon({
  iconUrl: markerIcon,
  iconRetinaUrl: markerIcon2x,
  shadowUrl: markerShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
})

export function createRedMarkerIcon(count = 1) {
  const label = count > 1 ? String(count) : ''
  return L.divIcon({
    className: 'device-map-marker',
    html: `<div class="device-map-marker-dot">${label}</div>`,
    iconSize: [28, 28],
    iconAnchor: [14, 14],
    popupAnchor: [0, -14],
  })
}

export function createDefaultIcon() {
  return defaultIcon
}

export const DEFAULT_MAP_CENTER = [-33.45, -70.66]
export const DEFAULT_MAP_ZOOM = 6

export async function geocodeLocation(query) {
  const trimmed = String(query || '').trim()
  if (!trimmed) return null

  const url = `https://nominatim.openstreetmap.org/search?format=json&limit=1&q=${encodeURIComponent(trimmed)}`
  const response = await fetch(url, {
    headers: { Accept: 'application/json' },
  })
  if (!response.ok) return null

  const results = await response.json()
  if (!Array.isArray(results) || results.length === 0) return null

  const hit = results[0]
  return {
    latitude: Number(hit.lat),
    longitude: Number(hit.lon),
    label: hit.display_name || trimmed,
  }
}
