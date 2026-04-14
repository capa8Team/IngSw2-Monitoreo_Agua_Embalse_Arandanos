-- FIX_USERS_ROLES_RLS_RECURSION.sql
-- Ejecuta este script en Supabase SQL Editor para corregir:
-- "infinite recursion detected in policy for relation users_roles"

begin;

-- 0) Trigger de alta de auth.users -> users_roles con rol desde metadata
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
  v_role text;
begin
  v_role := coalesce(new.raw_user_meta_data->>'role', 'employee');
  if v_role not in ('admin', 'employee', 'user') then
    v_role := 'employee';
  end if;

  insert into public.users_roles (id, email, full_name, role)
  values (
    new.id,
    new.email,
    coalesce(new.raw_user_meta_data->>'full_name', new.email),
    v_role
  )
  on conflict (id) do update
  set
    email = excluded.email,
    full_name = excluded.full_name,
    role = excluded.role,
    updated_at = now();

  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
after insert on auth.users
for each row execute function public.handle_new_user();

-- 1) Funcion helper para verificar si el usuario autenticado es admin.
-- SECURITY DEFINER evita recursion al consultar users_roles dentro de la propia politica.
create or replace function public.is_admin(_uid uuid default auth.uid())
returns boolean
language sql
security definer
set search_path = public
as $$
  select exists (
    select 1
    from public.users_roles ur
    where ur.id = _uid
      and ur.role = 'admin'
  );
$$;

revoke all on function public.is_admin(uuid) from public;
grant execute on function public.is_admin(uuid) to authenticated;

-- 2) Reemplazar politicas de users_roles que generan recursion.
drop policy if exists "Usuarios pueden ver su propio perfil" on public.users_roles;
drop policy if exists "Admins pueden ver todos los usuarios" on public.users_roles;
drop policy if exists "Solo admin puede insertar usuarios" on public.users_roles;
drop policy if exists "Solo admin puede actualizar roles" on public.users_roles;
drop policy if exists "Solo admin puede eliminar usuarios" on public.users_roles;

create policy "users_roles_select_own"
on public.users_roles
for select
to authenticated
using (auth.uid() = id);

create policy "users_roles_select_admin"
on public.users_roles
for select
to authenticated
using (public.is_admin());

create policy "users_roles_insert_admin"
on public.users_roles
for insert
to authenticated
with check (public.is_admin());

create policy "users_roles_update_admin"
on public.users_roles
for update
to authenticated
using (public.is_admin())
with check (public.is_admin());

create policy "users_roles_delete_admin"
on public.users_roles
for delete
to authenticated
using (public.is_admin());

-- 3) Ajustar otras politicas relacionadas para usar helper y evitar subconsultas repetidas.
drop policy if exists "Admins pueden ver todos los límites" on public.alert_limits;
drop policy if exists "Admins pueden actualizar límites" on public.alert_limits;
drop policy if exists "Solo admin puede editar límites globales" on public.alert_limits;
drop policy if exists "Only admins can create alert limits" on public.alert_limits;
drop policy if exists "Only admins can update alert limits" on public.alert_limits;
drop policy if exists "Only admins can delete alert limits" on public.alert_limits;
drop policy if exists "Admins can view all alert limits" on public.alert_limits;
drop policy if exists "Admins can manage their alert limits" on public.alert_limits;

do $$
begin
  if not exists (
    select 1 from pg_policies
    where schemaname = 'public'
      and tablename = 'alert_limits'
      and policyname = 'alert_limits_select_admin'
  ) then
    create policy "alert_limits_select_admin"
    on public.alert_limits
    for select
    to authenticated
    using (public.is_admin());
  end if;

  if not exists (
    select 1 from pg_policies
    where schemaname = 'public'
      and tablename = 'alert_limits'
      and policyname = 'alert_limits_insert_admin'
  ) then
    create policy "alert_limits_insert_admin"
    on public.alert_limits
    for insert
    to authenticated
    with check (public.is_admin());
  end if;

  if not exists (
    select 1 from pg_policies
    where schemaname = 'public'
      and tablename = 'alert_limits'
      and policyname = 'alert_limits_update_admin'
  ) then
    create policy "alert_limits_update_admin"
    on public.alert_limits
    for update
    to authenticated
    using (public.is_admin())
    with check (public.is_admin());
  end if;

  if not exists (
    select 1 from pg_policies
    where schemaname = 'public'
      and tablename = 'alert_limits'
      and policyname = 'alert_limits_delete_admin'
  ) then
    create policy "alert_limits_delete_admin"
    on public.alert_limits
    for delete
    to authenticated
    using (public.is_admin());
  end if;
end $$;

-- 4) Verificacion rapida
-- select public.is_admin(auth.uid()) as am_i_admin;

commit;
