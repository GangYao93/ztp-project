from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, select
from schemas.response import Response
from entity.VO.DeviceVO import DeviceRegister
from entity.ansible_env import AnsibleEnv
from entity.device_config import DeviceConfig
from entity.device_info import DeviceInfo
from entity.device_profile import DeviceProfile
from entity.playbook import Playbook
import logging
import ansible_runner
import tempfile

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger("device_service")
# log.format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

ZTP_SSH_COMMON_ARGS = "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o GlobalKnownHostsFile=/dev/null"

DEFAULT_ANSIBLE_USER = "admin"
DEFAULT_ANSIBLE_PASS = "password"


@dataclass
class AnsibleRunConfig:
    config_json: dict[str, Any]
    playbook_name: str
    playbook_version: int
    playbook_content: str
    ansible_env_json: dict[str, Any]


async def register_device(device: DeviceRegister, db: AsyncSession):
    device_data = device.model_dump()
    device_data["ansible_user"] = device.ansible_user or DEFAULT_ANSIBLE_USER
    device_data["ansible_ssh_pass"] = device.ansible_ssh_pass or DEFAULT_ANSIBLE_PASS
    device_info = DeviceInfo(**device_data)
    stmt = select(DeviceInfo).where(DeviceInfo.mac == device_info.mac)
    res = await db.execute(stmt)
    target_device = res.scalars().first()
    if target_device:
        if target_device.ip_address != device.ip_address:
            target_device.ip_address = device_info.ip_address
        log.info(f"Old device refreshed: {device_info.mac}")
        # target_device.status = device.status
        target_device.device_type = device.device_type
        target_device.os_type = device.os_type
        if device.ansible_user is not None or target_device.ansible_user is None:
            target_device.ansible_user = device_info.ansible_user
        if device.ansible_ssh_pass is not None or target_device.ansible_ssh_pass is None:
            target_device.ansible_ssh_pass = device_info.ansible_ssh_pass
    else:
        db.add(device_info)
        log.info(f"New device registered: {device_info.mac}")
    try:
        await db.flush()
        return Response.success({"id": target_device.id if target_device else device_info.id})
    except Exception as e:
        return Response.fail({"error": str(e)})


async def get_ansible_run_config(device: DeviceRegister, db: AsyncSession) -> AnsibleRunConfig | None:
    stmt = (
        select(
            DeviceConfig.config_json,
            Playbook.name,
            Playbook.version,
            Playbook.content,
            AnsibleEnv.env_json,
        )
        .select_from(DeviceConfig)
        .join(
            DeviceProfile,
            and_(
                DeviceProfile.device_type == device.device_type,
                DeviceProfile.os_type == device.os_type,
            )
        )
        .join(Playbook, Playbook.id == DeviceProfile.playbook_id)
        .join(AnsibleEnv, AnsibleEnv.id == DeviceProfile.ansible_env_id)
        .where(DeviceConfig.mac == device.mac)
    )
    res = await db.execute(stmt)
    row = res.first()
    if not row:
        return None

    config_json, playbook_name, playbook_version, playbook_content, ansible_env_json = row
    return AnsibleRunConfig(
        config_json=config_json,
        playbook_name=playbook_name,
        playbook_version=playbook_version,
        playbook_content=playbook_content,
        ansible_env_json=ansible_env_json,
    )


async def ansible_test(device: DeviceRegister, db: AsyncSession):
    stmt = select(DeviceInfo).where(DeviceInfo.mac == device.mac)
    res = await db.execute(stmt)
    device_info = res.scalars().first()
    if not device_info:
        return Response.fail(f"{device.mac} has no device info")
    if not device_info.ansible_user or not device_info.ansible_ssh_pass:
        return Response.fail(f"{device.mac} has no ansible credential")

    run_config = await get_ansible_run_config(device, db)
    if not run_config:
        return Response.fail(f"{device.mac} has no runnable ansible config")

    env = {
        **run_config.ansible_env_json,
        "ansible_user": device_info.ansible_user,
        "ansible_ssh_pass": device_info.ansible_ssh_pass,
        **run_config.config_json
    }
    log.info(f"Playbook: {run_config.playbook_name} v{run_config.playbook_version}")
    log.info(f"env: {env}")
    with tempfile.TemporaryDirectory() as tmp_dir:
        playbook_path = Path(tmp_dir) / "playbook.yml"
        playbook_path.write_text(run_config.playbook_content, encoding="utf-8")
        print(playbook_path)
        r = ansible_runner.run(
            private_data_dir=str(tmp_dir),
            playbook=str(playbook_path),
            inventory={
                "all": {
                    "hosts": {
                        "device": {
                            "ansible_host": device.ip_address,
                            "ansible_ssh_common_args": ZTP_SSH_COMMON_ARGS
                        }
                    }
                }
            },
            envvars={
                "ANSIBLE_HOST_KEY_CHECKING": "False"
            },
            extravars=env
        )
        if r.rc != 0:
            return Response.fail(r.stderr)
        return Response.success(r.stdout)
