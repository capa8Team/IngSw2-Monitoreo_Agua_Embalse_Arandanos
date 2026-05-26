-- Elimina un usuario de Supabase Auth y tablas publicas relacionadas.
-- Requiere FIX_USERS_ROLES_RLS_RECURSION.sql (función is_admin).
-- Idempotente. No falla si tablas opcionales (sensor_readings, alert_limits) no existen.

begin;

drop function if exists public.admin_delete_auth_user(uuid);

create function public.admin_delete_auth_user(target_user_id uuid)
returns boolean
language plpgsql
security definer
set search_path = public, auth
as $$
declare
  deleted_count int;
  tbl text;
begin
  if not public.is_admin() then
    raise exception 'Solo administradores pueden eliminar usuarios';
  end if;

  if target_user_id is null then
    raise exception 'ID de usuario invalido';
  end if;

  if target_user_id = auth.uid() then
    raise exception 'No puedes eliminar tu propia cuenta mientras estas conectado';
  end if;

  -- Tablas opcionales: solo borrar si existen en el proyecto
  foreach tbl in array array['alert_limits', 'sensor_readings'] loop
    if exists (
      select 1
      from information_schema.tables
      where table_schema = 'public'
        and table_name = tbl
    ) then
      execute format('delete from public.%I where user_id = $1', tbl)
      using target_user_id;
    end if;
  end loop;

  if exists (
    select 1 from information_schema.tables
    where table_schema = 'public' and table_name = 'users_roles'
  ) then
    delete from public.users_roles where id = target_user_id;
  end if;

  delete from auth.identities where user_id = target_user_id;
  delete from auth.users where id = target_user_id;

  get diagnostics deleted_count = row_count;

  return deleted_count > 0;
end;
$$;

revoke all on function public.admin_delete_auth_user(uuid) from public;
grant execute on function public.admin_delete_auth_user(uuid) to authenticated;

commit;
