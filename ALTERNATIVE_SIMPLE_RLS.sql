-- ALTERNATIVE_SIMPLE_RLS.sql
-- Si el script anterior no funciona, usa este para simplificar al máximo
-- Desactiva RLS temporalmente para debugging

-- OPCIÓN 1: DESACTIVAR RLS COMPLETAMENTE (más inseguro pero útil para debug)
ALTER TABLE public.users_roles DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.alert_limits DISABLE ROW LEVEL SECURITY;

SELECT 'RLS desactivado - ahora todos los usuarios autenticados pueden aceder' as status;

-- OPCIÓN 2: O si quieres volver a activar RLS después
-- ALTER TABLE public.users_roles ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.alert_limits ENABLE ROW LEVEL SECURITY;

-- Verifica que puedes acceder
SELECT email, full_name, role FROM public.users_roles LIMIT 10;
