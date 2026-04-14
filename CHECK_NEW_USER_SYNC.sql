-- CHECK_NEW_USER_SYNC.sql
-- Verifica si el nuevo usuario está en users_roles y en auth.users
-- Script simplificado para evitar errores

-- 1) Ver el usuario más reciente en auth.users
SELECT '[AUTH.USERS] Último usuario creado:' as info;
SELECT id, email, created_at FROM auth.users ORDER BY created_at DESC LIMIT 1;

-- 2) Ver si ese usuario está en users_roles
SELECT '[USERS_ROLES] Último usuario creado:' as info;
SELECT id, email, full_name, role, created_at FROM public.users_roles ORDER BY created_at DESC LIMIT 1;

-- 3) Contar totales
SELECT '[TOTALES]' as info;
SELECT COUNT(*) as "Usuarios en auth.users" FROM auth.users;
SELECT COUNT(*) as "Usuarios en users_roles" FROM public.users_roles;

-- 4) Comparar últimos 3 usuarios
SELECT '[ÚLTIMOS 3 USUARIOS - COMPARACIÓN]' as info;
SELECT 
  au.email as "Email en auth",
  ur.email as "Email en users_roles",
  CASE WHEN ur.id IS NOT NULL THEN '✅ Sincronizado' ELSE '❌ NO sincronizado' END as "Estado"
FROM auth.users au
LEFT JOIN public.users_roles ur ON au.id = ur.id
ORDER BY au.created_at DESC
LIMIT 3;

