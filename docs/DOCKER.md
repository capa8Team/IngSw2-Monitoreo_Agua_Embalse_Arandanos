# Docker — Monitoreo Embalse Arándanos

## Requisitos

- Docker Desktop (o Docker Engine + Compose v2)
- Archivo `.env` en la **raíz del repo** (copiar desde `.env.example`)

Variables mínimas recomendadas:

```env
VITE_SUPABASE_URL=https://tu-proyecto.supabase.co
VITE_SUPABASE_ANON_KEY=tu-anon-key
VITE_DATA_MODE=simulated
JWT_SECRET=un-secreto-largo-y-aleatorio
AUTH_DEMO_PASSWORD=123456789
MONGO_ROOT_PASSWORD=Panconpalta1
```

`VITE_API_URL` debe quedar **vacío** en Docker: el frontend llama a `/api/...` y nginx reenvía al backend.

## Levantar el sistema

```bash
docker compose up --build -d
```

| Servicio   | URL en el host        |
|-----------|------------------------|
| Frontend  | http://localhost:5173 |
| API       | http://localhost:8000 |
| MongoDB   | localhost:27017       |

Login demo (JWT): correo con `admin` → administrador; contraseña = `AUTH_DEMO_PASSWORD` (por defecto `123456789`).

Para **gestión de usuarios en Supabase**, el mismo correo/contraseña debe existir en Supabase Auth con rol `admin` en `users_roles`.

## Comandos útiles

```bash
docker compose ps
docker compose logs -f backend
docker compose logs -f frontend
docker compose down
docker compose down -v   # borra volúmenes (Mongo)
```

## PostgreSQL opcional (legado)

```bash
docker compose --profile postgres up -d database
```

## Supabase SQL

Ver `database/supabase/README.md` sobre qué scripts son idempotentes y cuáles no.
