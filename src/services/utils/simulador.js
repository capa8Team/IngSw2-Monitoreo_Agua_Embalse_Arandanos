// Lógica de simulación basada en tus criterios de aceptación (SCRUM-12)
export const generarLecturaSensor = () => {
    return {
        ph: parseFloat((Math.random() * (8.5 - 6.0) + 6.0).toFixed(2)),
        temp: parseFloat((Math.random() * (30 - 15) + 15).toFixed(1)),
        conductividad: parseFloat((Math.random() * (2.0 - 0.5) + 0.5).toFixed(2)),
        timestamp: new Date().toISOString()
    };
};

// Lógica de alertas (SCRUM-15 y 16)
export const verificarAlerta = (valor, min, max) => {
    return valor < min || valor > max;
};
