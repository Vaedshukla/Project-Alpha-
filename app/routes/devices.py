import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_claims
from app.models.device import Device
from app.models.user import User, UserRole
from app.schemas.device import DeviceCreate, DeviceOut
from app.services.email_service import send_email
from app.utils.responses import success


router = APIRouter(prefix="/devices", tags=["devices"])


@router.post("/register")
async def register_device(payload: DeviceCreate, claims=Depends(get_current_user_claims), db: AsyncSession = Depends(get_db)):
    user_id = claims.get("sub")
    device = Device(id=uuid.uuid4(), user_id=user_id, device_name=payload.device_name, mac_address=payload.mac_address, ip_address=payload.ip_address)
    db.add(device)
    await db.commit()
    await db.refresh(device)
    # notify admins
    admins = (await db.execute(select(User.email).where(User.role == UserRole.admin))).scalars().all()
    send_email("Device registered", admins, f"Device {device.device_name} registered for user {user_id}", rate_key=f"device-register:{device.id}")
    return success("registered", DeviceOut.model_validate(device).model_dump())


@router.get("")
async def list_devices(claims=Depends(get_current_user_claims), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Device).where(Device.user_id == claims.get("sub")))
    items = [DeviceOut.model_validate(d).model_dump() for d in result.scalars().all()]
    return success("ok", items)


@router.get("/{device_id}")
async def get_device(device_id: str, claims=Depends(get_current_user_claims), db: AsyncSession = Depends(get_db)):
    device = await db.get(Device, device_id)
    if not device or str(device.user_id) != claims.get("sub"):
        raise HTTPException(status_code=404, detail="Device not found")
    return success("ok", DeviceOut.model_validate(device).model_dump())


@router.delete("/{device_id}")
async def delete_device(device_id: str, claims=Depends(get_current_user_claims), db: AsyncSession = Depends(get_db)):
    device = await db.get(Device, device_id)
    if not device or str(device.user_id) != claims.get("sub"):
        raise HTTPException(status_code=404, detail="Device not found")
    await db.delete(device)
    await db.commit()
    return success("deleted", {"id": device_id})

