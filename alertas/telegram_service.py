"""
Servicio de Telegram para notificaciones de alertas en tiempo real.
Incluye polling automático y gestión de suscriptores.
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
# CONFIGURACIÓN
# ============================================================================

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN no está configurado en variables de entorno.")

PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "http://localhost:8000")
WEBAPP_URL = os.getenv("WEBAPP_URL", f"{PUBLIC_BASE_URL}/")

BASE_DIR = Path(__file__).resolve().parent
SUBSCRIBERS_FILE = BASE_DIR / "telegram_subscribers.json"

# ============================================================================
# GESTIÓN DE SUSCRIPTORES
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
    """Agregar o actualizar suscripción."""
    TelegramService.subscribed_chats.add(chat_id)
    save_subscribers(TelegramService.subscribed_chats)


def unsubscribe_chat(chat_id: int) -> None:
    """Remover suscripción."""
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
    @classmethod
    async def initialize(cls) -> bool:
        """Inicializar el bot y la aplicación."""
        try:
            cls.bot = Bot(token=TOKEN)
            cls.application = Application.builder().token(TOKEN).build()

            # Agregar handlers
            cls.application.add_handler(CommandHandler("start", cls._handle_start))
            cls.application.add_handler(CommandHandler("help", cls._handle_help))
            cls.application.add_handler(CommandHandler("webapp", cls._handle_webapp))
            cls.application.add_handler(CommandHandler("estado", cls._handle_status))
            cls.application.add_handler(
                CommandHandler("suscribirme", cls._handle_subscribe)
            )
            cls.application.add_handler(
                CommandHandler("desuscribirme", cls._handle_unsubscribe)
            )
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
            logger.error("Aplicación no inicializada")
            return

        try:
            logger.info("[TELEGRAM] Iniciando polling del bot de Telegram...")
            await cls.application.initialize()
            await cls.application.start()
            await cls.application.updater.start_polling(
                allowed_updates=Update.ALL_TYPES
            )
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
        """Maneja /start - bienvenida y suscripción automática."""
        chat_id = update.effective_chat.id
        subscribe_chat(chat_id)

        message = (
            "[INICIO] Bienvenido al Sistema de Monitoreo del Embalse Arandanos\n\n"
            "=== QUE ES ESTE BOT ===\n"
            "Este bot te proporciona notificaciones en TIEMPO REAL sobre el estado del agua "
            "del Embalse Arandanos. Monitorea continuamente tres parametros clave:\n\n"
            "  * pH del agua (rango normal: 6.0 - 8.5)\n"
            "  * Temperatura (rango normal: 5°C - 35°C)\n"
            "  * Conductividad (rango normal: 100 - 2000 uS/cm)\n\n"
            "Cuando alguno de estos valores sale del rango permitido, RECIBIRAS UNA ALERTA INMEDIATA.\n\n"
            "=== CARACTERISTICAS ===\n"
            "✓ Alertas en tiempo real cuando hay problemas\n"
            "✓ Dashboard embebido para visualizar datos\n"
            "✓ Historial completo de mediciones\n"
            "✓ Suscripcion flexible (puedes pausar en cualquier momento)\n"
            "✓ Funciona con datos reales (sensores) o simulados (para pruebas)\n\n"
            "=== COMANDOS DISPONIBLES ===\n"
            "/start - Mostrar este mensaje de bienvenida\n"
            "/help - Ver lista de comandos\n"
            "/webapp - Acceder al panel de control\n"
            "/suscribirme - Activar recepcion de alertas\n"
            "/desuscribirme - Dejar de recibir alertas\n"
            "/estado - Ver estado de suscripcion actual\n\n"
            "[OK] Ya estás suscrito. Recibirás alertas automáticas cuando sea necesario."
        )

        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("[ABRIR] Dashboard", url=WEBAPP_URL)]]
        )

        await context.bot.send_message(
            chat_id=chat_id, text=message, reply_markup=keyboard
        )

    @staticmethod
    async def _handle_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja /help - muestra información detallada."""
        chat_id = update.effective_chat.id
        message = (
            "[AYUDA] Comandos Disponibles en el Bot\n\n"
            "=== NAVEGACION ===\n"
            "/start - Ver introduccion y bienvenida\n"
            "/help - Este mensaje\n"
            "/estado - Ver tu estado de suscripcion actual\n\n"
            "=== ACCESO AL DASHBOARD ===\n"
            "/webapp - Abre el panel de control en tu navegador\n\n"
            "=== GESTIONAR SUSCRIPCION ===\n"
            "/suscribirme - Activar alertas automaticas\n"
            "/desuscribirme - Desactivar alertas\n\n"
            "=== INFORMACION ===\n"
            "El dashboard te permite:\n"
            "  * Ver valores actuales de sensores (pH, temperatura, conductividad)\n"
            "  * Ver historico de mediciones\n"
            "  * Recibir alertas cuando hay problemas\n"
            "  * Funciona con datos REALES (sensores Arduino) o SIMULADOS (pruebas)\n\n"
            "=== RANGOS NORMALES ===\n"
            "pH: 6.0 - 8.5\n"
            "Temperatura: 5°C - 35°C\n"
            "Conductividad: 100 - 2000 µS/cm\n\n"
            "Cuando un valor sale de estos rangos, recibirás una ALERTA INMEDIATA."
        )
        await context.bot.send_message(
            chat_id=chat_id, text=message
        )

    @staticmethod
    async def _handle_webapp(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja /webapp - redirije al dashboard del frontend."""
        chat_id = update.effective_chat.id
        subscribe_chat(chat_id)

        message = (
            "PANEL DE CONTROL - ACCESO DIRECTO\n\n"
            "Clickea el link de abajo para abrir el dashboard:\n\n"
            f">>> {WEBAPP_URL} <<<\n\n"
            "En el dashboard podras:\n"
            "✓ Ver valores en tiempo real de todos los sensores\n"
            "✓ pH, Temperatura y Conductividad\n"
            "✓ Graficos e historial de datos\n"
            "✓ Todas las alertas registradas\n"
            "✓ Control y monitoreo 24/7\n\n"
            "Presiona o toca el link para abrir en tu navegador"
        )

        await context.bot.send_message(
            chat_id=chat_id,
            text=message,
        )

    @staticmethod
    async def _handle_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja /estado - ver estado de suscripcion."""
        chat_id = update.effective_chat.id
        is_subscribed = chat_id in TelegramService.subscribed_chats
        
        if is_subscribed:
            status_text = "[OK] SUSCRITO - Recibirás alertas automáticas"
        else:
            status_text = "[PAUSADO] NO SUSCRITO - No recibirás alertas"
        
        message = (
            "[ESTADO] Tu Suscripcion al Sistema de Alertas\n\n"
            f"Estado actual: {status_text}\n\n"
            f"Total de suscriptores activos: {len(TelegramService.subscribed_chats)}\n"
            f"Tu ID de chat: {chat_id}\n\n"
            "Para cambiar tu estado de suscripcion usa:\n"
            "  /suscribirme - Activar alertas\n"
            "  /desuscribirme - Desactivar alertas"
        )

        await context.bot.send_message(
            chat_id=chat_id,
            text=message,
        )

    @staticmethod
    async def _handle_subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja /suscribirme."""
        chat_id = update.effective_chat.id
        was_subscribed = chat_id in TelegramService.subscribed_chats
        subscribe_chat(chat_id)
        
        if was_subscribed:
            message = "[OK] Ya estabas suscrito. Seguirás recibiendo alertas."
        else:
            message = (
                "[OK] Suscripcion ACTIVADA\n\n"
                "A partir de ahora recibiras alertas automaticas cuando:\n"
                "  * pH fuera de rango (6.0 - 8.5)\n"
                "  * Temperatura fuera de rango (5°C - 35°C)\n"
                "  * Conductividad fuera de rango (100 - 2000 µS/cm)\n\n"
                "Usa /desuscribirme en cualquier momento para pausar las alertas."
            )
        
        await context.bot.send_message(
            chat_id=chat_id,
            text=message,
        )

    @staticmethod
    async def _handle_unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja /desuscribirme."""
        chat_id = update.effective_chat.id
        was_subscribed = chat_id in TelegramService.subscribed_chats
        unsubscribe_chat(chat_id)
        
        if was_subscribed:
            message = (
                "[PAUSADO] Desuscripcion COMPLETADA\n\n"
                "Ya no recibiras alertas automaticas del sistema.\n"
                "Siempre puedes reactivarlas con /suscribirme"
            )
        else:
            message = "[INFO] Ya no estabas suscrito. Usa /suscribirme para activar alertas."
        
        await context.bot.send_message(
            chat_id=chat_id,
            text=message,
        )

    @staticmethod
    async def _handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja mensajes de texto generales."""
        chat_id = update.effective_chat.id
        message_text = update.message.text if update.message else ""
        
        response = (
            "[INFO] El bot no reconoce ese texto como comando.\n\n"
            "Si escribiste un comando, usa el formato correcto con /\n"
            f"Texto recibido: {message_text}\n\n"
            "Comandos disponibles:\n"
            "/start - Ver introduccion\n"
            "/help - Ver todos los comandos\n"
            "/dashboard - Acceder al panel\n"
            "/estado - Ver tu suscripcion\n\n"
            "Usa /help para mas informacion."
        )
        
        await context.bot.send_message(
            chat_id=chat_id,
            text=response,
        )

    # ========================================================================
    # ENVÍO DE NOTIFICACIONES
    # ========================================================================

    @classmethod
    async def send_alert(cls, payload: SensorAlertPayload) -> dict[str, Any]:
        """Enviar alerta a todos los suscriptores."""
        if not cls.bot:
            return {"status": "error", "message": "Bot no inicializado"}

        if not cls.subscribed_chats:
            return {
                "status": "ignored",
                "reason": "no-subscribed-chats",
                "message": "No hay suscriptores",
            }

        # Verificar si hay valores fuera de rango
        has_alert = cls._is_alert_condition(payload)
        if not has_alert:
            return {"status": "ignored", "reason": "values-in-range"}

        # Construir mensaje
        message = cls._build_alert_message(payload)
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("[VER] Dashboard", url=WEBAPP_URL)]]
        )

        # Enviar a todos los suscriptores
        sent = 0
        failed = 0
        for chat_id in list(cls.subscribed_chats):
            try:
                await cls.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    reply_markup=keyboard,
                )
                sent += 1
                await asyncio.sleep(0.1)  # Evitar rate limiting
            except Exception as e:
                logger.error(f"[TELEGRAM] Error enviando mensaje a {chat_id}: {e}")
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
        """Enviar mensaje directo a un chat."""
        if not cls.bot:
            return False
        try:
            await cls.bot.send_message(chat_id=chat_id, text=message)
            return True
        except Exception as e:
            logger.error(f"[TELEGRAM] Error enviando mensaje a {chat_id}: {e}")
            return False

    # ========================================================================
    # UTILIDADES
    # ========================================================================

    @staticmethod
    def _is_alert_condition(payload: SensorAlertPayload) -> bool:
        """Verificar si hay algún valor fuera de rango."""
        ph_alert = payload.ph < 6.0 or payload.ph > 8.5
        temp_alert = payload.temperature < 5.0 or payload.temperature > 35.0
        cond_alert = payload.conductivity < 100.0 or payload.conductivity > 2000.0
        return ph_alert or temp_alert or cond_alert

    @staticmethod
    def _build_alert_message(payload: SensorAlertPayload) -> str:
        """Construir mensaje formateado de alerta."""
        ph_status = "[FUERA RANGO]" if payload.ph < 6.0 or payload.ph > 8.5 else "[OK]"
        temp_status = "[FUERA RANGO]" if payload.temperature < 5.0 or payload.temperature > 35.0 else "[OK]"
        cond_status = "[FUERA RANGO]" if payload.conductivity < 100.0 or payload.conductivity > 2000.0 else "[OK]"

        return (
            "========== ALERTA DE MONITOREO ==========\n\n"
            f"Ubicacion: {payload.deviceName}\n"
            f"Fecha: {payload.date}\n"
            f"Hora: {payload.time}\n\n"
            "====== PARAMETROS ======\n"
            f"{ph_status} pH: {payload.ph:.2f} (rango seguro: 6.0-8.5)\n"
            f"{temp_status} Temperatura: {payload.temperature:.2f}°C (rango seguro: 5-35°C)\n"
            f"{cond_status} Conductividad: {payload.conductivity:.2f} µS/cm (rango seguro: 100-2000)\n\n"
            "====== ACCIONES ======\n"
            "- Revisa el dashboard para mas detalles\n"
            "- Contacta al administrador si es critico\n"
            "- El sistema sigue monitorizando automaticamente\n"
        )

    @classmethod
    def get_stats(cls) -> dict[str, Any]:
        """Obtener estadísticas del servicio."""
        return {
            "subscribed_chats": len(cls.subscribed_chats),
            "subscribers": sorted(list(cls.subscribed_chats)),
            "bot_initialized": cls.bot is not None,
        }


# ============================================================================
# FUNCIONES DE CONVENIENCIA
# ============================================================================


async def initialize_telegram() -> bool:
    """Inicializar el servicio de Telegram."""
    return await TelegramService.initialize()


async def start_telegram_polling() -> None:
    """Iniciar polling en background."""
    await TelegramService.start_polling()


async def send_sensor_alert(payload: SensorAlertPayload) -> dict[str, Any]:
    """Enviar alerta de sensor."""
    return await TelegramService.send_alert(payload)


async def send_telegram_message(chat_id: int, message: str) -> bool:
    """Enviar mensaje a chat específico."""
    return await TelegramService.send_message(chat_id, message)


def get_telegram_subscribers() -> set[int]:
    """Obtener lista de suscriptores."""
    return TelegramService.subscribed_chats.copy()


def get_telegram_stats() -> dict[str, Any]:
    """Obtener estadísticas."""
    return TelegramService.get_stats()
