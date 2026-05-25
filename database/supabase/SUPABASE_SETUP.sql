-- ========================================
-- SUPABASE DATABASE SETUP SCRIPT
-- Sistema de Autenticación y Roles
-- ========================================

-- Tabla para almacenar roles de usuarios (users_roles)
CREATE TABLE IF NOT EXISTS users_roles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email TEXT NOT NULL UNIQUE,
  full_name TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'admin')),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabla para almacenar límites de alerta por usuario
CREATE TABLE IF NOT EXISTS alert_limits (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  ph_min DECIMAL(4, 2) DEFAULT 6.5,
  ph_max DECIMAL(4, 2) DEFAULT 8.5,
  temp_min DECIMAL(5, 2) DEFAULT 15,
  temp_max DECIMAL(5, 2) DEFAULT 30,
  conductivity_min DECIMAL(10, 2) DEFAULT 0,
  conductivity_max DECIMAL(10, 2) DEFAULT 2000,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(user_id)
);


-- Tabla de historial de sensores (opcional)
CREATE TABLE IF NOT EXISTS sensor_readings (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  device_id TEXT NOT NULL,
  sensor_name TEXT NOT NULL,
  value DECIMAL(10, 3) NOT NULL,
  unit TEXT NOT NULL,
  status TEXT DEFAULT 'normal' CHECK (status IN ('normal', 'warning', 'critical')),
  timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Crear índices para optimización
CREATE INDEX idx_users_roles_role ON users_roles(role);
CREATE INDEX idx_alert_limits_user_id ON alert_limits(user_id);
CREATE INDEX idx_sensor_readings_user_id ON sensor_readings(user_id);
CREATE INDEX idx_sensor_readings_timestamp ON sensor_readings(timestamp DESC);

-- Habilitar Row Level Security (RLS)
ALTER TABLE users_roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE alert_limits ENABLE ROW LEVEL SECURITY;
ALTER TABLE sensor_readings ENABLE ROW LEVEL SECURITY;

-- Políticas RLS para users_roles
CREATE POLICY "Usuarios pueden ver su propio perfil"
  ON users_roles FOR SELECT
  USING (auth.uid() = id);

CREATE POLICY "Admins pueden ver todos los usuarios"
  ON users_roles FOR SELECT
  USING (
    auth.uid() IN (SELECT id FROM users_roles WHERE role = 'admin')
  );

CREATE POLICY "Solo admin puede insertar usuarios"
  ON users_roles FOR INSERT
  WITH CHECK (
    auth.uid() IN (SELECT id FROM users_roles WHERE role = 'admin')
  );

CREATE POLICY "Solo admin puede actualizar roles"
  ON users_roles FOR UPDATE
  USING (
    auth.uid() IN (SELECT id FROM users_roles WHERE role = 'admin')
  );

-- Políticas RLS para alert_limits
CREATE POLICY "Usuarios pueden ver sus límites"
  ON alert_limits FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Admins pueden ver todos los límites"
  ON alert_limits FOR SELECT
  USING (
    auth.uid() IN (SELECT id FROM users_roles WHERE role = 'admin')
  );

CREATE POLICY "Admins pueden actualizar límites"
  ON alert_limits FOR UPDATE
  USING (
    auth.uid() IN (SELECT id FROM users_roles WHERE role = 'admin')
  );

-- Políticas RLS para sensor_readings
CREATE POLICY "Usuarios pueden ver sus lecturas"
  ON sensor_readings FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Admins pueden ver todas las lecturas"
  ON sensor_readings FOR SELECT
  USING (
    auth.uid() IN (SELECT id FROM users_roles WHERE role = 'admin')
  );

-- Crear función para manejar usuarios nuevos
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.users_roles (id, email, full_name, role)
  VALUES (new.id, new.email, COALESCE(new.raw_user_meta_data->>'full_name', new.email), 'user');
  RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

-- Trigger para crear entrada en users_roles cuando se crea un nuevo usuario
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Función para crear límites de alerta por defecto
CREATE OR REPLACE FUNCTION public.create_default_alert_limits()
RETURNS TRIGGER AS $$
DECLARE
  global_limits RECORD;
BEGIN
  IF NEW.role = 'user' THEN
    -- Leer límites globales
    SELECT ph_min, ph_max, temp_min, temp_max, conductivity_min, conductivity_max
    INTO global_limits
    FROM public.global_alert_limits
    LIMIT 1;
    
    -- Si no existen límites globales, usar valores por defecto
    IF global_limits IS NULL THEN
      INSERT INTO public.alert_limits (user_id, ph_min, ph_max, temp_min, temp_max, conductivity_min, conductivity_max)
      VALUES (NEW.id, 6.5, 8.5, 15, 30, 0, 2000)
      ON CONFLICT (user_id) DO NOTHING;
    ELSE
      -- Copiar límites globales al nuevo usuario
      INSERT INTO public.alert_limits (user_id, ph_min, ph_max, temp_min, temp_max, conductivity_min, conductivity_max)
      VALUES (NEW.id, global_limits.ph_min, global_limits.ph_max, global_limits.temp_min, global_limits.temp_max, global_limits.conductivity_min, global_limits.conductivity_max)
      ON CONFLICT (user_id) DO NOTHING;
    END IF;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger para crear límites de alerta por defecto
DROP TRIGGER IF EXISTS on_user_role_created ON users_roles;
CREATE TRIGGER on_user_role_created
  AFTER INSERT ON users_roles
  FOR EACH ROW EXECUTE FUNCTION public.create_default_alert_limits();

-- ========================================
-- DATOS DE PRUEBA (OPCIONAL)
-- ========================================

-- Usuario Admin de prueba (contraseña: demo123)
-- Nota: En una aplicación real, crear usuarios a través de la interfaz de autenticación
-- Este es solo para propósitos de demostración

-- Para crear usuarios de prueba:
-- 1. Ir a Supabase Dashboard > Authentication
-- 2. Click en "New user"
-- 3. Email: admin@demo.com, Password: demo123
-- 4. Luego ejecutar en SQL Editor:

-- INSERT INTO users_roles (id, email, full_name, role) 
-- VALUES ('<uuid-del-admin-aqui>', 'admin@demo.com', 'Admin Usuario', 'admin')
-- ON CONFLICT DO NOTHING;

-- INSERT INTO alert_limits (user_id, ph_min, ph_max, temp_min, temp_max, turbidity_max)
-- VALUES ('<uuid-del-admin-aqui>', 6.0, 9.0, 10, 40, 10)
-- ON CONFLICT (user_id) DO NOTHING;
-- 🔥 AGREGAR ESTA TABLA PARA LÍMITES GLOBALES (solo admin puede editar)
CREATE TABLE IF NOT EXISTS global_alert_limits (
  id BIGSERIAL PRIMARY KEY,
  ph_min DECIMAL(4, 2) DEFAULT 6.5,
  ph_max DECIMAL(4, 2) DEFAULT 8.5,
  temp_min DECIMAL(5, 2) DEFAULT 15,
  temp_max DECIMAL(5, 2) DEFAULT 30,
  conductivity_min DECIMAL(10, 2) DEFAULT 0,
  conductivity_max DECIMAL(10, 2) DEFAULT 2000,
  updated_by UUID REFERENCES auth.users(id),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Política RLS: Solo admin puede editar límites globales
CREATE POLICY "Solo admin puede editar límites globales"
  ON global_alert_limits FOR UPDATE
  USING (
    auth.uid() IN (SELECT id FROM users_roles WHERE role = 'admin')
  );

-- Insertar registro inicial de límites globales
INSERT INTO public.global_alert_limits (ph_min, ph_max, temp_min, temp_max, conductivity_min, conductivity_max)
VALUES (6.5, 8.5, 15, 30, 0, 2000)
ON CONFLICT DO NOTHING;
