#!/usr/bin/env python3
"""Insertar datos de prueba en MongoDB para ver el frontend funcionando"""

import pymongo
from datetime import datetime, timedelta
import random

# Conexión a MongoDB
MONGO_URL = "mongodb://localhost:27017"
MONGO_DB = "embalse_arandanos"
MONGO_COLLECTION = "sensor_readings"

client = pymongo.MongoClient(MONGO_URL)
db = client[MONGO_DB]
collection = db[MONGO_COLLECTION]

# Generar datos de prueba
test_data = []
base_time = datetime.utcnow() - timedelta(hours=2)

for i in range(20):
    test_data.append({
        "ph": round(7.0 + random.uniform(-0.5, 0.5), 2),
        "temperature": round(20 + random.uniform(-2, 5), 2),
        "conductivity": round(1000 + random.uniform(-200, 300), 2),
        "timestamp": base_time + timedelta(minutes=i*6),
        "device_id": "ESP8266_TEST",
        "location": "Embalse Arandanos"
    })

# Insertar en MongoDB
try:
    result = collection.insert_many(test_data)
    print(f"✓ {len(result.inserted_ids)} registros insertados exitosamente")
    
    # Mostrar último registro
    latest = collection.find_one(sort=[("timestamp", -1)])
    print(f"\nÚltimo registro guardado:")
    print(f"  pH: {latest['ph']}")
    print(f"  Temperatura: {latest['temperature']}°C")
    print(f"  Conductividad: {latest['conductivity']} µS/cm")
    print(f"  Timestamp: {latest['timestamp']}")
except Exception as e:
    print(f"✗ Error al insertar datos: {e}")
finally:
    client.close()
