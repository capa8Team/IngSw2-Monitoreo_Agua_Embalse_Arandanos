from datetime import datetime
import json
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo


app = FastAPI()

BASE_DIR = Path(__file__).resolve().parents[1]
DIST_DIR = BASE_DIR / "dist"

if DIST_DIR.exists():
    app.mount("/webapp", StaticFiles(directory=str(DIST_DIR), html=True), name="webapp")

# Configure with environment variables when available.
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8744757844:AAGWn_DJtMf7wMDng4IgYHrrcH-HgdjH364")
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "https://budgetary-hunter-overdramatically.ngrok-free.dev")
WEBAPP_URL = os.getenv("WEBAPP_URL", f"{PUBLIC_BASE_URL}/webapp/")

bot = Bot(token=TOKEN)
SUBSCRIBERS_FILE = BASE_DIR / "alertas" / "telegram_subscribers.json"


def load_subscribers() -> set[int]:
    if not SUBSCRIBERS_FILE.exists():
        return set()
    try:
        data = json.loads(SUBSCRIBERS_FILE.read_text(encoding="utf-8"))
        return {int(chat_id) for chat_id in data if str(chat_id).strip()}
    except Exception:
        return set()


def save_subscribers(subscribers: set[int]) -> None:
    SUBSCRIBERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SUBSCRIBERS_FILE.write_text(
        json.dumps(sorted(subscribers), ensure_ascii=True, indent=2),
        encoding="utf-8",
    )


def subscribe_chat(chat_id: int) -> None:
    if chat_id not in subscribed_chats:
        subscribed_chats.add(chat_id)
        save_subscribers(subscribed_chats)


subscribed_chats: set[int] = load_subscribers()


class SensorAlertPayload(BaseModel):
    deviceName: str
    ph: float
    temperature: float
    conductivity: float
    date: str
    time: str


def is_out_of_range(value: float, minimum: float, maximum: float) -> bool:
    return value < minimum or value > maximum


def build_sensor_status_lines(payload: SensorAlertPayload) -> list[str]:
    ph_alert = is_out_of_range(payload.ph, 6.0, 8.5)
    temp_alert = is_out_of_range(payload.temperature, 5.0, 35.0)
    cond_alert = is_out_of_range(payload.conductivity, 100.0, 2000.0)

    return [
        f"pH: {payload.ph:.2f} ({'FUERA DE RANGO' if ph_alert else 'normal'})",
        f"Temperatura: {payload.temperature:.2f} C ({'FUERA DE RANGO' if temp_alert else 'normal'})",
        f"Conductividad: {payload.conductivity:.2f} uS/cm ({'FUERA DE RANGO' if cond_alert else 'normal'})",
    ]


async def send_notification_to_chat(chat_id: int, payload: SensorAlertPayload) -> None:
    lines = build_sensor_status_lines(payload)
    message = (
        "ALERTA DEL SISTEMA DE MONITOREO\n"
        f"Embalse/Sector: {payload.deviceName}\n"
        f"Fecha: {payload.date}\n"
        f"Hora: {payload.time}\n\n"
        + "\n".join(lines)
    )

    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Abrir Dashboard", web_app=WebAppInfo(url=WEBAPP_URL))]]
    )

    await bot.send_message(chat_id=chat_id, text=message, reply_markup=keyboard)


async def enviar_alerta_telegram(chat_id: int, sensor_id: str, nivel_actual: float, umbral: float):
    mensaje = (
        "ALERTA DE SISTEMA\n"
        f"Sensor: {sensor_id}\n"
        "Estado: Critico\n"
        f"Nivel: {nivel_actual}%\n"
        f"Umbral configurado: {umbral}%\n\n"
        "Usa /webapp para gestionar."
    )

    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Abrir Dashboard", web_app=WebAppInfo(url=WEBAPP_URL))]]
    )

    await bot.send_message(
        chat_id=chat_id,
        text=mensaje,
        reply_markup=keyboard,
    )


@app.post("/telegram-webhook")
async def telegram_webhook(request: Request):
    data = await request.json()

    if "message" not in data:
        return {"status": "ignored"}

    chat_id = data["message"]["chat"]["id"]
    text = data["message"].get("text", "")

    if text == "/start":
        subscribe_chat(chat_id)
        await bot.send_message(
            chat_id=chat_id,
            text="Bienvenido al sistema de alertas del embalse. Usa /webapp para abrir el dashboard."
                 "\n\nTu chat ya quedo suscrito para recibir alertas automaticas.",
        )
    elif text == "/webapp":
        subscribe_chat(chat_id)
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("Ver Dashboard", web_app=WebAppInfo(url=WEBAPP_URL))]]
        )
        await bot.send_message(
            chat_id=chat_id,
            text="Haz clic abajo para acceder al panel de control:",
            reply_markup=keyboard,
        )
    elif text == "/suscribirme":
        subscribe_chat(chat_id)
        await bot.send_message(
            chat_id=chat_id,
            text="Suscripcion activada. Recibiras alertas automaticas del sistema.",
        )
    else:
        await bot.send_message(
            chat_id=chat_id,
            text="Acceso restringido. Este bot solo responde al comando /webapp.",
        )

    return {"status": "ok"}


@app.post("/api/notify-sensor-alert")
async def notify_sensor_alert(payload: SensorAlertPayload) -> dict[str, Any]:
    if not subscribed_chats:
        return {
            "status": "ignored",
            "reason": "no-subscribed-chats",
            "message": "Nadie ha ejecutado /start en el bot todavia.",
        }

    has_alert = (
        is_out_of_range(payload.ph, 6.0, 8.5)
        or is_out_of_range(payload.temperature, 5.0, 35.0)
        or is_out_of_range(payload.conductivity, 100.0, 2000.0)
    )
    if not has_alert:
        return {
            "status": "ignored",
            "reason": "values-in-range",
        }

    sent = 0
    failed = 0
    for chat_id in list(subscribed_chats):
        try:
            await send_notification_to_chat(chat_id, payload)
            sent += 1
        except Exception:
            failed += 1

    return {
        "status": "ok",
        "sent": sent,
        "failed": failed,
        "subscribers": len(subscribed_chats),
    }


@app.get("/test-alerta/{chat_id}")
async def test_alerta(chat_id: int):
    await enviar_alerta_telegram(chat_id, "Sector-Norte-01", 12.5, 20.0)
    return {"message": "Alerta de prueba enviada", "timestamp": datetime.utcnow().isoformat()}
