#!/usr/bin/env python3
import requests
import json

try:
    response = requests.get("http://127.0.0.1:8000/api/dashboard", timeout=5)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print("\n✓ Datos disponibles:")
        print(f"  pH: {data['ph']['value']} {data['ph']['status']}")
        print(f"  Temperatura: {data['temperature']['value']}°C {data['temperature']['status']}")
        print(f"  Conductividad: {data['conductivity']['value']} µS/cm {data['conductivity']['status']}")
        print(f"  Arduino conectado: {data['metadata']['arduinoConnected']}")
    else:
        print(f"\n✗ Error: {response.text}")
except Exception as e:
    print(f"✗ Error de conexión: {e}")
