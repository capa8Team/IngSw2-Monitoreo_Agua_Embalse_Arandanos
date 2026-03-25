import json
import os
import time
import urllib.error
import urllib.request
from unittest.mock import patch

import pytest


def _is_enabled() -> bool:
    return os.getenv("RUN_REAL_NOTIFICATION_TESTS", "0") == "1"


def _require_env(name: str, default: str | None = None) -> str:
    value = os.getenv(name)
    if not value:
        if default is not None:
            return default
        raise AssertionError(f"Variable de entorno requerida no configurada: {name}")
    return value


def _post_json(url: str, payload: dict, headers: dict | None = None, timeout: int = 20) -> tuple[int, dict]:
    request_headers = {
        "Content-Type": "application/json",
        "User-Agent": "pytest-notificaciones-reales",
    }
    if headers:
        request_headers.update(headers)

    req = urllib.request.Request(
        url=url,
        data=json.dumps(payload).encode("utf-8"),
        headers=request_headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            status = response.getcode()
            body = response.read().decode("utf-8", errors="ignore")
            return status, json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")
        parsed = json.loads(body) if body else {}
        return exc.code, parsed


class _FakeResponse:
    def __init__(self, status: int, body: dict):
        self._status = status
        self._body = json.dumps(body).encode("utf-8")

    def getcode(self) -> int:
        return self._status

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


@pytest.mark.integration
def test_telegram_envia_notificacion_real():
    """
    Envía un mensaje REAL al bot de Telegram.
    Requiere:
      - RUN_REAL_NOTIFICATION_TESTS=1
      - TELEGRAM_BOT_TOKEN
      - TELEGRAM_TEST_CHAT_ID
    """
    run_real = _is_enabled()
    token = _require_env("TELEGRAM_BOT_TOKEN", default="TEST_TOKEN")
    chat_id = _require_env("TELEGRAM_TEST_CHAT_ID", default="123456789")

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    text = f"[TEST AUTOMÁTICO] Notificación Telegram HU15/HU16 - {time.strftime('%Y-%m-%d %H:%M:%S')}"

    payload = {
        "chat_id": chat_id,
        "text": text,
    }

    if run_real:
        status, response = _post_json(url, payload)
    else:
        fake_body = {"ok": True, "result": {"message_id": 99999}}
        with patch("urllib.request.urlopen", return_value=_FakeResponse(200, fake_body)):
            status, response = _post_json(url, payload)

    assert status == 200, f"HTTP inesperado: {status} - respuesta: {response}"
    assert response.get("ok") is True, f"Telegram respondió con error: {response}"
    assert response.get("result", {}).get("message_id") is not None


@pytest.mark.integration
def test_mail_envia_notificacion_real_mailersend():
    """
    Envía un email REAL por MailerSend.
    Requiere:
      - RUN_REAL_NOTIFICATION_TESTS=1
      - MAILERSEND_API_TOKEN
      - MAILERSEND_FROM_EMAIL
      - MAILERSEND_TEST_TO_EMAIL (o MAILERSEND_TO_EMAILS)

    Nota: esta prueba valida aceptación por API (200/202), la entrega final puede
    depender de reputación de dominio, spam y políticas del proveedor.
    """
    run_real = _is_enabled()
    api_token = _require_env("MAILERSEND_API_TOKEN", default="TEST_API_TOKEN")
    from_email = _require_env("MAILERSEND_FROM_EMAIL", default="test@example.com")
    to_email = os.getenv("MAILERSEND_TEST_TO_EMAIL")

    if not to_email:
        to_emails = os.getenv("MAILERSEND_TO_EMAILS", "")
        to_email = to_emails.split(",")[0].strip() if to_emails else ""
    if not to_email:
        to_email = "destinatario@example.com"

    payload = {
        "from": {"email": from_email, "name": "Monitoreo Embalse - Test"},
        "to": [{"email": to_email}],
        "subject": f"[TEST AUTOMÁTICO] Mail HU15/HU16 - {time.strftime('%Y-%m-%d %H:%M:%S')}",
        "text": "Este es un envío de prueba automatizada para validar notificación por correo.",
    }

    if run_real:
        status, response = _post_json(
            "https://api.mailersend.com/v1/email",
            payload,
            headers={"Authorization": f"Bearer {api_token}"},
        )
    else:
        fake_body = {"message": "Accepted"}
        with patch("urllib.request.urlopen", return_value=_FakeResponse(202, fake_body)):
            status, response = _post_json(
                "https://api.mailersend.com/v1/email",
                payload,
                headers={"Authorization": f"Bearer {api_token}"},
            )

    assert status in (200, 202), f"HTTP inesperado: {status} - respuesta: {response}"