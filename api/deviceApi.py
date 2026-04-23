from pathlib import Path

import ansible_runner
from fastapi import APIRouter, Depends,BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from VO.DeviceVO import DeviceRegister
from schemas.response import Response
from database.database import get_database
from service import device_service
import os

print("deviceApi loaded")

router = APIRouter(
    prefix="/device",
    tags=["device"],
)


@router.post("/register", response_model=Response)
async def register_device(device: DeviceRegister, db: AsyncSession = Depends(get_database)):
    device_info = await device_service.register_device(device, db)
    # if not device_info.id:
    #     return Response.fail()
    await device_service.ansible_test(device.mac,device.ip_address)
    # BackgroundTasks.add_task(device_service.ansible_test, device.mac, device.ip_address)
    return Response.success(device_info)


@router.get("/test")
async def test(ip: str = Path()):
    base_dir = Path(__file__).resolve().parent.parent
    playbook_name = "rawtest.yml"
    playbook_path = base_dir / "playbook" / playbook_name
    print(playbook_path)
    test_json = {
        "interfaces": [
            {
                "name": "eth3",
                "address": "192.168.3.1/24"
            },
            {
                "name": "eth4",
                "address": "192.168.4.1/24"
            }
        ],
        "ospf_areas": [
            {
                "area": "0",
                "networks": ["192.168.3.0/24"]
            },
            {
                "area": "1",
                "networks": ["192.168.4.0/24"]
            }
        ]
    }
    r = ansible_runner.run(
        private_data_dir=str(base_dir),
        playbook=str(playbook_path),
        inventory={
            "all": {
                "hosts": {
                    "vyos_routers": {
                        "ansible_host": ip
                    }
                }
            }
        },
        extravars={
            "ansible_user": "admin",
            "ansible_ssh_pass": "password",
            "ansible_connection": "network_cli",
            "ansible_network_os": "vyos.vyos.vyos",
            **test_json
        }
    )

    if r.rc == 0:
        print("✅ 配置成功")
    else:
        print(f"❌ 失败，状态码: {r.rc}")

    print(f"检测到 Playbook 路径: {playbook_path}")
    return {"test": "test"}
