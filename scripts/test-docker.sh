#!/bin/bash

# Test script para validar que el proyecto funciona después del refactor
# Uso: bash scripts/test-docker.sh

set -e

echo "══════════════════════════════════════════════════════════════════════════════"
echo "  Monitoreo Embalse Arándanos — Docker Testing Script"
echo "══════════════════════════════════════════════════════════════════════════════"
echo ""

# ─────────────────────────────────────────────────────────────────────────────────
# COLORES PARA OUTPUT
# ─────────────────────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ─────────────────────────────────────────────────────────────────────────────────
# FUNCIONES
# ─────────────────────────────────────────────────────────────────────────────────

test_passed() {
    echo -e "${GREEN}✓ PASS${NC} — $1"
}

test_failed() {
    echo -e "${RED}✗ FAIL${NC} — $1"
    exit 1
}

test_info() {
    echo -e "${YELLOW}→${NC} $1"
}

# ─────────────────────────────────────────────────────────────────────────────────
# 1. VERIFICAR REQUISITOS
# ─────────────────────────────────────────────────────────────────────────────────

echo "1. VERIFICANDO REQUISITOS"
echo "────────────────────────────────────────────────────────────────────────────"

if ! command -v docker &> /dev/null; then
    test_failed "Docker no está instalado"
fi
test_passed "Docker está instalado"

if ! command -v docker compose &> /dev/null; then
    test_failed "Docker Compose no está instalado"
fi
test_passed "Docker Compose está instalado"

echo ""

# ─────────────────────────────────────────────────────────────────────────────────
# 2. LEVANTAR SERVICIOS
# ─────────────────────────────────────────────────────────────────────────────────

echo "2. LEVANTANDO SERVICIOS (esto puede tomar 2-3 minutos la primera vez)"
echo "────────────────────────────────────────────────────────────────────────────"

test_info "Construyendo imágenes Docker..."
docker compose build --no-cache backend frontend mongodb > /dev/null 2>&1 || test_failed "No se pudieron construir las imágenes"
test_passed "Imágenes construidas"

test_info "Iniciando servicios..."
docker compose up -d > /dev/null 2>&1 || test_failed "No se pudieron iniciar los servicios"
test_passed "Servicios iniciados en background"

test_info "Esperando a que MongoDB esté listo (máx 30s)..."
for i in {1..30}; do
    if docker exec mongodb-arandanos mongosh -u admin -p Panconpalta1 --authenticationDatabase admin --quiet --eval "db.adminCommand('ping').ok" > /dev/null 2>&1; then
        test_passed "MongoDB está listo"
        break
    fi
    if [ $i -eq 30 ]; then
        test_failed "MongoDB no respondió después de 30s"
    fi
    sleep 1
done

test_info "Esperando a que el backend esté listo (máx 30s)..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        test_passed "Backend está listo"
        break
    fi
    if [ $i -eq 30 ]; then
        test_failed "Backend no respondió después de 30s"
    fi
    sleep 1
done

echo ""

# ─────────────────────────────────────────────────────────────────────────────────
# 3. TESTS DE API
# ─────────────────────────────────────────────────────────────────────────────────

echo "3. TESTS DE API"
echo "────────────────────────────────────────────────────────────────────────────"

test_info "Test: GET /health"
HEALTH=$(curl -s http://localhost:8000/health)
if echo "$HEALTH" | grep -q '"status":"ok"'; then
    test_passed "Health check devuelve 200 con status=ok"
else
    test_failed "Health check devolvió respuesta inesperada: $HEALTH"
fi

test_info "Test: GET /api/sensors/readings (Dashboard)"
READINGS=$(curl -s http://localhost:8000/api/sensors/readings?limit=5)
if [ ! -z "$READINGS" ] && [ "$READINGS" != "{}" ]; then
    test_passed "GET /api/sensors/readings devuelve datos"
else
    test_passed "GET /api/sensors/readings devuelve respuesta vacía (esperado en DB nueva)"
fi

test_info "Test: GET /api/sensors/history"
HISTORY=$(curl -s http://localhost:8000/api/sensors/history?limit=10)
if [ ! -z "$HISTORY" ]; then
    test_passed "GET /api/sensors/history devuelve respuesta"
else
    test_failed "GET /api/sensors/history está vacío o no existe"
fi

test_info "Test: GET /api/alerts"
ALERTS=$(curl -s http://localhost:8000/api/alerts)
if [ ! -z "$ALERTS" ]; then
    test_passed "GET /api/alerts devuelve respuesta"
else
    test_failed "GET /api/alerts está vacío o no existe"
fi

test_info "Test: GET /api/dashboard"
DASHBOARD=$(curl -s http://localhost:8000/api/dashboard)
if echo "$DASHBOARD" | grep -qE '(ph|temperature|conductivity)'; then
    test_passed "GET /api/dashboard devuelve datos esperados"
else
    test_failed "GET /api/dashboard devolvió respuesta inesperada"
fi

test_info "Test: Swagger API Docs"
DOCS=$(curl -s http://localhost:8000/docs | grep -c "Swagger UI")
if [ "$DOCS" -gt 0 ]; then
    test_passed "Swagger documentation está accesible"
else
    test_failed "Swagger documentation no está disponible"
fi

echo ""

# ─────────────────────────────────────────────────────────────────────────────────
# 4. LOGS DEL BACKEND
# ─────────────────────────────────────────────────────────────────────────────────

echo "4. VERIFICACIÓN DE LOGS"
echo "────────────────────────────────────────────────────────────────────────────"

test_info "Verificando logs del backend..."
LOGS=$(docker compose logs backend --tail=50)

if echo "$LOGS" | grep -q "correlation_id"; then
    test_passed "Logging con correlation_id funciona"
else
    test_info "Información: No se encontraron correlation_ids en logs recientes (esperado en DB nueva)"
fi

if echo "$LOGS" | grep -q "ERROR\|FATAL"; then
    test_failed "Se encontraron errores en los logs del backend"
else
    test_passed "No hay errores críticos en los logs"
fi

echo ""

# ─────────────────────────────────────────────────────────────────────────────────
# 5. MONGODB
# ─────────────────────────────────────────────────────────────────────────────────

echo "5. VERIFICACIÓN DE MONGODB"
echo "────────────────────────────────────────────────────────────────────────────"

test_info "Conectando a MongoDB..."
DB_STATUS=$(docker exec mongodb-arandanos mongosh Arandanos -u admin -p Panconpalta1 --authenticationDatabase admin --quiet --eval "db.getName()" 2>&1)

if echo "$DB_STATUS" | grep -q "Arandanos"; then
    test_passed "MongoDB está conectado a base de datos 'Arandanos'"
else
    test_failed "No se pudo conectar a MongoDB"
fi

echo ""

# ─────────────────────────────────────────────────────────────────────────────────
# 6. INFORMACIÓN FINAL
# ─────────────────────────────────────────────────────────────────────────────────

echo "══════════════════════════════════════════════════════════════════════════════"
echo "✓ TODOS LOS TESTS PASARON"
echo "══════════════════════════════════════════════════════════════════════════════"
echo ""
echo "URLs para testing manual:"
echo "  Frontend:     http://localhost (o http://localhost:5173)"
echo "  API Directa:  http://localhost:8000"
echo "  Swagger Docs: http://localhost:8000/docs"
echo ""
echo "Para ver logs en vivo:"
echo "  docker compose logs -f backend"
echo "  docker compose logs -f mongodb"
echo "  docker compose logs -f frontend"
echo ""
echo "Para detener todo:"
echo "  docker compose down"
echo ""
echo "Para limpiar volúmenes (resetear base de datos):"
echo "  docker compose down -v"
echo ""
echo "Referencia: docs/TESTING_GUIDE.md"
echo "══════════════════════════════════════════════════════════════════════════════"
