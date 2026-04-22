#!/usr/bin/env python3
"""
Script de diagnóstico para el bot de Telegram.
Verifica:
1. Validez del token
2. Estado del bot
3. Intenta enviar mensaje de prueba
"""

import asyncio
import os
import json
from dotenv import load_dotenv
from telegram import Bot
from pathlib import Path

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
SUBSCRIBERS_FILE = Path(__file__).parent / "alertas" / "telegram_subscribers.json"

async def main():
    print("[*] DIAGNOSTICO DEL BOT DE TELEGRAM\n")
    
    # 1. Verificar token
    if not TOKEN:
        print("[ERROR] No hay TELEGRAM_BOT_TOKEN configurado en .env")
        return
    
    print(f"[OK] Token encontrado: {TOKEN[:20]}...{TOKEN[-10:]}\n")
    
    # 2. Crear instancia del bot y verificar
    bot = Bot(token=TOKEN)
    
    try:
        me = await bot.get_me()
        print(f"[OK] Bot conectado correctamente")
        print(f"    - Nombre: {me.first_name}")
        print(f"    - Username: @{me.username}")
        print(f"    - ID: {me.id}\n")
    except Exception as e:
        print(f"[ERROR] No se pudo conectar al bot: {e}\n")
        return
    
    # 3. Verificar suscriptores
    print("[*] ARCHIVO DE SUSCRIPTORES\n")
    
    if not SUBSCRIBERS_FILE.exists():
        print(f"[WARNING] Archivo no existe: {SUBSCRIBERS_FILE}")
        print("[*] Creando archivo con suscriptor de prueba\n")
        # Crear archivo vacio
        SUBSCRIBERS_FILE.write_text("[]")
    
    try:
        subscribers = json.loads(SUBSCRIBERS_FILE.read_text())
        print(f"[OK] Archivo leído: {SUBSCRIBERS_FILE}")
        print(f"[INFO] Suscriptores actuales: {subscribers}")
        print(f"[INFO] Total: {len(subscribers)} suscriptor(es)\n")
    except Exception as e:
        print(f"[ERROR] Error leyendo archivo: {e}\n")
        return
    
    # 4. Test de envío
    if subscribers:
        print("[*] TEST DE ENVIO A SUSCRIPTOR\n")
        test_chat_id = subscribers[0]
        print(f"[*] Intentando enviar mensaje a chat_id: {test_chat_id}")
        
        try:
            test_message = (
                "[TEST] Mensaje de Diagnostico\n\n"
                "Si ves esta prueba, el bot funciona correctamente.\n"
                "El chat_id registrado es VALIDO.\n\n"
                "Responde /start cuando estés listo."
            )
            
            await bot.send_message(
                chat_id=test_chat_id,
                text=test_message
            )
            print(f"[OK] Mensaje enviado exitosamente!\n")
        except Exception as e:
            print(f"[ERROR] Fallo al enviar: {str(e)}\n")
            print("[SOLUCION] Probablemente el chat_id es inválido o el usuario ha bloqueado al bot.")
            print("[INSTRUCCION] Por favor:")
            print("  1. Abre Telegram")
            print("  2. Busca el bot por nombre o token")
            print("  3. Envía /start en Telegram")
            print("  4. Esto registrará tu chat_id correctamente\n")
    else:
        print("[WARNING] No hay suscriptores.")
        print("[INSTRUCCION] Para empezar:")
        print("  1. Abre Telegram")
        print("  2. Busca el bot")
        print("  3. Envía /start")
        print("  4. Esto te registrará como suscriptor\n")
    
    print("[*] DIAGNOSTICO COMPLETADO\n")

if __name__ == "__main__":
    asyncio.run(main())
