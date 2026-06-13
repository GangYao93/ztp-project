from typing import Any

from sqlalchemy import JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from database.database import Base


class AnsibleEnv(Base):
    __tablename__ = "ansible_env"
    __table_args__ = (
        UniqueConstraint("name", "version", name="uq_ansible_env_name_version"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    name: Mapped[str] = mapped_column(index=True, nullable=False)
    version: Mapped[int] = mapped_column(nullable=False)
    env_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
