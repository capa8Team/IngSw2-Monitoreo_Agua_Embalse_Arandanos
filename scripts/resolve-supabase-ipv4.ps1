# Resuelve IPv4 del host Supabase y sugiere SUPABASE_DB_HOSTADDR para .env (Docker sin IPv6).
param(
    [string]$HostName = "db.ithzvwlpefaxwllbboyc.supabase.co"
)

$addrs = [System.Net.Dns]::GetHostAddresses($HostName) |
    Where-Object { $_.AddressFamily -eq [System.Net.Sockets.AddressFamily]::InterNetwork }

if (-not $addrs) {
    Write-Error "No se encontró registro A (IPv4) para $HostName"
    exit 1
}

$ipv4 = $addrs[0].IPAddressToString
Write-Host "IPv4 para $HostName : $ipv4"
Write-Host ""
Write-Host "Agrega en tu .env de la raíz del proyecto:"
Write-Host "SUPABASE_DB_HOSTADDR=$ipv4"
Write-Host ""
Write-Host "Luego: docker compose up --build -d backend"
