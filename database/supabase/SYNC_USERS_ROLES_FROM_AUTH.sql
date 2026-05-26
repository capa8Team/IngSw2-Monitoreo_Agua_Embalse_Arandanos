-- Rellena users_roles con usuarios que existen en auth.users pero no tienen fila en users_roles.
-- Ejecutar una vez en SQL Editor (no borra datos). Idempotente.

begin;

insert into public.users_roles (id, email, full_name, role)
select
  u.id,
  u.email,
  coalesce(u.raw_user_meta_data->>'full_name', u.email),
  coalesce(
    nullif(trim(u.raw_user_meta_data->>'role'), ''),
    case when u.email ilike '%admin%' then 'admin' else 'employee' end
  )
from auth.users u
where not exists (
  select 1 from public.users_roles ur where ur.id = u.id
)
on conflict (id) do update
set
  email = excluded.email,
  full_name = excluded.full_name,
  updated_at = now();

commit;
