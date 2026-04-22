#!/usr/bin/env python3
"""
Script de prueba para verificar el funcionamiento del sistema de alertas y Telegram.
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json"}

def print_section(title):
    """Imprimir un separador de sección."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_health():
    """Prueba que el backend está vivo."""
    print_section("1. PRUEBA DE SALUD DEL BACKEND")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_telegram_stats():
    """Obtener estadísticas de Telegram."""
    print_section("2. ESTADÍSTICAS DE TELEGRAM")
    try:
        response = requests.get(f"{BASE_URL}/api/telegram/stats", timeout=5)
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_get_subscribers():
    """Obtener lista de suscriptores."""
    print_section("3. SUSCRIPTORES DE TELEGRAM")
    try:
        response = requests.get(f"{BASE_URL}/api/telegram/subscribers", timeout=5)
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_dashboard():
    """Obtener estado del dashboard."""
    print_section("4. ESTADO DEL DASHBOARD")
    try:
        response = requests.get(f"{BASE_URL}/api/dashboard", timeout=5)
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Response (resumen):")
        print(f"  pH: {data.get('ph', {}).get('value')} (status: {data.get('ph', {}).get('status')})")
        print(f"  Temperatura: {data.get('temperature', {}).get('value')} (status: {data.get('temperature', {}).get('status')})")
        print(f"  Conductividad: {data.get('conductivity', {}).get('value')} (status: {data.get('conductivity', {}).get('status')})")
        print(f"  Arduino Connected: {data.get('metadata', {}).get('arduinoConnected')}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_get_latest_reading():
    """Obtener última lectura de sensores."""
    print_section("5. ÚLTIMA LECTURA DE SENSORES")
    try:
        response = requests.get(f"{BASE_URL}/api/sensors/latest", timeout=5)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if data:
                print(f"Response:")
                print(f"  pH: {data.get('ph')}")
                print(f"  Temperatura: {data.get('temperature')}°C")
                print(f"  Conductividad: {data.get('conductivity')} µS/cm")
                print(f"  Timestamp: {data.get('timestamp')}")
            else:
                print("  No hay lectura disponible aún")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_send_test_alert():
    """Enviar una alerta de prueba."""
    print_section("6. ENVIAR ALERTA DE PRUEBA")
    try:
        response = requests.post(f"{BASE_URL}/api/telegram/test-alert", timeout=10)
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_send_alert_out_of_range():
    """Enviar alerta fuera de rango para pruebas."""
    print_section("7. ENVIAR ALERTA FUERA DE RANGO")
    try:
        response = requests.post(f"{BASE_URL}/api/telegram/test-alert-out-of-range", timeout=10)
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_create_alert():
    """Crear una alerta de sensores."""
    print_section("8. CREAR ALERTA DE SENSOR")
    try:
        payload = {
            "embalse": "Sector Norte",
            "sensor": "pH",
            "medicion": "7.5",
            "nombreDispositivo": "Embalse Arándanos",
            "valor": 7.5,
            "minimo": 6.0,
            "maximo": 8.5
        }
        response = requests.post(f"{BASE_URL}/api/alerts", json=payload, timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 201:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
        else:
            print(f"Response: {response.text}")
        return response.status_code == 201
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_get_alerts():
    """Obtener lista de alertas."""
    print_section("9. LISTA DE ALERTAS")
    try:
        response = requests.get(f"{BASE_URL}/api/alerts", timeout=5)
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Total de alertas: {len(data)}")
        if data:
            print(f"Últimas 3 alertas:")
            for alert in data[-3:]:
                print(f"  - [{alert.get('id')}] {alert.get('embalse')} - {alert.get('sensor')} ({alert.get('fecha')} {alert.get('hora')})")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    """Ejecutar todas las pruebas."""
    print("\n")
    print("*" * 60)
    print("*  SISTEMA DE MONITOREO - PRUEBAS COMPLETAS")
    print("*" * 60)
    print(f"\nInicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Base URL: {BASE_URL}")
    
    results = {
        "Salud del Backend": test_health(),
        "Estadísticas Telegram": test_telegram_stats(),
        "Suscriptores": test_get_subscribers(),
        "Dashboard": test_dashboard(),
        "Última Lectura": test_get_latest_reading(),
        "Alerta de Prueba": test_send_test_alert(),
        "Alerta Fuera de Rango": test_send_alert_out_of_range(),
        "Crear Alerta": test_create_alert(),
        "Lista de Alertas": test_get_alerts(),
    }
    
    print_section("RESUMEN DE RESULTADOS")
    print(f"{'Prueba':<30} {'Resultado':<15}")
    print("-" * 45)
    
    passed = 0
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"{test_name:<30} {status:<15}")
        if result:
            passed += 1
    
    print("-" * 45)
    print(f"Total: {passed}/{len(results)} pruebas pasadas")
    print(f"\nFin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n")

if __name__ == "__main__":
    main()
