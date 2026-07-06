from pathlib import Path
from typing import List, Self

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Raíz del repo (backend_fastapi/core -> parents[2])
PROJECT_ROOT = Path(__file__).resolve().parents[2]
IOT_CORE_DIR = PROJECT_ROOT / "IotCore"
# Prefijo de archivos generados en AWS IoT (carpeta IotCore/)
IOT_CERT_ID = "4bb52c4252bfb1b205ea09eb59a655000d689f05c3b72aa689f775caa548496e"
# Endpoint y topic del sketch ReciberConPostMQTT (secrets.h / ReciberConPostMQTT.ino)
AWS_IOT_DEFAULT_ENDPOINT = "a319gtmfe1r2jb-ats.iot.sa-east-1.amazonaws.com"
AWS_IOT_DEFAULT_TOPIC = "boya/sensores"


class Settings(BaseSettings):
    # ========================================================================
    # APP & SERVER
    # ========================================================================
    API_PORT: int = 8000
    API_HOST: str = "0.0.0.0"
    APP_ENV: str = "development"
    
    # ========================================================================
    # MONGODB (Docker Compose o instancia local)
    # ========================================================================
    MONGODB_URL: str = "mongodb://admin:Panconpalta1@localhost:27017/?authSource=admin"
    MONGODB_DB: str = "Arandanos"

    # ========================================================================
    # AWS IoT Core (MQTT — telemetría de sensores)
    # ========================================================================
    AWS_IOT_ENABLED: bool = False
    AWS_IOT_ENDPOINT: str = AWS_IOT_DEFAULT_ENDPOINT
    AWS_IOT_PORT: int = 8883
    AWS_IOT_CLIENT_ID: str = "embalse-backend"
    AWS_IOT_TOPIC: str = AWS_IOT_DEFAULT_TOPIC
    AWS_IOT_CERT_PATH: str | None = None
    AWS_IOT_KEY_PATH: str | None = None
    AWS_IOT_CA_PATH: str | None = None
    AWS_IOT_DEFAULT_DEVICE_ID: str = "boya"

    model_config = SettingsConfigDict(
        env_file=(str(PROJECT_ROOT / ".env"), ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def resolve_iot_cert_paths(self) -> Self:
        """Rutas por defecto a IotCore/ (mismos certificados que ReciberConPostMQTT)."""
        if not self.AWS_IOT_CERT_PATH:
            self.AWS_IOT_CERT_PATH = str(IOT_CORE_DIR / f"{IOT_CERT_ID}-certificate.pem.crt")
        if not self.AWS_IOT_KEY_PATH:
            self.AWS_IOT_KEY_PATH = str(IOT_CORE_DIR / f"{IOT_CERT_ID}-private.pem.key")
        if not self.AWS_IOT_CA_PATH:
            self.AWS_IOT_CA_PATH = str(IOT_CORE_DIR / "AmazonRootCA1.pem")
        return self

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
    SUPABASE_URL: str | None = None
    SUPABASE_ANON_KEY: str | None = None
    VITE_SUPABASE_URL: str | None = None
    VITE_SUPABASE_ANON_KEY: str | None = None
    DEFAULT_ORGANIZATION_SLUG: str = "embalse-arandanos"

    # ========================================================================
    # OPENWEATHER API
    # ========================================================================
    OPENWEATHER_API_KEY: str | None = None

    # ========================================================================
    # REDIS (caché cache-aside)
    # ========================================================================
    REDIS_URL: str | None = None

    @property
    def openweather_api_key(self) -> str | None:
        """Obtiene la clave de API de OpenWeather desde variables de entorno."""
        return self.OPENWEATHER_API_KEY

    @property
    def parsed_to_emails(self) -> List[str]:
        """Convierte el string de correos separados por coma en una lista limpia."""
        if not self.MAILERSEND_TO_EMAILS:
            return []
        return list(dict.fromkeys(email.strip() for email in self.MAILERSEND_TO_EMAILS.split(",") if email.strip()))

# Instancia global para importar en todo el proyecto
settings = Settings()