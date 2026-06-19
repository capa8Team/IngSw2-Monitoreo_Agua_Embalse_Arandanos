import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from core.tenant import TenantContext, get_tenant_context
from models import DeviceGroupCreate, DeviceGroupResponse, DeviceGroupUpdate
from services.mongodb import (
    create_device_group,
    delete_device_group,
    get_all_device_groups,
    get_device_group,
    update_device_group,
)
from core.log_service import log_service
from core.log_origins import LogLevel, LogOrigin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/device-groups", tags=["Grupos de dispositivos"])


def _ensure_group_in_tenant(group_id: str, tenant: TenantContext) -> dict:
    from services.mongodb import db

    if db is None:
        raise HTTPException(status_code=404, detail="Grupo no encontrado")
    doc = db["device_groups"].find_one({"_id": group_id, "active": {"$ne": False}})
    if not doc:
        raise HTTPException(status_code=404, detail="Grupo no encontrado")
    org_id = tenant.organization_id
    if org_id and doc.get("organization_id") and doc.get("organization_id") != org_id:
        raise HTTPException(status_code=404, detail="Grupo no encontrado")
    slug = tenant.organization_slug
    if slug and doc.get("organization_slug") and doc.get("organization_slug") != slug:
        raise HTTPException(status_code=404, detail="Grupo no encontrado")
    group = get_device_group(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Grupo no encontrado")
    return group


@router.get("", response_model=list[DeviceGroupResponse])
def list_device_groups(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    active_only: bool = Query(True),
):
    """Lista grupos/embalses de la organización activa."""
    groups = get_all_device_groups(active_only=active_only, org_filter=tenant.device_filter())
    return [DeviceGroupResponse(**group) for group in groups]


@router.post("", response_model=DeviceGroupResponse, status_code=201)
async def create_group(
    payload: DeviceGroupCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
) -> DeviceGroupResponse:
    """Crea un grupo de dispositivos (embalse / ubicación compartida)."""
    group = create_device_group(
        name=payload.name,
        latitude=payload.latitude,
        longitude=payload.longitude,
        description=payload.description,
        location_label=payload.location_label,
        city=payload.city,
        organization_id=tenant.organization_id,
        organization_slug=tenant.organization_slug,
    )
    if not group:
        raise HTTPException(status_code=500, detail="Error creando grupo")

    log_service.log(
        LogOrigin.DASHBOARD,
        LogLevel.INFO,
        f"Nuevo grupo creado: {payload.name}",
        component="api.device_groups",
        operation="create",
        details={"organization_id": tenant.organization_id},
    )
    return DeviceGroupResponse(**group)


@router.get("/{group_id}", response_model=DeviceGroupResponse)
def get_group_info(
    group_id: str,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
) -> DeviceGroupResponse:
    group = _ensure_group_in_tenant(group_id, tenant)
    return DeviceGroupResponse(**group)


@router.put("/{group_id}", response_model=DeviceGroupResponse)
async def update_group_info(
    group_id: str,
    payload: DeviceGroupUpdate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
) -> DeviceGroupResponse:
    _ensure_group_in_tenant(group_id, tenant)
    group = update_device_group(
        group_id=group_id,
        name=payload.name,
        description=payload.description,
        location_label=payload.location_label,
        city=payload.city,
        latitude=payload.latitude,
        longitude=payload.longitude,
        active=payload.active,
    )
    if not group:
        raise HTTPException(status_code=404, detail="Grupo no encontrado")
    return DeviceGroupResponse(**group)


@router.delete("/{group_id}", status_code=204)
async def delete_group_endpoint(
    group_id: str,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
):
    _ensure_group_in_tenant(group_id, tenant)
    if not delete_device_group(group_id):
        raise HTTPException(status_code=404, detail="Grupo no encontrado")
