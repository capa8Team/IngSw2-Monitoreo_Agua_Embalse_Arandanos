#!/usr/bin/env python3
"""
Script para probar el comando /webapp
"""

import asyncio
import os
from dotenv import load_dotenv
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent / "alertas"))

from telegram_service import TelegramService, load_subscribers
from telegram import Update, Chat, User, Message

load_dotenv()

async def test_webapp_command():
    print("[*] PRUEBA DEL COMANDO /WEBAPP\n")
    
    # 1. Obtener suscriptores
    subscribers = load_subscribers()
    print(f"[INFO] Suscriptores actuales: {subscribers}")
    
    if not subscribers:
        print("[ERROR] No hay suscriptores registrados")
        print("[INSTRUCCION] Primero necesitas:")
        print("  1. Abrir Telegram")
        print("  2. Buscar el bot @alertaEmbalseBot")
        print("  3. Enviar /start para registrarte")
        return
    
    # 2. Inicializar Telegram si no está inicializado
    stats = TelegramService.get_stats()
    if not stats.get("bot_initialized"):
        print("[*] Inicializando Telegram...")
        await TelegramService.initialize()
        await TelegramService.start_polling()
    
    # 3. Enviar mensaje con el link del dashboard
    print(f"\n[*] Enviando mensaje de /webapp a {len(subscribers)} suscriptor(es)...\n")
    
    WEBAPP_URL = os.getenv("WEBAPP_URL", "http://localhost:5173/")
    
    for chat_id in subscribers:
        try:
            message = (
                "ACCESO AL DASHBOARD\n\n"
                "Link directo al panel de control:\n"
                f"{WEBAPP_URL}\n\n"
                "En el dashboard podras:\n"
                "- Ver valores ACTUALES de sensores (pH, temperatura, conductividad)\n"
                "- Visualizar graficos e historial de mediciones\n"
                "- Revisar todas las alertas registradas\n"
                "- Monitoreo en tiempo real del sistema\n\n"
                "Copia o toca el link arriba para abrir en tu navegador."
            )
            
            await TelegramService.bot.send_message(
                chat_id=chat_id,
                text=message,
            )
            
            print(f"[OK] Mensaje enviado exitosamente a chat_id: {chat_id}")
            print(f"[INFO] Link incluido: {WEBAPP_URL}\n")
        except Exception as e:
            print(f"[ERROR] No se pudo enviar a {chat_id}: {e}\n")

if __name__ == "__main__":
    asyncio.run(test_webapp_command())
