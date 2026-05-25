import logging
from datetime import datetime, timezone
from fastapi import APIRouter
from models import DashboardResponse, SensorData, Metadata
from services.mongodb import update_dashboard_state_from_mongodb
from core.log_service import log_service
from core.log_origins import LogLevel, LogOrigin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


def _empty_dashboard() -> DashboardResponse:
    now = datetime.now(timezone.utc)
    empty_sensor = SensorData(
        value=0.0, min=0.0, max=0.0, safeMax=0.0,
        lastUpdated=now, status="stable",
    )
    return DashboardResponse(
        ph=empty_sensor,
        temperature=empty_sensor,
        conductivity=empty_sensor,
        metadata=Metadata(
            systemStatus="degraded",
            arduinoConnected=False,
            lastSync=now,
            uptime=0,
            activeSensors=0,
        ),
        battery=0,
    )


@router.get("", response_model=DashboardResponse)
def get_dashboard_data() -> DashboardResponse:
    state = update_dashboard_state_from_mongodb()
    if state is None:
        logger.warning("No hay datos en la BD. Retornando estado vacío.")
        return _empty_dashboard()
    log_service.log(LogOrigin.DASHBOARD, LogLevel.INFO, "Dashboard data fetched", component="api.dashboard")
    return state
