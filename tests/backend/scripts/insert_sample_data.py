#!/usr/bin/env python3
"""
Script para insertar datos de prueba en MongoDB.
Esto permite probar el dashboard con datos reales sin esperar por Arduino.
"""

import os
import sys
from datetime import datetime, timedelta
from pymongo import MongoClient
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv("backend_fastapi/.env")

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
MONGODB_DB = os.getenv("MONGODB_DB", "embalse_arandanos")

def insert_sample_data():
    """Insertar datos de prueba en MongoDB"""
    try:
        print(f"Conectando a MongoDB: {MONGODB_URL}")
        client = MongoClient(
            MONGODB_URL,
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=10000,
            socketTimeoutMS=10000,
            tlsAllowInvalidCertificates=True,
            tlsAllowInvalidHostnames=True,
        )
        
        # Verificar conexión
        client.admin.command('ping')
        print("✓ Conexión a MongoDB exitosa")
        
        # Obtener base de datos
        db = client[MONGODB_DB]
        print(f"✓ Base de datos '{MONGODB_DB}' seleccionada")
        
        # Obtener colección
        collection = db["sensor_readings"]
        
        # Generar datos de prueba con timestamps recientes
        sample_data = []
        now = datetime.utcnow()
        
        # Crear 10 lecturas con tiempos espaciados
        for i in range(10):
            timestamp = now - timedelta(seconds=i*10)  # Una lectura cada 10 segundos hacia atrás
            reading = {
                "arduino_id": "ESP8266-EMBALSE-1",
                "timestamp": timestamp,
                "mediciones": {
                    "ph": 7.2 + (i * 0.05),  # Variar ligeramente
                    "temperatura": 20.5 + (i * 0.1),
                    "conductividad": 850.0 + (i * 5),
                },
                "bateria": 95 - (i * 2),  # Simular descarga de batería
            }
            sample_data.append(reading)
        
        # Insertar datos
        result = collection.insert_many(sample_data)
        print(f"✓ {len(result.inserted_ids)} registros insertados exitosamente")
        
        # Mostrar última lectura
        latest = collection.find_one(sort=[("timestamp", -1)])
        if latest:
            print("\n📊 Última lectura:")
            print(f"  - Timestamp: {latest['timestamp']}")
            print(f"  - pH: {latest['mediciones']['ph']}")
            print(f"  - Temperatura: {latest['mediciones']['temperatura']}°C")
            print(f"  - Conductividad: {latest['mediciones']['conductividad']}")
            print(f"  - Batería: {latest['bateria']}%")
        
        # Cerrar conexión
        client.close()
        print("\n✓ Datos de prueba insertados correctamente")
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = insert_sample_data()
    sys.exit(0 if success else 1)
