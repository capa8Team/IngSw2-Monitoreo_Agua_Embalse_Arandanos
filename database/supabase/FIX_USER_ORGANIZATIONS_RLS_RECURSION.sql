-- Corrige: infinite recursion detected in policy for relation "user_organizations"
-- Idempotente: puede ejecutarse varias veces en Supabase SQL Editor.

begin;

-- Helper: ¿el usuario es admin de la organización?
create or replace function public.is_org_admin(
  _organization_id uuid,
  _uid uuid default auth.uid()
)
returns boolean
language sql
security definer
set search_path = public
as $$
  select exists (
    select 1
    from public.user_organizations uo
    where uo.user_id = _uid
      and uo.organization_id = _organization_id
      and uo.org_role = 'admin'
  );
$$;

revoke all on function public.is_org_admin(uuid, uuid) from public;
grant execute on function public.is_org_admin(uuid, uuid) to authenticated;

-- IDs de organizaciones del usuario (evita subconsultas recursivas en políticas)
create or replace function public.user_organization_ids(_uid uuid default auth.uid())
returns setof uuid
language sql
security definer
set search_path = public
stable
as $$
  select uo.organization_id
  from public.user_organizations uo
  where uo.user_id = _uid;
$$;

revoke all on function public.user_organization_ids(uuid) from public;
grant execute on function public.user_organization_ids(uuid) to authenticated;

-- Eliminar políticas existentes de user_organizations
do $$
declare
  policy_record record;
begin
  for policy_record in
    select policyname
    from pg_policies
    where schemaname = 'public'
      and tablename = 'user_organizations'
  loop
    execute 'drop policy if exists "' || policy_record.policyname || '" on public.user_organizations';
  end loop;
end $$;

create policy "user_organizations_select_own"
  on public.user_organizations for select
  to authenticated
  using (auth.uid() = user_id);

create policy "user_organizations_select_org_admin"
  on public.user_organizations for select
  to authenticated
  using (public.is_org_admin(organization_id));

create policy "user_organizations_insert_org_admin"
  on public.user_organizations for insert
  to authenticated
  with check (public.is_org_admin(organization_id));

create policy "user_organizations_update_org_admin"
  on public.user_organizations for update
  to authenticated
  using (public.is_org_admin(organization_id))
  with check (public.is_org_admin(organization_id));

create policy "user_organizations_delete_org_admin"
  on public.user_organizations for delete
  to authenticated
  using (public.is_org_admin(organization_id));

-- organizations: lectura sin recursión
do $$
declare
  policy_record record;
begin
  for policy_record in
    select policyname
    from pg_policies
    where schemaname = 'public'
      and tablename = 'organizations'
  loop
    execute 'drop policy if exists "' || policy_record.policyname || '" on public.organizations';
  end loop;
end $$;

create policy "organizations_select_member"
  on public.organizations for select
  to authenticated
  using (id in (select public.user_organization_ids()));

commit;
