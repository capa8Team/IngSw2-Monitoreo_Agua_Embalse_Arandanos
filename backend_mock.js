import express from 'express';
import cors from 'cors';

const app = express();
const PORT = 8000;

// Middleware
app.use(cors());
app.use(express.json());

// Mock data
const mockDevices = [
  {
    id: 1,
    name: 'Sensor pH - Estación 1',
    type: 'pH',
    location: 'Profundidad 5m',
    value: 7.2,
    min: 6.5,
    max: 8.5,
    unit: 'pH',
    status: 'online',
    lastUpdate: new Date().toISOString(),
  },
  {
    id: 2,
    name: 'Sensor Temperatura - Estación 1',
    type: 'Temperature',
    location: 'Profundidad 5m',
    value: 18.5,
    min: 5,
    max: 30,
    unit: '°C',
    status: 'online',
    lastUpdate: new Date().toISOString(),
  },
  {
    id: 3,
    name: 'Sensor Conductividad - Estación 1',
    type: 'Conductivity',
    location: 'Profundidad 5m',
    value: 450,
    min: 200,
    max: 800,
    unit: 'µS/cm',
    status: 'online',
    lastUpdate: new Date().toISOString(),
  },
];

// API Routes

// GET / - Raíz
app.get('/', (req, res) => {
  res.json({ 
    message: 'Backend Mock API running',
    version: '1.0.0',
    timestamp: new Date().toISOString()
  });
});

// GET /api/devices - Obtener todos los dispositivos
app.get('/api/devices', (req, res) => {
  res.json(mockDevices);
});

// GET /api/devices/:id - Obtener dispositivo por ID
app.get('/api/devices/:id', (req, res) => {
  const device = mockDevices.find(d => d.id === parseInt(req.params.id));
  if (!device) {
    return res.status(404).json({ error: 'Dispositivo no encontrado' });
  }
  res.json(device);
});

// GET /api/devices/:id/history - Obtener historial de un dispositivo
app.get('/api/devices/:id/history', (req, res) => {
  const history = [];
  for (let i = 0; i < 24; i++) {
    const timestamp = new Date();
    timestamp.setHours(timestamp.getHours() - i);
    history.push({
      timestamp: timestamp.toISOString(),
      value: Math.random() * 10 + 15,
    });
  }
  res.json(history);
});

// POST /api/alerts - Crear alerta
app.post('/api/alerts', (req, res) => {
  res.json({ id: 1, message: 'Alerta creada', ...req.body });
});

// GET /api/alerts - Obtener alertas
app.get('/api/alerts', (req, res) => {
  res.json([
    { id: 1, message: 'Sensor pH fuera de rango', severity: 'high', timestamp: new Date().toISOString() },
    { id: 2, message: 'Sensor de temperatura bajo mantenimiento', severity: 'medium', timestamp: new Date().toISOString() },
  ]);
});

// Health check
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', message: 'Backend mock running' });
});

// Error handling
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({ error: 'Error interno del servidor' });
});

// Start server
app.listen(PORT, () => {
  console.log(`🚀 Backend mock running on http://localhost:${PORT}`);
  console.log(`📊 API ready for frontend at http://localhost:${PORT}/api`);
});
