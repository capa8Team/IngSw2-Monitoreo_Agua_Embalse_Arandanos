import logging
import asyncio
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Configuración centralizada
from core.config import settings
from core.logging_config import setup_fallback_logging
from core.log_service import log_service
from core.log_origins import LogLevel, LogOrigin
from core.middleware import CorrelationIdMiddleware

# Importación de Routers
from routers.sensors import router as sensors_router
from routers.alerts import router as alerts_router
from routers.dashboard import router as dashboard_router
from routers.telegram import router as telegram_router
from routers.diagnostics import router as diagnostics_router
from services.telegram import initialize_telegram, TelegramService
from services.aws_iot import aws_iot_service
from routers.logs_router import router as logs_router
from routers.auth_jwt import router as auth_jwt_router

logger = logging.getLogger(__name__)
API_PATH_PREFIX = "/api/"

# Inicialización de la App
app = FastAPI(
    title="API Monitoreo Embalse Arandanos",
    description="API para exponer lecturas de sensores y respaldo de alertas del dashboard.",
    version="1.0.0",
)

# Middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(CorrelationIdMiddleware)

# Registro de Routers
app.include_router(auth_jwt_router, prefix="/api/auth", tags=["auth"])
app.include_router(logs_router)
app.include_router(sensors_router)
app.include_router(alerts_router)
app.include_router(dashboard_router)
app.include_router(telegram_router)
app.include_router(diagnostics_router)

# Manejo Global de Excepciones
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if API_PATH_PREFIX in request.url.path:
        return JSONResponse(status_code=exc.status_code, content={"error": True, "message": str(exc.detail)})
    return JSONResponse(status_code=exc.status_code, content={"detail": str(exc.detail)})

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error processing request")
    log_service.log(
        LogOrigin.DASHBOARD, LogLevel.FATAL, f"Excepción no controlada: {exc}",
        component="api.exception", details={"path": request.url.path, "error_type": type(exc).__name__},
        correlation_id=getattr(request.state, "correlation_id", None),
    )
    if API_PATH_PREFIX in request.url.path:
        return JSONResponse(status_code=500, content={"error": True, "message": "Error processing API request!"})
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})

# Eventos de Ciclo de Vida
@app.on_event("startup")
async def startup_event():
    logger.info("[START] Aplicacion iniciando...")
    setup_fallback_logging()
    log_service.log(LogOrigin.DASHBOARD, LogLevel.INFO, "Iniciando API", component="system.startup")
    
    # Suscriptor AWS IoT Core (MQTT → MongoDB)
    try:
        aws_iot_service.start()
    except Exception as e:
        logger.error("[AWS_IOT] Error al iniciar suscriptor: %s", e)

    # Inicializar bot en background
    try:
        if await initialize_telegram():
            asyncio.create_task(TelegramService.start_polling())
    except Exception as e:
        logger.error(f"[TELEGRAM] Error al arrancar el bot en startup: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("[STOP] Aplicacion deteniendo...")
    aws_iot_service.stop()

# Endpoints Base de Salud
@app.get("/", tags=["Health"])
def root() -> dict[str, str]:
    return {"message": "API de Monitoreo Embalse Arandanos activa"}

@app.get("/health", tags=["Health"])
def health() -> dict[str, str]:
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host=settings.API_HOST, port=settings.API_PORT, log_level="info", reload=False)