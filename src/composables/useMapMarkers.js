import { computed } from 'vue'

/**
 * Agrupa dispositivos para el mapa: un marcador por grupo o por dispositivo suelto con coordenadas.
 */
export function buildMapMarkers(devices = [], groups = []) {
  const groupMap = new Map(groups.map((g) => [g.id, g]))
  const markers = []
  const groupedDeviceIds = new Set()

  for (const group of groups) {
    const groupDevices = devices.filter((d) => d.group_id === group.id)
    if (groupDevices.length === 0) continue
    if (group.latitude == null || group.longitude == null) continue

    groupDevices.forEach((d) => groupedDeviceIds.add(d.id))
    markers.push({
      id: `group-${group.id}`,
      type: 'group',
      groupId: group.id,
      name: group.name,
      latitude: group.latitude,
      longitude: group.longitude,
      deviceCount: groupDevices.length,
      devices: groupDevices,
      locationLabel: group.location_label || group.description || '',
    })
  }

  for (const device of devices) {
    if (groupedDeviceIds.has(device.id)) continue
    const lat = device.latitude
    const lng = device.longitude
    if (lat == null || lng == null) continue

    markers.push({
      id: `device-${device.id}`,
      type: 'device',
      deviceId: device.id,
      name: device.name,
      latitude: lat,
      longitude: lng,
      deviceCount: 1,
      devices: [device],
      locationLabel: device.location || '',
    })
  }

  return markers
}

export function useMapMarkers(devicesRef, groupsRef) {
  return computed(() => buildMapMarkers(devicesRef.value || [], groupsRef.value || []))
}
