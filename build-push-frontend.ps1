# =============================================================================
# build-push-frontend.ps1
# Buildea la imagen Docker del frontend con las variables de entorno de
# produccion y la pushea a Docker Hub para deploy en Dokploy.
#
# Uso:
#   .\build-push-frontend.ps1 -DockerHubUser "tu-usuario" -Tag "latest"
#
# Requiere tener Docker Desktop corriendo y sesion iniciada en Docker Hub:
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
    Write-Error "VITE_SUPABASE_URL no definida. Agrega -ViteSupabaseUrl o definela en .env"
    exit 1
}
if (-not $ViteSupabaseAnonKey) {
    Write-Error "VITE_SUPABASE_ANON_KEY no definida. Agrega -ViteSupabaseAnonKey o definela en .env"
    exit 1
}

$IMAGE = "$DockerHubUser/arandanos-frontend:$Tag"

Write-Host ""
Write-Host "=============================================" -ForegroundColor Green
Write-Host "  Buildeando imagen: $IMAGE" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
Write-Host "  VITE_SUPABASE_URL  : $ViteSupabaseUrl"
Write-Host "  VITE_DATA_MODE     : $ViteDataMode"
Write-Host "  VITE_API_URL       : (vacio - nginx proxy interno)"
Write-Host ""

# Armar argumentos como array para evitar problemas con comillas en PowerShell
$buildArgs = @(
    "build",
    "-f", "Dockerfile.frontend",
    "--build-arg", "VITE_API_URL=$ViteApiUrl",
    "--build-arg", "VITE_DATA_MODE=$ViteDataMode",
    "--build-arg", "VITE_SUPABASE_URL=$ViteSupabaseUrl",
    "--build-arg", "VITE_SUPABASE_ANON_KEY=$ViteSupabaseAnonKey",
    "-t", $IMAGE,
    "."
)

& docker @buildArgs

if ($LASTEXITCODE -ne 0) {
    Write-Error "docker build fallo"
    exit 1
}

Write-Host ""
Write-Host "Pusheando $IMAGE a Docker Hub..." -ForegroundColor Cyan
& docker push $IMAGE

if ($LASTEXITCODE -ne 0) {
    Write-Error "docker push fallo. Ejecuta 'docker login' primero"
    exit 1
}

Write-Host ""
Write-Host "=============================================" -ForegroundColor Green
Write-Host "  Imagen pusheada exitosamente!" -ForegroundColor Green
Write-Host "  $IMAGE" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Siguiente paso:" -ForegroundColor Cyan
Write-Host "  En Dokploy usa docker-compose.dokploy.prebuilt.yml" -ForegroundColor Cyan
Write-Host "  y setea FRONTEND_IMAGE=$IMAGE" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Green
