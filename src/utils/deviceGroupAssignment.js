/**
 * Resuelve la selección de grupo al crear o actualizar un dispositivo.
 */
export async function resolveGroupAssignment(groupSelection, deviceGroupStore) {
  if (!groupSelection) {
    return { group_id: null, latitude: null, longitude: null }
  }

  if (groupSelection.mode === 'new') {
    const ng = groupSelection.new_group || {}
    if (!ng.name?.trim()) {
      throw new Error('El nombre del grupo es obligatorio')
    }
    if (ng.latitude == null || ng.longitude == null) {
      throw new Error('Define las coordenadas del grupo en el mapa')
    }
    const created = await deviceGroupStore.createGroup({
      name: ng.name.trim(),
      description: '',
      location_label: ng.location_label || '',
      city: ng.city || '',
      latitude: Number(ng.latitude),
      longitude: Number(ng.longitude),
    })
    return { group_id: created.id, latitude: null, longitude: null }
  }

  if (groupSelection.mode === 'existing') {
    if (!groupSelection.group_id) {
      throw new Error('Selecciona un grupo existente')
    }
    return { group_id: groupSelection.group_id, latitude: null, longitude: null }
  }

  return {
    group_id: null,
    latitude: groupSelection.latitude ?? null,
    longitude: groupSelection.longitude ?? null,
  }
}

export function buildDeviceUpdatePayload(formPayload, assignment) {
  const body = {
    name: formPayload.name,
    location: formPayload.location || '',
    city: formPayload.city || '',
    arduino_id: formPayload.arduino_id || null,
    telemetry_key: formPayload.telemetry_key || null,
    topic: formPayload.topic || null,
  }

  if (assignment.group_id) {
    body.group_id = assignment.group_id
  } else {
    body.group_id = ''
  }

  if (assignment.latitude != null && assignment.longitude != null) {
    body.latitude = assignment.latitude
    body.longitude = assignment.longitude
  }

  return body
}
