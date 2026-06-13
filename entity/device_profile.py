from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from database.database import Base


class DeviceProfile(Base):
    __tablename__ = "device_profile"
    __table_args__ = (
        UniqueConstraint("device_type", "os_type", name="uq_device_profile_type_os"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    device_type: Mapped[str] = mapped_column(index=True, nullable=False)
    os_type: Mapped[str] = mapped_column(index=True, nullable=False)
    playbook_id: Mapped[int] = mapped_column(ForeignKey("playbook.id"), nullable=False)
    ansible_env_id: Mapped[int] = mapped_column(ForeignKey("ansible_env.id"), nullable=False)
