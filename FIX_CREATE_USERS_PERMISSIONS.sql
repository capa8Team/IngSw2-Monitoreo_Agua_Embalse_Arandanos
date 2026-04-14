-- FIX_CREATE_USERS_PERMISSIONS.sql
-- Arregla los permisos para que los admins puedan crear usuarios
-- Ejecuta esto en Supabase SQL Editor

-- PASO 1: Verificar que la función is_admin está correcta
CREATE OR REPLACE FUNCTION public.is_admin(_uid uuid DEFAULT auth.uid())
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT EXISTS (
    SELECT 1
    FROM public.users_roles ur
    WHERE ur.id = _uid
      AND ur.role = 'admin'
  );
$$;

-- PASO 2: Eliminar las políticas problemáticas
DROP POLICY IF EXISTS "select_own" ON public.users_roles;
DROP POLICY IF EXISTS "select_as_admin" ON public.users_roles;
DROP POLICY IF EXISTS "insert_as_admin" ON public.users_roles;
DROP POLICY IF EXISTS "update_as_admin" ON public.users_roles;
DROP POLICY IF EXISTS "delete_as_admin" ON public.users_roles;

-- PASO 3: Crear políticas NUEVAS correctas
-- Política SELECT: cualquier usuario autenticado puede ver su propio perfil o si es admin ve todos
CREATE POLICY "users_can_select_own_profile"
ON public.users_roles
FOR SELECT
TO authenticated
USING (auth.uid() = id);

CREATE POLICY "admins_can_select_all_users"
ON public.users_roles
FOR SELECT
TO authenticated
USING (public.is_admin());

-- Política INSERT: solo admins pueden insertar (para crear nuevos usuarios)
CREATE POLICY "admins_can_insert_users"
ON public.users_roles
FOR INSERT
TO authenticated
WITH CHECK (public.is_admin());

-- Política UPDATE: solo admins pueden actualizar
CREATE POLICY "admins_can_update_users"
ON public.users_roles
FOR UPDATE
TO authenticated
USING (public.is_admin())
WITH CHECK (public.is_admin());

-- Política DELETE: solo admins pueden eliminar
CREATE POLICY "admins_can_delete_users"
ON public.users_roles
FOR DELETE
TO authenticated
USING (public.is_admin());

SELECT 'Políticas de INSERT/UPDATE/DELETE recreadas correctamente para admins' as status;

-- PASO 4: Verificar que la tabla tiene RLS habilitado
ALTER TABLE public.users_roles ENABLE ROW LEVEL SECURITY;

SELECT 'RLS habilitado en users_roles' as status;

-- PASO 5: Verificar que el trigger existe y está activo
SELECT trigger_name FROM information_schema.triggers 
WHERE event_object_table = 'users_roles' AND trigger_name = 'on_auth_user_created';

-- PASO 6: Test - verificar que es_admin funciona
SELECT public.is_admin() as "¿Eres admin?" FROM public.users_roles LIMIT 1;
