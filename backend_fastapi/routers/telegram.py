import logging
import asyncio
from typing import Any
from fastapi import APIRouter

from services.telegram import (
    TelegramService, SensorAlertPayload, initialize_telegram,
    get_telegram_stats, get_telegram_subscribers, send_sensor_alert
)
from services.mongodb import chile_now

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/telegram", tags=["Telegram"])

async def ensure_telegram_initialized():
    """Asegurar que el servicio de Telegram está inicializado."""
    stats = get_telegram_stats()
    if not stats.get("bot_initialized"):
        logger.info("[TELEGRAM] Bot no inicializado, intentando inicializar...")
        try:
            success = await initialize_telegram()
            if success:
                asyncio.create_task(TelegramService.start_polling())
                logger.info("[TELEGRAM] Bot inicializado exitosamente")
            else:
                logger.warning("[TELEGRAM] No se pudo inicializar el bot")
        except Exception as e:
            logger.error(f"[TELEGRAM] Error inicializando: {e}")

@router.get("/stats")
async def get_telegram_statistics() -> dict[str, Any]:
    await ensure_telegram_initialized()
    return get_telegram_stats()

@router.get("/subscribers")
async def list_telegram_subscribers() -> dict[str, Any]:
    await ensure_telegram_initialized()
    subscribers = get_telegram_subscribers()
    return {"count": len(subscribers), "subscribers": sorted(list(subscribers))}

@router.post("/test-alert")
async def send_test_alert() -> dict[str, Any]:
    await ensure_telegram_initialized()
    now = chile_now()
    test_alert = SensorAlertPayload(
        deviceName="Embalse PRUEBA", ph=7.5, temperature=25.0, conductivity=1500.0,
        date=now.strftime("%Y-%m-%d"), time=now.strftime("%H:%M:%S")
    )
    result = await send_sensor_alert(test_alert)
    return {
        "status": result.get("status"), "message": "Alerta de prueba enviada",
        "sent": result.get("sent"), "failed": result.get("failed"), "subscribers": result.get("subscribers")
    }

@router.post("/test-alert-out-of-range")
async def send_test_alert_out_of_range() -> dict[str, Any]:
    await ensure_telegram_initialized()
    now = chile_now()
    test_alert = SensorAlertPayload(
        deviceName="Embalse Arándanos - Sector Norte", ph=3.5, temperature=40.0, conductivity=2500.0,
        date=now.strftime("%Y-%m-%d"), time=now.strftime("%H:%M:%S")
    )
    result = await send_sensor_alert(test_alert)
    return {
        "status": result.get("status"), "message": "Alerta de prueba (FUERA DE RANGO) enviada",
        "sent": result.get("sent"), "failed": result.get("failed"), "subscribers": result.get("subscribers")
    }

@router.post("/init")
async def initialize_telegram_service() -> dict[str, Any]:
    try:
        success = await initialize_telegram()
        if success:
            asyncio.create_task(TelegramService.start_polling())
            return {"status": "success", "message": "Servicio de Telegram inicializado manualmente", "polling": "iniciado en background"}
        else:
            return {"status": "error", "message": "No se pudo inicializar el servicio de Telegram"}
    except Exception as e:
        logger.error(f"Error inicializando Telegram manualmente: {e}")
        return {"status": "error", "message": str(e)}