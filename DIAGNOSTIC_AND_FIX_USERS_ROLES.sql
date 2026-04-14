-- DIAGNOSTIC_AND_FIX_USERS_ROLES.sql
-- Script completo de diagnóstico y corrección
-- Ejecuta esto en Supabase SQL Editor

-- ==============================================================
-- PARTE 1: DIAGNÓSTICO
-- ==============================================================
SELECT '=== DIAGNÓSTICO ===' as estado;

-- 1) Ver cuántos usuarios en auth
SELECT 'Usuarios en auth.users' as check_item, COUNT(*) as cantidad
FROM auth.users;

-- 2) Ver cuántos usuarios en users_roles
SELECT 'Usuarios en users_roles' as check_item, COUNT(*) as cantidad
FROM public.users_roles;

-- 3) Ver si existe la función is_admin
SELECT 'Función is_admin existe' as check_item, 
  CASE WHEN EXISTS(
    SELECT 1 FROM pg_proc 
    WHERE proname = 'is_admin' 
    AND pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
  ) THEN 'SÍ' ELSE 'NO' END as resultado;

-- 4) Ver si existe el trigger
SELECT 'Trigger on_auth_user_created existe' as check_item,
  CASE WHEN EXISTS(
    SELECT 1 FROM information_schema.triggers 
    WHERE trigger_name = 'on_auth_user_created'
  ) THEN 'SÍ' ELSE 'NO' END as resultado;

-- 5) Ver las políticas RLS
SELECT 'Políticas RLS en users_roles:' as check_item;
SELECT policyname FROM pg_policies 
WHERE schemaname = 'public' AND tablename = 'users_roles';

-- ==============================================================
-- PARTE 2: CORRECCIÓN - RECREAR TRIGGER CORRECTAMENTE
-- ==============================================================

-- Paso 1: Recrear función handle_new_user
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_role text;
BEGIN
  v_role := COALESCE(new.raw_user_meta_data->>'role', 'employee');
  IF v_role NOT IN ('admin', 'employee', 'user') THEN
    v_role := 'employee';
  END IF;

  INSERT INTO public.users_roles (id, email, full_name, role)
  VALUES (
    new.id,
    new.email,
    COALESCE(new.raw_user_meta_data->>'full_name', new.email),
    v_role
  )
  ON CONFLICT (id) DO UPDATE
  SET
    email = EXCLUDED.email,
    full_name = EXCLUDED.full_name,
    role = EXCLUDED.role,
    updated_at = NOW();

  RETURN new;
END;
$$;

-- Paso 2: Eliminar trigger antiguo si existe
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;

-- Paso 3: Recrear trigger
CREATE TRIGGER on_auth_user_created
AFTER INSERT ON auth.users
FOR EACH ROW
EXECUTE FUNCTION public.handle_new_user();

SELECT 'Trigger recreado exitosamente' as status;

-- ==============================================================
-- PARTE 3: SIMPLIFICAR POLÍTICAS RLS (eliminar recursión)
-- ==============================================================

-- Verifica que is_admin exista, si no créala
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

-- Eliminar todas las políticas existentes
DO $$
DECLARE
  policy_record record;
BEGIN
  FOR policy_record IN
    SELECT policyname
    FROM pg_policies
    WHERE schemaname = 'public' AND tablename = 'users_roles'
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.users_roles', policy_record.policyname);
  END LOOP;
END $$;

-- Crear nuevas políticas SIMPLES sin recursión directa
CREATE POLICY "select_own" ON public.users_roles FOR SELECT
  USING (auth.uid() = id);

CREATE POLICY "select_as_admin" ON public.users_roles FOR SELECT
  USING (public.is_admin());

CREATE POLICY "insert_as_admin" ON public.users_roles FOR INSERT
  WITH CHECK (public.is_admin());

CREATE POLICY "update_as_admin" ON public.users_roles FOR UPDATE
  USING (public.is_admin());

CREATE POLICY "delete_as_admin" ON public.users_roles FOR DELETE
  USING (public.is_admin());

SELECT 'Políticas RLS recreadas exitosamente' as status;

-- ==============================================================
-- PARTE 4: SINCRONIZAR USUARIOS EXISTENTES
-- ==============================================================

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

SELECT 'Usuarios sincronizados' as status;

-- ==============================================================
-- PARTE 5: VERIFICACIÓN FINAL
-- ==============================================================
SELECT '=== VERIFICACIÓN FINAL ===' as estado;
SELECT email, full_name, role FROM public.users_roles ORDER BY created_at DESC;
