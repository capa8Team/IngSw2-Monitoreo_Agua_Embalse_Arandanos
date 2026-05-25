import logging
from fastapi import APIRouter, HTTPException

from models import AlertRecord, AlertCreate
from services.mongodb import chile_now
from services.mailersend import measurement_is_out_of_range, send_mailersend_notification
from core.log_service import log_service
from core.log_origins import LogLevel

# Importación temporal hasta que movamos telegram a services/telegram.py
from services.telegram import send_sensor_alert, SensorAlertPayload

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/alerts", tags=["Alertas"])

# Mantenemos el estado de las alertas en memoria aquí por ahora
alerts_store: list[AlertRecord] = [
    AlertRecord(
        id=1, fecha="2026-03-24", hora="14:30",
        embalse="Embalse Norte", sensor="Conductividad", medicion="1.2 mS/cm"
    )
]

@router.get("", response_model=list[AlertRecord])
def list_alerts() -> list[AlertRecord]:
    return alerts_store

@router.post("", response_model=AlertRecord, status_code=201)
async def create_alert(payload: AlertCreate) -> AlertRecord:
    now = chile_now()
    device_name = payload.nombreDispositivo or payload.embalse
    new_alert = AlertRecord(
        id=(alerts_store[-1].id + 1) if alerts_store else 1,
        fecha=now.strftime("%Y-%m-%d"),
        hora=now.strftime("%H:%M"),
        embalse=device_name,
        sensor=payload.sensor,
        medicion=payload.medicion,
    )

    if measurement_is_out_of_range(payload):
        # Disparar alerta por Email
        send_mailersend_notification(device_name, payload.sensor, payload.medicion, now)
        
        # Disparar alerta por Telegram
        try:
            telegram_alert = SensorAlertPayload(
                deviceName=device_name,
                ph=float(payload.valor) if payload.valor else 0.0,
                temperature=float(payload.valor) if payload.valor else 0.0,
                conductivity=float(payload.valor) if payload.valor else 0.0,
                date=now.strftime("%Y-%m-%d"),
                time=now.strftime("%H:%M:%S"),
            )
            result = await send_sensor_alert(telegram_alert)
            sent = int(result.get("sent", 0) or 0)
            failed = int(result.get("failed", 0) or 0)
            
            level = LogLevel.INFO if failed == 0 else LogLevel.WARN
            if sent == 0 and failed > 0:
                level = LogLevel.FATAL
                
            log_service.log_telegram(
                level, "Alerta de sensor enviada por Telegram",
                sent_count=sent, failed_count=failed,
                details={"device": device_name, "sensor": payload.sensor},
            )
        except Exception as e:
            logger.error(f"[TELEGRAM] Error enviando alerta: {e}")
            log_service.log_telegram(LogLevel.FATAL, f"Error enviando alerta Telegram: {e}", details={"error_type": type(e).__name__})

    alerts_store.append(new_alert)
    return new_alert

@router.get("/{alert_id}", response_model=AlertRecord)
def get_alert(alert_id: int) -> AlertRecord:
    for alert in alerts_store:
        if alert.id == alert_id:
            return alert
    raise HTTPException(status_code=404, detail="Alerta no encontrada")