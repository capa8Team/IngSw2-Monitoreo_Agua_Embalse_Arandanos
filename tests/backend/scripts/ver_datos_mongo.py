#!/usr/bin/env python3
"""
Script para ver todos los datos guardados en MongoDB
"""

from pymongo import MongoClient
from datetime import datetime

MONGODB_URL = 'mongodb://admin:Panconpalta1@localhost:27017/'
MONGODB_DB = 'Arandanos'

try:
    print("Conectando a MongoDB...")
    client = MongoClient(MONGODB_URL, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    print("OK Conectado a MongoDB\n")
    
    db = client[MONGODB_DB]
    collection = db['sensor_readings']
    
    # Contar documentos
    total = collection.count_documents({})
    print(f"Total de registros en MongoDB: {total}\n")
    
    # Obtener último registro
    ultimo = collection.find_one(sort=[("timestamp", -1)])
    
    if ultimo:
        print("="*60)
        print("ULTIMO REGISTRO")
        print("="*60)
        print(f"ID: {ultimo['_id']}")
        print(f"Arduino: {ultimo['arduino_id']}")
        print(f"Timestamp: {ultimo['timestamp']}")
        print(f"pH: {ultimo['mediciones']['ph']}")
        print(f"Temperatura: {ultimo['mediciones']['temperatura']}C")
        print(f"Conductividad: {ultimo['mediciones']['conductividad']} uS/cm")
        print(f"Bateria: {ultimo['bateria']}%")
        print("="*60 + "\n")
    
    # Listar todos
    print(f"TODOS LOS REGISTROS ({total}):\n")
    for i, doc in enumerate(collection.find().sort("timestamp", -1), 1):
        print(f"{i}. [{doc['timestamp']}]")
        print(f"   pH: {doc['mediciones']['ph']}")
        print(f"   Temp: {doc['mediciones']['temperatura']}C")
        print(f"   Conducti: {doc['mediciones']['conductividad']} uS/cm")
        print(f"   Bateria: {doc['bateria']}%")
        print()
    
    client.close()
    
except Exception as e:
    print(f"Error: {e}")
