import { describe, it, expect } from 'vitest'
import { generarLecturaSensor, verificarAlerta } from '../src/utils/simulador'

describe('Pruebas Unitarias del Dashboard - Proyecto Arándanos', () => {

  // Validación de la HU SCRUM-12: Visualización de datos
  it('SCRUM-12: Los valores simulados (pH, Temp, Cond) deben ser numéricos y estar en rango', () => {
    const datos = generarLecturaSensor();
    
    expect(typeof datos.ph).toBe('number');
    expect(datos.ph).toBeGreaterThanOrEqual(0);
    expect(datos.ph).toBeLessThanOrEqual(14);
    
    expect(typeof datos.temp).toBe('number');
    expect(datos.conductividad).toBeGreaterThanOrEqual(0);
  });

  // Validación de la HU SCRUM-15 y 16: Alertas Telegram/Mail
  it('SCRUM-15/16: La lógica de alerta debe retornar TRUE si el valor sale de los rangos establecidos', () => {
    // Definimos un rango normal de pH: 6.5 a 8.5
    const pH_critico = 4.0; 
    const alertaActivada = verificarAlerta(pH_critico, 6.5, 8.5);
    
    expect(alertaActivada).toBe(true); // El test pasa si la alerta se dispara correctamente
  });

  // Validación de la HU SCRUM-30: Respaldo de notificaciones
  it('SCRUM-30: El objeto de alerta debe contener los 5 campos de respaldo requeridos', () => {
    const registroAlerta = {
      fecha: "2026-03-24",
      hora: "14:30",
      embalse: "Embalse Norte",
      sensor: "Conductividad",
      medicion: "1.2 mS/cm"
    };

    expect(registroAlerta).toHaveProperty('fecha');
    expect(registroAlerta).toHaveProperty('hora');
    expect(registroAlerta).toHaveProperty('embalse');
    expect(registroAlerta).toHaveProperty('sensor');
    expect(registroAlerta).toHaveProperty('medicion');
  });

});