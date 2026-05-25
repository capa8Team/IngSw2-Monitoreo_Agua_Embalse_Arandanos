#!/usr/bin/env python3
"""
Script para monitorear en tiempo real si MongoDB está guardando datos
Actualiza cada 5 segundos
"""

from pymongo import MongoClient
from datetime import datetime
import time

MONGODB_URL = 'mongodb://admin:Panconpalta1@localhost:27017/'
MONGODB_DB = 'Arandanos'

try:
    client = MongoClient(MONGODB_URL, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    db = client[MONGODB_DB]
    collection = db['sensor_readings']
    
    print("="*60)
    print("MONITOREANDO MONGODB EN TIEMPO REAL")
    print("="*60)
    print("Presiona Ctrl+C para detener\n")
    
    contador_registros_anterior = 0
    
    while True:
        # Contar registros actuales
        total_registros = collection.count_documents({})
        
        # Obtener el último registro
        ultimo = collection.find_one(sort=[("timestamp", -1)])
        
        # Limpiar pantalla (Windows)
        import os
        os.system('cls' if os.name == 'nt' else 'clear')
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] MONITOREANDO...")
        print("="*60)
        print(f"Total registros en MongoDB: {total_registros}")
        
        # Mostrar si hay cambios
        if total_registros > contador_registros_anterior:
            cambios = total_registros - contador_registros_anterior
            print(f"✓ NUEVOS REGISTROS: +{cambios}")
            contador_registros_anterior = total_registros
        
        if ultimo:
            print("\nULTIMO REGISTRO GUARDADO:")
            print(f"  Arduino: {ultimo['arduino_id']}")
            print(f"  Timestamp: {ultimo['timestamp']}")
            print(f"  pH: {ultimo['mediciones']['ph']}")
            print(f"  Temperatura: {ultimo['mediciones']['temperatura']}C")
            print(f"  Conductividad: {ultimo['mediciones']['conductividad']} uS/cm")
            print(f"  Bateria: {ultimo['bateria']}%")
        
        print("\n" + "="*60)
        print("Actualizando en 5 segundos... (Ctrl+C para salir)")
        
        time.sleep(5)

except Exception as e:
    print(f"Error: {e}")
