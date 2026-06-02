# Guía rápida: Postgres de Supabase desde Docker (Actividad de cuentas)
Write-Host @"

=== Actividad de cuentas / logs en Supabase ===

El host directo db.*.supabase.co usa IPv6. Docker en Windows suele fallar con
«Network is unreachable». Elige UNA de estas opciones:

OPCIÓN A (recomendada) — Session pooler (IPv4)
  1. Supabase Dashboard → Project Settings → Database → Connection string
  2. Modo: «Session pooler» (puerto 5432)
  3. Copia la URI completa y en .env agrega:
     SUPABASE_DB_POOLER_URL=postgresql+psycopg2://postgres.TU_PROYECTO:PASSWORD@HOST_POOLER:5432/postgres
  4. docker compose up --build -d backend

OPCIÓN B — Auto pooler (si conoces la región, p. ej. us-east-2)
  En .env:
     SUPABASE_DB_USE_POOLER=1
     SUPABASE_DB_POOLER_REGION=us-east-2
  (El host puede ser aws-0 o aws-1; si falla, usa OPCIÓN A.)

OPCIÓN C — IPv6 en Docker
  Este repo ya habilita IPv6 en docker-compose (red arandanos-network).
  Reinicia Docker Desktop y: docker compose down && docker compose up --build -d

Verifica:
  http://localhost:8000/api/diagnostics  →  logs_db.connected debe ser true

Tablas de logs (primera vez):
  Ejecuta database/supabase/supabase_logs_schema.sql en el SQL Editor de Supabase.

"@
