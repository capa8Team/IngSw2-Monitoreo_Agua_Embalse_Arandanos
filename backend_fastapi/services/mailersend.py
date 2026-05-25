import logging
from datetime import datetime
import requests

from core.config import settings
from core.log_service import log_service
from core.log_origins import LogLevel
from models import AlertCreate

logger = logging.getLogger(__name__)

def chunk_recipients(recipients: list[str], chunk_size: int) -> list[list[str]]:
    if chunk_size <= 0:
        chunk_size = 1
    return [recipients[i:i + chunk_size] for i in range(0, len(recipients), chunk_size)]

def is_mailersend_recipient_limit_error(response: requests.Response) -> bool:
    if response.status_code != 422:
        return False
    text = response.text or ""
    if "MS42205" in text:
        return True
    try:
        data = response.json()
        if isinstance(data, dict):
            message_text = f"{data.get('message', '')} {data.get('code', '')}"
            if "MS42205" in message_text:
                return True
    except ValueError:
        pass
    return False

def measurement_is_out_of_range(payload: AlertCreate) -> bool:
    if payload.valor is None or payload.minimo is None or payload.maximo is None:
        return True
    return payload.valor < payload.minimo or payload.valor > payload.maximo

def send_mailersend_notification(device_name: str, sensor: str, medicion: str, now: datetime) -> None:
    if not settings.MAILERSEND_API_TOKEN or not settings.MAILERSEND_FROM_EMAIL or not settings.parsed_to_emails:
        logger.warning("MailerSend no configurado completamente en las variables de entorno.")
        log_service.log_mailersend(
            LogLevel.WARN, "MailerSend no configurado",
            details={"has_token": bool(settings.MAILERSEND_API_TOKEN), "has_from": bool(settings.MAILERSEND_FROM_EMAIL)},
        )
        return

    logger.info(f"Enviando alerta por email: {device_name} - {sensor}")

    day_names = {0: "Lunes", 1: "Martes", 2: "Miercoles", 3: "Jueves", 4: "Viernes", 5: "Sabado", 6: "Domingo"}
    day_name = day_names[now.weekday()]
    fecha = now.strftime("%Y-%m-%d")
    hora = now.strftime("%H:%M:%S")

    def build_payload(recipients: list[str]) -> dict:
        return {
            "from": {
                "email": settings.MAILERSEND_FROM_EMAIL,
                "name": settings.MAILERSEND_FROM_NAME,
            },
            "to": [{"email": email} for email in recipients],
            "subject": f"⚠️ Alerta: {sensor} fuera de rango - {device_name}",
            "template_id": settings.MAILERSEND_TEMPLATE_ID,
            "personalization": [
                {
                    "email": email,
                    "data": {
                        "DEVICE_NAME": device_name, "DAY_NAME": day_name,
                        "FECHA": fecha, "HORA": hora, "SENSOR": sensor, "MEDICION": medicion,
                    }
                }
                for email in recipients
            ],
        }

    headers = {
        "Authorization": f"Bearer {settings.MAILERSEND_API_TOKEN}",
        "Content-Type": "application/json",
    }

    recipient_batches = chunk_recipients(settings.parsed_to_emails, settings.MAILERSEND_MAX_RECIPIENTS_PER_REQUEST)

    for recipients_batch in recipient_batches:
        try:
            response = requests.post(
                "https://api.mailersend.com/v1/email",
                json=build_payload(recipients_batch),
                headers=headers,
                timeout=10,
            )
        except requests.RequestException as exc:
            logger.error(f"Error enviando email a lote {recipients_batch}: {exc}")
            log_service.log_mailersend(LogLevel.WARN, f"Error de red MailerSend: {exc}", recipient_count=len(recipients_batch))
            continue

        if response.status_code in [200, 202]:
            logger.info(f"Email enviado exitosamente a lote {recipients_batch}")
            log_service.log_mailersend(LogLevel.INFO, "Correo de alerta enviado", http_status=response.status_code, recipient_count=len(recipients_batch))
            continue

        if is_mailersend_recipient_limit_error(response) and len(recipients_batch) > 1:
            logger.warning("MailerSend limito cantidad de destinatarios en lote. Reintentando 1 a 1.")
            for email in recipients_batch:
                try:
                    single_response = requests.post(
                        "https://api.mailersend.com/v1/email", json=build_payload([email]), headers=headers, timeout=10,
                    )
                    if single_response.status_code in [200, 202]:
                        logger.info(f"Email enviado exitosamente a {email}")
                    else:
                        logger.error("Respuesta MailerSend individual %s para %s", single_response.status_code, email)
                except requests.RequestException as single_exc:
                    logger.error(f"Error enviando email individual a {email}: {single_exc}")
            continue

        logger.error("Respuesta MailerSend para lote %s: %s - %s", recipients_batch, response.status_code, response.text)
        log_service.log_mailersend(
            LogLevel.WARN if response.status_code < 500 else LogLevel.FATAL,
            "Respuesta MailerSend no exitosa",
            http_status=response.status_code,
            recipient_count=len(recipients_batch),
            details={"batch": recipients_batch},
        )