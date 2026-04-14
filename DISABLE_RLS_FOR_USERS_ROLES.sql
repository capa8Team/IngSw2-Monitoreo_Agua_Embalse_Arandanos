-- DISABLE_RLS_FOR_USERS_ROLES.sql
-- Desactiva RLS en users_roles para permitir lectura/escritura completa
-- Esto es temporal para debugging

-- OPCIÓN 1: DESACTIVAR RLS COMPLETAMENTE
ALTER TABLE public.users_roles DISABLE ROW LEVEL SECURITY;

SELECT 'RLS desactivado en users_roles' as status;

-- Verificar que ahora podemos leer todos los usuarios
SELECT COUNT(*) as total_usuarios FROM public.users_roles;
SELECT email, full_name, role FROM public.users_roles ORDER BY created_at DESC LIMIT 10;

-- NOTA: Si esto resuelve el problema, entonces el RLS era el culpable
-- Para volver a activar RLS después, ejecuta:
-- ALTER TABLE public.users_roles ENABLE ROW LEVEL SECURITY;
