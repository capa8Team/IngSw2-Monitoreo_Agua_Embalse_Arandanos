-- FIX_TRIGGER_PERMISSIONS.sql
-- Arregla el trigger para que pueda insertar usuarios sin permisos RLS
-- Ejecuta esto en Supabase SQL Editor

-- PASO 1: Recrear la función handle_new_user CON PERMISOS ESPECIALES
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_role text;
  v_result record;
BEGIN
  BEGIN
    v_role := COALESCE(new.raw_user_meta_data->>'role', 'employee');
    IF v_role NOT IN ('admin', 'employee', 'user') THEN
      v_role := 'employee';
    END IF;

    -- Insertar el nuevo usuario en users_roles (sin restricciones RLS porque tiene SECURITY DEFINER)
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

    RAISE LOG 'Usuario % creado en users_roles con rol %', new.email, v_role;
  EXCEPTION WHEN OTHERS THEN
    RAISE LOG 'Error en handle_new_user para %: %', new.email, SQLERRM;
    -- No lanzar error, solo logear para que el usuario se cree en auth de todas formas
  END;

  RETURN new;
END;
$$;

-- PASO 2: Recrear el trigger asegurando que existe
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;

CREATE TRIGGER on_auth_user_created
AFTER INSERT ON auth.users
FOR EACH ROW
EXECUTE FUNCTION public.handle_new_user();

SELECT 'Trigger recreado con SECURITY DEFINER correcto' as status;

-- PASO 3: ALTERNATIVA: Si el RLS sigue siendo problema, deshabilitar temporalmente
-- Descomenta la siguiente línea si el error persiste:
-- ALTER TABLE public.users_roles DISABLE ROW LEVEL SECURITY;

-- PASO 4: Verificación - contar usuarios
SELECT COUNT(*) as total_usuarios FROM public.users_roles;
