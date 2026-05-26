-- Lista usuarios registrados en Supabase Auth (auth.users) para el panel admin.
-- Requiere haber ejecutado antes FIX_USERS_ROLES_RLS_RECURSION.sql (función is_admin).
-- Idempotente: puede ejecutarse varias veces (incluye DROP si cambió la firma).

begin;

-- Si ya existía la función sin is_verified, PostgreSQL exige DROP antes de cambiar el tipo de retorno.
drop function if exists public.admin_list_auth_users();

create function public.admin_list_auth_users()
returns table (
  id uuid,
  email text,
  full_name text,
  role text,
  created_at timestamptz,
  email_confirmed_at timestamptz,
  last_sign_in_at timestamptz,
  is_verified boolean
)
language plpgsql
security definer
set search_path = public, auth
as $$
begin
  if not public.is_admin() then
    raise exception 'Solo administradores pueden listar usuarios de Auth';
  end if;

  return query
  select
    u.id,
    u.email::text,
    coalesce(u.raw_user_meta_data->>'full_name', u.email::text)::text as full_name,
    coalesce(
      nullif(trim((select ur.role from public.users_roles ur where ur.id = u.id limit 1)), ''),
      nullif(trim(u.raw_user_meta_data->>'role'), ''),
      'employee'
    )::text as role,
    u.created_at,
    u.email_confirmed_at,
    u.last_sign_in_at,
    (u.email_confirmed_at is not null or u.last_sign_in_at is not null) as is_verified
  from auth.users u
  order by u.created_at desc nulls last;
end;
$$;

create or replace function public.admin_auth_users_count()
returns bigint
language plpgsql
security definer
set search_path = public, auth
as $$
declare
  total bigint;
begin
  if not public.is_admin() then
    raise exception 'Solo administradores pueden contar usuarios de Auth';
  end if;

  select count(*)::bigint into total from auth.users;
  return total;
end;
$$;

revoke all on function public.admin_list_auth_users() from public;
revoke all on function public.admin_auth_users_count() from public;
grant execute on function public.admin_list_auth_users() to authenticated;
grant execute on function public.admin_auth_users_count() to authenticated;

commit;

-- Verificación en el panel (no en SQL Editor sin sesión admin de la app):
-- Tras login admin en la app → Gestión de usuarios → Actualizar.
-- Debe coincidir con Authentication → Users (total y verificados tras confirmar email).
