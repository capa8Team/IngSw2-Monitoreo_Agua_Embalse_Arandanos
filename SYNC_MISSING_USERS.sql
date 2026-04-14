-- SYNC_MISSING_USERS.sql
-- Sincroniza los usuarios que están en auth.users pero NO en users_roles

INSERT INTO public.users_roles (id, email, full_name, role, created_at)
SELECT 
  au.id,
  au.email,
  COALESCE(au.raw_user_meta_data->>'full_name', au.email),
  COALESCE(au.raw_user_meta_data->>'role', 'employee'),
  au.created_at
FROM auth.users au
WHERE au.id NOT IN (SELECT id FROM public.users_roles)
ON CONFLICT (id) DO UPDATE
SET 
  email = EXCLUDED.email,
  full_name = EXCLUDED.full_name,
  role = EXCLUDED.role,
  updated_at = NOW();

SELECT 'Sincronización completada' as status;

-- Verificar que todos están sincronizados ahora
SELECT 
  au.email,
  CASE WHEN ur.id IS NOT NULL THEN '✅ Sincronizado' ELSE '❌ NO sincronizado' END as Estado
FROM auth.users au
LEFT JOIN public.users_roles ur ON au.id = ur.id
ORDER BY au.created_at DESC;
