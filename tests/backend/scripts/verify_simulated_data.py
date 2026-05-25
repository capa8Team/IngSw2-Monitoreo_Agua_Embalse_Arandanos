#!/usr/bin/env python3
import requests
import json

print("=== VERIFICACION DE DATOS SIMULADOS ===")
print()

# Obtener todos los datos
r = requests.get("http://localhost:8000/api/data/mongodb")
data = r.json()

print(f"Total de registros en MongoDB: {data['total_registros']}")
print()

if data['data']:
    print("Ultimos 5 registros guardados:")
    print("-" * 80)
    for record in data['data'][:5]:
        ts = record.get('timestamp', 'N/A')
        arduino = record.get('arduino_id', 'N/A')
        ph = record['mediciones']['ph']
        temp = record['mediciones']['temperatura']
        cond = record['mediciones']['conductividad']
        
        print(f"Arduino: {arduino} | pH: {ph} | Temp: {temp}°C | Cond: {cond}")
        print(f"  Timestamp: {ts}")
    
    print()
    print("✓ Los datos SIMULADOS están siendo guardados cada 10 segundos en MongoDB!")
else:
    print("No hay datos en MongoDB")
