from typing import Any

from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column

from database.database import Base


class DeviceConfig(Base):
    __tablename__ = "device_config"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    mac: Mapped[str] = mapped_column(index=True, unique=True, nullable=False)
    config_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
