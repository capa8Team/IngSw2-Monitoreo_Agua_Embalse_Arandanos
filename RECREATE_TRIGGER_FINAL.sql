-- RECREATE_TRIGGER_FINAL.sql
-- Recrea el trigger handle_new_user correctamente

-- PASO 1: Recrear la función
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

-- PASO 2: Eliminar el trigger si existe
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;

-- PASO 3: Crear el trigger
CREATE TRIGGER on_auth_user_created
AFTER INSERT ON auth.users
FOR EACH ROW
EXECUTE FUNCTION public.handle_new_user();

SELECT 'Trigger recreado exitosamente' as status;
