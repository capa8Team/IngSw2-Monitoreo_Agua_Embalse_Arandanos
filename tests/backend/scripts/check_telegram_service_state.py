#!/usr/bin/env python3
"""
Script para verificar el estado actual de TelegramService.
"""

import asyncio
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent / "alertas"))

from telegram_service import TelegramService, SensorAlertPayload, send_sensor_alert, get_telegram_stats
import os
from dotenv import load_dotenv

load_dotenv()

async def main():
    print("[*] VERIFICANDO ESTADO DE TELEGRAMSERVICE\n")
    
    # 1. Obtener stats
    stats = get_telegram_stats()
    print(f"[INFO] Stats actual: {stats}\n")
    
    # 2. Crear alerta de prueba fuera de rango
    print("[*] Creando alerta fuera de rango...")
    alert = SensorAlertPayload(
        deviceName="Test Device",
        ph=3.5,  # Fuera de rango
        temperature=40.0,  # Fuera de rango
        conductivity=2500.0,  # Fuera de rango
        date="2026-04-22",
        time="17:10:00"
    )
    
    print(f"[*] Enviando alerta...")
    result = await send_sensor_alert(alert)
    
    print(f"\n[RESULTADO DE ENVIO]")
    print(f"  Status: {result.get('status')}")
    print(f"  Mensaje: {result.get('message')}")
    print(f"  Enviados: {result.get('sent')}")
    print(f"  Fallidos: {result.get('failed')}")
    print(f"  Total suscriptores: {result.get('subscribers')}")

if __name__ == "__main__":
    asyncio.run(main())
