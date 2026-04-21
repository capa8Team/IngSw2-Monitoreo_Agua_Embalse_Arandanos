-- Script para crear la tabla alert_limits en Supabase
-- Este script es compatible con la implementación actual de la aplicación

-- Si la tabla ya existe, eliminarla para recrearla
DROP TABLE IF EXISTS alert_limits CASCADE;

-- Crear tabla de límites de alerta
CREATE TABLE alert_limits (
  id BIGSERIAL PRIMARY KEY,
  admin_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  sensor_type TEXT NOT NULL CHECK (sensor_type IN ('ph', 'temperature', 'conductivity')),
  min_value DECIMAL(10, 4) NOT NULL,
  max_value DECIMAL(10, 4) NOT NULL,
  safe_max DECIMAL(10, 4),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  -- Restricción de unicidad: un admin solo puede tener una configuración por tipo de sensor
  UNIQUE(admin_id, sensor_type)
);

-- Crear índices para optimización
CREATE INDEX idx_alert_limits_admin_id ON alert_limits(admin_id);
CREATE INDEX idx_alert_limits_sensor_type ON alert_limits(sensor_type);
CREATE INDEX idx_alert_limits_admin_sensor ON alert_limits(admin_id, sensor_type);

-- Habilitar Row Level Security (RLS)
ALTER TABLE alert_limits ENABLE ROW LEVEL SECURITY;

-- Política RLS: Los admins pueden ver y modificar sus propios límites
CREATE POLICY "Admins can manage their alert limits"
  ON alert_limits
  USING (auth.uid() = admin_id)
  WITH CHECK (auth.uid() = admin_id);

-- Política RLS: Los admins pueden ver los límites de todos los sensores
CREATE POLICY "Admins can view all alert limits"
  ON alert_limits FOR SELECT
  USING (
    auth.uid() IN (SELECT id FROM users_roles WHERE role = 'admin')
  );

-- Política RLS: Los empleados pueden ver todos los límites de alerta
CREATE POLICY "Users can view alert limits"
  ON alert_limits FOR SELECT
  USING (true);

-- Política RLS: Solo admins pueden insertar límites de alerta
CREATE POLICY "Only admins can create alert limits"
  ON alert_limits FOR INSERT
  WITH CHECK (
    auth.uid() IN (SELECT id FROM users_roles WHERE role = 'admin')
  );

-- Política RLS: Solo admins pueden actualizar límites de alerta
CREATE POLICY "Only admins can update alert limits"
  ON alert_limits FOR UPDATE
  USING (
    auth.uid() IN (SELECT id FROM users_roles WHERE role = 'admin')
  );

-- Política RLS: Solo admins pueden eliminar límites de alerta
CREATE POLICY "Only admins can delete alert limits"
  ON alert_limits FOR DELETE
  USING (
    auth.uid() IN (SELECT id FROM users_roles WHERE role = 'admin')
  );

-- Insertar datos de ejemplo (opcional)
-- INSERT INTO alert_limits (admin_id, sensor_type, min_value, max_value, safe_max)
-- SELECT id, 'ph', 6.5, 8.5, 8.0
-- FROM users_roles
-- WHERE role = 'admin'
-- LIMIT 1;
