-- Primer inicio de sesión: el usuario debe definir su contraseña en Supabase Auth
begin;

alter table public.users_roles
  add column if not exists must_set_password boolean not null default false;

-- Sincronizar flag desde metadata al crear usuario en Auth
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
  v_role text;
  v_must_set_password boolean;
begin
  v_role := coalesce(new.raw_user_meta_data->>'role', 'employee');
  if v_role not in ('admin', 'employee', 'user') then
    v_role := 'employee';
  end if;

  v_must_set_password := coalesce(
    (new.raw_user_meta_data->>'must_set_password')::boolean,
    false
  );

  insert into public.users_roles (id, email, full_name, role, must_set_password)
  values (
    new.id,
    new.email,
    coalesce(new.raw_user_meta_data->>'full_name', new.email),
    v_role,
    v_must_set_password
  )
  on conflict (id) do update
  set
    email = excluded.email,
    full_name = excluded.full_name,
    role = excluded.role,
    must_set_password = excluded.must_set_password,
    updated_at = now();

  return new;
end;
$$;

commit;
