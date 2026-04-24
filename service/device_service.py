from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from schemas.response import Response
from VO.DeviceVO import DeviceRegister
from entity.device_info import DeviceInfo
import logging
import ansible_runner
import tempfile

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
        ],
        "dhcp_servers":[
            {
                "pool_name": "pool1",
                "subnet": "192.168.100.0/24",
                "id": "1",
                "gateway": "192.168.100.1",
                "listen_ip": "192.168.12.1",
                "start_ip": "192.168.100.10",
                "end_ip": "192.168.100.254",
            },
            {
                "pool_name": "pool2",
                "subnet": "192.168.200.0/24",
                "id": "2",
                "gateway": "192.168.200.1",
                "listen_ip": "192.168.13.1",
                "start_ip": "192.168.200.10",
                "end_ip": "192.168.200.254",
            }
        ]
    },
    "0c:e7:2f:0d:00:00": {
        "interfaces": [
            {
                "name": "eth1",
                "address": "192.168.12.2/24"
            },
            {
                "name": "eth2",
                "address": "192.168.23.2/24"
            },
            {
                "name": "eth3",
                "address": "192.168.100.1/24"
            }
        ],
        "ospf_areas": [
            {
                "area": "0",
                "networks": [
                    "192.168.12.0/24",
                    "192.168.23.0/24",
                    "192.168.100.0/24"
                ]
            }
        ],
        "dhcp_relay": {
            "servers": [
                "192.168.12.1",
            ],
            "interfaces": [
                "eth3",
                "eth1"
            ]
        }
    },
    "0c:21:dc:c6:00:00": {
        "interfaces": [
            {
                "name": "eth1",
                "address": "192.168.13.3/24"
            },
            {
                "name": "eth2",
                "address": "192.168.23.3/24"
            },
            {
                "name": "eth3",
                "address": "192.168.200.1/24"
            }
        ],
        "ospf_areas": [
            {
                "area": "0",
                "networks": [
                    "192.168.23.0/24",
                    "192.168.13.0/24",
                    "192.168.200.0/24"
                ]
            }
        ],
        "dhcp_relay": {
            "servers": [
                "192.168.13.1",
            ],
            "interfaces": [
                "eth3",
                "eth1"
            ]
        }
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
    playbook_name = "test_playbook.yml"
    playbook_path = base_dir / "playbook" / playbook_name
    print(playbook_path)
    with tempfile.TemporaryDirectory() as tmp_dir:
        r = ansible_runner.run(
            private_data_dir=str(tmp_dir),
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
                "ansible_user": "vyos",
                "ansible_ssh_pass": "vyos",
                "ansible_connection": "network_cli",
                "ansible_network_os": "vyos.vyos.vyos",
                **conf
            }
        )
        if r.rc != 0:
            return Response.fail(r.stderr)
        return Response.success(r.stdout)
