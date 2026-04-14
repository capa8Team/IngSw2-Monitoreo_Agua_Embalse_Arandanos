-- DEBUG_USERS_ROLES.sql
-- Ejecuta esto en Supabase SQL Editor para diagnosticar el problema

-- 1) Ver cuántos usuarios existen en la tabla
SELECT 'Total usuarios en users_roles' as diagnostico, COUNT(*) as cantidad
FROM public.users_roles;

-- 2) Listar todos los usuarios (ignorando RLS temporalmente)
SET row_security TO OFF;
SELECT id, email, full_name, role, created_at FROM public.users_roles ORDER BY created_at DESC;
SET row_security TO ON;

-- 3) Verificar si la función is_admin existe
SELECT routine_name, routine_type FROM information_schema.routines 
WHERE routine_schema = 'public' AND routine_name = 'is_admin';

-- 4) Ver todas las políticas en users_roles
SELECT policyname, qual, with_check FROM pg_policies 
WHERE schemaname = 'public' AND tablename = 'users_roles'
ORDER BY policyname;

-- 5) Verificar el trigger
SELECT trigger_name, event_manipulation, event_object_table 
FROM information_schema.triggers 
WHERE trigger_schema = 'public' AND event_object_table = 'users_roles';

-- 6) Si necesitas ver TODOS los usuarios directamente (sin considerar RLS)
-- Descomenta esto para un SUPER ADMIN QUERY:
-- SELECT * FROM auth.users LIMIT 10;
-- SELECT * FROM public.users_roles LIMIT 10;
