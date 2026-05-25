"""Tests del sistema de logging estructurado."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "backend_fastapi"))

from core.log_origins import LogLevel, LogOrigin, VALID_LEVELS, VALID_ORIGINS
from core.log_sanitizer import hash_chat_id, sanitize_details


def test_sanitize_sensitive():
    result = sanitize_details({"email": "a@b.com", "password": "secret"})
    assert result["password"] == "[REDACTED]"


def test_hash_chat_id_stable():
    assert hash_chat_id("1") == hash_chat_id("1")
    assert hash_chat_id("1") != hash_chat_id("2")


def test_origins_count():
    assert len(VALID_ORIGINS) == 7
    assert LogLevel.FATAL.value in VALID_LEVELS
