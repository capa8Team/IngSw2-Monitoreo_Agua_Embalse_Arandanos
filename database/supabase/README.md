# Scripts SQL — Supabase

Scripts activos para el sistema actual (multi-organización, auth, alertas, logs).

## Orden sugerido (instalación nueva)

1. `CREATE_ORGANIZATIONS.sql` — tablas `organizations`, `user_organizations`, RLS y org por defecto
2. `CREATE_ALERT_LIMITS_TABLE.sql` — tabla `alert_limits` (esquema `admin_id` + `sensor_type`)
3. `FIX_USERS_ROLES_RLS_RECURSION.sql` — trigger `handle_new_user`, políticas RLS (idempotente)
3b. `FIX_USER_ORGANIZATIONS_RLS_RECURSION.sql` — políticas RLS de `user_organizations` (idempotente)
4. `ALTER_USERS_ROLES_MUST_SET_PASSWORD.sql` — columna `must_set_password` para primer acceso
5. `ADMIN_LIST_AUTH_USERS.sql` — RPC listado de usuarios Auth (panel admin)
6. `ADMIN_DELETE_AUTH_USER.sql` — RPC borrado de usuarios en Auth
7. `UPDATE_ASSIGN_ORG_FROM_METADATA.sql` — asigna org al crear usuario según metadata del admin
8. `supabase_logs_schema.sql` — tablas de logs de actividad
9. `CREATE_NEW_ORGANIZATION_AND_ADMIN.sql` — plantilla paso a paso: nueva org + admin inicial

## Re-ejecución segura

| Script | ¿Re-ejecutar? |
|--------|---------------|
| `FIX_USERS_ROLES_RLS_RECURSION.sql` | Sí |
| `FIX_USER_ORGANIZATIONS_RLS_RECURSION.sql` | Sí |
| `UPDATE_ASSIGN_ORG_FROM_METADATA.sql` | Sí |
| `ALTER_USERS_ROLES_MUST_SET_PASSWORD.sql` | Sí (`IF NOT EXISTS`) |
| `ADMIN_LIST_AUTH_USERS.sql` | Sí (incluye `DROP FUNCTION`) |
| `ADMIN_DELETE_AUTH_USER.sql` | Sí |
| `supabase_logs_schema.sql` | Sí (tablas con `IF NOT EXISTS`) |
| `CREATE_ORGANIZATIONS.sql` | Con cuidado (usa `IF NOT EXISTS` en tablas) |
| `CREATE_ALERT_LIMITS_TABLE.sql` | **No** en producción — hace `DROP TABLE` |

## Referencias en código

- `ADMIN_LIST_AUTH_USERS.sql`, `FIX_USERS_ROLES_RLS_RECURSION.sql`, `ADMIN_DELETE_AUTH_USER.sql` → `src/services/SupabaseAuthService.js`
- `supabase_logs_schema.sql` → `backend_fastapi/routers/admin_activity.py`
