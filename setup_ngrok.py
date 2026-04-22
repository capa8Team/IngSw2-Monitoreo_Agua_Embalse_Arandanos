#!/usr/bin/env python3
"""
Script para configurar ngrok y obtener una URL pública para localhost
Requiere: pip install pyngrok
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv, set_key

def setup_ngrok():
    try:
        from pyngrok import ngrok
        
        print("[*] CONFIGURACION DE NGROK PARA DESARROLLO\n")
        
        # Detener túnels previos
        ngrok.kill()
        
        # Crear túneles para frontend y backend
        print("[*] Creando túneles ngrok...")
        
        # Frontend tunnel (Vite en puerto 5173)
        frontend_tunnel = ngrok.connect(5173, "http")
        frontend_url = frontend_tunnel.public_url
        print(f"[OK] Frontend: {frontend_url}")
        
        # Backend tunnel (FastAPI en puerto 8000)
        backend_tunnel = ngrok.connect(8000, "http")
        backend_url = backend_tunnel.public_url
        print(f"[OK] Backend: {backend_url}")
        
        print(f"\n[*] Actualizando .env...")
        
        env_file = Path(".env")
        
        # Actualizar .env
        set_key(env_file, "WEBAPP_URL", f"{frontend_url}/")
        set_key(env_file, "PUBLIC_BASE_URL", backend_url)
        
        print(f"[OK] WEBAPP_URL={frontend_url}/")
        print(f"[OK] PUBLIC_BASE_URL={backend_url}")
        
        print(f"\n[INFO] Los túneles se mantendrán abiertos mientras este script corra")
        print(f"[INFO] Presiona Ctrl+C para detener y cerrar los túneles")
        print(f"\n[*] Manteniendo túneles abiertos...")
        
        # Mantener el programa corriendo
        import time
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print(f"\n[*] Cerrando túneles...")
            ngrok.kill()
            print(f"[OK] Túneles cerrados")
            
            # Restaurar localhost en .env
            set_key(env_file, "WEBAPP_URL", "http://localhost:5173/")
            set_key(env_file, "PUBLIC_BASE_URL", "http://localhost:8000")
            print(f"[OK] .env restaurado a localhost")
            
    except ImportError:
        print("[ERROR] pyngrok no está instalado")
        print("[INSTRUCCION] Instala con: pip install pyngrok")
    except Exception as e:
        print(f"[ERROR] {e}")

if __name__ == "__main__":
    setup_ngrok()
