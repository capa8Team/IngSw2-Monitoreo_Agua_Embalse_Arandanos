"""
Servicio de Telegram para notificaciones de alertas en tiempo real.
Incluye polling automatico y gestion de suscriptores.
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

load_dotenv()

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURACION
# ============================================================================

# TOKEN puede ser None — el backend arranca igual; Telegram queda desactivado
# si la variable de entorno no esta configurada.
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    logger.warning(
        "[TELEGRAM] TELEGRAM_BOT_TOKEN no configurado. "
        "El servicio de Telegram estara desactivado."
    )

PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "http://localhost")
WEBAPP_URL = os.getenv("WEBAPP_URL", f"{PUBLIC_BASE_URL}/")

BASE_DIR = Path(__file__).resolve().parent
SUBSCRIBERS_FILE = BASE_DIR / "telegram_subscribers.json"

# ============================================================================
# GESTION DE SUSCRIPTORES
# ============================================================================


def load_subscribers() -> set[int]:
    """Cargar lista de chats suscritos desde archivo JSON."""
    if not SUBSCRIBERS_FILE.exists():
        return set()
    try:
        data = json.loads(SUBSCRIBERS_FILE.read_text(encoding="utf-8"))
        return {int(chat_id) for chat_id in data if str(chat_id).strip()}
    except Exception as e:
        logger.error(f"Error cargando suscriptores: {e}")
        return set()


def save_subscribers(subscribers: set[int]) -> None:
    """Guardar suscriptores en archivo JSON."""
    try:
        SUBSCRIBERS_FILE.parent.mkdir(parents=True, exist_ok=True)
        SUBSCRIBERS_FILE.write_text(
            json.dumps(sorted(subscribers), ensure_ascii=True, indent=2),
            encoding="utf-8",
        )
        logger.info(f"Suscriptores guardados: {len(subscribers)}")
    except Exception as e:
        logger.error(f"Error guardando suscriptores: {e}")


def subscribe_chat(chat_id: int) -> None:
    """Agregar o actualizar suscripcion."""
    TelegramService.subscribed_chats.add(chat_id)
    save_subscribers(TelegramService.subscribed_chats)


def unsubscribe_chat(chat_id: int) -> None:
    """Remover suscripcion."""
    TelegramService.subscribed_chats.discard(chat_id)
    save_subscribers(TelegramService.subscribed_chats)


# ============================================================================
# MODELOS
# ============================================================================


class SensorAlertPayload:
    """Estructura de datos para alertas de sensores."""

    def __init__(
        self,
        deviceName: str,
        ph: float,
        temperature: float,
        conductivity: float,
        date: str,
        time: str,
    ):
        self.deviceName = deviceName
        self.ph = ph
        self.temperature = temperature
        self.conductivity = conductivity
        self.date = date
        self.time = time


# ============================================================================
# SERVICIO PRINCIPAL DE TELEGRAM
# ============================================================================


class TelegramService:
    """Servicio centralizado para manejar notificaciones de Telegram."""

    subscribed_chats: set[int] = load_subscribers()
    bot: Optional[Bot] = None
    application: Optional[Application] = None

    @classmethod
    async def initialize(cls) -> bool:
        """Inicializar el bot y la aplicacion."""
        if not TOKEN:
            logger.warning("[TELEGRAM SERVICE] No se puede inicializar: TOKEN no configurado.")
            return False
        try:
            cls.bot = Bot(token=TOKEN)
            cls.application = Application.builder().token(TOKEN).build()

            cls.application.add_handler(CommandHandler("start", cls._handle_start))
            cls.application.add_handler(CommandHandler("help", cls._handle_help))
            cls.application.add_handler(CommandHandler("webapp", cls._handle_webapp))
            cls.application.add_handler(CommandHandler("estado", cls._handle_status))
            cls.application.add_handler(CommandHandler("suscribirme", cls._handle_subscribe))
            cls.application.add_handler(CommandHandler("desuscribirme", cls._handle_unsubscribe))
            cls.application.add_handler(
                MessageHandler(filters.TEXT & ~filters.COMMAND, cls._handle_message)
            )

            logger.info("[TELEGRAM SERVICE] Servicio de Telegram inicializado correctamente")
            return True
        except Exception as e:
            logger.error(f"[TELEGRAM SERVICE] Error al inicializar Telegram: {e}")
            return False

    @classmethod
    async def start_polling(cls) -> None:
        """Iniciar polling para recibir mensajes."""
        if not cls.application:
            logger.error("Aplicacion no inicializada")
            return

        try:
            logger.info("[TELEGRAM] Iniciando polling del bot de Telegram...")
            await cls.application.initialize()
            await cls.application.start()
            await cls.application.updater.start_polling(allowed_updates=Update.ALL_TYPES)
            logger.info("[TELEGRAM] Polling de Telegram iniciado")
        except Exception as e:
            logger.error(f"[TELEGRAM] Error en polling: {e}")

    @classmethod
    async def stop_polling(cls) -> None:
        """Detener polling."""
        if cls.application:
            try:
                await cls.application.updater.stop()
                await cls.application.stop()
                logger.info("[TELEGRAM] Polling de Telegram detenido")
            except Exception as e:
                logger.error(f"[TELEGRAM] Error al detener polling: {e}")

    # ========================================================================
    # MANEJADORES DE COMANDOS
    # ========================================================================

    @staticmethod
    async def _handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        subscribe_chat(chat_id)
        message = (
            "[INICIO] Bienvenido al Sistema de Monitoreo del Embalse Arandanos\n\n"
            "pH (rango normal: 6.0 - 8.5)\n"
            "Temperatura (rango normal: 5C - 35C)\n"
            "Conductividad (rango normal: 100 - 2000 uS/cm)\n\n"
            "Comandos:\n"
            "/start - Bienvenida\n/help - Ayuda\n/webapp - Dashboard\n"
            "/suscribirme - Activar alertas\n/desuscribirme - Desactivar alertas\n"
            "/estado - Ver estado\n\n"
            "[OK] Ya estas suscrito. Recibiras alertas automaticas."
        )
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("[ABRIR] Dashboard", url=WEBAPP_URL)]]
        )
        await context.bot.send_message(chat_id=chat_id, text=message, reply_markup=keyboard)

    @staticmethod
    async def _handle_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        message = (
            "[AYUDA] Comandos Disponibles\n\n"
            "/start - Introduccion\n/help - Este mensaje\n"
            "/estado - Estado de suscripcion\n/webapp - Panel de control\n"
            "/suscribirme - Activar alertas\n/desuscribirme - Desactivar alertas\n\n"
            "Rangos normales:\npH: 6.0 - 8.5\nTemperatura: 5C - 35C\nConductividad: 100 - 2000 uS/cm"
        )
        await context.bot.send_message(chat_id=chat_id, text=message)

    @staticmethod
    async def _handle_webapp(update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        subscribe_chat(chat_id)
        message = f"PANEL DE CONTROL\n\n>>> {WEBAPP_URL} <<<"
        await context.bot.send_message(chat_id=chat_id, text=message)

    @staticmethod
    async def _handle_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        is_subscribed = chat_id in TelegramService.subscribed_chats
        status_text = "[OK] SUSCRITO" if is_subscribed else "[PAUSADO] NO SUSCRITO"
        message = (
            f"[ESTADO] Tu Suscripcion\n\n{status_text}\n"
            f"Suscriptores activos: {len(TelegramService.subscribed_chats)}\n"
            f"Tu ID: {chat_id}"
        )
        await context.bot.send_message(chat_id=chat_id, text=message)

    @staticmethod
    async def _handle_subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        subscribe_chat(chat_id)
        await context.bot.send_message(chat_id=chat_id, text="[OK] Suscripcion ACTIVADA. Recibiras alertas automaticas.")

    @staticmethod
    async def _handle_unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        unsubscribe_chat(chat_id)
        await context.bot.send_message(chat_id=chat_id, text="[PAUSADO] Desuscripcion COMPLETADA. Usa /suscribirme para reactivar.")

    @staticmethod
    async def _handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        await context.bot.send_message(
            chat_id=chat_id,
            text="[INFO] Usa /help para ver los comandos disponibles."
        )

    # ========================================================================
    # ENVIO DE NOTIFICACIONES
    # ========================================================================

    @classmethod
    async def send_alert(cls, payload: SensorAlertPayload) -> dict[str, Any]:
        """Enviar alerta a todos los suscriptores."""
        if not cls.bot:
            return {"status": "error", "message": "Bot no inicializado"}
        if not cls.subscribed_chats:
            return {"status": "ignored", "reason": "no-subscribed-chats"}

        if not cls._is_alert_condition(payload):
            return {"status": "ignored", "reason": "values-in-range"}

        message = cls._build_alert_message(payload)
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("[VER] Dashboard", url=WEBAPP_URL)]]
        )

        sent = 0
        failed = 0
        for chat_id in list(cls.subscribed_chats):
            try:
                await cls.bot.send_message(chat_id=chat_id, text=message, reply_markup=keyboard)
                sent += 1
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"[TELEGRAM] Error enviando a {chat_id}: {e}")
                failed += 1

        return {
            "status": "ok",
            "sent": sent,
            "failed": failed,
            "subscribers": len(cls.subscribed_chats),
            "timestamp": datetime.now().isoformat(),
        }

    @classmethod
    async def send_message(cls, chat_id: int, message: str) -> bool:
        if not cls.bot:
            return False
        try:
            await cls.bot.send_message(chat_id=chat_id, text=message)
            return True
        except Exception as e:
            logger.error(f"[TELEGRAM] Error enviando a {chat_id}: {e}")
            return False

    # ========================================================================
    # UTILIDADES
    # ========================================================================

    @staticmethod
    def _is_alert_condition(payload: SensorAlertPayload) -> bool:
        ph_alert = payload.ph < 6.0 or payload.ph > 8.5
        temp_alert = payload.temperature < 5.0 or payload.temperature > 35.0
        cond_alert = payload.conductivity < 100.0 or payload.conductivity > 2000.0
        return ph_alert or temp_alert or cond_alert

    @staticmethod
    def _build_alert_message(payload: SensorAlertPayload) -> str:
        ph_status = "[FUERA RANGO]" if payload.ph < 6.0 or payload.ph > 8.5 else "[OK]"
        temp_status = "[FUERA RANGO]" if payload.temperature < 5.0 or payload.temperature > 35.0 else "[OK]"
        cond_status = "[FUERA RANGO]" if payload.conductivity < 100.0 or payload.conductivity > 2000.0 else "[OK]"
        return (
            "========== ALERTA DE MONITOREO ==========\n\n"
            f"Ubicacion: {payload.deviceName}\n"
            f"Fecha: {payload.date} {payload.time}\n\n"
            f"{ph_status} pH: {payload.ph:.2f} (rango: 6.0-8.5)\n"
            f"{temp_status} Temperatura: {payload.temperature:.2f}C (rango: 5-35)\n"
            f"{cond_status} Conductividad: {payload.conductivity:.2f} uS/cm (rango: 100-2000)\n"
        )

    @classmethod
    def get_stats(cls) -> dict[str, Any]:
        return {
            "subscribed_chats": len(cls.subscribed_chats),
            "subscribers": sorted(list(cls.subscribed_chats)),
            "bot_initialized": cls.bot is not None,
        }


# ============================================================================
# FUNCIONES DE CONVENIENCIA
# ============================================================================


async def initialize_telegram() -> bool:
    return await TelegramService.initialize()


async def start_telegram_polling() -> None:
    await TelegramService.start_polling()


async def send_sensor_alert(payload: SensorAlertPayload) -> dict[str, Any]:
    return await TelegramService.send_alert(payload)


async def send_telegram_message(chat_id: int, message: str) -> bool:
    return await TelegramService.send_message(chat_id, message)


def get_telegram_subscribers() -> set[int]:
    return TelegramService.subscribed_chats.copy()


def get_telegram_stats() -> dict[str, Any]:
    return TelegramService.get_stats()
