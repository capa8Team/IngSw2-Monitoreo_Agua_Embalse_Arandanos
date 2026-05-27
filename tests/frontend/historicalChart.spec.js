import { describe, it, expect } from 'vitest'
import {
  buildChartSeriesFromReadings,
  computeChartStats,
  expandReadingsForRegisteredDevices,
  readingMatchesDeviceTelemetry,
} from '../../src/utils/sensorUtils.js'

const dispositivo1 = {
  id: '1',
  name: 'Dispositivo 1',
  arduino_id: 'Dispositivo 1',
  topic: 'boya/sensores',
}
const norte = {
  id: '2',
  name: 'Norte',
  arduino_id: 'Norte',
  telemetry_key: 'Dispositivo 1',
  topic: 'boya/sensores',
}
const registered = [dispositivo1, norte]

describe('alias / réplicas MQTT', () => {
  it('Norte usa la clave de telemetría de Dispositivo 1', () => {
    expect(readingMatchesDeviceTelemetry('Dispositivo 1', norte)).toBe(true)
    expect(readingMatchesDeviceTelemetry('Dispositivo 1-10', norte)).toBe(true)
  })

  it('expande lecturas con el nombre de cada réplica del mismo topic', () => {
    const records = [{
      device: 'Dispositivo 1',
      timestamp: new Date(),
      ph: 7,
      temperature: 20,
      conductivity: 900,
    }]
    const expanded = expandReadingsForRegisteredDevices(records, registered)
    const names = expanded.map((r) => r.device).sort()
    expect(names).toEqual(['Dispositivo 1', 'Norte'])
  })
})

describe('buildChartSeriesFromReadings', () => {
  it('agrupa última hora en bloques de 5 minutos', () => {
    const now = Date.now()
    const readings = Array.from({ length: 6 }, (_, i) => ({
      timestamp: new Date(now - (50 - i * 10) * 60 * 1000),
      ph: 7 + i * 0.1,
      temperature: 20,
      conductivity: 900,
      device: 'A',
    }))

    const { labels, values } = buildChartSeriesFromReadings(readings, 'ph', 'hour')

    expect(labels).toHaveLength(12)
    expect(values).toHaveLength(12)
    expect(values.filter((v) => v !== null).length).toBeGreaterThan(0)
  })

  it('agrupa por hora en modo día usando lecturas reales', () => {
    const base = Date.now() - 2 * 60 * 60 * 1000
    const readings = [
      { timestamp: new Date(base), ph: 7.0, temperature: 20, conductivity: 900, device: 'A' },
      { timestamp: new Date(base + 30 * 60 * 1000), ph: 7.4, temperature: 21, conductivity: 950, device: 'A' },
    ]

    const { labels, values } = buildChartSeriesFromReadings(readings, 'ph', 'day')

    expect(labels.length).toBe(values.length)
    expect(labels.length).toBeGreaterThanOrEqual(2)
    expect(values.every((v) => v !== null)).toBe(true)
    expect(Math.min(...values)).toBeGreaterThanOrEqual(7.0)
    expect(Math.max(...values)).toBeLessThanOrEqual(7.4)
  })

  it('calcula estadísticas solo con puntos válidos', () => {
    const stats = computeChartStats([7.0, 7.5, null, 7.2], 'ph')
    expect(stats.max).toBe(7.5)
    expect(stats.min).toBe(7.0)
    expect(stats.avg).toBeCloseTo(7.233, 2)
  })
})
