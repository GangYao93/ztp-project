from fastapi_pagination import Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import String, cast, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from entity.VO.AutomationVO import (
    AnsibleEnvQuery,
    AnsibleEnvSave,
    DeviceProfileQuery,
    DeviceProfileSave,
    PlaybookQuery,
    PlaybookSave,
)
from entity.ansible_env import AnsibleEnv
from entity.device_profile import DeviceProfile
from entity.playbook import Playbook
from schemas.response import Response


def _pagination_data(page, items: list[dict]):
    return {
        "items": items,
        "total": page.total,
        "page": page.page,
        "size": page.size,
        "pages": page.pages,
    }


def _playbook_data(playbook: Playbook):
    return {
        "id": playbook.id,
        "name": playbook.name,
        "version": playbook.version,
        "content": playbook.content,
        "is_active": playbook.is_active,
        "create_time": playbook.create_time,
        "update_time": playbook.update_time,
    }


def _env_data(ansible_env: AnsibleEnv):
    return {
        "id": ansible_env.id,
        "name": ansible_env.name,
        "version": ansible_env.version,
        "env_json": ansible_env.env_json,
        "is_active": ansible_env.is_active,
        "create_time": ansible_env.create_time,
        "update_time": ansible_env.update_time,
    }


def _profile_data(
    profile: DeviceProfile,
    playbook_name: str,
    playbook_version: int,
    env_name: str,
    env_version: int,
):
    return {
        "id": profile.id,
        "device_type": profile.device_type,
        "os_type": profile.os_type,
        "playbook_id": profile.playbook_id,
        "playbook_name": playbook_name,
        "playbook_version": playbook_version,
        "ansible_env_id": profile.ansible_env_id,
        "ansible_env_name": env_name,
        "ansible_env_version": env_version,
        "create_time": profile.create_time,
        "update_time": profile.update_time,
    }


async def list_playbooks(query: PlaybookQuery, db: AsyncSession):
    stmt = select(Playbook).order_by(Playbook.name, Playbook.version.desc())
    filters = []
    if query.name:
        filters.append(Playbook.name.like(f"%{query.name}%"))
    if query.version is not None:
        filters.append(Playbook.version == query.version)
    if query.is_active is not None:
        filters.append(Playbook.is_active == query.is_active)
    if query.keyword:
        keyword = f"%{query.keyword}%"
        filters.append(or_(Playbook.name.like(keyword), Playbook.content.like(keyword)))
    if filters:
        stmt = stmt.where(*filters)

    page = await paginate(db, stmt, params=Params(page=query.page, size=query.size))
    return Response.success(_pagination_data(page, [_playbook_data(item) for item in page.items]))


async def get_playbook(playbook_id: int, db: AsyncSession):
    playbook = await db.get(Playbook, playbook_id)
    if playbook is None:
        return Response.fail({"error": "playbook not found"})
    return Response.success(_playbook_data(playbook))


async def save_playbook(data: PlaybookSave, db: AsyncSession):
    duplicate_stmt = select(Playbook.id).where(
        Playbook.name == data.name,
        Playbook.version == data.version,
    )
    if data.id is not None:
        duplicate_stmt = duplicate_stmt.where(Playbook.id != data.id)
    if await db.scalar(duplicate_stmt) is not None:
        return Response.fail({"error": "playbook name and version already exist"})

    if data.id is None:
        playbook = Playbook()
        db.add(playbook)
        created = True
    else:
        playbook = await db.get(Playbook, data.id)
        if playbook is None:
            return Response.fail({"error": "playbook not found"})
        created = False

    playbook.name = data.name
    playbook.version = data.version
    playbook.content = data.content
    playbook.is_active = data.is_active
    try:
        await db.flush()
        result = _playbook_data(playbook)
        result["created"] = created
        return Response.success(result)
    except Exception as exc:
        await db.rollback()
        return Response.fail({"error": str(exc)})


async def delete_playbook(playbook_id: int, db: AsyncSession):
    playbook = await db.get(Playbook, playbook_id)
    if playbook is None:
        return Response.fail({"error": "playbook not found"})

    profile_ids = list(await db.scalars(
        select(DeviceProfile.id).where(DeviceProfile.playbook_id == playbook_id)
    ))
    if profile_ids:
        return Response.fail({
            "error": "playbook is referenced by device profiles",
            "profile_ids": profile_ids,
        })

    try:
        await db.delete(playbook)
        await db.flush()
        return Response.success({"id": playbook_id})
    except Exception as exc:
        await db.rollback()
        return Response.fail({"error": str(exc)})


async def list_ansible_envs(query: AnsibleEnvQuery, db: AsyncSession):
    stmt = select(AnsibleEnv).order_by(AnsibleEnv.name, AnsibleEnv.version.desc())
    filters = []
    if query.name:
        filters.append(AnsibleEnv.name.like(f"%{query.name}%"))
    if query.version is not None:
        filters.append(AnsibleEnv.version == query.version)
    if query.is_active is not None:
        filters.append(AnsibleEnv.is_active == query.is_active)
    if query.keyword:
        keyword = f"%{query.keyword}%"
        filters.append(
            or_(
                AnsibleEnv.name.like(keyword),
                cast(AnsibleEnv.env_json, String).like(keyword),
            )
        )
    if filters:
        stmt = stmt.where(*filters)

    page = await paginate(db, stmt, params=Params(page=query.page, size=query.size))
    return Response.success(_pagination_data(page, [_env_data(item) for item in page.items]))


async def get_ansible_env(env_id: int, db: AsyncSession):
    ansible_env = await db.get(AnsibleEnv, env_id)
    if ansible_env is None:
        return Response.fail({"error": "ansible env not found"})
    return Response.success(_env_data(ansible_env))


async def save_ansible_env(data: AnsibleEnvSave, db: AsyncSession):
    duplicate_stmt = select(AnsibleEnv.id).where(
        AnsibleEnv.name == data.name,
        AnsibleEnv.version == data.version,
    )
    if data.id is not None:
        duplicate_stmt = duplicate_stmt.where(AnsibleEnv.id != data.id)
    if await db.scalar(duplicate_stmt) is not None:
        return Response.fail({"error": "ansible env name and version already exist"})

    if data.id is None:
        ansible_env = AnsibleEnv()
        db.add(ansible_env)
        created = True
    else:
        ansible_env = await db.get(AnsibleEnv, data.id)
        if ansible_env is None:
            return Response.fail({"error": "ansible env not found"})
        created = False

    ansible_env.name = data.name
    ansible_env.version = data.version
    ansible_env.env_json = data.env_json
    ansible_env.is_active = data.is_active
    try:
        await db.flush()
        result = _env_data(ansible_env)
        result["created"] = created
        return Response.success(result)
    except Exception as exc:
        await db.rollback()
        return Response.fail({"error": str(exc)})


async def delete_ansible_env(env_id: int, db: AsyncSession):
    ansible_env = await db.get(AnsibleEnv, env_id)
    if ansible_env is None:
        return Response.fail({"error": "ansible env not found"})

    profile_ids = list(await db.scalars(
        select(DeviceProfile.id).where(DeviceProfile.ansible_env_id == env_id)
    ))
    if profile_ids:
        return Response.fail({
            "error": "ansible env is referenced by device profiles",
            "profile_ids": profile_ids,
        })

    try:
        await db.delete(ansible_env)
        await db.flush()
        return Response.success({"id": env_id})
    except Exception as exc:
        await db.rollback()
        return Response.fail({"error": str(exc)})


def _profile_select():
    return (
        select(
            DeviceProfile,
            Playbook.name,
            Playbook.version,
            AnsibleEnv.name,
            AnsibleEnv.version,
        )
        .join(Playbook, Playbook.id == DeviceProfile.playbook_id)
        .join(AnsibleEnv, AnsibleEnv.id == DeviceProfile.ansible_env_id)
    )


async def list_device_profiles(query: DeviceProfileQuery, db: AsyncSession):
    stmt = _profile_select().order_by(DeviceProfile.device_type, DeviceProfile.os_type)
    filters = []
    if query.device_type:
        filters.append(DeviceProfile.device_type == query.device_type)
    if query.os_type:
        filters.append(DeviceProfile.os_type == query.os_type)
    if query.playbook_id is not None:
        filters.append(DeviceProfile.playbook_id == query.playbook_id)
    if query.ansible_env_id is not None:
        filters.append(DeviceProfile.ansible_env_id == query.ansible_env_id)
    if query.keyword:
        keyword = f"%{query.keyword}%"
        filters.append(
            or_(
                DeviceProfile.device_type.like(keyword),
                DeviceProfile.os_type.like(keyword),
                Playbook.name.like(keyword),
                AnsibleEnv.name.like(keyword),
            )
        )
    if filters:
        stmt = stmt.where(*filters)

    page = await paginate(db, stmt, params=Params(page=query.page, size=query.size))
    items = [_profile_data(*row) for row in page.items]
    return Response.success(_pagination_data(page, items))


async def get_device_profile(profile_id: int, db: AsyncSession):
    row = (await db.execute(
        _profile_select().where(DeviceProfile.id == profile_id)
    )).first()
    if row is None:
        return Response.fail({"error": "device profile not found"})
    return Response.success(_profile_data(*row))


async def save_device_profile(data: DeviceProfileSave, db: AsyncSession):
    playbook = await db.get(Playbook, data.playbook_id)
    if playbook is None:
        return Response.fail({"error": "playbook not found"})
    ansible_env = await db.get(AnsibleEnv, data.ansible_env_id)
    if ansible_env is None:
        return Response.fail({"error": "ansible env not found"})

    duplicate_stmt = select(DeviceProfile.id).where(
        DeviceProfile.device_type == data.device_type,
        DeviceProfile.os_type == data.os_type,
    )
    if data.id is not None:
        duplicate_stmt = duplicate_stmt.where(DeviceProfile.id != data.id)
    if await db.scalar(duplicate_stmt) is not None:
        return Response.fail({"error": "device type and os type already have a profile"})

    if data.id is None:
        profile = DeviceProfile()
        db.add(profile)
        created = True
    else:
        profile = await db.get(DeviceProfile, data.id)
        if profile is None:
            return Response.fail({"error": "device profile not found"})
        created = False

    profile.device_type = data.device_type
    profile.os_type = data.os_type
    profile.playbook_id = data.playbook_id
    profile.ansible_env_id = data.ansible_env_id
    try:
        await db.flush()
        result = _profile_data(
            profile,
            playbook.name,
            playbook.version,
            ansible_env.name,
            ansible_env.version,
        )
        result["created"] = created
        return Response.success(result)
    except Exception as exc:
        await db.rollback()
        return Response.fail({"error": str(exc)})


async def delete_device_profile(profile_id: int, db: AsyncSession):
    profile = await db.get(DeviceProfile, profile_id)
    if profile is None:
        return Response.fail({"error": "device profile not found"})

    try:
        await db.delete(profile)
        await db.flush()
        return Response.success({"id": profile_id})
    except Exception as exc:
        await db.rollback()
        return Response.fail({"error": str(exc)})
