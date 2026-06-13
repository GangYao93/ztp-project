from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from database.database import Base


class Playbook(Base):
    __tablename__ = "playbook"
    __table_args__ = (
        UniqueConstraint("name", "version", name="uq_playbook_name_version"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    name: Mapped[str] = mapped_column(index=True, nullable=False)
    version: Mapped[int] = mapped_column(nullable=False)
    content: Mapped[str] = mapped_column(nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
