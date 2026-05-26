# Cómo compartir tu configuración actual (sin exponer secretos)

No pegues claves (`anon key`, `service_role`, contraseñas) en chats ni en issues públicos.

## Plantilla para copiar y completar

```text
### Supabase SQL (marca lo que ya ejecutaste)
- [ ] SUPABASE_SETUP.sql (primera vez)
- [ ] FIX_USERS_ROLES_RLS_RECURSION.sql
- [ ] ALTER_USERS_ROLES_EMPLOYEE.sql
- [ ] ADMIN_LIST_AUTH_USERS.sql  ← necesario para el contador en el frontend

### Auth (Dashboard Supabase)
- Confirm email desactivado: sí / no
- Usuarios en Authentication → Users: ___ (número)
- Admin del panel (email): ___@___
- Ese admin existe en Supabase Auth: sí / no
- Rol en users_roles para ese admin: admin / otro

### Consultas SQL (pega solo resultados numéricos)
SELECT count(*) FROM auth.users;        → ___
SELECT count(*) FROM public.users_roles; → ___

### Frontend / Docker
- Corres con: npm run dev / Docker (puerto 5173)
- Archivo .env en raíz: sí / no (sin pegar valores)
- VITE_SUPABASE_URL configurada: sí / no
- Tras login, ¿ves aviso amarillo de sesión Supabase?: sí / no

### Error (si hay)
- Mensaje exacto en pantalla o consola (F12):
```

## Qué puedes adjuntar de forma segura

- Captura de **Authentication → Users** (tapa UUIDs si quieres).
- Captura del apartado **Gestión de usuarios** mostrando el total.
- Resultado de las dos consultas `count(*)` de arriba.
- Este archivo rellenado.

## Orden SQL recomendado ahora

Si ya hiciste el setup antes, ejecuta **solo** estos dos en el SQL Editor (en orden):

1. `database/supabase/FIX_USERS_ROLES_RLS_RECURSION.sql`
2. `database/supabase/ADMIN_LIST_AUTH_USERS.sql`

Opcional si falla rol `employee`: `ALTER_USERS_ROLES_EMPLOYEE.sql`
