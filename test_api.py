#!/usr/bin/env python3
import requests
import json
from datetime import datetime

API_URL = "http://localhost:8000"

print("=" * 80)
print(f"Probando API en {API_URL}")
print(f"Hora: {datetime.now().isoformat()}")
print("=" * 80)

# Probar /api/dashboard
print("\n[1] Probando /api/dashboard")
print("-" * 80)
try:
    response = requests.get(f"{API_URL}/api/dashboard", timeout=5)
    print(f"Status: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    print(f"Body (raw): {response.text[:500]}")
    try:
        data = response.json()
        print(f"Body (JSON):\n{json.dumps(data, indent=2)}")
    except Exception as e:
        print(f"Error parseando JSON: {e}")
except Exception as e:
    print(f"Error en request: {e}")

# Probar /api/sensors/history
print("\n[2] Probando /api/sensors/history?limit=5")
print("-" * 80)
try:
    response = requests.get(f"{API_URL}/api/sensors/history?limit=5", timeout=5)
    print(f"Status: {response.status_code}")
    print(f"Body (JSON):\n{json.dumps(response.json(), indent=2)[:1000]}")
except Exception as e:
    print(f"Error en request: {e}")

# Probar /docs
print("\n[3] Probando /docs (Swagger)")
print("-" * 80)
try:
    response = requests.get(f"{API_URL}/docs", timeout=5)
    print(f"Status: {response.status_code}")
    print(f"Swagger disponible: {'OK' if response.status_code == 200 else 'FAIL'}")
except Exception as e:
    print(f"Error en request: {e}")
