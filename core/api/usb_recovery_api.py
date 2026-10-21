# Path: C:\ProgramasGodMode\DGM-MAT\core\api\usb_recovery_api.py
"""Authenticated operator endpoints for local USB/ADB recovery."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from core.operator.usb_recovery import get_usb_recovery_monitor_state, usb_recovery_service

router = APIRouter(prefix="/mobile/usb-recovery", tags=["mobile-usb-recovery"])


class UsbRepairRequest(BaseModel):
    action: str = Field(min_length=1, max_length=40)
    confirm_install: bool = False

    model_config = ConfigDict(extra="forbid")


@router.get("/diagnose")
def diagnose_usb_connection():
    """Read-only inspection of ADB and the connected Android device."""
    report = usb_recovery_service.diagnose()
    report["automatic_monitor"] = get_usb_recovery_monitor_state()
    return report


@router.get("/state")
def usb_recovery_state():
    """Report the automatic recovery monitor without running any repair."""
    return get_usb_recovery_monitor_state()


@router.post("/repair")
def repair_usb_connection(request: UsbRepairRequest):
    """Run one explicit allowlisted, reversible repair or confirmed APK reinstall."""
    return usb_recovery_service.repair(
        request.action,
        confirm_install=request.confirm_install,
    )
