#!/usr/bin/env pwsh
# Script para iniciar Backend y Frontend del Embalse Arandanos
# Uso: .\start-dev.ps1

param(
    [switch]$Backend,
    [switch]$Frontend,
    [switch]$Both,
    [switch]$Open
)

# Si no se especifica nada, asumir que quieren ambos
if (-not $Backend -and -not $Frontend -and -not $Both) {
    $Both = $true
}

$PythonPath = "C:\Users\Alumno\AppData\Local\Programs\Python\Python311\python.exe"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Join-Path $ProjectRoot "backend_fastapi"

Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  🚀 Arandanos Embalse - Development Environment" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan

# Agregar Python y npm al PATH
$env:PATH = "$env:PATH;C:\Users\Alumno\AppData\Local\Programs\Python\Python311;C:\Users\Alumno\AppData\Local\Programs\Python\Python311\Scripts"

# Función para iniciar Backend
function Start-Backend {
    Write-Host "`n📦 Iniciando BACKEND (FastAPI)..." -ForegroundColor Green
    Write-Host "   📍 Ubicación: $BackendDir" -ForegroundColor Gray
    Write-Host "   🔗 URL: http://localhost:8000" -ForegroundColor Gray
    Write-Host "   📚 Docs: http://localhost:8000/docs" -ForegroundColor Gray
    
    Push-Location $BackendDir
    
    # Verificar que MongoDB esté disponible
    Write-Host "`n   ⏳ Verificando MongoDB..." -ForegroundColor Yellow
    $MongoTest = & $PythonPath -c "from pymongo import MongoClient; print('MongoDB OK')" 2>&1
    if ($MongoTest -like "*ERROR*" -or $MongoTest -like "*refused*") {
        Write-Host "   ⚠️  MongoDB no parece estar disponible. ¿Está corriendo?" -ForegroundColor Yellow
        Write-Host "   💡 Inicia MongoDB con: mongod" -ForegroundColor Yellow
    } else {
        Write-Host "   ✓ MongoDB detectado" -ForegroundColor Green
    }
    
    Write-Host "`n   ⏳ Iniciando servidor..." -ForegroundColor Yellow
    & $PythonPath main.py
    
    Pop-Location
}

# Función para iniciar Frontend
function Start-Frontend {
    Write-Host "`n💻 Iniciando FRONTEND (Vue.js + Vite)..." -ForegroundColor Green
    Write-Host "   📍 Ubicación: $ProjectRoot" -ForegroundColor Gray
    Write-Host "   🔗 URL: http://localhost:5173" -ForegroundColor Gray
    
    Push-Location $ProjectRoot
    Write-Host "`n   ⏳ Iniciando servidor..." -ForegroundColor Yellow
    npm run dev
    
    Pop-Location
}

# Iniciar servicios según las banderas
if ($Both -or $Backend) {
    # Iniciar backend en una nueva ventana de PowerShell
    Write-Host "`n🔄 Abriendo backend en nueva ventana..." -ForegroundColor Cyan
    $BackendScript = {
        $PythonPath = "C:\Users\Alumno\AppData\Local\Programs\Python\Python311\python.exe"
        $ProjectRoot = "$PSScriptRoot"
        $BackendDir = Join-Path $ProjectRoot "backend_fastapi"
        $env:PATH = "$env:PATH;C:\Users\Alumno\AppData\Local\Programs\Python\Python311"
        
        Push-Location $BackendDir
        Write-Host "🚀 Backend iniciando..." -ForegroundColor Green
        & $PythonPath main.py
    }
    
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$ProjectRoot'; `$PythonPath = 'C:\Users\Alumno\AppData\Local\Programs\Python\Python311\python.exe'; `$env:PATH = `"`$env:PATH;C:\Users\Alumno\AppData\Local\Programs\Python\Python311`"; Push-Location 'backend_fastapi'; & `$PythonPath main.py"
    
    Start-Sleep -Seconds 2
}

if ($Both -or $Frontend) {
    # Iniciar frontend en una nueva ventana de PowerShell
    Write-Host "🔄 Abriendo frontend en nueva ventana..." -ForegroundColor Cyan
    
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$ProjectRoot'; npm run dev"
    
    Start-Sleep -Seconds 2
}

if ($Both -or $Backend -or $Frontend) {
    Write-Host "`n════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "✅ Servidores iniciados" -ForegroundColor Green
    Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    
    if ($Backend -or $Both) {
        Write-Host "`n  Backend (FastAPI)" -ForegroundColor Green
        Write-Host "    🌐 http://localhost:8000" -ForegroundColor Cyan
        Write-Host "    📚 Docs:  http://localhost:8000/docs" -ForegroundColor Cyan
        Write-Host "    💾 Admin: http://localhost:8000/redoc" -ForegroundColor Cyan
    }
    
    if ($Frontend -or $Both) {
        Write-Host "`n  Frontend (Vue.js)" -ForegroundColor Green
        Write-Host "    🌐 http://localhost:5173" -ForegroundColor Cyan
        Write-Host "    📱 Dashboard" -ForegroundColor Cyan
    }
    
    Write-Host "`n  📋 Logs:" -ForegroundColor Yellow
    Write-Host "    Backend:  Mostrado arriba ▲" -ForegroundColor Gray
    Write-Host "    Frontend: Mostrado arriba ▲" -ForegroundColor Gray
    
    Write-Host "`n  🛑 Para detener: Presiona Ctrl+C en ambas ventanas" -ForegroundColor Yellow
    Write-Host "════════════════════════════════════════════════════════════`n" -ForegroundColor Cyan
}

Write-Host ""
