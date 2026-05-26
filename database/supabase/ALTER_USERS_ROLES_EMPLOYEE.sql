-- Permite el rol "employee" en users_roles (además de user y admin).
-- Ejecutar en Supabase SQL Editor si la creación de trabajadores falla por CHECK constraint.

begin;

alter table public.users_roles drop constraint if exists users_roles_role_check;

alter table public.users_roles
  add constraint users_roles_role_check
  check (role in ('user', 'admin', 'employee'));

commit;
