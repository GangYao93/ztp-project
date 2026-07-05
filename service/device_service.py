from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fastapi_pagination import Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import String, and_, cast, or_, select
from schemas.response import Response
from entity.VO.DeviceVO import DeviceConfigQuery, DeviceRegister
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
    username = device.username
    password = device.password
    device_data["username"] = username or DEFAULT_ANSIBLE_USER
    device_data["password"] = password or DEFAULT_ANSIBLE_PASS
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
        if username is not None or target_device.username is None:
            target_device.username = device_info.username
        if password is not None or target_device.password is None:
            target_device.password = device_info.password
    else:
        db.add(device_info)
        log.info(f"New device registered: {device_info.mac}")
    try:
        await db.flush()
        return Response.success({"id": target_device.id if target_device else device_info.id})
    except Exception as e:
        return Response.fail({"error": str(e)})


async def list_device_configs(query: DeviceConfigQuery, db: AsyncSession):
    stmt = (
        select(DeviceConfig, DeviceInfo)
        .outerjoin(DeviceInfo, DeviceInfo.mac == DeviceConfig.mac)
        .order_by(DeviceConfig.id.desc())
    )

    filters = []
    if query.mac:
        filters.append(DeviceConfig.mac.like(f"%{query.mac}%"))
    if query.device_type:
        filters.append(DeviceInfo.device_type == query.device_type)
    if query.os_type:
        filters.append(DeviceInfo.os_type == query.os_type)
    if query.status:
        filters.append(DeviceInfo.status == query.status)
    if query.keyword:
        keyword = f"%{query.keyword}%"
        filters.append(
            or_(
                DeviceConfig.mac.like(keyword),
                cast(DeviceConfig.config_json, String).like(keyword),
            )
        )
    if filters:
        stmt = stmt.where(*filters)

    page = await paginate(db, stmt, params=Params(page=query.page, size=query.size))
    items = []
    for row in page.items:
        device_config, device_info = row
        items.append({
            "id": device_config.id,
            "mac": device_config.mac,
            "device_type": device_info.device_type if device_info else None,
            "os_type": device_info.os_type if device_info else None,
            "ip_address": device_info.ip_address if device_info else None,
            "status": device_info.status if device_info else None,
            "config_json": device_config.config_json,
        })

    return Response.success({
        "items": items,
        "total": page.total,
        "page": page.page,
        "size": page.size,
        "pages": page.pages,
    })


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
    if not device_info.username or not device_info.password:
        return Response.fail(f"{device.mac} has no ansible credential")

    run_config = await get_ansible_run_config(device, db)
    if not run_config:
        return Response.fail(f"{device.mac} has no runnable ansible config")

    env = {
        **run_config.ansible_env_json,
        "ansible_user": device_info.username,
        "ansible_ssh_pass": device_info.password,
        **run_config.config_json
    }
    if run_config.ansible_env_json.get("ansible_become_method") == "sudo":
        env["ansible_become_password"] = device_info.password
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
