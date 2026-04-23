from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from schemas.response import Response
from VO.DeviceVO import DeviceRegister
from entity.device_info import DeviceInfo
import logging
import ansible_runner

log = logging.getLogger("device_service")

data = {
    "0c:67:0d:13:00:00": {
        "interfaces": [
            {
                "name": "eth1",
                "address": "192.168.12.1/24"
            },
            {
                "name": "eth2",
                "address": "192.168.13.1/24"
            }
        ],
        "ospf_areas": [
            {
                "area": "0",
                "networks": [
                    "192.168.12.0/24",
                    "192.168.13.0/24"
                ]
            }
        ]
    },
    "0c:e7:2f:0d:00:00": {
        "interfaces": [
            {
                "name": "eth1",
                "address": "192.168.12.1/24"
            },
            {
                "name": "eth2",
                "address": "192.168.23.1/24"
            }
        ],
        "ospf_areas": [
            {
                "area": "0",
                "networks": [
                    "192.168.12.0/24",
                    "192.168.23.0/24"
                ]
            }
        ]
    },
    "0c:21:dc:c6:00:00": {
        "interfaces": [
            {
                "name": "eth1",
                "address": "192.168.13.1/24"
            },
            {
                "name": "eth4",
                "address": "192.168.23.1/24"
            }
        ],
        "ospf_areas": [
            {
                "area": "0",
                "networks": [
                    "192.168.23.0/24",
                    "192.168.13.0/24"
                ]
            }
        ]
    }
}


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


async def ansible_test(mac: str, ip_address: str):

    conf = data[mac]
    if not conf:
        return Response.fail(f"{mac} not registered")
    base_dir = Path(__file__).resolve().parent.parent
    playbook_name = "test2.yml"
    playbook_path = base_dir / "playbook" / playbook_name
    print(playbook_path)
    r = ansible_runner.run(
        private_data_dir=str(base_dir),
        playbook=str(playbook_path),
        inventory={
            "all": {
                "hosts": {
                    "vyos1": {
                        "ansible_host": ip_address
                    }
                }
            }
        },
        extravars={
            "ansible_user": "admin",
            "ansible_ssh_pass": "password",
            "ansible_connection": "network_cli",
            "ansible_network_os": "vyos.vyos.vyos",
            "vlan_desc": "USER_VLAN",
            **conf
        }
    )
    if r.rc != 0:
        return Response.fail(r.stderr)
    return Response.success(r.stdout)
