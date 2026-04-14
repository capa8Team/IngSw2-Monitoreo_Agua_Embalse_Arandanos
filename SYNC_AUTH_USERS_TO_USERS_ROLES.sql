-- SYNC_AUTH_USERS_TO_USERS_ROLES.sql
-- Sincroniza usuarios de auth.users a la tabla users_roles
-- Ejecuta esto en Supabase SQL Editor

BEGIN;

-- 1) Copiar usuarios de auth.users a users_roles
INSERT INTO public.users_roles (id, email, full_name, role, created_at)
SELECT 
  au.id,
  au.email,
  COALESCE(au.raw_user_meta_data->>'full_name', au.email),
  CASE 
    WHEN au.email = 'admin@test.com' THEN 'admin'
    ELSE 'employee'
  END as role,
  au.created_at
FROM auth.users au
WHERE au.id NOT IN (SELECT id FROM public.users_roles)
  AND au.email IS NOT NULL
ON CONFLICT (id) DO UPDATE
SET 
  email = EXCLUDED.email,
  full_name = EXCLUDED.full_name,
  role = EXCLUDED.role,
  updated_at = NOW();

-- 2) Verificación: contar cuántos se sincronizaron
SELECT COUNT(*) as "Usuarios sincronizados en users_roles" 
FROM public.users_roles;

-- 3) Listar todos después de sincronizar
SELECT email, full_name, role, created_at 
FROM public.users_roles 
ORDER BY created_at DESC;

COMMIT;
