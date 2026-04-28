# =============================================================================
# build-push-all.ps1
# Buildea y pushea las imagenes del frontend Y backend a Docker Hub.
# Usar cuando la integracion con GitHub en Dokploy no esta disponible.
#
# Uso:
#   .\build-push-all.ps1 -DockerHubUser "doriajacke"
#
# Requiere Docker Desktop corriendo y sesion iniciada:
#   docker login
# =============================================================================

param(
    [Parameter(Mandatory=$true)]
    [string]$DockerHubUser,

    [string]$Tag = "latest",

    [string]$ViteSupabaseUrl     = $env:VITE_SUPABASE_URL,
    [string]$ViteSupabaseAnonKey = $env:VITE_SUPABASE_ANON_KEY,
    [string]$ViteApiUrl          = "",
    [string]$ViteDataMode        = "real"
)

$ErrorActionPreference = "Stop"

# --- Leer .env local si las variables estan vacias ----------------------------
if ((-not $ViteSupabaseUrl) -or (-not $ViteSupabaseAnonKey)) {
    if (Test-Path ".env") {
        Write-Host "Leyendo variables desde .env local..." -ForegroundColor Cyan
        Get-Content ".env" | ForEach-Object {
            if ($_ -match "^VITE_SUPABASE_URL=(.+)$")      { $ViteSupabaseUrl     = $Matches[1].Trim() }
            if ($_ -match "^VITE_SUPABASE_ANON_KEY=(.+)$") { $ViteSupabaseAnonKey = $Matches[1].Trim() }
        }
    }
}

if (-not $ViteSupabaseUrl) {
    Write-Error "VITE_SUPABASE_URL no definida."
    exit 1
}
if (-not $ViteSupabaseAnonKey) {
    Write-Error "VITE_SUPABASE_ANON_KEY no definida."
    exit 1
}

$FRONTEND_IMAGE = "$DockerHubUser/arandanos-frontend:$Tag"
$BACKEND_IMAGE  = "$DockerHubUser/arandanos-backend:$Tag"

# =============================================================================
# FRONTEND
# =============================================================================
Write-Host ""
Write-Host "=============================================" -ForegroundColor Green
Write-Host "  [1/4] Buildeando FRONTEND: $FRONTEND_IMAGE" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green

$frontendBuildArgs = @(
    "build",
    "-f", "Dockerfile.frontend",
    "--build-arg", "VITE_API_URL=$ViteApiUrl",
    "--build-arg", "VITE_DATA_MODE=$ViteDataMode",
    "--build-arg", "VITE_SUPABASE_URL=$ViteSupabaseUrl",
    "--build-arg", "VITE_SUPABASE_ANON_KEY=$ViteSupabaseAnonKey",
    "-t", $FRONTEND_IMAGE,
    "."
)

& docker @frontendBuildArgs
if ($LASTEXITCODE -ne 0) { Write-Error "docker build frontend fallo"; exit 1 }

Write-Host ""
Write-Host "  [2/4] Pusheando FRONTEND..." -ForegroundColor Cyan
& docker push $FRONTEND_IMAGE
if ($LASTEXITCODE -ne 0) { Write-Error "docker push frontend fallo"; exit 1 }

# =============================================================================
# BACKEND
# =============================================================================
Write-Host ""
Write-Host "=============================================" -ForegroundColor Green
Write-Host "  [3/4] Buildeando BACKEND: $BACKEND_IMAGE" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green

$backendBuildArgs = @(
    "build",
    "-f", "backend_fastapi/Dockerfile",
    "--build-context", "backend=backend_fastapi",
    "-t", $BACKEND_IMAGE,
    "backend_fastapi"
)

& docker @backendBuildArgs
if ($LASTEXITCODE -ne 0) { Write-Error "docker build backend fallo"; exit 1 }

Write-Host ""
Write-Host "  [4/4] Pusheando BACKEND..." -ForegroundColor Cyan
& docker push $BACKEND_IMAGE
if ($LASTEXITCODE -ne 0) { Write-Error "docker push backend fallo"; exit 1 }

# =============================================================================
# RESUMEN
# =============================================================================
Write-Host ""
Write-Host "=============================================" -ForegroundColor Green
Write-Host "  Todo pusheado exitosamente!" -ForegroundColor Green
Write-Host ""
Write-Host "  $FRONTEND_IMAGE" -ForegroundColor Yellow
Write-Host "  $BACKEND_IMAGE" -ForegroundColor Yellow
Write-Host ""
Write-Host "  En Dokploy > Environment Variables agregar:" -ForegroundColor Cyan
Write-Host "    FRONTEND_IMAGE=$FRONTEND_IMAGE" -ForegroundColor White
Write-Host "    BACKEND_IMAGE=$BACKEND_IMAGE" -ForegroundColor White
Write-Host "    MONGODB_URL=<tu-url-mongodb-atlas>" -ForegroundColor White
Write-Host "    JWT_SECRET=<secreto-largo>" -ForegroundColor White
Write-Host ""
Write-Host "  Compose file a usar: docker-compose.dokploy.prebuilt.yml" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Green
