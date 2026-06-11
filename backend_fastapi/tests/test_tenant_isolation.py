"""Pruebas unitarias de aislamiento multi-organización (sin DB externa)."""
from __future__ import annotations

import pytest
from fastapi import HTTPException

from core.tenant import TenantContext, ensure_device_in_tenant


def _tenant(org_id: str, slug: str = "org-a") -> TenantContext:
    return TenantContext(
        organization_id=org_id,
        organization_slug=slug,
        user_id="user-1",
        email="u@example.com",
        organizations=[],
    )


def test_device_with_other_org_id_is_rejected():
    device = {"organization_id": "org-b", "organization_slug": "org-b"}
    with pytest.raises(HTTPException) as exc:
        ensure_device_in_tenant(device, _tenant("org-a", "org-a"))
    assert exc.value.status_code == 403


def test_device_with_matching_org_id_is_allowed():
    device = {"organization_id": "org-a", "organization_slug": "org-a"}
    ensure_device_in_tenant(device, _tenant("org-a", "org-a"))


def test_legacy_device_slug_mismatch_is_rejected():
    device = {"organization_slug": "org-b"}
    with pytest.raises(HTTPException) as exc:
        ensure_device_in_tenant(device, _tenant("org-a", "org-a"))
    assert exc.value.status_code == 403


def test_legacy_device_same_slug_is_allowed():
    device = {"organization_slug": "org-a"}
    ensure_device_in_tenant(device, _tenant("org-a", "org-a"))
