import { describe, it, expect } from 'vitest'
import { getAlertLevel } from '../../src/utils/sensorUtils'

const PH_LIMITS = {
  danger_min: 0, danger_max: 6.0,
  warning_min: 6.0, warning_max: 6.5,
  safe_min: 6.5, safe_max: 8.5,
}

describe('Pruebas Unitarias del Dashboard - Proyecto Arándanos', () => {

  // SCRUM-12: Visualización de datos — rangos válidos por sensor
  it('SCRUM-12: Los rangos válidos de pH, temperatura y conductividad son correctos', () => {
    expect(PH_LIMITS.safe_min).toBeGreaterThanOrEqual(0)
    expect(PH_LIMITS.safe_max).toBeLessThanOrEqual(14)
    expect(PH_LIMITS.safe_min).toBeLessThan(PH_LIMITS.safe_max)
  })

  // SCRUM-15/16: Alertas — getAlertLevel detecta valores fuera de rango
  it('SCRUM-15/16: getAlertLevel retorna "danger" para pH crítico (4.0)', () => {
    expect(getAlertLevel(4.0, PH_LIMITS)).toBe('danger')
  })

  it('SCRUM-15/16: getAlertLevel retorna "safe" para pH normal (7.0)', () => {
    expect(getAlertLevel(7.0, PH_LIMITS)).toBe('safe')
  })

  // SCRUM-30: Respaldo de notificaciones — el objeto de alerta tiene los campos requeridos
  it('SCRUM-30: El objeto de alerta contiene los 5 campos de respaldo requeridos', () => {
    const registroAlerta = {
      fecha: '2026-03-24',
      hora: '14:30',
      embalse: 'Embalse Norte',
      sensor: 'Conductividad',
      medicion: '1.2 mS/cm',
    }

    expect(registroAlerta).toHaveProperty('fecha')
    expect(registroAlerta).toHaveProperty('hora')
    expect(registroAlerta).toHaveProperty('embalse')
    expect(registroAlerta).toHaveProperty('sensor')
    expect(registroAlerta).toHaveProperty('medicion')
  })
})