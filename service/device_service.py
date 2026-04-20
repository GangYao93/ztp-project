from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from schemas.response import Response
from VO.DeviceVO import DeviceRegister
from entity.device_info import DeviceInfo
import logging


log = logging.getLogger("device_service")

async def register_device(device: DeviceRegister, db: AsyncSession):
    device_info = DeviceInfo(**device.model_dump())
    stmt = select(DeviceInfo).where(DeviceInfo.mac == device_info.mac)
    res = await db.execute(stmt)
    target_device = res.scalars().first()
    if target_device:
        if target_device.ip_address != device.ip_address:
            target_device.ip_address = device_info.ip_address
            log.info(f"Old device registered: {device_info.mac}")
        else:
            return Response.fail(f"{device_info.mac} already registered")
    else:
        db.add(device_info)
        log.info(f"New device registered: {device_info.mac}")
    try:
        await db.flush()
        return Response.success({"id": device_info.id})
    except Exception as e:
        return Response.fail({"error": str(e)})
