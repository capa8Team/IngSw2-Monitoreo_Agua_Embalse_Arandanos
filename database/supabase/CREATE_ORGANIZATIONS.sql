-- ============================================================

-- MULTI-ORGANIZACIÓN

-- Ejecutar en Supabase SQL Editor (una sola vez)

-- Roles de app: administrador y trabajador (users_roles)

-- ============================================================



begin;



-- 1. Organizaciones (PYMEs, empresas, instituciones)

create table if not exists public.organizations (

  id          uuid primary key default gen_random_uuid(),

  name        text not null,

  slug        text not null unique,

  active      boolean not null default true,

  created_at  timestamptz not null default now(),

  updated_at  timestamptz not null default now()

);



-- 2. Membresía usuario ↔ organización

create table if not exists public.user_organizations (

  id              uuid primary key default gen_random_uuid(),

  user_id         uuid not null references auth.users(id) on delete cascade,

  organization_id uuid not null references public.organizations(id) on delete cascade,

  org_role        text not null default 'employee'

    check (org_role in ('admin', 'employee')),

  created_at      timestamptz not null default now(),

  unique (user_id, organization_id)

);



create index if not exists idx_user_organizations_user

  on public.user_organizations(user_id);

create index if not exists idx_user_organizations_org

  on public.user_organizations(organization_id);



-- 3. Organización por defecto (datos actuales del sistema)

insert into public.organizations (name, slug)

values ('Embalse Arándanos', 'embalse-arandanos')

on conflict (slug) do nothing;



-- 4. Asignar usuarios existentes a Embalse Arándanos

insert into public.user_organizations (user_id, organization_id, org_role)

select

  ur.id,

  o.id,

  case when ur.role in ('admin', 'administrador') then 'admin' else 'employee' end

from public.users_roles ur

cross join public.organizations o

where o.slug = 'embalse-arandanos'

on conflict (user_id, organization_id) do nothing;



-- 5. RLS

alter table public.organizations enable row level security;

alter table public.user_organizations enable row level security;



drop policy if exists "usuarios_ven_sus_orgs" on public.user_organizations;

create policy "usuarios_ven_sus_orgs"

  on public.user_organizations for select

  using (auth.uid() = user_id);



drop policy if exists "usuarios_ven_orgs_asignadas" on public.organizations;

create policy "usuarios_ven_orgs_asignadas"

  on public.organizations for select

  using (

    id in (

      select organization_id

      from public.user_organizations

      where user_id = auth.uid()

    )

  );



drop policy if exists "org_admin_ve_miembros" on public.user_organizations;

create policy "org_admin_ve_miembros"

  on public.user_organizations for select

  using (

    organization_id in (

      select organization_id

      from public.user_organizations

      where user_id = auth.uid() and org_role = 'admin'

    )

  );



drop policy if exists "org_admin_asigna_miembros" on public.user_organizations;

create policy "org_admin_asigna_miembros"

  on public.user_organizations for insert

  with check (

    organization_id in (

      select organization_id

      from public.user_organizations

      where user_id = auth.uid() and org_role = 'admin'

    )

  );



-- Nuevos usuarios en users_roles → Embalse Arándanos si no tienen organización

create or replace function public.assign_default_organization()

returns trigger

language plpgsql

security definer

set search_path = public

as $$

begin

  insert into public.user_organizations (user_id, organization_id, org_role)

  select

    new.id,

    o.id,

    case when new.role in ('admin', 'administrador') then 'admin' else 'employee' end

  from public.organizations o

  where o.slug = 'embalse-arandanos'

  on conflict (user_id, organization_id) do nothing;

  return new;

end;

$$;



drop trigger if exists trg_assign_default_organization on public.users_roles;

create trigger trg_assign_default_organization

  after insert on public.users_roles

  for each row

  execute function public.assign_default_organization();



commit;


