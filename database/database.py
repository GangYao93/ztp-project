from datetime import datetime

from sqlalchemy import DateTime, func, select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

DATABASE_URL = "sqlite+aiosqlite:///./ztp.db"

engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    pool_size=10,
    max_overflow=20
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def init_database():
    from entity import ansible_env, device_config, device_info, device_profile, playbook  # noqa: F401
    from database.initial_ansible_envs import INITIAL_ANSIBLE_ENVS
    from database.initial_device_configs import INITIAL_DEVICE_CONFIGS
    from database.initial_device_profiles import INITIAL_DEVICE_PROFILES
    from database.initial_playbooks import INITIAL_PLAYBOOKS
    from entity.ansible_env import AnsibleEnv
    from entity.device_config import DeviceConfig
    from entity.device_profile import DeviceProfile
    from entity.playbook import Playbook

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        for mac, config in INITIAL_DEVICE_CONFIGS.items():
            stmt = select(DeviceConfig.id).where(DeviceConfig.mac == mac)
            existing_id = await session.scalar(stmt)
            if existing_id is None:
                session.add(DeviceConfig(mac=mac, config_json=config))

        for item in INITIAL_PLAYBOOKS:
            stmt = select(Playbook.id).where(
                Playbook.name == item["name"],
                Playbook.version == item["version"]
            )
            existing_id = await session.scalar(stmt)
            if existing_id is None:
                session.add(Playbook(
                    name=item["name"],
                    version=item["version"],
                    content=item["content"],
                    is_active=item["is_active"]
                ))

        for item in INITIAL_ANSIBLE_ENVS:
            stmt = select(AnsibleEnv.id).where(
                AnsibleEnv.name == item["name"],
                AnsibleEnv.version == item["version"]
            )
            existing_id = await session.scalar(stmt)
            if existing_id is None:
                session.add(AnsibleEnv(
                    name=item["name"],
                    version=item["version"],
                    env_json=item["env_json"],
                    is_active=item["is_active"]
                ))

        await session.flush()

        for profile in INITIAL_DEVICE_PROFILES:
            playbook_id = await session.scalar(
                select(Playbook.id).where(
                    Playbook.name == profile["playbook_name"],
                    Playbook.is_active == True
                ).order_by(Playbook.version.desc())
            )
            ansible_env_id = await session.scalar(
                select(AnsibleEnv.id).where(
                    AnsibleEnv.name == profile["env_name"],
                    AnsibleEnv.is_active == True
                ).order_by(AnsibleEnv.version.desc())
            )
            if playbook_id is None or ansible_env_id is None:
                continue

            stmt = select(DeviceProfile).where(
                DeviceProfile.device_type == profile["device_type"],
                DeviceProfile.os_type == profile["os_type"]
            )
            existing_profile = await session.scalar(stmt)
            if existing_profile is None:
                session.add(DeviceProfile(
                    device_type=profile["device_type"],
                    os_type=profile["os_type"],
                    playbook_id=playbook_id,
                    ansible_env_id=ansible_env_id
                ))
            elif (
                existing_profile.playbook_id is None
                or existing_profile.ansible_env_id is None
                or existing_profile.playbook_id != playbook_id
                or existing_profile.ansible_env_id != ansible_env_id
            ):
                existing_profile.playbook_id = playbook_id
                existing_profile.ansible_env_id = ansible_env_id
        await session.commit()


async def get_database():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()

class Base(DeclarativeBase):
    create_time: Mapped[datetime] = mapped_column(DateTime,insert_default=func.now())
    update_time: Mapped[datetime] = mapped_column(DateTime,insert_default=func.now())


# Base = declarative_base()
