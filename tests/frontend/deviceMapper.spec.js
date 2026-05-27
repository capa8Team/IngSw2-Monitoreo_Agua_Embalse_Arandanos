import { describe, it, expect } from 'vitest'
import {
  mapApiDeviceToCard,
  mapApiStatusToCard,
  mergeCardWithTelemetry,
  applyDashboardToTelemetry,
} from '../../src/utils/deviceMapper.js'

describe('deviceMapper', () => {
  it('mapApiStatusToCard traduce estados del API', () => {
    expect(mapApiStatusToCard('online')).toBe('connected')
    expect(mapApiStatusToCard('offline')).toBe('disconnected')
    expect(mapApiStatusToCard('unknown')).toBe('disconnected')
  })

  it('mapApiDeviceToCard genera modelo legible para DeviceCard', () => {
    const card = mapApiDeviceToCard({
      id: 'abc-123',
      name: 'Boya Norte',
      device_type: 'ESP8266',
      location: 'Zona A',
      status: 'online',
      battery: 88,
      arduino_id: 'esp-01',
      topic: 'boya/sensores',
    })
    expect(card.id).toBe('abc-123')
    expect(card.name).toBe('Boya Norte')
    expect(card.model).toContain('ESP8266')
    expect(card.model).toContain('Zona A')
    expect(card.status).toBe('connected')
    expect(card.battery).toBe(88)
    expect(card.topic).toBe('boya/sensores')
  })

  it('mergeCardWithTelemetry combina overlay de sensores', () => {
    const base = mapApiDeviceToCard({ id: '1', name: 'X', device_type: 'Arduino', status: 'offline' })
    const merged = mergeCardWithTelemetry(base, {
      status: 'connected',
      sensors: { ph: 7.1, temperature: 20, conductivity: 500 },
    })
    expect(merged.status).toBe('connected')
    expect(merged.sensors.ph).toBe(7.1)
  })

  it('applyDashboardToTelemetry mapea respuesta del dashboard', () => {
    const telemetry = applyDashboardToTelemetry({
      ph: { value: 7.2 },
      temperature: { value: 18 },
      conductivity: { value: 400 },
      metadata: { arduinoConnected: true, lastSync: new Date().toISOString() },
      battery: 75,
    })
    expect(telemetry.status).toBe('connected')
    expect(telemetry.sensors.ph).toBe(7.2)
    expect(telemetry.battery).toBe(75)
  })
})
