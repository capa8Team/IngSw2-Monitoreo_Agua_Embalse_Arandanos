import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # ========================================================================
    # APP & SERVER
    # ========================================================================
    API_PORT: int = 8000
    API_HOST: str = "0.0.0.0"
    APP_ENV: str = "development"
    
    # ========================================================================
    # MONGODB
    # ========================================================================
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB: str = "Arandanos"

    # ========================================================================
    # MAILERSEND
    # ========================================================================
    MAILERSEND_API_TOKEN: str | None = None
    MAILERSEND_FROM_EMAIL: str | None = None
    MAILERSEND_FROM_NAME: str = "Monitoreo Embalse Arandanos"
    MAILERSEND_TO_EMAILS: str = ""
    MAILERSEND_TEMPLATE_ID: str = "351ndgw8m7rgzqx8"
    MAILERSEND_MAX_RECIPIENTS_PER_REQUEST: int = 1

    # ========================================================================
    # TELEGRAM
    # ========================================================================
    TELEGRAM_BOT_TOKEN: str | None = None
    PUBLIC_BASE_URL: str = "http://localhost"
    WEBAPP_URL: str = "http://localhost/"

    # ========================================================================
    # LOGGING
    # ========================================================================
    LOG_DIR: str = "logs"
    LOG_FILE_MAX_BYTES: int = 5242880
    LOG_FILE_BACKUP_COUNT: int = 5

    # ========================================================================
    # AUTH & SUPABASE
    # ========================================================================
    JWT_SECRET: str = "secret"
    JWT_ACCESS_MINUTES_ADMIN: int = 30
    JWT_ACCESS_HOURS_EMPLOYEE: int = 8
    JWT_REFRESH_DAYS: int = 7
    AUTH_DEMO_PASSWORD: str = "123456789"
    SUPABASE_DB_URL: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def parsed_to_emails(self) -> List[str]:
        """Convierte el string de correos separados por coma en una lista limpia"""
        if not self.MAILERSEND_TO_EMAILS:
            return []
        return list(dict.fromkeys(email.strip() for email in self.MAILERSEND_TO_EMAILS.split(",") if email.strip()))

# Instancia global para importar en todo el proyecto
settings = Settings()