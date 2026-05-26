# Scripts SQL — Supabase

## ¿Qué pasa si ejecuto otra vez?

| Script | ¿Re-ejecutar? | Qué ocurre |
|--------|---------------|------------|
| `FIX_USERS_ROLES_RLS_RECURSION.sql` | **Sí, seguro** | Idempotente: recrea políticas y el trigger sin error. |
| `ALTER_USERS_ROLES_EMPLOYEE.sql` | **Sí, seguro** | Quita y vuelve a crear el `CHECK` del rol. |
| `ADMIN_LIST_AUTH_USERS.sql` | **Sí** | Incluye `DROP FUNCTION` si cambió la firma. |
| `ADMIN_DELETE_AUTH_USER.sql` | **Sí** | Habilita botón Eliminar (Auth + `users_roles`). |
| `supabase_logs_schema.sql` | **Sí** (tablas) | `CREATE TABLE IF NOT EXISTS` no duplica tablas. Las políticas nuevas pueden fallar si ya existen con el mismo nombre. |
| `SUPABASE_SETUP.sql` | **Con cuidado** | Tablas: OK (`IF NOT EXISTS`). **Políticas y triggers**: si ya existen, PostgreSQL devuelve error del tipo *policy already exists*. No borra datos. |

### Recomendación práctica

1. Primera vez: `SUPABASE_SETUP.sql` → `FIX_USERS_ROLES_RLS_RECURSION.sql` → `ALTER_USERS_ROLES_EMPLOYEE.sql` → `ADMIN_LIST_AUTH_USERS.sql` → `ADMIN_DELETE_AUTH_USER.sql` → `SYNC_USERS_ROLES_FROM_AUTH.sql` (opcional).
2. Si solo corriges RLS o roles: ejecuta **solo** `FIX_...` y/o `ALTER_...`.
3. Si el frontend no muestra el total de Auth: ejecuta **`ADMIN_LIST_AUTH_USERS.sql`** (seguro re-ejecutar; incluye `DROP FUNCTION` si cambió la firma).
4. Error `cannot change return type`: vuelve a ejecutar **`ADMIN_LIST_AUTH_USERS.sql`** completo (ya trae el `DROP`).
5. Botón **Eliminar** no borra en Authentication: ejecuta **`ADMIN_DELETE_AUTH_USER.sql`**.
6. No vuelvas a ejecutar `SUPABASE_SETUP.sql` completo salvo que comentes o elimines las líneas `CREATE POLICY` que ya aplicaste.

Orden sugerido: **Setup → Fix RLS → Alter employee → Admin list Auth → Admin delete Auth**.
