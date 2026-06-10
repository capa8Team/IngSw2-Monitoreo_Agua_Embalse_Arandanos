-- Asigna user_organizations según organization_id en metadata de Auth al crear cuenta.
-- Si no hay metadata, mantiene fallback a embalse-arandanos.
-- Idempotente: ejecutar en Supabase SQL Editor.

begin;

create or replace function public.assign_default_organization()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
  v_org_id uuid;
  v_org_role text;
  v_meta_org text;
begin
  v_org_role := case
    when new.role in ('admin', 'administrador') then 'admin'
    else 'employee'
  end;

  select nullif(trim(u.raw_user_meta_data->>'organization_id'), '')
  into v_meta_org
  from auth.users u
  where u.id = new.id;

  if v_meta_org is not null then
    begin
      v_org_id := v_meta_org::uuid;
    exception
      when others then
        v_org_id := null;
    end;
  end if;

  if v_org_id is null then
    select o.id
    into v_org_id
    from public.organizations o
    where o.slug = coalesce(
      nullif(trim((
        select u.raw_user_meta_data->>'organization_slug'
        from auth.users u
        where u.id = new.id
      )), ''),
      'embalse-arandanos'
    )
    and o.active = true
    limit 1;
  end if;

  if v_org_id is not null then
    insert into public.user_organizations (user_id, organization_id, org_role)
    values (new.id, v_org_id, v_org_role)
    on conflict (user_id, organization_id) do update
    set org_role = excluded.org_role;
  end if;

  return new;
end;
$$;

commit;
